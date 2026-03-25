import asyncio
import struct
import logging
import argparse
import time
import random
from vulnerability_base import TargetContext

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("VulnerableTarget")

class VulnerabilityPluginManager:
    def __init__(self, bug_list):
        self.plugins = []
        self._load_plugins(bug_list)

    def _load_plugins(self, bug_list):
        if not bug_list: return
        
        mapping = {
            "BUG_LEAK": ("vulnerabilities.leak_plugin", "LeakPlugin"),
            "BUG_STACK": ("vulnerabilities.stack_hang_plugin", "StackHangPlugin"),
            "BUG_OOB": ("vulnerabilities.oob_crash_plugin", "OOBCrashPlugin"),
            "BUG_HONEYPOT": ("vulnerabilities.honeypot_plugin", "HoneyPotPlugin"),
            "BUG_MISMATCH": ("vulnerabilities.mismatch_plugin", "MismatchPlugin"),
            "BUG_DELAY": ("vulnerabilities.delay_plugin", "DelayPlugin"),
        }
        
        for bug in bug_list:
            if bug in mapping:
                module_name, class_name = mapping[bug]
                try:
                    module = __import__(module_name, fromlist=[class_name])
                    plugin_class = getattr(module, class_name)
                    # 针对特定插件可以传入参数，目前保持默认
                    self.plugins.append(plugin_class())
                    logger.info(f"Loaded vulnerability plugin: {bug}")
                except Exception as e:
                    logger.error(f"Failed to load plugin {bug}: {e}")

    async def apply_on_connect(self, reader, writer, context):
        for p in self.plugins:
            await p.on_connect(reader, writer, context)

    async def apply_on_mbap_parsed(self, trans_id, length, context):
        for p in self.plugins:
            await p.on_mbap_parsed(trans_id, length, context)

    def apply_on_pdu_received(self, func_code, pdu, context):
        for p in self.plugins:
            func_code, pdu = p.on_pdu_received(func_code, pdu, context)
        return func_code, pdu

    def apply_on_response_prepared(self, response_pdu, context):
        for p in self.plugins:
            response_pdu = p.on_response_prepared(response_pdu, context)
        return response_pdu

    async def apply_on_send(self, mbap, pdu, context):
        for p in self.plugins:
            await p.on_send(mbap, pdu, context)

class VulnerableTarget:
    def __init__(self, port=5020, bugs=None):
        self.port = port
        self.bugs = bugs or []
        self.active_conns = 0
        self.plugin_manager = VulnerabilityPluginManager(self.bugs)

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        self.active_conns += 1
        
        ctx = TargetContext(addr)
        ctx.active_conns = self.active_conns

        # --- Hook: on_connect ---
        await self.plugin_manager.apply_on_connect(reader, writer, ctx)
        
        logger.info(f"Target: Client connected from {addr} (Active: {self.active_conns})")

        try:
            while True:
                # 1. 解析 MBAP
                try:
                    mbap_raw = await asyncio.wait_for(reader.readexactly(7), timeout=10.0)
                except: break
                
                trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', mbap_raw)
                ctx.trans_id = trans_id
                ctx.proto_id = proto_id
                ctx.unit_id = unit_id

                # --- Hook: on_mbap_parsed ---
                await self.plugin_manager.apply_on_mbap_parsed(trans_id, length, ctx)

                # 2. 读取 PDU
                try:
                    pdu_raw = await asyncio.wait_for(reader.readexactly(length - 1), timeout=10.0)
                except: break
                
                func_code = pdu_raw[0]

                # --- Hook: on_pdu_received ---
                func_code, pdu_raw = self.plugin_manager.apply_on_pdu_received(func_code, pdu_raw, ctx)

                # 正常响应处理逻辑 (简化版)
                # 如果是 BUG_OOB 触发了畸形响应，这里会直接透传
                if len(pdu_raw) == 5: # 垃圾数据的长度 (BUG_OOB)
                     response_pdu = pdu_raw 
                else:
                    # 获取寄存器值 (演示用，如果是 HoneyPot 插件，它会在 context 里做标记)
                    reg_value = 123 
                    response_pdu = struct.pack('>BBH', func_code, 2, reg_value)
                
                # --- Hook: on_response_prepared ---
                response_pdu = self.plugin_manager.apply_on_response_prepared(response_pdu, ctx)

                # 重新计算响应长度并构建 MBAP
                # 注意：ctx.trans_id 可能已经被 BUG_MISMATCH 修改
                mbap_final = struct.pack('>HHHB', ctx.trans_id, ctx.proto_id, len(response_pdu) + 1, ctx.unit_id)
                
                # --- Hook: on_send ---
                await self.plugin_manager.apply_on_send(mbap_final, response_pdu, ctx)

                writer.write(mbap_final + response_pdu)
                await writer.drain()

        except Exception as e:
            logger.error(f"Target connection error: {e}")
        finally:
            self.active_conns -= 1
            logger.info(f"Target: Client {addr} disconnected. (Active: {self.active_conns})")
            writer.close()

    async def start(self):
        server = await asyncio.start_server(self.handle_client, '0.0.0.0', self.port)
        logger.info(f"Vulnerable Target (Pluggable) started on port {self.port} (Active Bugs: {self.bugs})")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modbus Vulnerable Target (HoneyPot for Testing)")
    parser.add_argument("--port", type=int, default=5021)
    parser.add_argument("--bug", action="append", help="Enable specific bug: BUG_LEAK, BUG_OOB, BUG_STACK, BUG_HONEYPOT, BUG_MISMATCH, BUG_DELAY")
    
    args = parser.parse_args()
    target = VulnerableTarget(port=args.port, bugs=args.bug)
    asyncio.run(target.start())

