import asyncio
import struct
import logging
import argparse
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("VulnerableTarget")

class VulnerableTarget:
    def __init__(self, port=5020, bugs=None):
        self.port = port
        self.bugs = bugs or []
        self.active_conns = 0
        self.max_allowed_conns = 5 # 故意调低，用于测试 BUG_LEAK

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        
        # --- BUG_LEAK 模拟 ---
        if "BUG_LEAK" in self.bugs:
            if self.active_conns >= self.max_allowed_conns:
                logger.error(f"[BUG_LEAK] Max connections exceeded ({self.active_conns}). FREEZING this handler.")
                # 故障表现：既不关闭连接，也不处理数据，模拟线程/句柄死锁
                while True:
                    await asyncio.sleep(60)
        
        self.active_conns += 1
        logger.info(f"Target: Client connected from {addr} (Active: {self.active_conns})")

        try:
            while True:
                # 1. 解析 MBAP
                try:
                    mbap_raw = await asyncio.wait_for(reader.readexactly(7), timeout=10.0)
                except: break
                
                trans_id, proto_id, length, unit_id = struct.unpack('>HHHB', mbap_raw)

                # 2. 读取 PDU
                # --- BUG_STACK 模拟 ---
                if "BUG_STACK" in self.bugs and length > 200:
                    logger.warning(f"[BUG_STACK] Received illegal length {length}. Parser HANGING.")
                    # 故意卡死解析器，不读完剩余字节
                    while True: await asyncio.sleep(10)

                try:
                    pdu_raw = await asyncio.wait_for(reader.readexactly(length - 1), timeout=10.0)
                except: break
                
                func_code = pdu_raw[0]

                # --- BUG_OOB 模拟 ---
                if "BUG_OOB" in self.bugs and func_code == 0x03:
                    # 假设我们只预留了 10 个寄存器的内存
                    # 如果 client 请求读取 > 10 个寄存器，模拟内存溢出或拒绝响应
                    start_addr, count = struct.unpack('>HH', pdu_raw[1:5])
                    if count > 10:
                        logger.error(f"[BUG_OOB] Client requested {count} regs (Limit: 10). CRASHING response.")
                        # 故障表现：返回完全畸形的报文或直接断开
                        writer.write(b'\x00\x01\x02\x03\xff\xff\xff\xff\xff') # 垃圾数据
                        await writer.drain()
                        break

                # 正常响应处理
                response_pdu = struct.pack('>BBH', func_code, 2, 123) # 默认返回 123
                mbap_final = struct.pack('>HHHB', trans_id, proto_id, len(response_pdu) + 1, unit_id)
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
        logger.info(f"Vulnerable Target started on port {self.port} (Active Bugs: {self.bugs})")
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Modbus Vulnerable Target (HoneyPot for Testing)")
    parser.add_argument("--port", type=int, default=5021) # 默认 5021 避免与 fuzzer 冲突
    parser.add_argument("--bug", action="append", help="Enable specific bug: BUG_LEAK, BUG_OOB, BUG_STACK")
    
    args = parser.parse_args()
    target = VulnerableTarget(port=args.port, bugs=args.bug)
    asyncio.run(target.start())
