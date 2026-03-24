import unittest
import os
import sys

# 确保可以导入项目模块
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from factory_inspector.plugins.builtins.hardware_plugin import HardwarePlugin

class TestUTValidity(unittest.TestCase):
    """
    故意制造的异常用例，用于验证测试套件的有效性（防止过拟合）。
    该文件中的测试在正常回归中不应通过。
    """

    @unittest.skip("这是一个故意的失败示例，手动执行以验证测试套件捕获错误的能力")
    def test_intentional_logic_failure(self):
        """
        故意制造逻辑断言失败：
        验证如果插件返回结果与预期不符，测试框架是否能如实报错。
        """
        plugin = HardwarePlugin()
        # 故意制造一个不可能达到的预期（如 999 核）
        results = plugin.run({"min_cpu_cores": 999})
        cpu_res = next(r for r in results if "CPU" in r.name)
        
        # 故意写错断言：明知 status 是 False，却断言它是 True
        # 如果这个测试 PASS 了，说明测试套件“过拟合”或 Mock 逻辑有问题
        self.assertTrue(cpu_res.status, "【过拟合警报】预期失败但测试却通过了！")

if __name__ == "__main__":
    unittest.main()
