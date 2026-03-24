import unittest
import json
import os
import sys
from unittest.mock import patch, MagicMock

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.core.engine import InspectionEngine

class TestFullChainIntegration(unittest.TestCase):
    """全链路集成测试：从配置加载到插件执行与结果汇总"""

    def setUp(self):
        # 1. 准备一个测试用的配置文件路径
        self.test_config_path = os.path.join(os.path.dirname(__file__), "test_config_integration.yaml")
        with open(self.test_config_path, "w", encoding="utf-8") as f:
            f.write("""
hardware:
  min_cpu_cores: 4
  min_memory_gb: 8
route:
  max_default_routes: 1
service:
  items:
    - name: "nginx"
      min_version: "1.18.0"
""")
        
        # 2. 初始化引擎并发现内置插件
        self.engine = InspectionEngine(self.test_config_path)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        builtin_dir = os.path.join(base_dir, "../plugins/builtins")
        self.engine.discover_plugins([builtin_dir])

    def tearDown(self):
        if os.path.exists(self.test_config_path):
            os.remove(self.test_config_path)

    @patch("subprocess.check_output")
    @patch("subprocess.run")
    def test_engine_run_all_flow(self, mock_run, mock_check_output):
        """测试核心引擎运行全流程，模拟各种系统命令返回"""
        
        # 模拟各种命令的返回值 (Side Effect)
        def side_effect_check_output(cmd, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            if "nproc" in cmd_str:
                return b"8\n" # 8核 (PASS)
            if "ip -j route" in cmd_str:
                return json.dumps([{"dst": "default", "gateway": "192.168.1.1"}]).encode() # 1条路由 (PASS)
            if "lsblk" in cmd_str or "df" in cmd_str:
                return b"100G\n"
            return b""

        def side_effect_run(cmd, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            # 模拟 nginx 状态
            if "is-active nginx" in cmd_str:
                return MagicMock(stdout="active\n", stderr="", returncode=0)
            # 模拟 nginx 版本号
            if "nginx -v" in cmd_str:
                return MagicMock(stdout="", stderr="nginx version: nginx/1.18.0\n", returncode=0)
            return MagicMock(stdout="", stderr="", returncode=0)

        mock_check_output.side_effect = side_effect_check_output
        mock_run.side_effect = side_effect_run

        # 执行全项检测
        results = self.engine.run_all()

        # 验证结果汇总数量 (期待：CPU, 内存, 路由, Nginx状态, Nginx版本)
        # 注意：内存检测读取的是 /proc/meminfo，无法通过 subprocess mock，
        # 在非 Linux 环境下会因找不到文件报 [FAIL]，这也是集成测试的一部分。
        self.assertTrue(len(results) >= 4)
        
        # 验证 CPU 检测通过 (由于 mock 了 nproc)
        cpu_res = next((r for r in results if "CPU" in r.name), None)
        self.assertIsNotNone(cpu_res)
        self.assertTrue(cpu_res.status)

        # 验证 路由检测通过 (由于 mock 了 ip route)
        route_res = next((r for r in results if "路由" in r.name), None)
        self.assertIsNotNone(route_res)
        self.assertTrue(route_res.status)

        # 验证 Nginx 状态通过 (由于 mock 了 systemctl)
        nginx_res = next((r for r in results if "nginx" in r.name.lower() and "状态" in r.name), None)
        self.assertIsNotNone(nginx_res)
        self.assertTrue(nginx_res.status)

if __name__ == "__main__":
    unittest.main()
