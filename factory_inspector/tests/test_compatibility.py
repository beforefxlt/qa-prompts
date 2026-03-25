import unittest
import os
import sys

class TestPythonCompatibility(unittest.TestCase):
    """
    针对 Ubuntu 20.04 (Python 3.8) 默认环境的兼容性测试。
    验证核心插件文件是否包含 'from __future__ import annotations'
    以此支持 Python 3.9+ 的类型标注语法（如 list[T], dict[K, V]）。
    """

    def setUp(self):
        # 定义需要检查兼容性头部的文件列表
        self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.files_to_check = [
            os.path.join(self.base_dir, "plugins", "base.py"),
            os.path.join(self.base_dir, "plugins", "builtins", "hardware_plugin.py"),
            os.path.join(self.base_dir, "plugins", "builtins", "network_plugin.py"),
            os.path.join(self.base_dir, "plugins", "builtins", "route_plugin.py"),
            os.path.join(self.base_dir, "plugins", "builtins", "service_plugin.py"),
        ]

    def test_future_annotations_present(self):
        """检查关键源文件是否包含兼容性 import"""
        missing_files = []
        for file_path in self.files_to_check:
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                if "from __future__ import annotations" not in content:
                    missing_files.append(os.path.basename(file_path))
        
        self.assertEqual(len(missing_files), 0, 
                         f"以下文件缺少兼容 Python 3.8 的头部声明: {missing_files}")

    def test_no_incompatible_syntax(self):
        """
        扫描是否有其他 Python 3.8 不支持的常见新语法。
        例如 match 语句 (3.10+) 或 Union 类型 X | Y (3.10+)。
        """
        import re
        incompatible_regex = {
            r"^\s*match\s+.*:": "Python 3.10+ match/case 语法",
            r"^\s*case\s+.*:": "Python 3.10+ match/case 语法",
            r"\w+\s*\|\s*\w+": "Python 3.10+ Union 类型语法 (X | Y)"
        }
        
        found_issues = []
        for file_path in self.files_to_check:
            if not os.path.exists(file_path):
                continue
            
            with open(file_path, "r", encoding="utf-8") as f:
                for line_no, line in enumerate(f, 1):
                    # 简单检查，排除注释掉的代码
                    if line.strip().startswith("#"):
                        continue
                        
                    for pattern, desc in incompatible_regex.items():
                        if re.search(pattern, line):
                            # 对 Union 类型进行二次确认，排除位运算或字符串拼接
                            if "|" in pattern:
                                # 如果是类型提示中的 | (通常在 def 或 -> 之后)
                                if ":" in line or "->" in line:
                                    found_issues.append(f"{os.path.basename(file_path)}:{line_no}: {desc}")
                            else:
                                found_issues.append(f"{os.path.basename(file_path)}:{line_no}: {desc}")
        
        self.assertEqual(len(found_issues), 0, 
                         f"检测到 Python 3.8 可能不支持的语法: {found_issues}")

if __name__ == "__main__":
    unittest.main()
