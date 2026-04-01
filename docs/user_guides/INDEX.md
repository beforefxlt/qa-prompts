# 用户指南索引

本目录收录面向使用者的操作指南。  
如果你已经知道自己要走哪条流程，可以直接打开对应文档；如果还不确定，先从本页判断入口。

## 推荐阅读顺序

1. 第一次接触工作流：
   `docs/onboarding.md`
2. 要走标准测试交付主链：
   `docs/user_guides/test_lifecycle_guide.md`
3. 要做缺陷初诊与问题隔离：
   `docs/user_guides/bug_diagnostic_flow_guide.md`
4. 要理解收口复核与测试代码整理边界：
   `docs/user_guides/qa_cleanup_principles_zh.md`

## 指南列表

| 文档 | 适用场景 | 说明 |
| :--- | :--- | :--- |
| `docs/user_guides/test_lifecycle_guide.md` | 测试主交付流程 | 解释 `/test-lifecycle` 的输入、步骤、主链边界与收口方式 |
| `docs/user_guides/bug_diagnostic_flow_guide.md` | 缺陷初诊与建单草稿 | 解释 `/bug-diagnostic-flow` 的补证、隔离、`/tmp/` 草稿边界 |
| `docs/user_guides/health_record_app_delivery_guide.md` | 家庭检查单管理应用交付 | 解释家庭健康数据应用从规格冻结到多 Subagent 开发与回归验收的推进方式 |
| `docs/user_guides/qa_cleanup_principles_zh.md` | 收口复核与测试代码整理 | 说明 `reviewer-agent` 与 `test-code-simplifier` 的共性原则 |
| `docs/user_guides/traceability_test_design_guide.md` | 可追溯测试架构设计 | 说明 TC 编号、P1-P5 分层、`traceability.yaml`、统一审计与门禁升级的设计方法 |

## 与其他文档的关系

- 如果你想先建立整个仓库的总览认知，先看 `docs/onboarding.md`
- 如果你想看技能与工作流为什么这样设计，去 `docs/plans/`
- 如果你想看案例、培训材料或长期方法论沉淀，去 `docs/training/` 与 `docs/studyInspire-insights/`
