import argparse
import sys
import os

# 将当前目录加入 Python 路径以支持 factory_inspector 导入
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from factory_inspector.core.engine import InspectionEngine
from factory_inspector.core.reporter import ConsoleReporter

def main():
    parser = argparse.ArgumentParser(description="Factory Inspection Tool - Ubuntu 20.04/22.04")
    parser.add_argument("--config", default="config.yaml", help="Path to config.yaml")
    parser.add_argument("--plugin-dir", action="append", help="Extra plugin directories")
    args = parser.parse_args()

    # 1. 确定运行环境与路径 (支持 PyInstaller 编译后的环境)
    if getattr(sys, 'frozen', False):
        # 如果是编译后的二进制文件，base_dir 为二进制文件所在目录
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
        # 确保二进制文件所在目录在 Python 路径中，以便加载外部插件
        parent_dir = os.path.dirname(base_dir)
        if base_dir not in sys.path:
            sys.path.append(base_dir)
        if parent_dir not in sys.path:
            sys.path.append(parent_dir)
    else:
        # 源码运行
        base_dir = os.path.dirname(os.path.abspath(__file__))

    builtin_plugin_dir = os.path.join(base_dir, "plugins", "builtins")
    custom_plugin_dir = os.path.join(base_dir, "plugins", "custom")

    # 2. 初始化引擎
    try:
        engine = InspectionEngine(args.config)
        reporter = ConsoleReporter()
    except Exception as e:
        print(f"初始化失败: {e}")
        sys.exit(1)

    # 3. 发现插件
    plugin_paths = [builtin_plugin_dir, custom_plugin_dir]
    if args.plugin_dir:
        plugin_paths.extend(args.plugin_dir)
    
    engine.discover_plugins(plugin_paths)

    # 4. 执行并上报
    print("开始进行出厂检测...")
    results = engine.run_all()
    
    if not results:
        print("未执行任何检测项，请检查配置文件与插件目录。")
        sys.exit(0)

    reporter.report(results)

if __name__ == "__main__":
    main()
