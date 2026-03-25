import asyncio
import logging
from vulnerability_base import VulnerabilityBase, TargetContext

logger = logging.getLogger("VulnerabilityPlugin")

class StackHangPlugin(VulnerabilityBase):
    """
    BUG_STACK: 模拟解析器挂起
    """
    async def on_mbap_parsed(self, trans_id, length, context: TargetContext):
        if length > 200:
            logger.warning(f"[BUG_STACK] Received illegal length {length}. Parser HANGING.")
            while True:
                await asyncio.sleep(10)
