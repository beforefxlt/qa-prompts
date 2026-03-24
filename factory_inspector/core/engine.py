import importlib
import inspect
import os
import yaml
from pathlib import Path
from typing import List, Dict, Type
from factory_inspector.plugins.base import BasePlugin, CheckResult
from factory_inspector.core.logger import setup_logger, get_logger

class InspectionEngine:
    """核心调度引擎"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config()
        self.plugins: List[BasePlugin] = []
        # 初始化日志
        self.logger = setup_logger()
        self.logger.info(">>> 出厂检测引擎启动，配置路径: %s", config_path)

    def _load_config(self) -> Dict:
        """加载 config.yaml"""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"未找到配置文件: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def discover_plugins(self, plugin_dirs: List[str]):
        """动态发现并加载插件"""
        for d in plugin_dirs:
            p = Path(d)
            print(f"正在扫描插件目录: {d} (绝对路径: {p.absolute()})")
            if not p.exists():
                print(f"⚠️ 警告: 插件目录不存在: {d}")
                self.logger.warning("插件目录不存在: %s", d)
                continue
            
            self.logger.info("正在从目录扫描插件: %s", d)
            
            # 扫描目录下所有的 .py 文件
            for file in p.glob("*.py"):
                if file.name == "__init__.py" or file.name == "base.py":
                    continue
                
                # 动态加载模块
                # 寻找相对于项目根目录的路径
                try:
                    # 使用 resolve() 处理 .. 和 符号链接
                    abs_file = file.resolve()
                    abs_cwd = Path(os.getcwd()).resolve()
                    rel_path = abs_file.relative_to(abs_cwd)
                    module_path = ".".join(rel_path.with_suffix("").parts)
                except ValueError:
                    # 如果不是在当前工作目录下，则采取保守方案
                    module_path = file.stem
                    if "plugins" in str(file):
                        module_path = f"factory_inspector.plugins.{'builtins' if 'builtins' in str(file) else 'custom'}.{file.stem}"

                try:
                    # 调试：打印尝试加载的模块路径
                    print(f"尝试加载插件模块: {module_path}")
                    module = importlib.import_module(module_path)
                    # 查找继承自 BasePlugin 的类
                    for name, obj in inspect.getmembers(module, inspect.isclass):
                        if issubclass(obj, BasePlugin) and obj is not BasePlugin:
                            self.plugins.append(obj())
                            print(f"载入插件: {name}")
                            self.logger.info("已加载插件类: %s (来自 %s)", name, module_path)
                except Exception as e:
                    print(f"无法加载插件 {module_path}: 错误详情: {e}")
                    import traceback
                    # traceback.print_exc() # 暂时不打印堆栈，以免刷屏

    def run_all(self) -> List[CheckResult]:
        """按配置顺序或逻辑顺序运行所有插件"""
        all_results = []
        
        # 依次运行已加载的插件
        for plugin in self.plugins:
            # 根据插件 ID 或名称从配置中获取对应的段落
            # 简化逻辑：插件类名即为配置 Key（转小写）
            config_key = plugin.__class__.__name__.lower().replace("plugin", "")
            plugin_config = self.config.get(config_key, {})
            
            if plugin_config:
                print(f"正在执行检测项: {config_key}...")
                self.logger.info(">>> 开始检测项: %s", config_key)
                results = plugin.run(plugin_config)
                all_results.extend(results)
                self.logger.info("<<< 检测项目 [%s] 完成，项数: %d", config_key, len(results))
            else:
                # 如果没有该插件的配置，默认不运行或跳过
                pass
                
        return all_results
