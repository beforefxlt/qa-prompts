# Factory Inspector (Ubuntu 出厂检测工具)

一套基于 Python 的模块化检测工具，旨在验证 Ubuntu 20.04/22.04 机器在出厂前是否符合预期的硬件、网络和服务配置。

## 📁 目录结构
- `main.py`: 核心启动脚本。
- `config.yaml`: 位于 `factory_inspector/` 目录下的检测标准配置文件（预期值）。
- `core/`: 调度系统，负责加载插件和渲染报告。
- `plugins/builtins/`: 内置插件（硬件、网络、服务）。
- `plugins/custom/`: 允许用户直接添加自定义检测逻辑。
- `tests/`: 单元测试与 Mock 工具。

## 🚀 快速开始

### 1. 安装依赖 (推荐使用虚拟环境)
```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
pip install pyyaml
```

### 2. 运行检测
> [!IMPORTANT]
> 建议从项目根目录执行，以确保插件命名空间对齐。
```bash
python3 factory_inspector/main.py
```

说明：
- 项目已自带一份默认参考配置 `factory_inspector/config.yaml`，可直接复制或原地修改后使用。
- 源码模式下默认读取 `factory_inspector/config.yaml`，不再依赖仓库根目录存在同名配置文件。
- 如果需要切换配置文件，可显式传入 `--config /path/to/your_config.yaml`。

### 2.1 运行回归测试
```bash
python3 factory_inspector/run_tests.py --unit
python3 factory_inspector/run_tests.py --integration
python3 factory_inspector/run_tests.py --all
```

说明：
- `--unit` 会顺序执行基础、失败与边界三组测试，不会因为前一组失败而提前短路。
- 日志相关测试会使用隔离的临时日志文件，避免不同测试之间互相污染。

### 3. (可选) 打包为二进制
在 Ubuntu 环境下执行：
```bash
pip install pyinstaller
pyinstaller --onefile factory_inspector/main.py
./dist/main --config factory_inspector/config.yaml
```

说明：
- 如果是从源码仓库直接验证二进制，可显式指定 `factory_inspector/config.yaml`。
- 如果是独立分发二进制，建议将 `config.yaml` 与二进制放在同一层级，再用 `--config ./config.yaml` 启动。

## 🛠️ 如何添加新检测项？
1. 在 `factory_inspector/plugins/custom/` 目录下创建一个新的 `.py` 文件。
2. 创建一个继承自 `BasePlugin` 的类。
3. 实现 `run(config)` 方法。
4. 在 `factory_inspector/config.yaml` 中添加对应的配置项。

该框架会自动发现并运行您的新插件。
