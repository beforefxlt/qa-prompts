import unittest
import os
import sys
from unittest.mock import patch, MagicMock

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.core.engine import InspectionEngine
from factory_inspector.core.logger import get_logger

class TestLoggingModule(unittest.TestCase):
    """日志模块集成测试"""

    def setUp(self):
        self.log_file = "test_inspection.log"
        if os.path.exists(self.log_file):
            os.remove(self.log_file)
        
        self.test_config_path = "test_config_logging.yaml"
        with open(self.test_config_path, "w") as f:
            f.write("hardware: {min_cpu_cores: 1}\n")
            
        # 初始化引擎 (会自动触发 setup_logger)
        with patch("factory_inspector.core.logger.setup_logger") as mock_setup:
            # 实际上我们想测真实的 logger，所以不完全 mock
            pass

    def tearDown(self):
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)
        if os.path.exists("inspection.log"):
            # 引擎默认写到 inspection.log
            pass

    @patch("subprocess.check_output")
    def test_logger_records_raw_data(self, mock_exec):
        """测试日志是否记录了原始数据"""
        mock_exec.return_value = b"4\n"
        
        # 强制重新配置日志到当前目录
        from factory_inspector.core.logger import setup_logger
        setup_logger("inspection.log")
        
        engine = InspectionEngine(self.test_config_path)
        # 发现 hardware 插件
        base_dir = os.path.dirname(os.path.abspath(__file__))
        engine.discover_plugins([os.path.join(base_dir, "../plugins/builtins")])
        
        # 运行
        engine.run_all()
        
        # 验证文件是否存在
        self.assertTrue(os.path.exists("inspection.log"))
        
        # 验证内容
        with open("inspection.log", "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("出厂检测引擎启动", content)
            self.assertIn("[Hardware] CPU 核数原始输出: 4", content)

if __name__ == "__main__":
    unittest.main()
