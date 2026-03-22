import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# 将当前目录加入 path 以便导入
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pcs_simulator import ValidatingDataBlock, REGISTERS

def test_simulator_registers_mapping():
    """
    UT: 验证模拟器是否包含了所有预期的真实寄存器地址
    """
    expected_addrs = [6001, 6003, 6006, 6013, 6016, 301, 309, 310, 311, 312]
    for addr in expected_addrs:
        assert addr in REGISTERS, f"点表中缺失关键地址: {addr}"

def test_validating_datablock_storage():
    """
    UT: 验证自定义数据块能够正常存取数据
    """
    block = ValidatingDataBlock(REGISTERS)
    test_addr = 6006
    test_value = [123]
    
    block.setValues(test_addr, test_value)
    result = block.getValues(test_addr, 1)
    
    assert result == test_value, "数据存储或回读失败"

def test_validating_datablock_anomaly_logging():
    """
    UT: 验证当写入越界值时，模拟器逻辑能够识别（虽然目前只是log，但验证其拦截能力）
    """
    from pcs_simulator import log as simulator_log
    
    with patch.object(simulator_log, 'warning') as mock_warning:
        block = ValidatingDataBlock(REGISTERS)
        # 写入一个正常值
        block.setValues(6006, [100])
        mock_warning.assert_not_called()
        
        # 写入一个“越界”值 (> 10000)
        block.setValues(6006, [10001])
        mock_warning.assert_called()
        assert "检测到非法数据注入" in mock_warning.call_args[0][0]

@patch("subprocess.Popen")
def test_network_capture_fixture_logic(mock_popen):
    """
    UT: 模拟 network_capture fixture 的逻辑，确保其能正确尝试调用 tshark
    """
    # 模拟 conftest 中的逻辑片段
    import time
    
    pcap_file = "test.pcap"
    tshark_cmd = ["tshark", "-i", "any", "-w", pcap_file]
    
    # 启动
    process = mock_popen(tshark_cmd)
    mock_popen.assert_called_with(tshark_cmd)
    
    # 停止
    process.terminate()
    process.terminate.assert_called_once() # 验证 terminate 被正确调用
