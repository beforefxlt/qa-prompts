import unittest
import os
import sys
from unittest.mock import patch

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.plugins.builtins.network_plugin import NetworkPlugin
from factory_inspector.plugins.builtins.hardware_plugin import HardwarePlugin
from factory_inspector.core.engine import InspectionEngine

class TestInfrastructureErrors(unittest.TestCase):
    """P3 级：系统基础设施异常测试"""

    def setUp(self):
        self.network_plugin = NetworkPlugin()
        self.hardware_plugin = HardwarePlugin()

    @patch("subprocess.check_output")
    def test_command_not_found_handling(self, mock_exec):
        """P3: 模拟系统缺少 'ip' 命令的情况 (FileNotFoundError)"""
        # 模拟系统找不到命令抛出的 OSError/FileNotFoundError
        mock_exec.side_effect = FileNotFoundError(2, "No such file or directory: 'ip'")
        
        results = self.network_plugin.run({"default_gateway": "192.168.1.1"})
        
        # 预期：不应崩溃，而是返回包含错误信息的失败结果
        self.assertTrue(len(results) > 0)
        error_res = results[0]
        self.assertFalse(error_res.status)
        self.assertIn("失败", error_res.actual)
        self.assertIn("No such file or directory", error_res.message)

    @patch("builtins.open")
    def test_file_permission_denied_handling(self, mock_file_open):
        """P3: 模拟 /proc/meminfo 无权访问的情况 (PermissionError)"""
        mock_file_open.side_effect = PermissionError(13, "Permission denied: '/proc/meminfo'")
        
        results = self.hardware_plugin.run({"min_memory_gb": 8})
        
        # 预期项应该返回 "读取错误"
        mem_res = next((r for r in results if "内存" in r.name), None)
        self.assertIsNotNone(mem_res)
        self.assertFalse(mem_res.status)
        self.assertEqual(mem_res.actual, "读取错误")
        self.assertIn("Permission denied", mem_res.message)

    @patch("builtins.print")
    @patch("logging.FileHandler.__init__")
    def test_logger_initialization_failure(self, mock_handler_init, mock_print):
        """P3: 模拟日志文件目录无写权限导致的初始化。预期引擎不崩溃且正常运行。"""
        # 模拟 logging 无法创建文件引发异常
        mock_handler_init.side_effect = PermissionError("Log directory is read-only")
        
        config_path = "tmp_test_config.yaml"
        with open(config_path, "w") as f:
            f.write("hardware: {min_cpu_cores: 4}\n")
            
        try:
            # 预期：不再抛出 PermissionError，而是打印警告并继续
            engine = InspectionEngine(config_path, log_file="readonly/inspection.log")
            self.assertIsNotNone(engine.logger)
            mock_print.assert_called()
            printed = " ".join(str(arg) for arg in mock_print.call_args[0])
            self.assertIn("无法创建日志文件", printed)
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)

if __name__ == "__main__":
    unittest.main()
