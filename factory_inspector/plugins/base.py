from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any

@dataclass
class CheckResult:
    """出厂检测单项结果数据类"""
    name: str           # 检测项名称 (如 "CPU核数")
    status: bool        # 是否通过 (True: PASS, False: FAIL)
    expected: Any       # 预期值
    actual: Any         # 实际值
    message: str = ""   # 详细说明/错误信息

class BasePlugin(ABC):
    """检测插件基类"""
    
    def __init__(self):
        self.plugin_id: str = self.__class__.__name__

    @abstractmethod
    def run(self, config: dict) -> list[CheckResult]:
        """
        运行检测逻辑。
        
        :param config: 从 config.yaml 传进来的该插件对应的配置片段
        :return: CheckResult 列表
        """
        pass
