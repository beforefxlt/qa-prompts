import unittest
import os
import sys
import tempfile
from unittest.mock import patch

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.core.engine import InspectionEngine
class TestLoggingModule(unittest.TestCase):
    """日志模块集成测试"""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "inspection.log")
        self.test_config_path = os.path.join(self.temp_dir.name, "test_config_logging.yaml")
        with open(self.test_config_path, "w", encoding="utf-8") as f:
            f.write("hardware: {min_cpu_cores: 1}\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("subprocess.check_output")
    def test_logger_records_raw_data(self, mock_exec):
        """测试日志是否记录了原始数据"""
        mock_exec.return_value = b"4\n"

        engine = InspectionEngine(self.test_config_path, log_file=self.log_file)
        # 发现 hardware 插件
        base_dir = os.path.dirname(os.path.abspath(__file__))
        engine.discover_plugins([os.path.join(base_dir, "../plugins/builtins")])
        
        # 运行
        engine.run_all()
        
        # 验证文件是否存在
        self.assertTrue(os.path.exists(self.log_file))
        
        # 验证内容
        with open(self.log_file, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("出厂检测引擎启动", content)
            self.assertIn("[Hardware] CPU 核数原始输出: 4", content)

if __name__ == "__main__":
    unittest.main()
