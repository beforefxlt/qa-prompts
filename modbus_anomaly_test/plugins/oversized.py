import os
from fuzzer_engine_v2 import BaseAnomaly, AnomalyContext

class OversizedPayload(BaseAnomaly):
    """
    超长报文插件：强制返回超过标准上限 (260字节) 的响应
    """
    def __init__(self, target_len=512):
        self.target_len = target_len

    def on_pdu_received(self, func_code, pdu, context):
        return func_code, pdu

    def on_response_ready(self, response_pdu, context: AnomalyContext):
        # 如果当前响应长度小于目标长度，则填充垃圾数据
        if len(response_pdu) < self.target_len:
            padding_len = self.target_len - len(response_pdu)
            print(f"[Oversized] Padding PDU with {padding_len} bytes")
            return response_pdu + os.urandom(padding_len)
        return response_pdu
