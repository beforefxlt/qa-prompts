import asyncio
import logging
from vulnerability_base import VulnerabilityBase, TargetContext

logger = logging.getLogger("VulnerabilityPlugin")

class LeakPlugin(VulnerabilityBase):
    """
    BUG_LEAK: 模拟连接泄漏导致死锁
    """
    def __init__(self, max_allowed_conns=5):
        self.max_allowed_conns = max_allowed_conns

    async def on_connect(self, reader, writer, context: TargetContext):
        if context.active_conns >= self.max_allowed_conns:
            logger.error(f"[BUG_LEAK] Max connections exceeded ({context.active_conns}). FREEZING this handler.")
            while True:
                await asyncio.sleep(60)
