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

---

## 3. 回归测试执行
目前共有 **21** 个自动化测试用例。可以通过以下指令运行全量回归：
```bash
python3 run_tests.py --all
```
