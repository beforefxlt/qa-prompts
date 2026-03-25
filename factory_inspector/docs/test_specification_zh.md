# 出厂检测工具 - 测试规格说明书 (Test Specification)

本文档详细描述了 `factory_inspector` 项目回归测试套件中的各个测试用例及其测试点，旨在确保工具在不同场景下的稳定性和可靠性。

## 1. 测试套件概览
目前共有 **27** 个自动化测试用例，涵盖以下六个维度：
- **基础功能 (Basic)**: 典型成功路径验证。
- **异常场景 (Fallures)**: 典型错误与配置不符场景验证。
- **边界值 (Boundary)**: 临界条件逻辑验证。
- **全链路集成 (Integration)**: 核心引擎与多插件协同验证。
- **日志审计 (Logging)**: 审计与原始输出记录验证。
- **容器化检测 (Docker)**: 针对大储控制器的 Docker 服务健康度验证。

---

## 2. 测试用例详情

### 2.1 基础功能测试 (`tests/test_basic.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_hardware_cpu_pass` | 验证当 CPU 核心数满足配置时，插件能正确识别并返回成功。 | Status: True, Actual: 8 | Happy Path |
| `test_hardware_mem_pass` | 验证对 `/proc/meminfo` 的解析逻辑及其向 GB 的转换精度。 | Status: True, Actual: 15.69 GB | Happy Path |
| `test_framework_core_modules_importable` | 验证核心模块 (`InspectionEngine`, `ConsoleReporter`) 可被稳定导入，测试入口具备最小运行能力。 | 类型可导入 | Happy Path |

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
| `test_engine_run_all_flow` | 验证从配置加载、插件自动发现、按序执行到结果汇总的全透明流程，并通过 mock 隔离宿主机内存/磁盘环境差异。 | 无 Exception, 返回 6 条完整结果 | Integration |
| `test_logger_records_raw_data` | 验证日志文件的生成，并确保其捕获了插件的原始命令输出；测试使用隔离临时目录，避免全局 logger 污染。 | 文件存在, 包含 "CPU 核数原始输出" | Logging |

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

### 2.10 环境兼容性测试 (`tests/test_compatibility.py`)
| 用例名称 | 测试点 | 预期结果 | 类型 |
| :--- | :--- | :--- | :--- |
| `test_future_annotations_present` | 验证核心插件文件是否包含 `from __future__ import annotations` 头部。 | 头部存在 | Compatibility |
| `test_no_incompatible_syntax` | 静态扫描代码中是否存在 Python 3.10+ 的语法（如 `match` 或 `|` 联合类型）。 | 无高版本语法风险 | Compatibility |

### 2.11 Docker 容器化检测 (`DockerPlugin`)
| 用例名称 | 测试点 | 预期结果 | 分类标签 |
| :--- | :--- | :--- | :--- |
| `test_docker_happy_path` | 验证配置中的容器处于 `Up` 状态且镜像标签匹配的黄金路径。 | Status: True, Actual: "Up", "Match" | P1 |
| `test_docker_container_missing` | 验证当配置的必要容器不存在时的拦截能力。 | Status: False, Message: "缺失" | P2 |
| `test_docker_container_stopped` | 验证当容器处于 `Exited` 状态时的拦截与状态显示。 | Status: False, Actual: "Exited" | P2 |
| `test_docker_tag_mismatch` | 验证容器镜像版本不符合 `image_tag` 要求时的拦截能力。 | Status: False, Message: "镜像版本不匹配" | P2 |
| `test_docker_daemon_down` | **基建容错**：模拟 Docker 服务未启动（Connection Refused）时的异常处理。 | Status: False, Message: "运行失败或未安装" | P3 |
| `test_docker_no_permission` | **权限风险**：模拟当前用户无权执行 `docker ps` 时的拦截能力。 | Status: False, Message 包含 "Permission denied" | P3 |
| `test_docker_cmd_not_found` | **依赖缺失**：模拟系统中未安装 Docker CLI 导致命令无法找到。 | Status: False, Message 包含 "not found" | P3 |
| `test_docker_tag_partial_match` | **边界值**：验证标签子串匹配逻辑（如 `v1.1` 匹配 `myimage:v1.1.2`）。 | Status: True (子串匹配成功) | P4 |
| `test_docker_empty_config` | **边界值**：验证当 `items` 配置为空列表时，插件应不报错且返回空结果。 | 返回空结果列表, 无 Error | P4 |
| `test_docker_error_feedback` | **交付体验**：验证当基础环境失败时，输出的错误信息是否具备自解释性。 | Message 清晰指向根因 | P5 |
| `test_docker_offline_run` | **交付体验**：验证在完全离线环境下，插件读取本地容器元数据的稳定性。 | 运行正常, 无网络请求依赖 | P5 |

---

## 3. 回归测试执行
目前共有 **27** 个自动化测试项。可以通过以下指令运行全量回归：
```bash
# 推荐从项目根目录执行
python3 factory_inspector/run_tests.py --all
```

补充说明：
- `python3 run_tests.py --unit` 会顺序执行 `test_basic.py`、`test_failures.py`、`test_boundary.py`，不会因为某一组失败而提前跳过后续组。
- 日志与集成测试已收紧为“尽量不依赖宿主机真实环境”，用于提升回归信号稳定性。
