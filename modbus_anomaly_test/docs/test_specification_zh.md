# Modbus 协议异常测试 - 测试规格说明书 (TCS)

本文档定义了 `modbus_anomaly_test` 工具集的测试维度与验证标准，遵循 P1-P5 测试模型。

## 1. 测试维度定义 (P1-P5)

| 维度 | 定义 | 核心测试点 |
| :--- | :--- | :--- |
| **P1 (核心路径)** | 业务可用性金标准 | 4种寄存器类型读写、0x10指令原子性、逻辑闭锁验证。 |
| **P2 (数据异常)** | 深度负向注入 | 协议栈极值溢出、非法数值篡改、数据类型强制冲突。 |
| **P3 (环境/时序)** | 物理链路健壮性 | 链路闪断、响应抖动注入、并发配额与资源争抢。 |
| **P4 (规约边界)** | 协议红线合规性 | MBAP 长度字段欺骗、报文不完整截断、TID 隔离失效（串话）。 |
| **P5 (交付视角)** | 稳定性与场景堆叠 | 组合攻击 (极值+延迟)、长时压力 (Soak) 下的系统漂移评估。 |

---

## 2. 自动化测试用例详情

### 2.1 基础功能测试 (`test_modbus_baseline.py`)
- **TC-BASE-001**: 验证 0x10 多寄存器原子性写入与 DataStore 全局状态更新。
- **TC-BASE-002**: 验证线圈 (Coils) 与 离散输入 (DI) 的位操作准确性。

### 2.2 协议模糊测试 (`test_modbus_anomaly.py`)
- **TC-ANOM-001 (Truncated)**: 模拟 MBAP Length > TCP Payload，观察主轴解析是否死锁。
- **TC-ANOM-002 (Mismatch)**: 响应 TID 与 请求 TID 偏移，验证主站的事务匹配逻辑。

### 2.3 并发与稳定性测试 (`test_modbus_soak.py`)
- **TC-SOAK-001 (Slow Response)**: 设置 5s 延迟，以 2s 频率查询，验证 TCP 连接句柄是否会出现指数级泄露。
- **TC-SOAK-002 (Task Accumulation)**: 观察在高频叠加请求下，系统是否会出现数据包序错乱。

### 2.4 架构 2.0 混合攻击 (`verify_v2.py`)
- **TC-V2-001 (Mixed)**: 叠加执行 `OversizedPayload` (512B) 与 `SlowTickling` (1B/Segment)，验证极致网络环境下的协议栈重组能力。
- **TC-V2-002 (Pluggable Archi)**: 验证 `VulnerableTarget` 的漏洞插件按需加载机制，具备 Hook 注入能力的架构稳定性 (P5)。

---

## 3. 执行指南
全量验证所有 P1-P5 场景：
```bash
./run_all_tests.sh
```

*版本: v1.1.0 (Pluggable Archi)*  
*最后更新: 2026-03-25*
