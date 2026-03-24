import subprocess
import re
from factory_inspector.plugins.base import BasePlugin, CheckResult
from factory_inspector.core.logger import get_logger

class ServicePlugin(BasePlugin):
    """服务检测插件: 运行状态与版本"""
    
    def run(self, config: dict) -> list[CheckResult]:
        results = []
        items = config.get("items", [])
        logger = get_logger()
        
        for item in items:
            name = item["name"]
            min_version = item.get("min_version")
            check_only = item.get("check_only", False)
            
            # 1. 检查服务运行状态 (systemctl is-active)
            try:
                status = subprocess.run(["systemctl", "is-active", name], 
                                     capture_output=True, text=True).stdout.strip()
                logger.info("[Service] 服务 [%s] 状态原始输出: %s", name, status)
                is_running = status == "active"
                results.append(CheckResult(
                    name=f"服务[{name}]状态",
                    status=is_running,
                    expected="active",
                    actual=status,
                    message="" if is_running else f"服务当前处于 {status} 状态"
                ))
            except Exception as e:
                results.append(CheckResult(f"服务[{name}]状态", False, "active", "错误", str(e)))
                continue

            # 2. 检查版本 (如果需要)
            if not check_only and min_version and is_running:
                version_found, actual_version = self._get_version(name)
                if version_found:
                    # 简单的字符串版本比对 (可以使用 packaging.version 库更专业)
                    is_version_ok = actual_version >= min_version
                    results.append(CheckResult(
                        name=f"服务[{name}]版本",
                        status=is_version_ok,
                        expected=f">= {min_version}",
                        actual=actual_version,
                        message="" if is_version_ok else "版本过低"
                    ))
                else:
                    results.append(CheckResult(f"服务[{name}]版本", False, f">= {min_version}", "未知", actual_version))
                    
        return results

    def _get_version(self, service_name: str) -> tuple[bool, str]:
        """尝试获取服务的版本号"""
        try:
            # 常用命令：<service> --version 或 <service> -v
            cmd = [service_name, "--version"]
            if service_name == "nginx":
                # nginx 把版本输出在 stderr
                proc = subprocess.run(["nginx", "-v"], capture_output=True, text=True)
                output = proc.stdout + proc.stderr
            else:
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            
            get_logger().info("[Service] 服务 [%s] 版本原始输出: %s", service_name, output.strip())
            
            # 使用正则提取版本号 (如 1.18.0)
            match = re.search(r"(\d+\.\d+(\.\d+)?)", output)
            if match:
                return True, match.group(1)
            return False, f"无法从输出解析版本: {output[:50]}..."
        except Exception as e:
            return False, str(e)
