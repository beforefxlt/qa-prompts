# Modbus Fuzzer 架构 2.0：插件化异常驱动方案

## 1. 设计目标
为了应对不断增加的协议异常场景（如超长报文、TCP 分片、非标功能码），2.0 架构将“异常注入逻辑”与“协议处理引擎”彻底分离，实现 **“热插拔、可堆叠、多维度输出”**。

## 2. 核心组件 (Core Modules)

### 2.1 驱动引擎 (Fuzzer Engine)
*   职责：处理基础 TCP/IP 链接、MBAP 解析、Plugin 生命周期管理。
*   核心逻辑：在 PDU 处理的关键生命周期点触发“钩子 (Hooks)”。

### 2.2 异常插件 (Anomaly Plugins)
每个异常被抽象为一个独立的类，继承自 `BaseAnomaly`。
*   **ON_PDU_RECEIVED**: 修改接收到的请求。
*   **ON_RESPONSE_PREPARE**: 修改即将发出的响应（如篡改长度、填充垃圾数据）。
*   **ON_RESPONSE_SEND**: 修改传输层行为（如模拟 TCP 分片写）。

### 2.3 报告与输出 (Reporters)
*   **PCAP Reporter**: 联动抓包，自动标记异常包序列。
*   **JSON/Markdown Reporter**: 聚合测试结果，生成漏洞扫描简报。

## 3. 插件化演进：以 Oversized 为例
以往需要修改 `malicious_simulator.py` 的 switch-case。现在只需新增 `plugins/oversized.py`：
```python
class OversizedAnomaly(BaseAnomaly):
    def on_response_prepare(self, pdu, context):
        # 强制将 Length 改为 512，并填充零
        return pdu + os.urandom(512 - len(pdu))
```

## 4. 实施路径
1.  **阶段 1**: 重构 `malicious_simulator.py` 为 `FuzzerEngine` 类。
2.  **阶段 2**: 引入 `PluginManager` 动态加载机制（基于 `importlib`）。
3.  **阶段 3**: 实现 `OversizedPayload` 与 `SlowTickling` (TCP 分片) 插件作为内建示例。
4.  **阶段 4**: 集成统一的日志与报告模块。

## 5. 预期收益
*   **开发解耦**: 测试工程师只需关注异常报文逻辑，无需操作 Socket。
*   **场景堆叠**: 可以同时开启“TID 篡改”+“响应延时”+“TCP 分片”组合攻击，最大程度模拟极端复杂工况。

---
*版本: v2.0.0-draft*
