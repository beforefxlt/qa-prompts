# 出厂检测脚本当代架构设计 (Factory Inspection Architecture)

> **目标 (Goal):** 使用 Python 为 Ubuntu 20.04/22.04 构建一套高可靠、可扩展的出厂检测工具。由于检测内容需要作为“插件”不断增加，架构上必须做到**引擎（公共服务端）**、**插件 (Plugins)** 与 **测试 (Tests)** 的严格解耦。

## 1. 核心架构与模块解耦 (Core Architecture & Decoupling)

整个项目被拆分为三个完全独立思考的维度：
1. **公共服务端 (Core Framework/Server)**：只负责“读配置、找插件、调插件、汇总打印”。它不知道任何一条具体的检测逻辑，做到绝对的底层抽象。
2. **插件仓库 (Plugins)**：纯粹的检测执行单元。负责执行系统命令查询真实数据并和预期值对比。它不知道报告最终怎么呈现。
3. **测试套件 (Tests)**：验证服务端调度逻辑与插件逻辑是否正常的独立工程。

### 目录结构规划 (Directory Structure)
```text
factory_inspector/
├── main.py                     # 入口程序 (可被 PyInstaller 打包)
├── config.yaml                 # 检测标准配置文件（如：CPU需>=8核，Nginx需==1.18）
│
├── core/                       # 【模块 1：公共服务端 (Server/Engine)】
│   ├── __init__.py
│   ├── engine.py               # 核心调度器：解析配置、动态发现并加载插件
│   ├── reporter.py             # 报告生成器：负责终端上的红绿彩色输出汇总
│   └── exception.py            # 自定义异常：如 PluginLoadError, CheckFailedException
│
├── plugins/                    # 【模块 2：插件仓库 (Plugins)】
│   ├── __init__.py
│   ├── base.py                 # 插件基类，定义统一接口 `run(expected_item)`
│   ├── hardware_plugin.py      # 硬件检测插件 (CPU, 内存, 硬盘)
│   ├── network_plugin.py       # 网络检测插件 (网卡配置, 默认路由)
│   ├── service_plugin.py       # 服务检测插件 (服务名称, 版本比对)
│   └── custom/                 # 自定义特殊检测脚本目录
│
└── tests/                      # 【模块 3：测试套件 (Tests)】
    ├── __init__.py
    ├── test_engine.py          # 验证公共服务端的插件加载和调度逻辑
    ├── test_hardware.py        # 验证硬件插件在 Mock 数据下的判断正确性
    └── test_network.py         # 验证网络插件的行为
```

### 执行数据流向 (Data Flow)
1. **启动与读取**：执行 `python3 main.py --config config.yaml`。
2. **调度分配**：`core.engine` 解析 YAML，发现 `services` 节点，就唤醒 `plugins.service_plugin`；发现 `hardware` 节点，就唤醒 `plugins.hardware_plugin`。
3. **插件执行**：插件通过 `subprocess` 在本机运行相应 Ubuntu 命令（如 `ip r`, `lscpu`, `systemctl status`），结合传入的 YAML 预期值进行断言。
4. **结果返回与输出**：插件向引擎返回标准化的结果对象，`core.reporter` 在终端输出最终的 `[PASS]` 或 `[FAIL]` 清单。

---

## 2. 并行开发模块拆解 (Parallel Module Breakdown)

为了提高开发效率，我们将项目拆解为以下 5 个可以并行开发或独立验证的编号模块：

### M1: 核心框架与插件基类 (Core Framework & Base)
*   **职责**：实现 `main.py` 入口、`core/engine.py` 调度逻辑、`plugins/base.py` 抽象接口。
*   **关键点**：定义插件如何被发现（importlib）、配置如何传递、结果如何统一返回给引擎。

### M2: 硬件检测插件 (Hardware Plugin)
*   **职责**：实现 CPU 核数、内存总量、硬盘容量及状态的检测。
*   **关键点**：解析 `/proc/cpuinfo`, `/proc/meminfo` 或使用 `lsblk` 命令，处理单位转换（GB/MB）。

### M3: 网络检测插件 (Network Plugin)
*   **职责**：检测指定网卡是否存在、IP是否配置正确、默认路由是否指向预期网关。
*   **关键点**：调用 `ip -j addr` 和 `ip -j route` 获取 JSON 格式输出，进行逻辑比对。

### M4: 服务检测插件 (Service Plugin)
*   **职责**：检查 Ubuntu 系统服务（systemd）的运行状态，并尝试获取其版本号。
*   **关键点**：调用 `systemctl is-active` 以及各服务自带的版本查询命令（如 `nginx -v`）。

### M5: 测试基础设施与 Mock 工具 (Testing & Mocks)
*   **职责**：建立 `pytest` 框架，编写能够模拟系统命令输出的 Mock 工具。
*   **关键点**：确保在非 Ubuntu 环境下也能通过 Mock 验证各插件逻辑，保障代码健壮性。

---
*设计方案已更新。您可以根据编号指定我先开发哪一个，或者要求我同时启动多个模块。*
