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

class TestBoundaryScenarios(unittest.TestCase):
    
    def setUp(self):
        self.hardware_plugin = HardwarePlugin()
        self.route_plugin = RoutePlugin()
        self.service_plugin = ServicePlugin()

    # --- Hardware BVA ---
    
    @patch("subprocess.check_output")
    def test_cpu_boundary_min(self, mock_exec):
        """BVA: CPU 正好等于最小值 (Valid Boundary)"""
        mock_exec.return_value = b"4\n"
        results = self.hardware_plugin.run({"min_cpu_cores": 4})
        res = next(r for r in results if "CPU" in r.name)
        self.assertTrue(res.status, "4核应满足配置要求")

    @patch("subprocess.check_output")
    def test_cpu_boundary_min_minus_1(self, mock_exec):
        """BVA: CPU 小于最小有效值 1 (Invalid Boundary)"""
        mock_exec.return_value = b"3\n"
        results = self.hardware_plugin.run({"min_cpu_cores": 4})
        res = next(r for r in results if "CPU" in r.name)
        self.assertFalse(res.status, "3核不应满足4核配置要求")

    def test_memory_boundary_min(self):
        """BVA: 内存正好等于最小值 (Valid Boundary)"""
        # 8GB = 8388608 KB
        mock_meminfo = "MemTotal:        8388608 kB\n"
        with patch("builtins.open", mock_open(read_data=mock_meminfo)):
            results = self.hardware_plugin.run({"min_memory_gb": 8})
            res = next(r for r in results if "内存" in r.name)
            self.assertTrue(res.status, "8.0GB 应满足 8GB 配置")

    # --- Route BVA ---

    @patch("subprocess.check_output")
    def test_route_boundary_max(self, mock_exec):
        """BVA: 默认路由正好等于最大允许值 (Valid Boundary)"""
        mock_routes = [{"dst": "default", "gateway": "192.168.1.1"}]
        mock_exec.return_value = json.dumps(mock_routes).encode()
        results = self.route_plugin.run({"max_default_routes": 1})
        self.assertTrue(results[0].status, "1条默认路由应允许")

    @patch("subprocess.check_output")
    def test_route_boundary_max_plus_1(self, mock_exec):
        """BVA: 默认路由超过最大允许值 1 (Invalid Boundary)"""
        mock_routes = [
            {"dst": "default", "gateway": "192.168.1.1"},
            {"dst": "default", "gateway": "10.0.0.1"}
        ]
        mock_exec.return_value = json.dumps(mock_routes).encode()
        results = self.route_plugin.run({"max_default_routes": 1})
        self.assertFalse(results[0].status, "2条默认路由不应允许")

    # --- Service Version BVA ---

    @patch("subprocess.run")
    def test_version_boundary_min(self, mock_run):
        """BVA: 版本正好等于最小值 (Valid Boundary)"""
        # 模拟 nginx 状态 active
        mock_run.side_effect = [
            type('obj', (object,), {'stdout': 'active\n', 'stderr': ''}), # 状态检查
            type('obj', (object,), {'stdout': '', 'stderr': 'nginx version: nginx/1.18.0\n'}) # 版本检查
        ]
        results = self.service_plugin.run({
            "items": [{"name": "nginx", "min_version": "1.18.0"}]
        })
        ver_res = next(r for r in results if "版本" in r.name)
        self.assertTrue(ver_res.status, "1.18.0 应通过 1.18.0 校验")

    @patch("subprocess.run")
    def test_version_boundary_min_minus_1(self, mock_run):
        """BVA: 版本略小于最小值 (Invalid Boundary)"""
        mock_run.side_effect = [
            type('obj', (object,), {'stdout': 'active\n', 'stderr': ''}),
            type('obj', (object,), {'stdout': '', 'stderr': 'nginx version: nginx/1.17.9\n'})
        ]
        results = self.service_plugin.run({
            "items": [{"name": "nginx", "min_version": "1.18.0"}]
        })
        ver_res = next(r for r in results if "版本" in r.name)
        self.assertFalse(ver_res.status, "1.17.9 不应通过 1.18.0 校验")

if __name__ == "__main__":
    unittest.main()
