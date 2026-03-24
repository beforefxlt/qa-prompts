# Ubuntu 出厂检测脚本用户说明书 (User Manual)

## 1. 产品概述
本工具是一套基于 Python 的模块化出厂检测框架，专门用于 Ubuntu 20.04/22.04 环境下的裸机或系统检测。它能够自动化验证硬件配置、网络设置、服务状态等是否符合预设的标准，并提供直观的彩色汇总报告。

### 1.1 核心价值
- **标准化**: 确保每一台出厂机器的配置完全一致。
- **自动化**: 一键运行，秒级完成数十项人工检查。
- **可扩展**: 采用插件化设计，可根据新机型需求快速增加检测项。

---

## 2. 环境要求
- **操作系统**: Ubuntu 20.04 或 22.04 (推荐)
- **软件依赖**: 
  - Python 3.8 或更高版本
  - `python3-yaml` 库 (用于读写配置)
  - 常用系统命令: `ip`, `systemctl`, `nproc`, `lsblk`, `df`

---

## 3. 安装与部署

### 3.1 获取文件
将得到的 `factory_inspector_v3.zip` 传输并解压到目标主机：
```bash
unzip factory_inspector_v3.zip
cd factory_inspector
```

### 3.2 安装依赖
```bash
sudo apt update
sudo apt install python3-yaml -y
```

---

## 4. 配置指南 (`config.yaml`)
通过修改根目录下的 `config.yaml` 来定义检测标准。

### 4.1 硬件检测 (`hardware`)
| 参数名 | 说明 | 示例值 |
| :--- | :--- | :--- |
| `min_cpu_cores` | 最小 CPU 核心数 | 4 |
| `min_memory_gb` | 最小内存总量 (Unit: GB) | 8 |
| `min_disk_gb` | 最小磁盘总量 (Unit: GB) | 100 |

### 4.2 网络检测 (`network`)
- `interfaces`: 列表形式，可检查多个网卡名称及对应的 IP 前缀。
- `default_gateway`: 预期的默认路由网关地址。

### 4.3 默认路由数量 (`route`)
- `max_default_routes`: 允许的最大默认路由条数（默认为 1）。

### 4.4 服务检测 (`service`)
- `items`: 列表形式，包含服务名、最低版本号或是否仅检查运行状态。

---

## 5. 操作规程

### 5.1 运行检测
```bash
python3 main.py --config config.yaml
```

### 5.2 结果判定
- **[PASS] (绿色)**: 该单项完全符合 `config.yaml` 设定。
- **[FAIL] (红色)**: 该单项不符合标准。在报告最下方会给出“原因”，如“核心数不足”或“版本过低”。

---

---

## 6. 高级：开发与添加新检测项 (Plugin Development)
本工具采用**热插拔插件架构**。当有新的出厂检测需求时（例如：检查 License 文件、特定硬件序列号），您无需修改核心引擎，只需按以下步骤操作：

### 6.1 插件开发规范
1. **存放位置**: 在 `factory_inspector/plugins/custom/` 目录下创建一个新的 `.py` 文件（如 `security_plugin.py`）。
2. **继承基类**: 类必须继承自 `factory_inspector.plugins.base.BasePlugin`。
3. **实现接口**: 必须实现 `run(self, config: dict) -> list[CheckResult]` 方法。
4. **命名约定**: 推荐类名以 `Plugin` 结尾。

### 6.2 核心数据结构
插件必须返回一个 `CheckResult` 列表，该对象包含：
- `name`: 检测项名称。
- `status`: 布尔值（True 为通过）。
- `expected`: 预期值（用于报告展示）。
- `actual`: 实际值（用于报告展示）。
- `message`: (可选) 失败时的详细描述。

### 6.3 实战示例：开发一个“文件检查”插件 (FileCheckPlugin)
假设需要检查 `/etc/license.key` 是否存在：

**第一步：编写插件代码** (`plugins/custom/file_plugin.py`)
```python
import os
from factory_inspector.plugins.base import BasePlugin, CheckResult

class FileCheckPlugin(BasePlugin):
    def run(self, config: dict) -> list[CheckResult]:
        results = []
        path = config.get("path")
        exists = os.path.exists(path)
        
        results.append(CheckResult(
            name=f"文件[{path}]存在性检查",
            status=exists,
            expected="文件应存在",
            actual="存在" if exists else "缺失",
            message="" if exists else f"路径 {path} 下未找到必要文件"
        ))
        return results
```

**第二步：更新配置文件** (`config.yaml`)
在 YAML 中添加一个与类名对应的字段（全部小写且去掉 Plugin 后缀）：
```yaml
filecheck:
  path: "/etc/license.key"
```

**第三步：运行检测**
```bash
python3 main.py
```
框架会自动扫描 `custom/` 目录，加载 `FileCheckPlugin` 并根据配置进行调度。

---

## 7. 回归测试管理 (Regression Testing)
为了保障产品在后续迭代（如添加新插件、修改核心逻辑）时不破坏原有功能，工具内置了统一的回归测试管理器 `run_tests.py`。

### 7.1 分阶段测试
您可以根据开发阶段选择运行特定类型的测试：
- **单元测试**: 验证插件的基础逻辑、异常处理和边界值。
  ```bash
  python3 run_tests.py --unit
  ```
- **集成测试**: 验证从配置加载到插件发现、全路径执行的完整链路。
  ```bash
  python3 run_tests.py --integration
  ```

### 7.2 全量测试
在发布新版本前，建议运行全量回归测试以确保 100% 的功能覆盖：
```bash
python3 run_tests.py --all
```

---

## 9. 日志管理 (Logging)
为了方便事后审计和故障排查，工具会自动将所有检测过程中的“原始打印信息”记录到日志文件中。

### 9.1 日志文件
- **文件名**: `inspection.log` (默认在运行目录下生成)
- **记录内容**:
    - 核心引擎的启动与插件加载过程。
    - **原始监测数据**: 例如 `nproc` 的输出、`/proc/meminfo` 的前几行、`ip addr` 的完整 JSON、以及服务状态的具体返回字符串。

### 9.2 查看日志
如果您对某项检测结果有疑问，可以随时查看日志：
```bash
cat inspection.log
```

---

## 10. 故障排除与常见问题
- **Q: 提示 `No such file or directory: 'ip'`?**
  - A: 确保您在 Linux 环境下运行，并安装了 `iproute2` 工具包。
- **Q: 提示 `ModuleNotFoundError: No module named 'yaml'`?**
  - A: 请执行 `sudo apt install python3-yaml`。
- **Q: 如何修改输出格式？**
  - A: 目前默认输出到终端。后续可扩展 `core/reporter.py` 以支持 JSON 输出。
