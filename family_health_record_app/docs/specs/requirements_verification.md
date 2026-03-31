# 需求核验报告 (Requirements Verification Report)

> 核验人: Agent-I  
> 核验日期: 2026-03-31  
> 项目: family_health_record_app  
> 依据文档: PRD.md §4.1、§5.1-§5.3 + UI_SPEC.md §3

---

## 核验结果总览

| 需求编号 | 需求描述 | 核验结果 | 代码证据 | 备注 |
|:---:|---|:---:|---|---|
| 1 | 家庭成员档案管理（支持多成员切换） | ✅ 已实现 | `backend/app/routers/members.py:62-143` — CRUD 全量实现（list/create/get/update/delete），含软删除(`is_deleted` 字段)。前端 `frontend/src/app/page.tsx:248-283` 展示成员卡片列表，支持点击切换。 | 成员类型(child/adult/senior)区分完整，前端有类型标签颜色映射。 |
| 2 | 检查单上传与原件保存 | ✅ 已实现 | `backend/app/routers/documents.py:61-99` — POST `/documents/upload` 接收文件并写入 `uploads/` 目录。`backend/app/models/document.py:10-24` — DocumentRecord 模型含 `file_url` 字段。 | 支持 JPG/PNG/PDF 上传，文件持久化到本地磁盘。 |
| 3 | 服务端私有环境完成脱敏后发送 OCR | ⚠️ 部分实现 | `backend/app/services/image_processor.py:5-27` — `desensitize_image()` 函数已实现（遮盖顶部15%+底部10%）。`backend/app/services/ocr_orchestrator.py:86-112` — 但 OCR 编排器**未调用脱敏函数**，直接将原图 base64 发送给 SiliconFlow API。 | **关键缺陷**: 脱敏函数存在但未被 OCR 流程调用，违反 PRD §7 中"不向公有云发送原图"约束。 |
| 4 | 多模态 OCR 候选结构化抽取 | ✅ 已实现 | `backend/app/services/ocr_orchestrator.py:86-156` — 调用 SiliconFlow API (DeepSeek-OCR) 进行多模态识别，解析 JSON 输出。含 E2E 快速通道模拟。 | 支持眼科指标(眼轴/视力)提取，含 JSON 清理和容错逻辑。 |
| 5 | 规则引擎校验 | ✅ 已实现 | `backend/app/services/rule_engine.py:45-84` — `check_ocr_result()` 实现: ①检查日期完整性 ②单位校验 ③生理阈值校验 ④左右眼配对校验。`ocr_orchestrator.py:142` 在 OCR 后自动调用。 | 覆盖 PRD §5.2 中 6 种触发条件中的 4 种（单位不匹配、左右眼缺失、重复冲突值、检查日期缺失）。 |
| 6 | 人工确认与修订 | ✅ 已实现 | `backend/app/routers/review.py:91-232` — approve/reject/save-draft 三态操作。`frontend/src/app/review/page.tsx:195-226` — 前端审核页支持字段编辑、置信度条、冲突提示、审核轨迹。 | 修订记录写入 `audit_trail` JSON 字段，含时间戳。 |
| 7 | 结构化入库 | ✅ 已实现 | `backend/app/routers/documents.py:156-236` 和 `review.py:144-230` — 审核通过后创建 ExamRecord、Observation、DerivedMetric 记录。`backend/app/models/observation.py:26-53` — 数据模型完整。 | Observation 为正式指标表唯一数据来源，符合 PRD §5.4。 |
| 8 | 3 个月趋势图与报警提示 | ⚠️ 部分实现 | `backend/app/routers/trends.py:15-64` — 趋势 API 返回 series + reference_range + alert_status + comparison。`frontend/src/app/page.tsx:406-449` — 眼轴趋势图使用 recharts。 | 后端支持多指标趋势查询，但前端**仅硬编码展示眼轴**，缺少血糖/血脂/身高/体重趋势图表。报警仅有 `alert_status` 字段，无红区可视化。 |
| 9 | 审核触发条件（6 种情况） | ⚠️ 部分实现 | `backend/app/services/rule_engine.py:49-83` — 实现 4 种: ①检查日期缺失 ②单位不匹配 ③数值越界 ④左右眼缺失。`ocr_orchestrator.py:114-116` — OCR 接口超时处理。 | **缺失**: "同一指标重复冲突值"检测未实现（规则引擎无冲突值去重逻辑）。 |
| 10 | 状态流转（标准+异常） | ⚠️ 部分实现 | `documents.py:95` uploaded → `ocr_orchestrator.py:154` rule_checking/approved → `documents.py:235` persisted。`review.py:246-258` review_rejected。模型 `document.py:17` 含 status 字段。 | **缺失**: `desensitizing` 和 `ocr_processing` 中间状态未显式流转（上传后直接进入 OCR，无状态更新）。异常状态 `ocr_failed` 仅返回 error 消息，未持久化到 DB。 |
| 11 | 数据留存与追溯（4 层存储） | ⚠️ 部分实现 | ①原始文件: `documents.py:87-89` 保存到 `uploads/`。②脱敏文件: `image_processor.py` 存在但未集成。③原始 OCR JSON: `document.py:32` OCRExtractionResult.raw_json。④人工修订: `review.py:128-141` audit_trail 含时间戳。 | **缺失**: 脱敏文件未实际生成和存储。正式 observation 是图表数据来源（符合 PRD §5.4）。 |
| 12 | 空状态引导页 | ✅ 已实现 | `frontend/src/app/page.tsx:148-233` — 无成员时显示欢迎文案、引导说明、「添加第一位成员」按钮。与 UI_SPEC §3.0 完全一致。 | 创建成功后自动返回列表页展示新成员卡片。 |
| 13 | 成员卡片列表 | ✅ 已实现 | `frontend/src/app/page.tsx:248-283` — 展示成员头像/首字母、名称、类型标签、最近检查时间、待审核数。与 UI_SPEC §3.1 一致。 | 待审核数和预警摘要依赖后端返回，当前后端未提供这些字段（前端仅展示静态数据）。 |
| 14 | 上传流程 | ⚠️ 部分实现 | `frontend/src/app/page.tsx:131-144` — 文件选择器 + 上传 + OCR 提交。`frontend/src/app/page.tsx:487-523` — OCR 失败时手工录入表单。 | **缺失**: 无进度条展示（UI_SPEC §3.4 要求"上传中→脱敏中→识别中"进度条）。文件类型说明缺失。 |
| 15 | OCR 审核页 | ✅ 已实现 | `frontend/src/app/review/page.tsx:1-516` — 完整实现: 置信度条(§3.5)、冲突提示区、左右分栏布局、字段编辑器、审核轨迹、三态操作按钮。 | 与 UI_SPEC §3.5 高度一致。脱敏图预览区域当前仅显示占位符（因脱敏未实际执行）。 |
| 16 | 趋势页 | ⚠️ 部分实现 | `frontend/src/app/page.tsx:406-449` — 眼轴趋势图含左右眼双线、参考区间背景。后端 `trends.py` 支持多指标查询。 | **缺失**: 无独立趋势页路由（集成在 Dashboard 中）。无指标切换标签栏、时间范围切换（1月/3月/6月/1年）。缺少血糖/血脂/身高/体重图表。 |
| 17 | 成员创建/编辑页 | ⚠️ 部分实现 | `frontend/src/app/page.tsx:171-232` 和 `295-358` — 创建表单含姓名/性别/出生日期/成员类型。编辑功能通过 API 支持（`client.ts:36-43`），但**前端无编辑入口 UI**。 | **缺失**: 成员编辑页 UI 未实现。删除成员的二次确认对话框未实现。 |

---

## 核验统计

| 状态 | 数量 | 占比 |
|:---:|:---:|:---:|
| ✅ 已实现 | 6 | 35% |
| ⚠️ 部分实现 | 11 | 65% |
| ❌ 未实现 | 0 | 0% |
| ❓ 无法确认 | 0 | 0% |

---

## 关键风险项 (P0)

1. **脱敏流程未接入 OCR 链路** (需求 #3): `image_processor.desensitize_image()` 已实现但未被 `ocr_orchestrator` 调用，原图直接发送至公有云 API，违反 PRD §7 安全约束。
2. **趋势图表覆盖不全** (需求 #8/#16): 前端仅展示眼轴趋势，缺少 PRD §4.4 定义的 9 项指标中的 7 项（身高/体重/血糖/血脂全套）。
3. **成员编辑功能缺失前端 UI** (需求 #17): 后端 API 完整，但前端无编辑入口和删除确认对话框。

## 次要风险项 (P1)

4. **审核触发条件不完整** (需求 #9): 缺少"同一指标重复冲突值"检测逻辑。
5. **状态流转不完整** (需求 #10): 缺少中间状态(desensitizing/ocr_processing)显式更新，`ocr_failed` 未持久化。
6. **脱敏文件未实际存储** (需求 #11): 4层存储中脱敏文件层缺失。
7. **上传流程缺少进度条** (需求 #14): UI_SPEC 要求的三阶段进度条未实现。

---

## 核验结论

项目核心业务链路（上传 → OCR → 规则校验 → 人工审核 → 入库 → 趋势）已贯通，但存在**1项安全红线问题**（脱敏未接入）和多项功能缺口。建议在修复脱敏链路后进入下一阶段测试。
