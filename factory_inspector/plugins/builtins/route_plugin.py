from __future__ import annotations
import subprocess
import json
from factory_inspector.plugins.base import BasePlugin, CheckResult
from factory_inspector.core.logger import get_logger

class RoutePlugin(BasePlugin):
    """路由检测插件: 专门检查默认路由数量"""
    
    def run(self, config: dict) -> list[CheckResult]:
        results = []
        logger = get_logger()
        max_default_routes = config.get("max_default_routes", 1)
        
        try:
            # 获取所有路由的 JSON 信息
            route_output = subprocess.check_output(["ip", "-j", "route"]).decode()
            logger.info("[Route] 路由原始输出 (数量校验): \n%s", route_output)
            routes = json.loads(route_output)
            
            # 过滤出所有目标为 'default' 的路由
            default_routes = [r for r in routes if r.get("dst") == "default"]
            count = len(default_routes)
            
            # 获取具体的网关信息用于展示
            gateways = [r.get("gateway", "未知") for r in default_routes]
            actual_info = f"数量: {count} (网关: {', '.join(gateways)})"
            
            status = count <= max_default_routes
            
            results.append(CheckResult(
                name="默认路由数量检测",
                status=status,
                expected=f"不超过 {max_default_routes} 条",
                actual=actual_info,
                message="" if status else f"检测到多余的默认路由，请清理！"
            ))
            
        except Exception as e:
            results.append(CheckResult("默认路由数量检测", False, f"<= {max_default_routes}", "错误", str(e)))

        return results
