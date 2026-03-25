# 开发日志 (Development Log) - 网络损伤模拟工具

## 2026-03-25: 修复致命缺陷并补齐单元测试

### 1. 缺陷修复 (Bug Fix)
- **问题描述**: `start_random_loop` 方法中 `jitter`, `delay`, `loss` 变量未定义即被调用，导致脚本启动后立即抛出 `NameError`。
- **修复方案**: 在 `while` 循环内部显式调用 `random` 模块根据 `DEFAULT_CONFIG` 生成这些参数。
- **关联缺陷单**: `BUG-001` (已验证通过)

### 2. 测试增强 (Test Enhancement)
- **新增单元测试**: 建立了 `tests/test_random_impairment.py`。
- **覆盖范围**:
    - `NetImpairmentManager` 的 `apply` 与 `clean` 核心方法 (Mock 系统调用)。
    - `check_privileges` 权限校验逻辑。
    - `KeyboardInterrupt` (Ctrl+C) 自动清理逻辑验证。
    - `tc` 命令执行失败时的异常捕获与日志记录。
- **环境隔离**: 引入了 `.venv` 虚拟环境，并使用 `pytest` 进行自动化验证。

### 3. 一致性检查
- 已更新 `network_impairment_tool/README.md` 中的测试说明。
- 已同步 P1-P5 测试策略大纲至 `network_impairment_tool/docs/test_specification_zh.md`。
- **独立性决策**: 根据要求，`network_impairment_tool` 的测试规格说明书保持独立，不合入 `factory_inspector` 全局文档。
