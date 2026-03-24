import unittest
import json
import os
import sys
from unittest.mock import patch, mock_open

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.plugins.builtins.hardware_plugin import HardwarePlugin
from factory_inspector.plugins.builtins.route_plugin import RoutePlugin
from factory_inspector.plugins.builtins.service_plugin import ServicePlugin

class TestFailureScenarios(unittest.TestCase):
    
    def setUp(self):
        self.hardware_plugin = HardwarePlugin()
        self.route_plugin = RoutePlugin()
        self.service_plugin = ServicePlugin()

    @patch("subprocess.check_output")
    def test_hardware_cpu_failure(self, mock_exec):
        """场景：CPU 核心实测 2 核，但预期 4 核"""
        mock_exec.return_value = b"2\n"
        results = self.hardware_plugin.run({"min_cpu_cores": 4})
        cpu_res = next(r for r in results if "CPU" in r.name)
        
        self.assertFalse(cpu_res.status)
        self.assertEqual(cpu_res.actual, 2)
        self.assertIn("核心数不足", cpu_res.message)

    def test_hardware_memory_failure(self):
        """场景：内存总量实测 4GB，预期 8GB"""
        mock_meminfo = "MemTotal:        4000000 kB\n"
        with patch("builtins.open", mock_open(read_data=mock_meminfo)):
            results = self.hardware_plugin.run({"min_memory_gb": 8})
            mem_res = next(r for r in results if "内存" in r.name)
            
            self.assertFalse(mem_res.status)
            self.assertIn("3.81 GB", mem_res.actual)
            self.assertIn("容量不足", mem_res.message)

    @patch("subprocess.check_output")
    def test_route_multiple_defaults_failure(self, mock_exec):
        """场景：默认路由存在 2 条，但预期最多 1 条"""
        mock_routes = [
            {"dst": "default", "gateway": "192.168.1.1", "dev": "eth0"},
            {"dst": "default", "gateway": "10.0.0.1", "dev": "eth1"}
        ]
        mock_exec.return_value = json.dumps(mock_routes).encode()
        results = self.route_plugin.run({"max_default_routes": 1})
        res = results[0]
        
        self.assertFalse(res.status)
        self.assertIn("数量: 2", res.actual)
        self.assertIn("多余的默认路由", res.message)

    @patch("subprocess.run")
    def test_service_inactive_failure(self, mock_run):
        """场景：服务处于 inactive 状态"""
        # 模拟 systemctl is-active 返回 inactive
        mock_run.return_value = type('obj', (object,), {'stdout': 'inactive\n', 'stderr': ''})
        results = self.service_plugin.run({
            "items": [{"name": "nginx", "check_only": True}]
        })
        res = results[0]
        self.assertFalse(res.status)
        self.assertEqual(res.actual, "inactive")
        self.assertIn("服务当前处于 inactive 状态", res.message)

if __name__ == "__main__":
    unittest.main()
