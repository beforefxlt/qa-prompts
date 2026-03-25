# Modbus 脆弱性靶机 (Vulnerable Target) 操作指南

## 1. 靶机定位
为了验证 `modbus_anomaly_test` 框架对真实协议漏洞的探测能力，我们提供了一个具备“故意缺陷”的仿真ターゲット：`vulnerable_target.py`。
它不像普通的 Fuzzer 只是产生异常，而是真实模拟了一个“写得烂”的设备，在受到特定攻击时会发生挂死、内存溢出或响应乱序。

## 2. 插件化架构设计 (New Archi)

为了提高漏洞扩展性，靶机已重构为与 Fuzzer Engine 2.0 对齐的插件化架构：
- **核心引擎 (`vulnerable_target.py`)**: 仅负责 TCP 管理与基础协议解析。
- **漏洞上下文 (`TargetContext`)**: 存储 TID、PDU、连接状态等关键信息。
- **漏洞插件 (`vulnerabilities/`)**: 每一个 BUG 都是一个独立插件类，通过生命周期钩子接入处理流程：
    - `on_connect`: 修改连接行为（如 BUG_LEAK）。
    - `on_mbap_parsed`: 拦截头部解析（如 BUG_STACK）。
    - `on_pdu_received`: 处理请求逻辑（如 BUG_OOB, BUG_HONEYPOT）。
    - `on_response_prepared`: 篡改响应内容（如 BUG_MISMATCH）。
    - `on_send`: 变更传输时序（如 BUG_DELAY）。

## 3. 内置漏洞模式 (Bugs)

### 3.1 BUG_OOB (缓冲区越界/内存溢出)
- **源码**: `vulnerabilities/oob_crash_plugin.py`
- **触发条件**: 客户端请求读取寄存器数量 > 10。
- **故障表现**: 返回非法的 Junk Data 并强制断开 Socket。

### 3.2 BUG_LEAK (连接泄露/资源枯竭)
- **源码**: `vulnerabilities/leak_plugin.py`
- **触发条件**: 活动连接数超过 5 个。
- **故障表现**: 第 6 个连接进入后不再响应数据（HANGING）。

### 3.3 BUG_STACK (解析器深度挂起)
- **源码**: `vulnerabilities/stack_hang_plugin.py`
- **触发条件**: 接收到的 MBAP Length > 200，但无足够后续数据。
- **故障表现**: 靶机协议解析协程进入无限等待。

### 3.4 BUG_HONEYPOT (数值逻辑陷阱)
- **源码**: `vulnerabilities/honeypot_plugin.py`
- **触发条件**: 读取地址 6000-6100 的寄存器。
- **故障表现**: 强制返回 `0xFFFF`。

### 3.5 BUG_MISMATCH (事务 ID 篡改)
- **源码**: `vulnerabilities/mismatch_plugin.py`
- **触发条件**: 任何请求。
- **故障表现**: 响应的 TID 将与请求不一致。

### 3.6 BUG_DELAY (响应时延/抖动)
- **源码**: `vulnerabilities/delay_plugin.py`
- **触发条件**: 任何请求。
- **故障表现**: 增加 0.5s - 3.0s 的随机延迟。

## 4. 闭环验证流程

1.  **启动靶机**:
    ```bash
    ./venv/bin/python vulnerable_target.py --port 5021 --bug BUG_OOB
    ```
2.  **运行探测脚本**:
    ```bash
    ./venv/bin/pytest test_vulnerable_repro.py
    ```
3.  **预期结果**: 探测脚本应能捕获到非标准响应或连接超时。

---
*版本: v1.1.0 (Pluggable Archi)*  
*维护者: QA 团队 / Antigravity*

