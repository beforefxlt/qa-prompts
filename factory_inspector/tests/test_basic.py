import unittest
import os
import sys
from unittest.mock import MagicMock, patch, mock_open

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.core.engine import InspectionEngine
from factory_inspector.core.reporter import ConsoleReporter
from factory_inspector.plugins.builtins.hardware_plugin import HardwarePlugin

class TestHardwareBasic(unittest.TestCase):
    """基础硬件插件功能测试"""

    def setUp(self):
        self.plugin = HardwarePlugin()

    @patch("subprocess.check_output")
    def test_hardware_cpu_pass(self, mock_exec):
        """测试 CPU 检测正常通过场景"""
        mock_exec.return_value = b"8\n"
        results = self.plugin.run({"min_cpu_cores": 4})
        cpu_res = next(r for r in results if "CPU" in r.name)
        self.assertTrue(cpu_res.status)
        self.assertEqual(cpu_res.actual, 8)

    def test_hardware_mem_pass(self):
        """测试内存检测正常通过场景"""
        mock_data = "MemTotal:       16457124 kB\n"
        with patch("builtins.open", mock_open(read_data=mock_data)):
            results = self.plugin.run({"min_memory_gb": 8})
            mem_res = next(r for r in results if "内存" in r.name)
            self.assertTrue(mem_res.status)
            self.assertIn("15.69 GB", mem_res.actual)

class TestFrameworkBasic(unittest.TestCase):
    """框架基础集成测试"""
    
    def test_framework_core_modules_importable(self):
        """验证核心模块可导入且导出的主类型可实例化/引用"""
        self.assertTrue(callable(InspectionEngine))
        self.assertTrue(callable(ConsoleReporter))

if __name__ == "__main__":
    unittest.main()
