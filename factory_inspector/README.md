# Factory Inspector (Ubuntu 出厂检测工具)

一套基于 Python 的模块化检测工具，旨在验证 Ubuntu 20.04/22.04 机器在出厂前是否符合预期的硬件、网络和服务配置。

## 📁 目录结构
- `main.py`: 核心启动脚本。
- `config.yaml`: 检测标准配置文件（预期值）。
- `core/`: 调度系统，负责加载插件和渲染报告。
- `plugins/builtins/`: 内置插件（硬件、网络、服务）。
- `plugins/custom/`: 允许用户直接添加自定义检测逻辑。
- `tests/`: 单元测试与 Mock 工具。

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install pyyaml
```

### 2. 运行检测
```bash
python3 factory_inspector/main.py --config config.yaml
```

### 3. (可选) 打包为二进制
在 Ubuntu 环境下执行：
```bash
pip install pyinstaller
pyinstaller --onefile factory_inspector/main.py
./dist/main --config config.yaml
```

## 🛠️ 如何添加新检测项？
1. 在 `factory_inspector/plugins/custom/` 目录下创建一个新的 `.py` 文件。
2. 创建一个继承自 `BasePlugin` 的类。
3. 实现 `run(config)` 方法。
4. 在 `config.yaml` 中添加对应的配置项。

该框架会自动发现并运行您的新插件。
