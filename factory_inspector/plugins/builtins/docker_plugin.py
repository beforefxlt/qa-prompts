from __future__ import annotations
import subprocess
import re
from factory_inspector.plugins.base import BasePlugin, CheckResult
from factory_inspector.core.logger import get_logger

class DockerPlugin(BasePlugin):
    """Docker 容器状态检测插件"""
    
    def run(self, config: dict) -> list[CheckResult]:
        results = []
        items = config.get("items", [])
        logger = get_logger()
        
        # 1. 获取所有容器的当前状态
        try:
            # 使用 tab 分隔，方便解析名称、状态和镜像
            proc = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}\t{{.Image}}"],
                capture_output=True, text=True, check=True
            )
            docker_output = proc.stdout.strip().split("\n")
            container_map = {}
            for line in docker_output:
                if not line.strip(): 
                    continue
                parts = line.split("\t")
                if len(parts) >= 3:
                    name, status, image = parts[0], parts[1], parts[2]
                    container_map[name] = {"status": status, "image": image}
            
            logger.info("[Docker] 成功获取 %d 个容器状态", len(container_map))
        except Exception as e:
            logger.error("[Docker] 无法执行 docker 命令: %s", e)
            return [CheckResult("Docker基础环境", False, "可运行", "运行失败或未安装", f"无法获取容器信息: {str(e)}")]

        # 2. 遍历配置项进行比对
        for item in items:
            name = item["name"]
            expected_image_tag = item.get("image_tag") # 可选：匹配镜像标签/版本
            
            if name not in container_map:
                results.append(CheckResult(
                    name=f"容器[{name}]状态",
                    status=False,
                    expected="Up (运行中)",
                    actual="缺失",
                    message="系统中未找到该名称的容器"
                ))
                continue
            
            # 检查运行状态 (通常是以 Up 开头)
            actual_status = container_map[name]["status"]
            is_up = actual_status.startswith("Up")
            
            results.append(CheckResult(
                name=f"容器[{name}]运行状态",
                status=is_up,
                expected="Up (运行中)",
                actual=actual_status,
                message="" if is_up else f"容器未运行，当前状态: {actual_status}"
            ))
            
            # 检查镜像版本 (如果配置了镜像标签要求)
            if expected_image_tag:
                actual_image = container_map[name]["image"]
                is_tag_match = expected_image_tag in actual_image
                results.append(CheckResult(
                    name=f"容器[{name}]镜像版本",
                    status=is_tag_match,
                    expected=f"包含 {expected_image_tag}",
                    actual=actual_image,
                    message="" if is_tag_match else f"镜像版本不匹配"
                ))
                    
        return results
