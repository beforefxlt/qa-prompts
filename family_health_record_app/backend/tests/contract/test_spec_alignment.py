import sys
import os
import re
import pytest
from httpx import AsyncClient
from uuid import uuid4
from pathlib import Path

# 定义规格文档路径
# 逻辑：当前文件在 tests/contract/，寻找 ../../../docs/specs/API_CONTRACT.md
SPEC_PATH = Path(__file__).parent.parent.parent.parent / "docs" / "specs" / "API_CONTRACT.md"

def extract_endpoints_from_spec():
    """
    从 API_CONTRACT.md 提取 (METHOD, PATH) 契约对
    """
    if not SPEC_PATH.exists():
        return []
    
    endpoints = []
    content = SPEC_PATH.read_text(encoding="utf-8")
    
    # 正则提取表格行: | `METHOD` | `/api/xxx` | ... |
    lines = content.split('\n')
    for line in lines:
        # 兼容带反引号的情况，例如 | `GET` | `/api/v1/members` |
        match = re.search(r'\|\s*`?(GET|POST|PUT|DELETE)`?\s*\|\s*`?(/api/v1/[^`|]+)`?\s*\|', line)
        if match:
            method = match.group(1).strip()
            # 清理路径：去除反引号，剥离查询参数（?之后的内容）
            path_val = match.group(2).strip().replace("`", "").split('?')[0]
            endpoints.append((method, path_val))
        
    return endpoints

# 获取所有契约定义的端点
ENDPOINTS = extract_endpoints_from_spec()

@pytest.mark.parametrize("method, spec_path", ENDPOINTS)
@pytest.mark.asyncio
async def test_endpoint_route_is_reachable(test_client, method, spec_path):
    """
    对 API_CONTRACT.md 中录入的所有端点执行路由可达性测试。
    我们的目标是确保文档描述的路径在后端真实存在（不返回 404）。
    """
    dummy_id = str(uuid4())
    real_path = re.sub(r'\{[^}]+\}', dummy_id, spec_path)
    
    print(f"\n[CONTRACT-DEBUG] Spec: {method} {spec_path}")
    print(f"[CONTRACT-DEBUG] Real: {method} {real_path}")
    
    response = await test_client.request(method, real_path)
    print(f"[CONTRACT-RESULT] Status: {response.status_code}")
    
    if response.status_code == 404:
        print(f"\n[CONTRACT-TRACE] 404 Detected for {method} {real_path}")
        from app.main import app
        registered_routes = []
        for route in app.routes:
            if hasattr(route, "path"):
                methods = getattr(route, "methods", [])
                registered_routes.append(f"{list(methods)} {route.path}")
        
        print("[CONTRACT-TRACE] Registered Routes in Backend:")
        for r in sorted(registered_routes):
            print(f"  - {r}")
    
    # 核心审计逻辑：路径描述必须在后端路由表中存在
    if response.status_code == 404:
        content = response.json() if response.headers.get("content-type") == "application/json" else {}
        detail = content.get("detail", "")
        # 如果 detail 包含业务信息（如“不存在”），说明路由已命中业务逻辑层，不算契约偏离
        if "不存在" in str(detail) or "NotFound" in str(detail):
            print(f"[CONTRACT-INFO] 路由已命中但数据不存在 (OK): {detail}")
            return
        assert False, f"契约偏离：后端路由表未发现接口 {method} {spec_path}"

    assert response.status_code != 405, f"方法偏离：端点不支持 {method}"
    
    # 后备建议：如果返回 405 (Method Not Allowed)，也说明路径匹配了但方法不匹配
    assert response.status_code != 405, f"方法偏离：文档定义了 {method} {spec_path}，但后端该路径不支持 {method}"

def test_spec_was_found():
    """确保测试脚本找到了规格文档"""
    assert len(ENDPOINTS) > 0, f"在 {SPEC_PATH} 中未检测到任何 API 契约定义。请检查文档路径和格式。"
