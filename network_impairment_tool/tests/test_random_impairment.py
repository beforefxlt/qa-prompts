import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import subprocess

# 将被测代码所在目录加入 sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from random_impairment import NetImpairmentManager, check_privileges

class TestNetImpairment(unittest.TestCase):
    def setUp(self):
        self.interface = "eth0"
        self.manager = NetImpairmentManager(self.interface)

    @patch('subprocess.run')
    def test_clean_success(self, mock_run):
        """测试清理逻辑是否正确调用 tc 命令"""
        self.manager.clean()
        mock_run.assert_called_with(f"tc qdisc del dev {self.interface} root", shell=True, check=True, capture_output=True)

    @patch('subprocess.run')
    def test_apply_success(self, mock_run):
        """测试应用损伤逻辑是否正确生成 tc 命令"""
        delay, jitter, loss = 100, 10, 5.0
        self.manager.apply(delay, jitter, loss)
        expected_cmd = f"tc qdisc replace dev {self.interface} root netem delay {delay}ms {jitter}ms distribution normal loss {loss}%"
        mock_run.assert_called_with(expected_cmd, shell=True, check=True, capture_output=True)

    @patch('subprocess.run')
    def test_run_cmd_failure_not_del(self, mock_run):
        """测试常规命令失败时是否打印错误信息而不中断"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "tc", stderr=b"Some error")
        with patch('sys.stdout') as mock_stdout:
            self.manager.run_cmd("tc qdisc add ...")
            # 不应抛出异常，逻辑内已捕获 CalledProcessError

    @patch('subprocess.run')
    def test_check_privileges_root(self, mock_run):
        """测试 root 权限检查 (UID=0)"""
        mock_run.return_value.stdout = b"0\n"
        try:
            check_privileges()
        except SystemExit:
            self.fail("check_privileges() unexpectedly exited with root user")

    @patch('subprocess.run')
    def test_check_privileges_non_root(self, mock_run):
        """测试非 root 权限检查 (UID=1000)"""
        mock_run.return_value.stdout = b"1000\n"
        with self.assertRaises(SystemExit) as cm:
            check_privileges()
        self.assertEqual(cm.exception.code, 1)

    @patch('time.sleep', side_effect=InterruptedError)
    @patch('random_impairment.NetImpairmentManager.apply')
    def test_start_random_loop_success(self, mock_apply, mock_sleep):
        """验证逻辑修复：start_random_loop 能够正常运行并生成随机参数"""
        from random_impairment import DEFAULT_CONFIG
        with self.assertRaises(InterruptedError):
            self.manager.start_random_loop()
        
        mock_apply.assert_called()
        args, _ = mock_apply.call_args
        delay, jitter, loss = args
        self.assertTrue(DEFAULT_CONFIG["delay_ms"][0] <= delay <= DEFAULT_CONFIG["delay_ms"][1])
        self.assertTrue(0 <= jitter < delay)
        self.assertTrue(DEFAULT_CONFIG["loss_percent"][0] <= loss <= DEFAULT_CONFIG["loss_percent"][1])

    @patch('random_impairment.NetImpairmentManager.apply', side_effect=KeyboardInterrupt)
    @patch('random_impairment.NetImpairmentManager.clean')
    def test_keyboard_interrupt_handling(self, mock_clean, mock_apply):
        """验证 Ctrl+C (KeyboardInterrupt) 时是否会自动调用 clean 清理现场"""
        with self.assertRaises(SystemExit) as cm:
            self.manager.start_random_loop()
        self.assertEqual(cm.exception.code, 0)
        mock_clean.assert_called_once()

if __name__ == '__main__':
    unittest.main()
