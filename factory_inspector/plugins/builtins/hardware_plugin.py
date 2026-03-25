from __future__ import annotations
import subprocess
from factory_inspector.plugins.base import BasePlugin, CheckResult
from factory_inspector.core.logger import get_logger

class HardwarePlugin(BasePlugin):
    """硬件检测插件: CPU, 内存, 硬盘"""
    
    def run(self, config: dict) -> list[CheckResult]:
        results = []
        logger = get_logger()
        
        # 1. 检测 CPU 核数
        min_cores = config.get("min_cpu_cores", 0)
        try:
            # 使用 nproc 获取核心数
            output = subprocess.check_output(["nproc"]).decode().strip()
            logger.info("[Hardware] CPU 核数原始输出: %s", output)
            cpu_count = int(output)
            results.append(CheckResult(
                name="CPU核数检测",
                status=cpu_count >= min_cores,
                expected=f">= {min_cores}",
                actual=cpu_count,
                message="" if cpu_count >= min_cores else "核心数不足"
            ))
        except Exception as e:
            results.append(CheckResult("CPU核数检测", False, f">= {min_cores}", "未知", str(e)))

        # 2. 检测内存总量 (GB)
        min_mem = config.get("min_memory_gb", 0)
        try:
            # 读取 /proc/meminfo 中的 MemTotal
            with open("/proc/meminfo", "r") as f:
                content = f.read()
                logger.info("[Hardware] /proc/meminfo 原始数据 (前5行): \n%s", "\n".join(content.splitlines()[:5]))
                for line in content.splitlines():
                    if "MemTotal" in line:
                        mem_kb = int(line.split()[1])
                        mem_gb = round(mem_kb / 1024 / 1024, 2)
                        results.append(CheckResult(
                            name="内存总量检测",
                            status=mem_gb >= min_mem,
                            expected=f">= {min_mem} GB",
                            actual=f"{mem_gb} GB",
                            message="" if mem_gb >= min_mem else "内存容量不足"
                        ))
                        break
        except Exception as e:
            results.append(CheckResult("内存总量检测", False, f">= {min_mem} GB", "读取错误", str(e)))

        # 3. 检测硬盘总量 (GB) - 简化逻辑：检查根目录所在的磁盘
        min_disk = config.get("min_disk_gb", 0)
        try:
            raw_output = subprocess.check_output(["df", "-k", "/"]).decode()
            logger.info("[Hardware] 磁盘空间原始输出 (df -k /): \n%s", raw_output)
            output = raw_output.splitlines()[1]
            total_disk_kb = int(output.split()[1])
            total_disk_gb = round(total_disk_kb / 1024 / 1024)
            results.append(CheckResult(
                name="硬盘空间检测",
                status=total_disk_gb >= min_disk,
                expected=f">= {min_disk} GB",
                actual=f"{total_disk_gb} GB",
                message="" if total_disk_gb >= min_disk else "硬盘容量不足"
            ))
        except Exception as e:
            results.append(CheckResult("硬盘空间检测", False, f">= {min_disk} GB", "未知", str(e)))

        return results
