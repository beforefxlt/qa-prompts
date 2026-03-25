import asyncio
import struct
import logging
import argparse
import os
from abc import ABC, abstractmethod

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("FuzzerEngineV2")

class AnomalyContext:
    """
    存储当前请求/响应的上下文信息，供插件共享
    """
    def __init__(self, addr, trans_id, proto_id, unit_id):
        self.addr = addr
        self.trans_id = trans_id
        self.proto_id = proto_id
        self.unit_id = unit_id

class BaseAnomaly(ABC):
    """
    所有异常模式插件的基类
    """
    def on_pdu_received(self, func_code, pdu, context: AnomalyContext):
        return func_code, pdu

    def on_response_ready(self, response_pdu, context: AnomalyContext):
        return response_pdu

    async def on_transport_send(self, writer, mbap, pdu, context: AnomalyContext):
        """
        返回 True 表示已接管发送逻辑，Engine 不再执行默认发送
        """
        return False

class NormalMode(BaseAnomaly):
    pass

class PluginManager:
    def __init__(self, config):
        self.config = config
        self.plugins = []
        self._load_plugins()

    def _load_plugins(self):
        # 导入插件 (本地目录)
        try:
            from plugins.oversized import OversizedPayload
            from plugins.segmentation import SlowTickling
        except ImportError:
            logger.warning("Required plugins not found in plugins/ directory.")
            return

        target_mode = self.config.get("mode", "NORMAL")
        logger.info(f"Activating Mode: {target_mode}")
        
        if target_mode == "NORMAL":
            self.plugins.append(NormalMode())
        elif target_mode == "OVERSIZED":
            self.plugins.append(OversizedPayload(target_len=self.config.get("target_len", 512)))
        elif target_mode == "SEGMENTATION":
            self.plugins.append(SlowTickling(delay_per_byte=self.config.get("delay_per_byte", 0.05)))
        elif target_mode == "MIXED":
            self.plugins.append(OversizedPayload(target_len=512))
            self.plugins.append(SlowTickling(delay_per_byte=0.02))

    def apply_on_pdu_received(self, func_code, pdu, context):
        for p in self.plugins:
            func_code, pdu = p.on_pdu_received(func_code, pdu, context)
        return func_code, pdu

    def apply_on_response_ready(self, response_pdu, context):
        for p in self.plugins:
            response_pdu = p.on_response_ready(response_pdu, context)
        return response_pdu

    async def apply_on_transport_send(self, writer, mbap, pdu, context):
        for p in self.plugins:
            if await p.on_transport_send(writer, mbap, pdu, context):
                return True
        return False

class FuzzerEngine:
    def __init__(self, host="0.0.0.0", port=5020, config=None):
        self.host = host
        self.port = port
        self.config = config or {}
        self.plugin_manager = PluginManager(self.config)
        self.active_conns = 0

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        self.active_conns += 1
        logger.info(f"Client connected: {addr} (Active: {self.active_conns})")
        
        try:
            while True:
                # 1. 读取 MBAP
                try:
                    mbap_raw = await asyncio.wait_for(reader.readexactly(7), timeout=5.0)
                except: break
                
                trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', mbap_raw)
                ctx = AnomalyContext(addr, trans_id, proto_id, unit_id)

                # 2. 读取 PDU
                try:
                    pdu_raw = await asyncio.wait_for(reader.readexactly(length - 1), timeout=5.0)
                except: break
                func_code = pdu_raw[0]

                # 3. 插件钩子：PDU 已收到
                func_code, pdu_raw = self.plugin_manager.apply_on_pdu_received(func_code, pdu_raw, ctx)

                # 4. 协议逻辑
                response_pdu = self._process_protocol_logic(func_code, pdu_raw)

                # 5. 插件钩子：响应准备就绪
                response_pdu = self.plugin_manager.apply_on_response_ready(response_pdu, ctx)

                # 6. 发送处理
                mbap_final = struct.pack('>HHHB', ctx.trans_id, ctx.proto_id, len(response_pdu) + 1, ctx.unit_id)
                if not await self.plugin_manager.apply_on_transport_send(writer, mbap_final, response_pdu, ctx):
                    writer.write(mbap_final + response_pdu)
                    await writer.drain()

        except Exception as e:
            logger.error(f"Error handling {addr}: {e}")
        finally:
            self.active_conns -= 1
            writer.close()

    def _process_protocol_logic(self, func_code, pdu):
        # 简单回显架构逻辑
        if func_code == 0x03:
             return struct.pack('>BBH', func_code, 2, 0)
        return bytes([func_code | 0x80, 0x01])

    async def start(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        logger.info(f"Fuzzer Engine V2 started on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modbus Fuzzer Engine V2")
    parser.add_argument("--port", type=int, default=5020)
    parser.add_argument("--mode", default="NORMAL", choices=["NORMAL", "OVERSIZED", "SEGMENTATION", "MIXED"])
    parser.add_argument("--target-len", type=int, default=512)
    parser.add_argument("--delay-byte", type=float, default=0.02)
    
    args = parser.parse_args()
    config = {
        "mode": args.mode,
        "target_len": args.target_len,
        "delay_per_byte": args.delay_byte
    }
    
    engine = FuzzerEngine(port=args.port, config=config)
    asyncio.run(engine.start())
