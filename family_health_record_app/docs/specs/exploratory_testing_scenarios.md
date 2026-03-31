# 探索性测试场景设计 (Exploratory Testing Scenarios)

> 基于"五边形人格"模型，针对 family_health_record_app 的破坏性/探索性测试场景。
> 版本: v1.0 | 日期: 2026-03-31 | 设计者: Agent-H

## 状态流转参考

- 标准流转: `uploaded → desensitizing → ocr_processing → rule_checking → pending_review → approved → persisted`
- 异常流转: `ocr_failed`, `rule_conflict`, `review_rejected`

---

## 1. 破坏者人格 (The Destroyer) — 打破系统假设

| 场景编号 | 人格类型 | 测试路径 | 预期系统行为 | 风险等级 |
|:---:|:---:|:---|:---|:---:|
| D-001 | 破坏者 | POST `/api/v1/documents/upload` 上传 `.txt` 纯文本文件 | 服务端应拒绝非图片/非PDF格式文件，返回 400 错误及明确提示 | P1 |
| D-002 | 破坏者 | POST `/api/v1/documents/upload` 上传 `.exe` 可执行文件 | 服务端应拒绝并记录安全告警，文件不应落盘到 `uploads/` 目录 | P1 |
| D-003 | 破坏者 | POST `/api/v1/documents/upload` 上传 `.pdf` 文件 | 应接受 PDF（PRD §5.1 明确支持），进入脱敏→OCR 流程 | P2 |
| D-004 | 破坏者 | POST `/api/v1/documents/upload` 上传 >50MB 超大图片 | 服务端应返回 413 Payload Too Large 或明确的大小限制提示，不应 OOM | P1 |
| D-005 | 破坏者 | POST `/api/v1/documents/upload` 上传 0 字节空文件 | 应返回 400 错误，不应创建 DocumentRecord 记录 | P2 |
| D-006 | 破坏者 | POST `/api/v1/documents/upload` 上传损坏的 JPEG（文件头正确但内容截断） | OCR 流程应捕获异常，状态流转至 `ocr_failed`，不应崩溃 | P2 |
| D-007 | 破坏者 | POST `/api/v1/documents/upload` 上传文件名含路径遍历字符 `../../../etc/passwd` | 服务端应 sanitize 文件名，防止路径遍历攻击 | P1 |
| D-008 | 破坏者 | 同一文件在 1 秒内并发发起 5 次上传请求 | 应创建 5 个独立 DocumentRecord 或去重拒绝，不应出现数据库死锁 | P2 |
| D-009 | 破坏者 | 上传后、OCR 处理中（`ocr_processing` 状态），调用 DELETE `/api/v1/members/{memberId}` 删除关联成员 | 成员应软删除（`is_deleted=True`），但 DocumentRecord 保留引用，OCR 流程应完成或安全终止 | P2 |
| D-010 | 破坏者 | POST `/api/v1/documents/upload` 时 `member_id` 传入已软删除成员的 UUID | 应返回 404（`documents.py:84-85` 已实现此校验） | P3 |
| D-011 | 破坏者 | POST `/api/v1/documents/{docId}/submit-ocr` 对同一 document 连续调用 3 次 | 第二次及后续调用应幂等处理或返回冲突，不应创建重复 OCRExtractionResult | P2 |
| D-012 | 破坏者 | 上传后手动删除 `uploads/` 下的物理文件，再调用 submit-ocr | OCR orchestrator 应返回 `error`（`ocr_orchestrator.py:59-61` 已检查文件存在性），状态应转为 `ocr_failed` | P2 |
| D-013 | 破坏者 | 上传含 SQL 注入 payload 的文件名（如 `test'; DROP TABLE members;--.jpg`） | 文件名应被安全存储，SQL 不应被执行 | P1 |
| D-014 | 破坏者 | 上传时不传 `member_id` 参数且数据库中无任何成员 | 应返回 400 "未找到可用成员，请先创建成员"（`documents.py:74-75` 已实现） | P3 |
| D-015 | 破坏者 | 上传同名文件覆盖已有文件（`uploads/` 目录中已存在同名文件） | 当前实现 `shutil.copyfileobj` 会静默覆盖（`documents.py:88-89`），应警告或生成唯一文件名 | P2 |

---

## 2. 混淆者人格 (The Confuser) — 制造数据混乱

| 场景编号 | 人格类型 | 测试路径 | 预期系统行为 | 风险等级 |
|:---:|:---:|:---|:---|:---:|
| C-001 | 混淆者 | 上传成人血糖血脂检查单，但关联到 `member_type=child` 的儿童成员 | OCR 应正常抽取，规则引擎不应拦截（当前 `rule_engine.py` 无成员类型×指标匹配校验），但趋势图可能展示不匹配数据 | P3 |
| C-002 | 混淆者 | 上传儿童身高体重检查单，关联到 `member_type=adult` 的成人成员 | 同上，系统不应阻止，但业务合理性存疑 | P3 |
| C-003 | 混淆者 | 同一张检查单中同一指标（如 `glucose`）出现两个不同值（如 5.2 和 7.8） | 规则引擎应检测到冲突（`rule_engine.py` 当前未实现重复值检测），应进入 `rule_conflict` 状态 | P2 |
| C-004 | 混淆者 | 左右眼数据互换：OCR 将左眼值识别到 `side=right`，右眼值识别到 `side=left` | 规则引擎无法检测语义串位（仅检查左右眼是否配对存在），应进入人工审核提示 | P3 |
| C-005 | 混淆者 | 检查日期设置为未来日期（如 2030-01-01） | 当前代码无未来日期校验（`documents.py:159` 仅做 `fromisoformat` 解析），应接受但趋势图会出现异常时间线 | P2 |
| C-006 | 混淆者 | 检查日期早于成员出生日期（如成员 DOB=2020-01-01，检查日期=2015-06-01） | 当前代码无此校验，`_calculate_baseline_age_months` 会返回负值后被 `max(0)` 截断，但业务上不合理 | P2 |
| C-007 | 混淆者 | 上传检查单中 `exam_date` 格式非法（如 "2026/13/45" 或 "March 31st"） | 应进入 `rule_conflict` 状态（`documents.py:160-164` 已处理解析异常） | P2 |
| C-008 | 混淆者 | 上传检查单中 `exam_date` 字段完全缺失 | 规则引擎应检测到（`rule_engine.py:52-53`），进入 `rule_conflict` | P2 |
| C-009 | 混淆者 | 上传检查单中指标单位错误（如身高单位传 `kg` 而非 `cm`） | 规则引擎应拒绝（`rule_engine.py:36-37` 单位校验），进入 `rule_conflict` | P2 |
| C-010 | 混淆者 | 上传检查单中指标值超出生理边界（如身高 500cm、体重 0.01kg） | 规则引擎应拒绝（`rule_engine.py:40-41` 阈值校验），进入 `rule_conflict` | P2 |
| C-011 | 混淆者 | 上传检查单中眼轴只有左眼数据，缺少右眼 | 规则引擎应检测到（`rule_engine.py:74-78` 左右眼配对校验），进入 `rule_conflict` | P2 |
| C-012 | 混淆者 | 上传检查单中所有 observations 为空数组 `[]` | 规则引擎应检测到（`rule_engine.py:57-58`），进入 `rule_conflict` | P2 |
| C-013 | 混淆者 | 上传检查单中 `metric_code` 为未定义指标（如 `blood_pressure`） | 规则引擎应放行（`rule_engine.py:33` 未定义指标暂时放行），但趋势图无法展示 | P3 |
| C-014 | 混淆者 | 审核通过后，手动修改数据库中 `observations` 表的 `value_numeric` 为异常值 | 趋势图应展示被篡改的值，系统无数据完整性校验机制 | P3 |
| C-015 | 混淆者 | 同一成员上传多张检查单，检查日期完全相同 | 系统应允许，趋势图中同日期多个数据点应正确渲染 | P3 |

---

## 3. 急躁者人格 (The Impatient User) — 测试并发和竞态

| 场景编号 | 人格类型 | 测试路径 | 预期系统行为 | 风险等级 |
|:---:|:---:|:---|:---|:---:|
| I-001 | 急躁者 | 在首页快速连续点击"录入新检查单"按钮 10 次 | 前端应防抖/节流，后端应处理并发上传请求，不应出现重复 DocumentRecord 或数据库异常 | P2 |
| I-002 | 急躁者 | 调用 `submit-ocr` 后立即刷新页面（中断 HTTP 连接） | 后端 OCR 流程应继续执行或安全回滚，不应出现文档悬停在 `ocr_processing` 永久状态 | P2 |
| I-003 | 急躁者 | 两个用户/标签页同时 POST `/api/v1/review-tasks/{taskId}/approve` 同一审核任务 | 第二个请求应返回 409 冲突（`review.py:103-104` 检查状态），不应重复写入 Observation | P1 |
| I-004 | 急躁者 | 在审核任务 `pending` 状态下，同时调用 approve 和 reject | 先到达的请求应生效，后到达的请求应返回 409 | P1 |
| I-005 | 急躁者 | 在审核过程中（审核页已打开但未提交），通过另一标签页修改成员信息（如出生日期） | 审核通过后 `baseline_age_months` 应基于审核时的成员信息计算，不应受中途修改影响 | P3 |
| I-006 | 急躁者 | 在 OCR 处理中（`ocr_processing` 状态），通过另一标签页删除该文档关联的成员 | 参考 D-009，OCR 应完成或安全终止，不应产生孤儿数据 | P2 |
| I-007 | 急躁者 | 快速切换成员（连续调用不同 memberId 的趋势接口） | 每个请求应返回对应成员的数据，不应出现数据串扰 | P3 |
| I-008 | 急躁者 | 在审核任务 `draft` 状态下，同时调用 save-draft 和 approve | 应正确处理状态转换，不应出现数据不一致 | P2 |
| I-009 | 急躁者 | 上传大文件后，在 OCR 超时前（120s 内）重复调用 `get_document` 查询状态 | 应正确返回当前状态，不应阻塞或超时 | P3 |
| I-010 | 急躁者 | 在趋势图加载过程中切换指标（metric 参数） | 前一个请求应被取消或忽略，应展示新指标的数据 | P3 |

---

## 4. 遗忘者人格 (The Forgetful User) — 测试空值和默认值

| 场景编号 | 人格类型 | 测试路径 | 预期系统行为 | 风险等级 |
|:---:|:---:|:---|:---|:---:|
| F-001 | 遗忘者 | 创建成员后，不上传任何检查单，直接访问该成员的趋势页 | 趋势接口应返回空 `series` 数组，`alert_status` 为 `normal`，前端应展示空状态引导 | P3 |
| F-002 | 遗忘者 | 上传检查单后，不调用 `submit-ocr`，直接返回列表页 | 文档应保持 `uploaded` 状态，前端应提示有待处理的检查单 | P3 |
| F-003 | 遗忘者 | 进入审核页（有待审核任务），不做任何操作直接离开/关闭浏览器 | 审核任务应保持 `pending` 状态，下次进入仍可查看 | P3 |
| F-004 | 遗忘者 | 删除有检查记录的成员（软删除后），再访问该成员的趋势接口 | 趋势接口应返回 404（`trends.py:17-24` 已过滤 `is_deleted=False`），前端应友好提示 | P2 |
| F-005 | 遗忘者 | 删除有检查记录的成员后，访问已关联该成员的审核任务 | 审核任务仍可访问（`review.py:62-88` 未检查成员删除状态），但成员信息可能不可用 | P2 |
| F-006 | 遗忘者 | 创建成员时 `member_type` 传入空字符串或非法值 | 后端应校验并返回 400（取决于 `MemberCreate` schema 定义） | P2 |
| F-007 | 遗忘者 | 审核任务 approve 时 `revised_items` 传空数组 `[]` | 应视为"无修改通过"，记录 `approved_without_changes` 审计事件（`review.py:133-137` 已处理） | P3 |
| F-008 | 遗忘者 | 上传检查单时 `member_id` 不传（为 null） | 系统应自动关联到第一个可用成员（`documents.py:68-76` 已实现此逻辑） | P3 |
| F-009 | 遗忘者 | 审核任务 reject 后，不重新上传也不处理 | 文档应保持 `review_rejected` 状态，前端应提供重试入口 | P3 |
| F-010 | 遗忘者 | OCR 失败（`ocr_failed` 状态）后，不重新上传也不处理 | 文档应保持在 `ocr_failed` 状态，前端应提示错误原因和重试选项 | P2 |
| F-011 | 遗忘者 | 创建成员后，立即删除，再创建同名成员 | 应允许创建（UUID 不同），历史数据不应混淆 | P3 |
| F-012 | 遗忘者 | 访问不存在的 document 详情接口 | 应返回 404（`documents.py:104-106` 已实现） | P3 |

---

## 5. 好奇者人格 (The Curious Explorer) — 探索非预期使用路径

| 场景编号 | 人格类型 | 测试路径 | 预期系统行为 | 风险等级 |
|:---:|:---:|:---|:---|:---:|
| E-001 | 好奇者 | 直接访问 `/review` 页面（无任何待审核任务） | 前端应展示空状态提示"暂无待审核任务"，不应报错 | P3 |
| E-002 | 好奇者 | 修改 URL 参数中的 `memberId` 为不存在的 UUID（如 `/members/00000000-0000-0000-0000-000000000000/trends?metric=height`） | 后端应返回 404，前端应展示友好错误页 | P2 |
| E-003 | 好奇者 | 尝试通过审核任务详情接口访问其他成员关联的审核任务（无成员级权限隔离） | 当前系统无成员级权限控制（PRD §4.3 内网免登录），应允许访问但应记录审计日志 | P3 |
| E-004 | 好奇者 | 在趋势页切换不存在的指标（如 `metric=blood_pressure`） | 趋势接口应返回空 `series` 数组（`trends.py:38` 无结果时为空列表），不应报错 | P3 |
| E-005 | 好奇者 | 直接调用 `/api/v1/members/{memberId}/vision-dashboard` 访问成人成员的视力面板 | 应返回数据（即使无视力数据），前端应优雅处理空数据 | P3 |
| E-006 | 好奇者 | 直接调用 `/api/v1/members/{memberId}/growth-dashboard` 访问成人成员的生长面板 | 应返回数据（即使无生长数据），前端应优雅处理空数据 | P3 |
| E-007 | 好奇者 | 通过浏览器开发者工具修改前端请求的 `Content-Type` 为 `application/json` 上传文件 | 后端应正确拒绝（`documents.py:62` 使用 `UploadFile` 需要 `multipart/form-data`） | P3 |
| E-008 | 好奇者 | 尝试访问不存在的 API 路由（如 `/api/v1/settings`） | 应返回 404 Not Found | P3 |
| E-009 | 好奇者 | 通过 curl 直接调用后端 API，绕过前端（如直接 POST 审核通过） | 应正常处理（内网免登录设计），但应记录审计轨迹 | P2 |
| E-010 | 好奇者 | 修改审核任务 approve 请求中的 `revised_items`，将 `value_numeric` 改为超出规则引擎边界的值 | 当前 approve 流程无二次规则校验（`review.py:182-204` 直接写入），异常值可能进入正式表 | P1 |
| E-011 | 好奇者 | 通过 URL 直接访问 `/api/v1/review-tasks/{taskId}` 获取 OCR 原始 JSON | 应返回完整 OCR 数据（`review.py:76-88`），包含 `ocr_raw_json` 和 `ocr_processed_items` | P3 |
| E-012 | 好奇者 | 尝试访问 `/health` 健康检查接口 | 应返回 `{"status": "ok", "version": "v1.3.0"}`（`main.py:33-35` 已实现） | P4 |
| E-013 | 好奇者 | 在趋势接口中传入特殊字符作为 metric（如 `metric=<script>alert(1)</script>`） | 后端应安全处理，不应出现 XSS 风险 | P2 |
| E-014 | 好奇者 | 尝试通过修改请求体中的 `document_id` 访问其他文档的 OCR 结果 | 应返回对应文档的数据（无权限隔离），但审计日志应记录访问 | P3 |
| E-015 | 好奇者 | 通过前端控制台直接调用 `fetch('/api/v1/members', {method: 'DELETE'})` | 后端 `/api/v1/members` GET 路由不匹配 DELETE 方法，应返回 405 Method Not Allowed | P3 |

---

## 风险等级说明

| 等级 | 含义 | 处理建议 |
|:---:|:---|:---|
| P1 | 严重 — 可能导致数据损坏、安全漏洞或系统崩溃 | 必须在发布前修复 |
| P2 | 高 — 可能导致功能异常或用户体验严重受损 | 应在当前迭代修复 |
| P3 | 中 — 边界情况，影响有限但应改进 | 纳入后续迭代优化 |
| P4 | 低 — 信息类或纯探索性场景 | 记录即可，无需立即处理 |

## 已发现的代码级问题汇总

基于代码审查，以下问题在测试中应重点关注：

1. **脱敏功能未接入流程**：`image_processor.py` 实现了 `desensitize_image`，但 `documents.py` 的上传流程中未调用，`desensitized_url` 始终为 `None`（违反 PRD §5.1 第 3 步和 §7 约束）
2. **文件名未做唯一化处理**：`documents.py:87` 直接使用 `file.filename`，同名文件会覆盖，且存在路径遍历风险
3. **文件类型和大小无校验**：上传接口未限制文件类型和大小
4. **approve 流程缺少二次规则校验**：`review.py:182-204` 审核通过时直接写入 Observation，未对修订后的值重新执行规则引擎校验
5. **OCR 重复提交无幂等保护**：`documents.py:117-236` 对同一 document 重复调用 submit-ocr 可能产生数据不一致
6. **无未来日期和日期逻辑校验**：检查日期可以设置为未来日期或早于出生日期
7. **同一指标重复值未检测**：`rule_engine.py` 未实现同一检查单中同一指标出现多次不同值的冲突检测
