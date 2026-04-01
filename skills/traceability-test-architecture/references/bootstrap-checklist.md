# 可追溯测试架构启动清单

## 初始化阶段

1. 确认规格来源文档。
2. 先拆出第一批正式 TC 编号。
3. 先创建 `traceability.yaml`。
4. 先创建测试目录分层。
5. 先创建 Python 编排脚本骨架。
6. 再开始补测试 stub。
7. 最后再推进具体实现代码。

## 第一批必须存在的文件

```text
traceability.yaml
scripts/qa_unit.py
scripts/qa_contract.py
scripts/qa_integration.py
scripts/qa_resilience.py
scripts/qa_golden.py
scripts/qa_e2e.py
scripts/qa_all.py
scripts/qa_audit.py
backend/tests/unit/
backend/tests/contract/
backend/tests/integration/
backend/tests/resilience/
backend/tests/golden/
frontend/e2e/
```

## 第一批校验点

1. 是否已经存在至少一个 `TC-P1-*` 或 `TC-P5-*`。
2. 是否能从 `traceability.yaml` 找到对应测试文件。
3. 是否已有统一入口可以跑完整摘要。
4. 是否已明确哪些条目是 `stub`、哪些是 `missing`。
