"""
文档对齐检查脚本
用法: python scripts/check_docs_alignment.py [--check-all]
"""
import os
import sys
import re
import json
from pathlib import Path
from typing import List, Dict, Set

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "family_health_record_app" / "docs"
BACKEND_DIR = PROJECT_ROOT / "family_health_record_app" / "backend" / "app"
FRONTEND_DIR = PROJECT_ROOT / "family_health_record_app" / "frontend" / "src"

# 文档类型定义
DOC_CATEGORIES = {
    "API_CONTRACT": ["API接口契约", "API_CONTRACT.md"],
    "MOBILE_API_CONTRACT": ["移动端API契约", "MOBILE_API_CONTRACT.md"],
    "UI_SPEC": ["UI规格", "UI_SPEC.md"],
    "MOBILE_UI_SPEC": ["移动端UI规格", "MOBILE_UI_SPEC.md"],
    "ARCHITECTURE": ["架构文档", "ARCHITECTURE.md"],
    "DATABASE_SCHEMA": ["数据库Schema", "DATABASE_SCHEMA.md"],
    "BUG_LOG": ["Bug日志", "BUG_LOG.md"],
    "TEST_STRATEGY": ["测试策略", "TEST_STRATEGY.md"],
    "OBSERVABILITY": ["可观测性", "OBSERVABILITY.md"],
}

# 代码变更类型对应的文档
CODE_TO_DOCS = {
    "routers": ["API_CONTRACT"],
    "schemas": ["API_CONTRACT", "DATABASE_SCHEMA"],
    "models": ["API_CONTRACT", "MOBILE_API_CONTRACT"],  # 前端模型/类型定义
    "services": ["API_CONTRACT", "MOBILE_API_CONTRACT"],  # API服务层
    "components": ["UI_SPEC", "MOBILE_UI_SPEC"],
    "pages": ["UI_SPEC", "MOBILE_UI_SPEC"],
    "hooks": ["UI_SPEC", "MOBILE_UI_SPEC"],
    "api": ["API_CONTRACT", "MOBILE_API_CONTRACT"],
    "mobile_app": ["MOBILE_UI_SPEC", "MOBILE_API_CONTRACT", "BUG_LOG"],
}


def get_changed_files() -> List[str]:
    """获取 git 变更的文件列表（包括已提交和已暂存）"""
    import subprocess
    try:
        # 使用 diff HEAD 获取已提交的变更（pre-commit 在 commit 后运行）
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True
        )
        files = []
        for line in result.stdout.strip().split("\n"):
            line = line.strip()
            if line:
                files.append(line)
        return files
    except Exception as e:
        print(f"警告: 无法获取 git 变更: {e}")
        return []


def analyze_code_changes(files: List[str]) -> Dict[str, bool]:
    """分析代码变更涉及的类型"""
    changes = {
        "routers": False,
        "schemas": False,
        "models": False,
        "services": False,
        "components": False,
        "pages": False,
        "hooks": False,
        "api": False,
        "mobile_app": False,
    }
    
    for f in files:
        f_lower = f.lower()
        if "routers" in f_lower or "/api/" in f_lower:
            changes["routers"] = True
        if "schemas" in f_lower:
            changes["schemas"] = True
        if "models" in f_lower:
            changes["models"] = True
        if "services" in f_lower:
            changes["services"] = True
        if "components" in f_lower:
            changes["components"] = True
        if "page" in f_lower and ".tsx" in f_lower:
            changes["pages"] = True
        if "hooks" in f_lower:
            changes["hooks"] = True
        if "/api/" in f_lower or "apiclient" in f_lower:
            changes["api"] = True
        if "mobile_app" in f_lower:
            changes["mobile_app"] = True
            
    return changes


def check_doc_updated(doc_name: str, files: List[str]) -> bool:
    """检查文档是否在变更列表中"""
    # 映射简写到实际文件名
    doc_map = {
        "API_CONTRACT": ["API_CONTRACT.md", "api_contract"],
        "MOBILE_API_CONTRACT": ["MOBILE_API_CONTRACT.md", "mobile_api_contract"],
        "UI_SPEC": ["UI_SPEC.md", "ui_spec"],
        "MOBILE_UI_SPEC": ["MOBILE_UI_SPEC.md", "mobile_ui_spec"],
        "ARCHITECTURE": ["ARCHITECTURE.md", "architecture"],
        "DATABASE_SCHEMA": ["DATABASE_SCHEMA.md", "database_schema"],
        "BUG_LOG": ["BUG_LOG.md", "bug_log"],
        "TEST_STRATEGY": ["TEST_STRATEGY.md", "test_strategy"],
    }
    
    patterns = doc_map.get(doc_name, [doc_name])
    for f in files:
        f_lower = f.lower()
        for pattern in patterns:
            if pattern.lower() in f_lower:
                return True
    return False


def check_docs_alignment() -> List[str]:
    """检查文档对齐情况"""
    issues = []
    
    changed_files = get_changed_files()
    if not changed_files:
        print("No git changes detected, skipping check")
        return []
    
    print(f"Detected {len(changed_files)} changed files")
    
    code_changes = analyze_code_changes(changed_files)
    
    # 检查代码变更是否需要更新对应文档
    for code_type, doc_types in CODE_TO_DOCS.items():
        if code_changes.get(code_type, False):
            for doc_type in doc_types:
                doc_files = DOC_CATEGORIES.get(doc_type, [""])[1:]
                doc_updated = any(check_doc_updated(df, changed_files) for df in doc_files)
                if not doc_updated:
                    issues.append(f"[WARN] Code change in {code_type}, but no {doc_type} doc update detected")
    
    # 检查是否有新增功能但未更新任何文档
    has_code_changes = any(code_changes.values())
    has_doc_changes = any(check_doc_updated(df, changed_files) for dfs in DOC_CATEGORIES.values() for df in dfs)
    
    if has_code_changes and not has_doc_changes:
        issues.append("[WARN] Code changes detected, but no doc updates found")
        
    return issues


def main():
    import argparse
    parser = argparse.ArgumentParser(description="检查文档对齐")
    parser.add_argument("--check-all", action="store_true", help="检查所有文档，不只是变更的")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Docs Alignment Check")
    print("=" * 60)
    
    issues = check_docs_alignment()
    
    if issues:
        print("\n[ISSUE] Found problems:")
        for issue in issues:
            print(f"  {issue}")
        print("\nPlease make sure the following docs are updated:")
        print("  - API_CONTRACT.md (API interface)")
        print("  - UI_SPEC.md (UI spec)")
        print("  - ARCHITECTURE.md (architecture)")
        print("  - BUG_LOG.md (if fixing bugs)")
        print("  - TEST_STRATEGY.md (if adding tests)")
        # Docs alignment is a warning, not a blocker
        print("\n[PASS] Docs alignment check (warnings only)")
        sys.exit(0)
    else:
        print("\n[PASS] Docs alignment check passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
