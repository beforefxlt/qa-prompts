import subprocess
import json
from factory_inspector.plugins.base import BasePlugin, CheckResult
from factory_inspector.core.logger import get_logger

class NetworkPlugin(BasePlugin):
    """网络检测插件: 网卡, IP, 路由"""
    
    def run(self, config: dict) -> list[CheckResult]:
        results = []
        
        # 获取所有网卡的 JSON 信息
        try:
            logger = get_logger()
            addr_output = subprocess.check_output(["ip", "-j", "addr"]).decode()
            logger.info("[Network] IP 地址原始输出: \n%s", addr_output)
            interfaces_data = json.loads(addr_output)
        except Exception as e:
            return [CheckResult("网络状态获取", False, "ip addr 成功", "失败", str(e))]

        # 1. 检测网卡及 IP 前缀
        expected_ifaces = config.get("interfaces", [])
        for exp_iface in expected_ifaces:
            ifname = exp_iface["name"]
            prefix = exp_iface["expected_ip_prefix"]
            
            # 查找匹配的网卡
            found_iface = next((i for i in interfaces_data if i["ifname"] == ifname), None)
            
            if not found_iface:
                results.append(CheckResult(f"网卡[{ifname}]存在性", False, "存在", "缺失"))
                continue
            
            # 检查 IP
            ip_found = False
            actual_ips = []
            for addr_info in found_iface.get("addr_info", []):
                actual_ip = addr_info.get("local", "")
                actual_ips.append(actual_ip)
                if actual_ip.startswith(prefix):
                    ip_found = True
                    break
            
            results.append(CheckResult(
                name=f"网卡[{ifname}]IP网段检测",
                status=ip_found,
                expected=f"前缀 {prefix}",
                actual=", ".join(actual_ips) if actual_ips else "无IP",
                message="" if ip_found else "未找到预期网段的IP"
            ))

        # 2. 检测默认网关 (Default Route)
        expected_gw = config.get("default_gateway")
        if expected_gw:
            try:
                route_output = subprocess.check_output(["ip", "-j", "route"]).decode()
                logger.info("[Network] 路由原始输出 (网关校验): \n%s", route_output)
                routes = json.loads(route_output)
                default_route = next((r for r in routes if r.get("dst") == "default"), None)
                
                actual_gw = default_route.get("gateway", "未发现") if default_route else "无默认路由"
                results.append(CheckResult(
                    name="默认网关检测",
                    status=actual_gw == expected_gw,
                    expected=expected_gw,
                    actual=actual_gw,
                    message="" if actual_gw == expected_gw else "默认路由网关不匹配"
                ))
            except Exception as e:
                results.append(CheckResult("默认网关检测", False, expected_gw, "未知", str(e)))

        return results
