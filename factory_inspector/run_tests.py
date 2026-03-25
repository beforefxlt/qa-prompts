import unittest
import argparse
import os
import sys

def run_tests(pattern="test_*.py"):
    """使用 unittest Discovery 运行指定模式的测试"""
    loader = unittest.TestLoader()
    start_dir = os.path.join(os.path.dirname(__file__), "tests")
    suite = loader.discover(start_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_test_patterns(patterns):
    """顺序运行多组测试，不因前一组失败而短路。"""
    success = True
    for pattern in patterns:
        success = run_tests(pattern) and success
    return success

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="出厂检测脚本 - 回归测试管理工具")
    parser.add_argument("--unit", action="store_true", help="只运行单元测试 (基础, 失败, 边界)")
    parser.add_argument("--integration", action="store_true", help="只运行全链路集成测试")
    parser.add_argument("--all", action="store_true", help="运行所有测试用例 (默认)")
    
    args = parser.parse_args()
    
    # 确定测试模式
    if args.unit:
        print(">>> 启动阶段 1: 单元测试 (Unit Tests)...")
        success = run_test_patterns([
            "test_basic.py",
            "test_failures.py",
            "test_boundary.py",
        ])
    elif args.integration:
        print(">>> 启动阶段 2: 集成测试 (Integration Tests)...")
        success = run_tests("test_integration.py")
    else:
        print(">>> 启动全量回归测试 (Full Regression)...")
        success = run_tests("test_*.py")
        
    if success:
        print("\n✅ 回归测试全部通过！")
        sys.exit(0)
    else:
        print("\n❌ 回归测试中存在失败项，请检查！")
        sys.exit(1)
