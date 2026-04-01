# 家庭检查单管理应用 - 当前状态与下一步计划

> **最后更新**: 2026-04-01 10:45
> **版本**: v2.0.0 (前端完备性重构版)
> **测试状态**: 72 pytest passed, MCP E2E 验证中 (1/8 发现 Bug)

---

## 一、当前状态总览

### 1. 后端 (FastAPI + SQLAlchemy 异步)
| 模块 | 状态 | 文件 |
|:---|:---|:---|
| 数据模型 | ✅ 完成 | `models/member.py`, `document.py`, `observation.py` (7表, 无accounts) |
| 成员服务 | ✅ 完成 | `routers/members.py` (GET/POST/PUT/DELETE) |
| 文档服务 | ✅ 完成 | `routers/documents.py` (上传/查询/submit-ocr, UUID文件名) |
| 审核服务 | ✅ 完成 | `routers/review.py` (approve/reject/save-draft) |
| 趋势服务 | ✅ 完成 | `routers/trends.py` (trends/vision-dashboard/growth-dashboard) |
| OCR编排 | ✅ 已完成 | `services/ocr_orchestrator.py` (Qwen2.5-VL-32B 模型 + JSON解析增强) |
| 规则引擎 | ✅ 完成 | `services/rule_engine.py` (单位/范围/左右眼校验) |
| 图像处理 | ✅ 完成 | `services/image_processor.py` (try/catch兜底) |
| 存储客户端 | ✅ 完成 | `services/storage_client.py` (MinIO boto3) |

### 2. 前端 (Next.js 15 + App Router)
| 模块 | 状态 | 文件/路由 |
|:---|:---|:---|
| 首页列表 | ✅ 完成 | `src/app/page.tsx` (精简列表页) |
| 成员看板 | ✅ 完成 | `src/app/members/[id]/page.tsx` (聚合看板) |
| 成员管理 | ✅ 完成 | `src/app/members/new/page.tsx`, `edit/page.tsx` |
| 趋势详情 | ✅ 完成 | `src/app/members/[id]/trends/page.tsx` |
| 记录详情 | ✅ 完成 | `src/app/members/[id]/records/[recordId]/page.tsx` |
| 审核工作流 | ✅ 完成 | `src/review/page.tsx` (双栏布局/冲突标红) |
| API 客户端 | ✅ 完成 | `src/app/api/client.ts` (新增详情接口支持) |
| 工程化 | ✅ 完成 | `tsconfig.json` (@/ 路径别名配置) |

### 3. 测试
| 类型 | 用例数 | 状态 |
|:---|:---|:---|
| 单元测试 | 42 | ✅ 通过 |
| API合约 | 7 | ✅ 通过 |
| Golden Set | 4 | ✅ 通过 |
| P3基建容灾 | 10 | ✅ 通过 |
| P5用户体验 | 11 | ✅ 通过 |
| 路由层测试 | 29 | ✅ 通过 |
| **总计** | **72** | **✅ 72 passed, 0 failed** |
| **覆盖率** | **54%** | 见下文ROI分析 |

### 4. 规格文档 (8个)
| 文档 | 状态 | 关键变更 |
|:---|:---|:---|
| PRD.md | ✅ 已更新 | 内网免登录+首次使用引导 |
| UI_SPEC.md | ✅ 已更新 | 8页信息架构(空状态/成员管理/审核页) |
| API_CONTRACT.md | ✅ 已更新 | 移除认证,补充CRUD+错误码 |
| DATABASE_SCHEMA.md | ✅ 已更新 | 移除accounts表,reviewer_id可选 |
| ARCHITECTURE.md | ✅ 已更新 | 移除鉴权模块 |
| TEST_STRATEGY.md | ✅ 已更新 | 补充P3/P5场景 |
| IMPLEMENTATION_PLAN.md | ✅ 已更新 | 9个Task(0→8) |
| OCR_SCHEMA.md | ✅ 已更新 | 置信度分级+审核交互约束 |

### 5. 测试设计资产 (4个)
| 文档 | 内容 |
|:---|:---|
| test_strategy_matrix.md | 107个P1-P5测试用例 |
| boundary_value_analysis.md | 145个边界值用例 |
| exploratory_testing_scenarios.md | 67个探索性测试场景 |
| requirements_verification.md | 17项需求核验(6✅/11⚠️) |

### 6. 缺陷治理 (Defect Governance)

本项目共修复 **17 个** 已知缺陷 (`BUG-001` ~ `BUG-017`)，涵盖架构偏离、隐私合规、模型幻觉及业务闭环四大维度。

> [!NOTE]
> 详细的根因分析、排查过程与修复方案已归档至 [缺陷与诊断排查记录 (Bug Log)](file:///c:/Users/Administrator/qa-prompts/family_health_record_app/docs/BUG_LOG.md)。

---

---

| 步骤 | 状态 | 详情 |
|:---|:---|:---|
| 1. 后端启动 | ✅ | 端口 8000 (已修复 CORS)，uvicorn 运行中 |
| 2. 前端启动 | ✅ | 端口 3001，已清理 .next 缓存 |
| 3. TC-MCP-001 | ⚠️ | 首页加载成功，但存在 Hydration Error 和 `/>` 字符外泄 |
| 4. TC-MCP-002 | ❌ | 成员创建被阻断。UI 优化已完成（出生年月选择），但点击保存无效 |
| 5. 后端稳定性 | ✅ | 已通过 `rebuild_db.py` 完成数据库重建，API 返回正常 |

**已定位的关键缺陷**:
- **BUG-018**: 前端组件 Hydration 冲突，导致事件绑定失效。
- **BUG-019**: JSX 渲染污染，页面出现悬空 `/>` 字符。
- **CORS 冲突**: 后端已更新 `main.py` 允许 `3001` 跨域。

**OCR 提取结果示例**:
```json
{
  "exam_date": "2018-09-21",
  "institution": "HAAG-STREIT DIAGNOSTICS",
  "observations": [
    {"metric_code": "axial_length", "value_numeric": 24.35, "unit": "mm", "side": "right"},
    {"metric_code": "axial_length", "value_numeric": 23.32, "unit": "mm", "side": "left"}
  ]
}
```

---

## 三、生产部署准备清单

### 3.1 最小化部署（内网低频使用）

**唯一目标**: 让内网同事能用浏览器打开并正常使用全部功能。

- [ ] PostgreSQL 数据库创建与配置（或继续用 SQLite）
- [ ] Alembic 迁移脚本生成与执行（如选 PostgreSQL）
- [ ] 后端启动: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [ ] 前端启动: `npm run dev` 或 `npm run build && npm start`
- [ ] 确认 72 个测试通过
- [ ] 手动验证核心流程：创建成员 → 上传 → 审核 → 趋势查看

### 3.2 不做（内网场景暂不需要）

| 项目 | 原因 |
|:---|:---|
| CORS 白名单限制 | 内网安全，无需限制 |
| 请求速率限制 | 极低频使用，无需限流 |
| 日志脱敏 | 内网自用，隐私要求低 |
| 数据库连接加密 | 内网环境，无外部风险 |
| 监控告警 | 低频使用，人工巡检即可 |
| Docker 容器化 | 简单直接部署，无需容器 |
| 性能测试 | 极低频，单用户场景 |

### 3.3 快速启动方式（推荐）

```bash
# 后端
cd family_health_record_app/backend
pip install -r requirements.txt  # 或 poetry install
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端
cd family_health_record_app/frontend
npm install
npm run dev

# 访问
# 内网同事访问: http://<服务器IP>:3001
```

**数据库**: 默认 SQLite，文件名 `health_record.db`，自动创建。
**存储**: 默认本地 `uploads/` 目录，MinIO 自动降级。
**OCR**: SiliconFlow API + Qwen2.5-VL-32B-Instruct 模型。

---

## 三、自动同步机制

已创建 `auto_sync.py` 脚本，每 15 分钟自动:
1. 运行 pytest 统计测试结果
2. 扫描代码文件数量
3. 检查 git 变更状态
4. 更新 DEVELOPMENT_LOG.md
5. 如有代码变更则自动 commit，并更新对应文档。

**使用方式**:
```bash
# 手动运行
python auto_sync.py

# Windows 任务计划程序 (每15分钟)
schtasks /create /tn "DevLogSync" /tr "python C:\Users\Administrator\qa-prompts\family_health_record_app\auto_sync.py" /sc minute /mo 5
```

---

## 四、下一步行动建议

### 立即执行 (开启新 Session 优先)
1. **修复前端 500 错误**: 彻底排查 `src/app/page.tsx` 语法，解决 `Internal Server Error`。
2. **回归 MCP 测试**: 顺序执行 `TC-MCP-001` 至 `TC-MCP-008`。
3. **完成成员创建**: 验证“保存并开始记录”按钮的连通性。

### 短期 (本周)
5. 配置 CI/CD 流水线
6. 补充 P5 用户体验测试
7. PostgreSQL 迁移配置

### 中期 (下周)
8. 性能优化 (分页/压缩)
9. 测试覆盖率提升至 80%+
10. 生产环境部署准备

---

## 五、关键文件路径

```
family_health_record_app/
├── DEVELOPMENT_LOG.md          # 开发日志 (自动同步)
├── auto_sync.py                # 自动同步脚本
├── update_dev_log.py           # 旧版更新脚本
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI 入口 (42行)
│   │   ├── db.py               # 数据库配置
│   │   ├── models/             # 7个数据模型
│   │   ├── routers/            # 4个路由文件
│   │   ├── schemas/            # Pydantic 模型
│   │   └── services/           # 4个服务文件
│   └── tests/                  # 9个测试文件 (32用例)
├── frontend/
│   ├── tsconfig.json           # 包含 @/ 别名配置
│   └── src/
│       ├── components/         # 3个核心提取组件 (TrendChart, MemberForm, UploadOverlay)
│       └── app/
│           ├── page.tsx        # 首页引导/列表
│           ├── api/client.ts   # 集成 vision/growth/record 详情接口
│           └── members/        # [NEW] 路由解耦层
│               ├── new/        # 创建成员
│               └── [id]/       
│                   ├── page.tsx       # Dashboard 看板
│                   ├── edit/          # 成员档案管理
│                   ├── trends/        # 趋势详情页
│                   └── records/
│                       └── [recordId]/ # 单次记录详情页
└── docs/specs/                 # 8个规格文档
```

---

## 六、环境配置

### 后端启动
```bash
cd family_health_record_app/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端启动
```bash
cd family_health_record_app/frontend
npm run dev
```

### 运行测试
```bash
cd family_health_record_app/backend
python -m pytest tests/ -v
```

### 环境变量
```
DATABASE_URL=sqlite+aiosqlite:///./health_record.db
SILICONFLOW_API_KEY=your_key_here
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```
