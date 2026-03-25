import asyncio
from fuzzer_engine_v2 import BaseAnomaly, AnomalyContext

class SlowTickling(BaseAnomaly):
    """
    分片发送插件 (L3)：将报文拆成 1 字节的小包发送，测试主站重组粘包的鲁棒性
    """
    def __init__(self, delay_per_byte=0.05):
        self.delay = delay_per_byte

    def on_pdu_received(self, func_code, pdu, context):
        return func_code, pdu
    
    def on_response_ready(self, response_pdu, context):
        return response_pdu

    async def on_transport_send(self, writer, mbap, pdu, context):
        full_msg = mbap + pdu
        print(f"[SlowTickling] Sending {len(full_msg)} bytes segment by segment...")
        for b in full_msg:
            writer.write(bytes([b]))
            await writer.drain()
            if self.delay > 0:
                await asyncio.sleep(self.delay)
