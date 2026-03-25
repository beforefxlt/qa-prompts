# 网络损伤模拟工具 - 测试规格说明书 (Test Specification)

本文档定义了 `network_impairment_tool` 的专项测试用例，涵盖基础功能、异常保护及边界工况。

## 1. 测试用例详情 (P1-P5)

| ID | 用例名称 | 测试点 | 预期结果 | 分类标签 |
| :--- | :--- | :--- | :--- | :--- |
| TC-NET-01 | `test_impairment_apply_delay` | 在 `br0` 上注入 100ms 随机延迟并验证内核规则。 | `tc qdisc show` 包含 `delay 100ms` | P1 |
| TC-NET-02 | `test_impairment_auto_cleanup` | 脚本运行中通过 `SIGINT` (Ctrl+C) 终止。 | `tc` 规则自动清空，网络恢复 | P1 |
| TC-NET-03 | `test_impairment_invalid_iface` | 传入非法的网口名称（如 `non-exist`）。 | 脚本捕获异常并友好报错，不崩溃 | P2 |
| TC-NET-04 | `test_impairment_no_root` | 以普通用户权限尝试运行脚本。 | 脚本精准拦截并提示 `sudo` | P2 |
| TC-NET-05 | `test_impairment_tc_missing` | 模拟环境中缺失 `tc` 命令。 | 脚本识别依赖缺失并记录错误日志 | P3 |
| TC-NET-06 | `test_impairment_force_kill` | 模拟进程被 `kill -9` 杀死后，通过 README 指令手动清理。 | 手动清理成功，残留规则消失 | P3 |
| TC-NET-07 | `test_impairment_jitter_correction` | 配置 `jitter=100ms, delay=50ms` 的冲突参数。 | 脚本自动更正 `jitter=49ms` 且执行成功 | P4 |
| TC-NET-08 | `test_impairment_bridge_delivery` | 严格按 README 配置双网口桥接联通性。 | 桥接成功，且损伤脚本能作用于 br0 | P5 |

---

## 2. 关联设计文档
- [需求审计报告](requirement_audit.md)
- [全景测试策略](test_strategy_draft.md)
- [合规复核报告](reviewer_report.md)
