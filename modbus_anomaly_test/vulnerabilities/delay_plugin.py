import asyncio
import logging
import random
from vulnerability_base import VulnerabilityBase, TargetContext

logger = logging.getLogger("VulnerabilityPlugin")

class DelayPlugin(VulnerabilityBase):
    """
    BUG_DELAY: 模拟响应延迟
    """
    async def on_send(self, mbap, pdu, context: TargetContext):
        delay_sec = random.uniform(0.5, 3.0)
        logger.info(f"[BUG_DELAY] Sleeping for {delay_sec:.2f}s before sending response.")
        await asyncio.sleep(delay_sec)
