---
name: protocol-fuzzing-test
version: v1.0.0
last_updated: 2026-03-24
description: Guide for executing TDD-based Fuzzing on industrial protocols (Modbus, CAN). Detects parsing vulnerabilities via baseline validation and negative injection (Honeypot, Drop storm, Truncated, Mismatch).
---

# Protocol Fuzzing Agent Skill

A layered fault-injection framework for testing the robustness of industrial protocol drivers (Modbus TCP/RTU, CAN) used in PCS, BMS, and other field equipment. Combines a configuration-driven Python simulator with industry-standard tools (Go Native Fuzzing, Toxiproxy) to systematically uncover fatal stability bugs.

## 🧰 Bundled Tools
The `scripts/` directory of this skill contains:
- `malicious_simulator.py` — Configuration-driven Modbus TCP protocol responder & injector
- `pcs_profile.json` / `bms_profile.json` — Sample device anomaly profiles
- `test_malicious_simulator.py` / `test_bms_fuzzing.py` — TDD test suites

## When to Use
- Testing stability of a new device integration (BMS, PCS, inverter, meter)
- User asks to "fuzz", "stress test", or "simulate anomalies" against a protocol stack
- Evaluating boundary conditions or error handling of a data acquisition program

## Core Philosophy
> **"You must prove the simulator is flawless before claiming the target is broken."**
> Baseline (Positive) validation is mandatory before any Negative/Malicious campaign.

---

## 🏗 Layered Testing Architecture

All fault injection MUST be organized into three decoupled layers:

| Layer | Target | What to Break | Recommended Tool |
|-------|--------|---------------|-----------------|
| **L1 — Parsing** | Memory safety & decoding | Slice OOB, type overflow, malformed PDU | Go Native Fuzz (`go test -fuzz`), malicious_simulator TRUNCATED mode |
| **L2 — Interaction** | State machine & transactions | TID mismatch, concurrent request isolation, session pollution | malicious_simulator MISMATCH mode + concurrent goroutine harness |
| **L3 — Link** | TCP/serial bus resilience | Half-open connections, bandwidth starvation, reconnect deadlocks, **Slave Congestion** | **Toxiproxy** (preferred), malicious_simulator DROP/DELAY mode |

---

## 🛠 Standard Operating Procedure (SOP)

### Phase 1: Code Review & Profile Generation
1. **Analyze Target Source Code** — Look for:
   - `data[idx:idx+2]` without length guard → L1 Slice OOB
   - `float64` → `uint16` direct cast with scaling → L1 Type overflow
   - `mutex.Lock()` inside reconnect retry loop → L3 Deadlock
   - No `conn.SetDeadline()` on TCP read → L3 Goroutine leak
2. **Draft Fuzzing Profile** — Create `<device>_profile.json`:
   - `honeypots`: addresses vulnerable to overflow, with `threshold_max`
   - `truncation`: fake MBAP length + dirty payload hex for block reads

### Phase 2: Baseline (Positive) Verification
1. Boot simulator in neutral mode, verify correct responses for valid traffic
2. Assert: write echo OK, read returns correct register count, zero false alerts
3. **Do NOT proceed to negative campaigns if Baseline fails**

### Phase 3: Negative Fuzz Campaign (by Layer)

#### L1 — Parsing Layer Attacks

**Mode 1: HONEYPOT (Type Overflow)**
- Python simulator detects when client sends overflow values (> `threshold_max`)
- Validates that upstream business logic lacks pre-cast boundary checks

**Mode 3: TRUNCATED (Slice Out-of-Bounds)**
- Fabricates MBAP header with inflated length, sends partial payload then FIN
- For Go targets: **prefer Go Native Fuzzing** — guide user to write:
  ```go
  func FuzzModbusDecoder(f *testing.F) {
      // Seed corpus: valid MBAP header + dirty payload
      f.Add([]byte{0x00,0x01, 0x00,0x00, 0x00,0x06, 0x01, 0x03, 0x20, 0xAA, 0xBB})
      f.Fuzz(func(t *testing.T, data []byte) {
          DecodeModbusFrame(data) // must not panic
      })
  }
  ```
  This pins crashes to exact source lines, far more precise than network-level injection.

> [!IMPORTANT]
> **Context-Aware Corpus Strategy**: Pure random byte mutation gets trapped at header validation and never reaches deep business logic (e.g., type casting). Seeds MUST use **"valid Header + dirty Payload"** structure. Use Go Fuzzing's dictionary feature (`-fuzz-dict`) to constrain mutations to payload boundary values and type-overflow ranges, concentrating compute on the code paths that actually matter.

#### L2 — Interaction Layer Attacks

**Mode 4: MISMATCH (Transaction Decoupling)**
- Tampers Transaction ID on response (+999 offset)
- **Enhanced: Concurrent State Machine Test** — spawn N goroutines sending parallel requests through a single Modbus handle; simulator delays/reorders 10% of responses. Assert: no cross-talk (A must never receive B's data).
- **Bundled Harness**: See `scripts/l2_concurrency_test.go` for a ready-to-adapt Go test scaffold (50 goroutines × 100 requests, TID isolation + latency assertions + pprof Block Profile export). Replace the mock section with your actual `ModbusClient` call.

> [!WARNING]
> **Connection Pool Observability Gap**: Correct TID correlation alone is insufficient. Coarse-grained Mutex in the connection pool may cause goroutine queuing congestion under high-frequency dispatch (e.g., EMS/AGC power commands at 100ms intervals), degrading real-time control responsiveness even without data cross-talk.
>
> **Required Metrics**: During L2 concurrent tests, enable `go tool pprof` Block Profile and monitor:
> - Modbus Client internal wait-queue depth
> - Goroutine blocking duration on Mutex acquisition
> - P99 round-trip latency per transaction under load
>
> Assert: blocking time must stay below control-cycle period; queue depth must not grow unbounded.

#### L3 — Link Layer Attacks

**Mode 2: DROP STORM (Connection Thrashing)**
- Lightweight: Python simulator drops connection after N packets
- **Production-grade alternative: Toxiproxy**
  ```bash
  # Insert proxy between Go client and real/simulated device
  toxiproxy-cli create modbus_proxy -l 0.0.0.0:5020 -u <device>:502
  # Inject toxic: reset connection after 5KB transferred
  toxiproxy-cli toxic add modbus_proxy -t limit_data -a bytes=5000
  # Inject toxic: 2000ms latency to trigger deadline exceeded
  toxiproxy-cli toxic add modbus_proxy -t latency -a latency=2000
  ```
- **Assertions**: Mutex released within configured timeout; Goroutine count must not grow unbounded; no `panic` in logs.

**Mode 5: CONGESTION (Sluggish Response)**
- Use `--delay <seconds>` to simulate a device that takes longer to respond than the polling cycle (e.g., 0.5s cycle vs 1.0s response).
- Use `--max-conns <N>` to simulate hardware connection limits (e.g., BMS can only handle 1-2 concurrent Modbus sessions).
- **Assertions**: Client must implement **Cycle-Dropping** (skip new scan if previous is pending) or **Strict Timeouts**. Failure to do so leads to "Task Stacking" and resource exhaustion on the slave.

> [!CAUTION]
> **Closed-Loop Deployment Constraint**: When using Toxiproxy with injected latency (e.g., `latency=2000`), physical network jitter between separate hosts compounds on top of the injected delay. This causes `conn.SetDeadline()` triggers to shift unpredictably, producing **flaky test results**.
>
> **Mandatory**: Deploy the target process, Toxiproxy proxy, and device simulator within the **same loopback network** (same Pod, same host `127.0.0.1`, or same Docker bridge). This guarantees deterministic fault injection timing and eliminates environmental noise from test assertions.

### Phase 4: Protocol-Specific Considerations

#### Modbus TCP
- Focus: TCP stream boundary handling (sticky/half packets), `io.ReadFull` edge cases
- Focus: TCP Keepalive / Reconnect backoff logic
- Focus: MBAP Transaction ID pool isolation under concurrency

#### CAN Bus
- Replace Mode 2 (DROP) with **Frame Flood / Bus Load Spiking** (CAN has no TCP connections)
- Focus: DLC length forgery, arbitration priority spoofing, Bus-Off injection
- Focus: Broadcast storm causing receiver buffer overflow

### Phase 5: Issue Reporting
- Document exact reproduction steps for any crash/hang/data poisoning
- Remediation constraints (examples):
  - _"Add `if len(data) < expected` before slice access"_
  - _"Validate domain limits before `uint16` narrowing"_
  - _"Set `conn.SetDeadline()` on every TCP read to prevent goroutine leak"_
  - _"Wrap reconnect in backoff with mutex timeout guard"_
