import logging
from vulnerability_base import VulnerabilityBase, TargetContext

logger = logging.getLogger("VulnerabilityPlugin")

class OOBCrashPlugin(VulnerabilityBase):
    """
    BUG_OOB: 模拟越界访问导致的响应崩溃
    """
    def on_pdu_received(self, func_code, pdu, context: TargetContext):
        if func_code == 0x03 and len(pdu) >= 5:
            import struct
            _, count = struct.unpack('>HH', pdu[1:5])
            if count > 10:
                logger.error(f"[BUG_OOB] Client requested {count} regs (Limit: 10). CRASHING response.")
                # 返回畸形数据并指示 Engine 停止（这里通过抛出异常或返回特定标识）
                # 为了保持简单，我们直接在这里返回一个畸形 PDU 并标记它
                return func_code, b'\xff\xff\xff\xff\xff' # 垃圾数据
        return func_code, pdu
