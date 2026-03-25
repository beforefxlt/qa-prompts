# Modbus 脆弱性靶机 (Vulnerable Target) 操作指南

## 1. 靶机定位
为了验证 `modbus_anomaly_test` 框架对真实协议漏洞的探测能力，我们提供了一个具备“故意缺陷”的仿真ターゲット：`vulnerable_target.py`。
它不像普通的 Fuzzer 只是产生异常，而是真实模拟了一个“写得烂”的设备，在受到特定攻击时会发生挂死、内存溢出或响应乱序。

## 2. 内置漏洞模式 (Bugs)

### 2.1 BUG_OOB (缓冲区越界/内存溢出)
*   **触发条件**: 客户端请求读取寄存器数量 > 10（如 `read_holding_registers(0, count=15)`）。
*   **故障表现**: 靶机会返回一串非法的随机 Junk Data 并强制断开 Socket。
*   **验证工具**: `python fuzzer_engine_v2.py --mode OVERSIZED` (作为攻击端) 或直接使用 `pytest`。

### 2.2 BUG_LEAK (连接泄露/资源枯竭)
*   **触发条件**: 活动连接数超过 5 个。
*   **故障表现**: 当第 6 个连接进来时，靶机不再响应任何数据（HANGING），也不主动断开，模拟受测设备句柄耗尽导致的死锁。
*   **验证工具**: `python test_modbus_soak.py --count 10 --interval 0.5`。

### 2.3 BUG_STACK (解析器深度挂起)
*   **触发条件**: 接收到的 MBAP Length 字段 > 200，但后续没有足够的数据负载。
*   **故障表现**: 靶机的协议解析协程进入无限等待，该连接被永久占用。
*   **验证工具**: 仿真器的 `TRUNCATED` 模式。

## 3. 闭环验证流程

1.  **启动靶机 (开启溢出漏洞)**:
    ```bash
    python vulnerable_target.py --port 5021 --bug BUG_OOB
    ```
2.  **运行探测脚本**:
    ```bash
    # 使用测试工具对靶机进行攻击性探测
    python verify_v2.py --port 5021
    ```
3.  **预期结果**: 探测脚本应能捕获到非标准响应或连接超时，从而证实“漏洞已发现”。

---
*版本: v1.0.0*  
*维护者: QA 团队*
