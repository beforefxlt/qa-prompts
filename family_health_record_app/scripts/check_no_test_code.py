"""
检查生产代码中是否包含测试专用逻辑
用法: python scripts/check_no_test_code.py [目录]
"""
import os
import sys
import re

# 禁止的模式
FORBIDDEN_PATTERNS = [
    # 文件名检查逻辑
    (r'if\s+["\'](?:test|e2e|mock|stub)["\'].*in.*(?:filename|file_url|url|path)', 
     "包含文件名/URL检查测试标识的逻辑"),
    
    # 环境变量检查返回mock
    (r'if\s+os\.getenv\(["\'](?:ENV|TEST|MOCK|DEBUG)["\'].*==.*["\'](?:test|true|1)["\']\).*return.*mock',
     "环境变量检查返回mock数据"),
    
    # 硬编码的测试数据（常见值）
    (r'(?:24\.35|23\.32|126\.0|25\.0).*#.*(?:test|mock|example|sample)',
     "硬编码的测试数据"),
    
    # TODO移除标记
    (r'#\s*(?:TODO|FIXME|HACK).*remove.*(?:before|for)\s*(?:production|release|deploy)',
     "TODO移除标记（不应存在于生产代码）"),
    
    # 明确的mock返回
    (r'return\s+\{.*["\'](?:mock|fake|stub|dummy|test).*["\']',
     "返回mock/fake数据"),
]

# 白名单文件（可以包含测试逻辑的文件）
WHITELIST_PATTERNS = [
    r'tests?/',
    r'test_.*\.py$',
    r'.*_test\.py$',
    r'.*\.spec\.(?:ts|js)$',
    r'.*\.test\.(?:ts|js)$',
    r'conftest\.py$',
    r'fixtures?/',
    r'mocks?/',
    r'__mocks__/',
]

# 白名单目录
WHITELIST_DIRS = ['tests', 'test', '__tests__', 'e2e', 'spec', 'mocks', '__mocks__', 'fixtures']


def is_whitelisted(filepath: str) -> bool:
    """检查文件是否在白名单中"""
    for pattern in WHITELIST_PATTERNS:
        if re.search(pattern, filepath, re.IGNORECASE):
            return True
    return False


def check_file(filepath: str) -> list:
    """检查单个文件"""
    violations = []
    
    if is_whitelisted(filepath):
        return violations
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for pattern, description in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line, re.IGNORECASE):
                        violations.append({
                            'file': filepath,
                            'line': line_num,
                            'content': line.strip()[:100],
                            'reason': description
                        })
    except Exception as e:
        print(f"警告: 无法读取文件 {filepath}: {e}", file=sys.stderr)
    
    return violations


def scan_directory(directory: str) -> list:
    """扫描目录"""
    all_violations = []
    
    for root, dirs, files in os.walk(directory):
        # 跳过白名单目录
        dirs[:] = [d for d in dirs if d not in WHITELIST_DIRS and not d.startswith('.')]
        
        for file in files:
            if file.endswith(('.py', '.ts', '.js', '.tsx', '.jsx')):
                filepath = os.path.join(root, file)
                violations = check_file(filepath)
                all_violations.extend(violations)
    
    return all_violations


def main():
    # 路径解析逻辑：优先使用参数，否则使用相对于脚本位置的后端目录
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
    
    if len(sys.argv) > 1:
        target_dir = sys.argv[1]
    else:
        # 兼容旧逻辑：如果脚本在 family_health_record_app/scripts，则 ../backend/app
        # 如果脚本在根目录/scripts，则 ../family_health_record_app/backend/app
        default_backend = os.path.join(PROJECT_ROOT, 'backend', 'app')
        if os.path.exists(default_backend):
            target_dir = default_backend
        else:
            # 兜底：尝试从脚本当前目录出发
            target_dir = os.path.join(SCRIPT_DIR, '..', 'backend', 'app')
    
    if not os.path.exists(target_dir):
        print(f"错误: 目录不存在 {target_dir}", file=sys.stderr)
        sys.exit(1)
    
    print(f"扫描目录: {target_dir}")
    print("-" * 60)
    
    violations = scan_directory(target_dir)
    
    if violations:
        print(f"\n[FAIL] 发现 {len(violations)} 个违规:\n")
        for v in violations:
            print(f"文件: {v['file']}")
            print(f"行号: {v['line']}")
            print(f"原因: {v['reason']}")
            print(f"内容: {v['content']}")
            print("-" * 40)
        
        print(f"\n总计: {len(violations)} 个违规")
        print("\n请移除生产代码中的测试逻辑，或将其移至 tests/ 目录")
        sys.exit(1)
    else:
        print("\n[PASS] 未发现测试逻辑混入生产代码")
        sys.exit(0)


if __name__ == "__main__":
    main()
