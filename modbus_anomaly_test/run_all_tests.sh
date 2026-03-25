#!/bin/bash

# Modbus 全量测试一键运行脚本

# 设置基础目录
BASE_DIR=$(cd "$(dirname "$0")"; pwd)
VENV_PYTHON="${BASE_DIR}/venv/bin/python3"
VENV_PYTEST="${BASE_DIR}/venv/bin/pytest"

# 1. 启动仿真器 (后台运行，Neutral 模式用于基线)
echo ">>> 启动仿真器 (NORMAL 模式)..."
$VENV_PYTHON malicious_simulator.py --port 5020 --mode HONEYPOT &
SIM_PID=$!
sleep 2

# 定义退出时的清理函数
cleanup() {
    echo ">>> 正在停止仿真器 (PID: $SIM_PID)..."
    kill $SIM_PID
}
trap cleanup EXIT

# 2. 运行基线验证
echo ">>> [Phase 1] 运行基线读写验证..."
$VENV_PYTEST test_modbus_baseline.py -v

# 3. 运行异常测试
echo ">>> [Phase 2] 运行原始异常注入测试 (L1/L3)..."
$VENV_PYTEST test_modbus_anomaly.py -v

# 4. 运行高并发压力测试
echo ">>> [Phase 3] 运行异步并发压力测试 (L2)..."
$VENV_PYTEST test_modbus_concurrency.py -v -s

echo ">>> [Success] 所有测试环节执行完毕。"
