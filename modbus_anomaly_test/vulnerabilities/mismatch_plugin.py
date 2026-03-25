import logging
import random
from vulnerability_base import VulnerabilityBase, TargetContext

logger = logging.getLogger("VulnerabilityPlugin")

class MismatchPlugin(VulnerabilityBase):
    """
    BUG_MISMATCH: 模拟 TID 不匹配
    """
    def on_pdu_received(self, func_code, pdu, context: TargetContext):
        # 记录原始 TID 并制造不匹配
        context.original_tid = context.trans_id
        context.trans_id = (context.trans_id + random.randint(1, 100)) % 65535
        logger.warning(f"[BUG_MISMATCH] Tampering TID from {context.original_tid} to {context.trans_id}")
        return func_code, pdu
