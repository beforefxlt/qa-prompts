# Modbus 协议鲁棒性与异常注入测试框架

本工具集旨在为储能系统 (ESS) 的 PCS、BMS 等核心组件提供基于协议层的深度负向测试（Negative Testing）。通过模拟恶意的 Modbus 从站 (Slave) 与高并发客户端，验证受测设备在极端通信环境下的稳定性和安全性。

---

## 1. 设计思路 (Design Philosophy)

本框架采用 **插件化架构 (Plugin-based Architecture)**，将协议引擎与业务规约彻底解耦：
*   **引擎层 (`malicious_simulator.py`)**: 负责异步 IO 处理、Modbus 系列协议编解码以及故障注入算法。
*   **插件层 (`*.json` Profile)**: 负责定义特定设备的寄存器点表、初始值 (Registers/Coils) 以及针对该设备的漏洞蜜罐 (Honeypot) 策略。

---

## 2. 核心能力 (Core Capabilities)

### 2.1 协议全栈覆盖
*   **4 种寄存器类型**: 完整支持线圈 (Coils)、离散输入 (Discrete Inputs)、保持寄存器 (Holding) 及输入寄存器 (Input) 的读写。
*   **关键功能码**: 支持 0x01, 0x02, 0x03, 0x04, 0x05, 0x06 以及工业常用的 **0x10 (写多寄存器)**。

### 2.2 仿真器故障注入模式
*   `HONEYPOT`: 基于配置的数值溢出诱捕。
*   `TRUNCATED`: 报文长度虚假申报与负载截断。
*   `DROP`: 随机或定量的静默丢包与连接拆除。
*   `MISMATCH`: 事务 ID (TID) 篡改导致的数据关联异常。

---

## 3. 实现原理 (Implementation Principles)

*   **异步协程架构**: 基于 `asyncio.start_server`，天然支持高并发连接压测，且具备连接数配额。
*   **状态一致性 (DataStore)**: 仿真器具备内存账本，支持写读闭环验证，模拟正式业务行为。
*   **安全防御机制**: 适配读操作超时保护，防止仿真器本身因恶意报文而挂起。

---

## 4. 推广与收益 (Benefits)

*   **跨设备平移**: 只需更换 JSON 配置文件即可无缝支持 PCS、BMS 或电网接口的测试。
*   **深度隐患挖掘**: 能够探测物理设备难以触发的协议角边场景（如 TID 碰撞、包内截断）。
*   **高度自动化**: 集成 Pytest 测试套件与 Shell 编排任务。

---

## 5. 快速上手

详见 **[操作手册](#4-操作手册)** 章节或查阅深度技术指南：**[docs/DESIGN_ZH.md](./docs/DESIGN_ZH.md)** (即将上线)。

### 5.1 环境启动
```bash
python3 malicious_simulator.py --port 5020 --mode HONEYPOT --config pcs_profile.json
```

---

## 6. 目录结构
*   `malicious_simulator.py`: 通用异常注入引擎。
*   `pcs_profile.json`: PCS 专用插件配置文件。
*   `test_modbus_baseline.py`: 4 寄存器全量基线验证。
*   `run_all_tests.sh`: 一键总控脚本。
