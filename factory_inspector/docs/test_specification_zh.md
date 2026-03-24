# 出厂检测工具 - 测试规格说明书 (Test Specification)

本文档详细描述了 `factory_inspector` 项目回归测试套件中的各个测试用例及其测试点，旨在确保工具在不同场景下的稳定性和可靠性。

## 1. 测试套件概览
目前共有 **16** 个自动化测试用例，涵盖以下五个维度：
- **基础功能 (Basic)**: 典型成功路径验证。
- **异常场景 (Fallures)**: 典型错误与配置不符场景验证。
- **边界值 (Boundary)**: 临界条件逻辑验证。
- **全链路集成 (Integration)**: 核心引擎与多插件协同验证。
- **日志审计 (Logging)**: 原始数据存证能力验证。

---

## 2. 测试用例详情

### 2.1 基础功能测试 (`tests/test_basic.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_hardware_cpu_pass` | 验证当 CPU 核心数满足配置时，插件能正确识别并返回成功。 | Status: True, Actual: 8 | Happy Path |
| `test_hardware_mem_pass` | 验证对 `/proc/meminfo` 的解析逻辑及其向 GB 的转换精度。 | Status: True, Actual: 15.69 GB | Happy Path |
| `test_framework_loading` | 验证项目目录结构（核心引擎、主入口）是否存在。 | 文件存在 | Happy Path |

### 2.2 异常/失败场景测试 (`tests/test_failures.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_hardware_cpu_failure` | 当 CPU 核心数少于配置要求时的拦截能力。 | Status: False, Message: "核心数不足" | Failure Path |
| `test_hardware_memory_failure`| 当物理内存容量低于配置要求时的拦截能力。 | Status: False, Message: "容量不足" | Failure Path |
| `test_route_multiple_defaults_failure` | 验证系统存在多条默认路由时（出厂不合规）的拦截能力。 | Status: False, Message: "多余的默认路由" | Failure Path |
| `test_service_inactive_failure` | 验证当配置的核心服务未运行（inactive）时的拦截能力。 | Status: False, Actual: "inactive" | Failure Path |

### 2.3 边界值分析测试 (`tests/test_boundary.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_cpu_boundary_min` | 验证 CPU 核心数刚好等于临界值 (n) 时。 | Status: True (通过) | Boundary |
| `test_cpu_boundary_min_minus_1` | 验证 CPU 核心数刚好小于临界值 (n-1) 时。 | Status: False (拒绝) | Boundary |
| `test_memory_boundary_min` | 验证内存容量刚好等于临界值 (n.0) 时。 | Status: True (通过) | Boundary |
| `test_route_boundary_max` | 验证默认路由数量刚好等于允许的最大值 (1) 时。 | Status: True (通过) | Boundary |
| `test_route_boundary_max_plus_1`| 验证默认路由数量超过允许的最大值 (1+1) 时。 | Status: False (拒绝) | Boundary |
| `test_version_boundary_min` | 验证服务版本号刚好等于最小要求版本 (Equal) 时。 | Status: True (通过) | Boundary |
| `test_version_boundary_min_minus_1` | 验证服务版本号略低于最小要求版本 (Lower) 时。 | Status: False (拒绝) | Boundary |

### 2.4 全链路与日志测试
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_engine_run_all_flow` | 验证从配置加载、插件自动发现、按序执行到结果汇总的全透明流程。 | 无 Exception, 结果汇总完整 | Integration |
| `test_logger_records_raw_data` | 验证 `inspection.log` 的生成，并确保其捕获了插件的原始命令输出。 | 文件存在, 包含 "CPU 核数原始输出" | Logging |

### 2.5 配置文件异常测试 (`tests/test_config.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_config_not_found` | 验证当指定的 `config.yaml` 路径不存在时，引擎能正确抛出 `FileNotFoundError`。 | 抛出 FileNotFoundError | Failure Path |
| `test_config_invalid_format` | 验证当 `config.yaml` 存在语法错误（非合法 YAML）时，引擎能正确拦截。 | 抛出 YAMLError/Exception | Failure Path |

### 2.6 系统基建异常测试 (P3 - `tests/test_infra_errors.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_command_not_found_handling` | 模拟系统缺失 `ip` 或 `nproc` 等关键命令。 | Status: False, Message 包含 "No such file" | Infra Error |
| `test_file_permission_denied_handling` | 模拟 `/proc/meminfo` 等核心系统文件无权访问。 | Status: False, Actual: "读取错误" | Infra Error |
| `test_logger_initialization_failure` | 模拟日志目录只读，无法创建 `inspection.log`。 | 引擎正常启动，提示警告，不崩溃 | Infra Error |

| `test_logger_initialization_failure` | 模拟日志目录只读，无法创建 `inspection.log`。 | 引擎正常启动，提示警告，不崩溃 | Infra Error |

### 2.7 UT 有效性校验 (Quality Gate - `tests/test_ut_quality.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_intentional_logic_failure` | **防过拟合测试**：故意在单测中对已知失败的结果断言为 True。 | **必须报错** (AssertionError) | Quality Gate |

> [!TIP]
> 上述用例在全量回归时默认跳过。开发人员可手动执行以验证测试套件是否具备识别逻辑错误的能力。

### 2.8 二进制打包与分布测试 (Binary Test - M20)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `binary_compilation_success` | 使用 PyInstaller 将 `main.py` 编译为 single-file 二进制。 | `dist/` 下生成可执行文件 | Packaging |
| `binary_plugin_discovery` | 验证在二进制模式下能否加载同级目录下的 `plugins/`。 | 成功识别并运行内置/自定义插件 | Packaging |

> [!IMPORTANT]
> 在出厂环境中分发二进制时，必须保证 `config.yaml` 和 `plugins/` 文件夹与二进制文件处于同一层级。

### 2.9 MES 外部推送测试 (`MesReporter` - P1 到 P5)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_mes_push_happy_path` | 验证标准 JSON 能成功推送至 MES Mock 接口。 | HTTP 200 OK | P1 |
| `test_mes_auth_failure` | 验证当 Token 错误时检测到 401 并记录错误。 | Status: False, Msg: 401 | P2 |
| `test_mes_payload_truncation` | 验证当插件输出超长日志时，推送内容被自动截断。 | Payload < 限制值 | P2 |
| `test_mes_network_timeout` | 模拟网络极慢（3s+），验证引擎在配置的 2s 超时后自动跳过。 | 不阻塞流程, 报错记录 | P3 |
| `test_mes_dns_error` | 模拟无效的 MES 域名解析失败。 | 报错记录 "DNS 无法解析" | P3 |
| `test_mes_binary_ssl_bundling`| 验证打包后的程序在无 Python 库环境下运行 HTTPS 推送。 | 无 SSL 握手错误 | P5 |
| `test_mes_config_ux` | 故意写错 MES URL 协议头（如 `htxp://`），验证报错是否易读。 | 提示 "URL 格式非法" | P5 |

---

## 3. 回归测试执行
目前共有 **30** 个自动化测试项（包含 29 个代码用例 + 1 个打包流程校验）。可以通过以下指令运行全量回归：
```bash
python3 run_tests.py --all
```
