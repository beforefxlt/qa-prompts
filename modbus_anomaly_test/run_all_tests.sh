#!/bin/bash

# Modbus 全量测试一键运行脚本

# 设置基础目录
BASE_DIR=$(cd "$(dirname "$0")"; pwd)
VENV_PYTEST="${BASE_DIR}/venv/bin/pytest"

# 1. 运行基线验证
#    由 conftest.py 的会话级夹具自动拉起仿真器，基线阶段使用 NORMAL 模式。
echo ">>> [Phase 1] 运行基线读写验证 (NORMAL)..."
MODBUS_SIM_AUTOSTART=1 MODBUS_SIM_REUSE_EXISTING=0 MODBUS_SIM_MODE=NORMAL \
    $VENV_PYTEST test_modbus_baseline.py -v

# 2. 运行异常测试
#    异常阶段切换为 HONEYPOT 模式，确保非法值会触发异常响应。
echo ">>> [Phase 2] 运行原始异常注入测试 (HONEYPOT)..."
MODBUS_SIM_AUTOSTART=1 MODBUS_SIM_REUSE_EXISTING=0 MODBUS_SIM_MODE=HONEYPOT \
    $VENV_PYTEST test_modbus_anomaly.py -v

# 3. 运行高并发压力测试
echo ">>> [Phase 3] 运行异步并发压力测试 (NORMAL)..."
MODBUS_SIM_AUTOSTART=1 MODBUS_SIM_REUSE_EXISTING=0 MODBUS_SIM_MODE=NORMAL \
    $VENV_PYTEST test_modbus_concurrency.py -v -s

echo ">>> [Success] 所有测试环节执行完毕。"
