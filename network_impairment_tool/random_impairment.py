#!/usr/bin/env python3
import subprocess
import time
import random
import signal
import sys
import argparse

"""
随机网络损伤模拟脚本 (Linux)
项目: qa-prompts / network_impairment_tool
版本: v1.2.0
功能: 在指定网口/桥接上交替换用随机生成的延迟、抖动和丢包设置，模拟波动网络。
更新: 增加了抖动(jitter)必须小于延迟(delay)的逻辑校验，防止内核配置冲突。
"""

# --- 配置区：损伤参数范围 ---
DEFAULT_CONFIG = {
    "delay_ms": (20, 200),      # 延迟范围 (min, max)
    "jitter_ms": (5, 50),       # 抖动范围
    "loss_percent": (0.1, 5.0), # 丢包率范围 %
    "interval_sec": (10, 30),   # 随机调整间隔 (秒)
}

class NetImpairmentManager:
    def __init__(self, interface):
        self.interface = interface
        print(f"[*] 初始化损伤管理器，目标网口: {self.interface}")

    def run_cmd(self, cmd):
        try:
            subprocess.run(cmd, shell=True, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            if "del" not in cmd:
                print(f"[!] 命令执行失败: {cmd}\n错误信息: {e.stderr.decode()}")

    def clean(self):
        print(f"[*] 清理 {self.interface} 上的所有 tc 规则...")
        self.run_cmd(f"tc qdisc del dev {self.interface} root")

    def apply(self, delay, jitter, loss):
        print(f"[+] 正在应用损伤: 延迟={delay}ms, 抖动={jitter}ms, 丢包={loss}%")
        cmd = f"tc qdisc replace dev {self.interface} root netem delay {delay}ms {jitter}ms distribution normal loss {loss}%"
        self.run_cmd(cmd)

    def start_random_loop(self):
        print("[*] 随机损伤循环已启动。按 Ctrl+C 停止测试并恢复网络。")
        try:
            while True:
                # 随机生成损伤参数
                delay = random.randint(*DEFAULT_CONFIG["delay_ms"])
                jitter = random.randint(*DEFAULT_CONFIG["jitter_ms"])
                loss = round(random.uniform(*DEFAULT_CONFIG["loss_percent"]), 2)

                # 逻辑校验：Jitter 必须小于 Delay，否则 netem 会产生非预期的重排或报错
                if jitter >= delay:
                    jitter = delay - 1
                    if jitter < 0: jitter = 0
                
                self.apply(delay, jitter, loss)
                
                wait_time = random.randint(*DEFAULT_CONFIG["interval_sec"])
                print(f"[*] 等待 {wait_time} 秒后进行下一次随机调整...")
                time.sleep(wait_time)
        except KeyboardInterrupt:
            self.clean()
            print("\n[*] 测试终止，已恢复网络正常状态。")
            sys.exit(0)

def check_privileges():
    if subprocess.run("id -u", shell=True, capture_output=True).stdout.decode().strip() != "0":
        print("[!] 错误：此脚本必须以 root 权限运行 (请使用 sudo)。")
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="随机网络损伤模拟脚本 (Linux)")
    parser.add_argument("iface", help="目标网口名称 (如 br0, eth1)")
    args = parser.parse_args()

    check_privileges()
    manager = NetImpairmentManager(args.iface)
    manager.start_random_loop()
