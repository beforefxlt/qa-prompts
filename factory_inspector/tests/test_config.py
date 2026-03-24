import unittest
import os
import sys
import yaml

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.core.engine import InspectionEngine

class TestConfigExceptions(unittest.TestCase):
    """验证配置文件相关的异常处理"""

    def test_config_not_found(self):
        """测试：尝试加载不存在的配置文件"""
        with self.assertRaises(FileNotFoundError):
            InspectionEngine("non_existent_config.yaml")

    def test_config_invalid_format(self):
        """测试：加载格式错误的 YAML 配置文件"""
        invalid_yaml_path = "invalid_format.yaml"
        with open(invalid_yaml_path, "w") as f:
            # 写入非法的 YAML (例如不匹配的缩进或非法字符)
            f.write("hardware:\n  min_cpu_cores: : invalid\n")
            
        try:
            with self.assertRaises(Exception): # yaml.YAMLError 或其他解析错误
                InspectionEngine(invalid_yaml_path)
        finally:
            if os.path.exists(invalid_yaml_path):
                os.remove(invalid_yaml_path)

if __name__ == "__main__":
    unittest.main()
