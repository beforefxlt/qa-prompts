import logging
import struct
from vulnerability_base import VulnerabilityBase, TargetContext

logger = logging.getLogger("VulnerabilityPlugin")

class HoneyPotPlugin(VulnerabilityBase):
    """
    BUG_HONEYPOT: 模拟关键地址返回非法值
    """
    def on_pdu_received(self, func_code, pdu, context: TargetContext):
        if func_code == 0x03 and len(pdu) >= 5:
            start_addr, _ = struct.unpack('>HH', pdu[1:5])
            if 6000 <= start_addr <= 6100:
                logger.warning(f"[BUG_HONEYPOT] Triggered for addr {start_addr}. Injecting 0xFFFF.")
                # 将该上下文标记为触发了蜜罐，稍后在 on_response_prepared 中处理
                context.honey_triggered = True
        return func_code, pdu

    def on_response_prepared(self, response_pdu, context: TargetContext):
        if hasattr(context, 'honey_triggered') and context.honey_triggered:
            # 假设响应 PDU 的结构是 [func_code, byte_count, value1_high, value1_low, ...]
            # 我们将第一个寄存器值强制改为 0xFFFF
            if len(response_pdu) >= 4:
                return response_pdu[:2] + b'\xff\xff' + response_pdu[4:]
        return response_pdu
