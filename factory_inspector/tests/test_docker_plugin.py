import unittest
from unittest.mock import patch, MagicMock
from factory_inspector.plugins.builtins.docker_plugin import DockerPlugin
from factory_inspector.plugins.base import CheckResult

class TestDockerPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = DockerPlugin()
        self.config = {
            "items": [
                {"name": "test_container_1", "image_tag": "v1.0.0"},
                {"name": "test_container_2"}
            ]
        }

    @patch("subprocess.run")
    def test_run_success(self, mock_run):
        # 模拟 docker ps 输出 (Names, Status, Image)
        mock_run.return_value.stdout = (
            "test_container_1\tUp 2 hours\tharbor.local/test:v1.0.0\n"
            "test_container_2\tUp 5 minutes\tharbor.local/test2:latest\n"
        )
        mock_run.return_value.returncode = 0
        
        results = self.plugin.run(self.config)
        
        # 每个容器 1 个运行状态检查 + 1 个版本检查(如果配置了)
        # test_container_1 -> 状态, 版本
        # test_container_2 -> 状态
        self.assertEqual(len(results), 3)
        
        # 验证运行状态
        self.assertTrue(results[0].status) # test_container_1 Up
        self.assertTrue(results[2].status) # test_container_2 Up
        
        # 验证版本
        self.assertTrue(results[1].status) # v1.0.0 match

    @patch("subprocess.run")
    def test_run_container_missing(self, mock_run):
        mock_run.return_value.stdout = "other_container\tUp 1 hour\timage:tag\n"
        mock_run.return_value.returncode = 0
        
        results = self.plugin.run(self.config)
        # test_container_1 缺失 -> 1个结果
        # test_container_2 缺失 -> 1个结果
        self.assertEqual(len(results), 2)
        self.assertFalse(results[0].status)
        self.assertIn("缺失", results[0].actual)

    @patch("subprocess.run")
    def test_run_container_exited(self, mock_run):
        mock_run.return_value.stdout = "test_container_1\tExited (1) 10 minutes ago\timage:tag\n"
        mock_run.return_value.returncode = 0
        
        # 只测 test_container_1
        results = self.plugin.run({"items": [{"name": "test_container_1"}]})
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0].status)
        self.assertIn("Exited", results[0].actual)

if __name__ == "__main__":
    unittest.main()
