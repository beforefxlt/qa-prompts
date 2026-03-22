# API 契约与业务逻辑测试生成器

**版本**: v1.0
**适用场景**: RESTful API 测试、接口契约测试、业务逻辑校验
**模板编号**: API-001

---

## 模板定义

```markdown
# Role: 自动化接口测试专家

# Context:
我们需要为以下接口设计全方位的测试用例集，包含契约测试（Contract）与功能逻辑测试。

# API Specification (Swagger/JSON):
{{api_spec}}

# Business Rules:
{{business_rules}} (例如：Token 有效期 2 小时，积分扣减不能为负)

# Task:
1. 生成针对 HTTP 状态码（200, 400, 401, 403, 500）的覆盖用例
2. 针对 Payload 字段进行类型破坏性测试（Type Mismatch）
3. 根据业务规则设计跨字段的逻辑校验用例

# Constraints:
- 必须包含 Header（Content-Type, Authorization 等）的缺失测试
- 模拟高并发/幂等性测试场景（多次调用同一接口的结果预期）
- 输出格式：JSON 或 Markdown 表格

# Output Format:
| 接口路径 | 方法 | 测试场景 | 输入参数 (JSON) | 预期响应码 | 断言逻辑 |
| :--- | :--- | :--- | :--- | :--- | :--- |
```

---

## 使用示例

### 示例 1：创建订单接口测试

**输入变量**：

```json
{{api_spec}} = {
  "path": "/api/v1/orders",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {token}"
  },
  "body": {
    "product_id": "integer, required",
    "quantity": "integer, required, min=1",
    "coupon_code": "string, optional",
    "address_id": "integer, required"
  }
}
```

```
{{business_rules}} =
1. Token 有效期 2 小时，过期需刷新
2. 库存不足时不能下单
3. 优惠券不能叠加使用
4. 同一商品不能重复下单（防重）
5. 积分抵扣不能超过订单金额的 50%
```

**预期输出**：

| 用例编号 | 接口路径 | 方法 | 测试场景 | 输入参数 (JSON) | 预期响应码 | 断言逻辑 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **契约测试 - 必传字段** |
| API-001 | /api/v1/orders | POST | 正常创建订单 | `{product_id:1, quantity:2, address_id:100}` | 201 | 返回订单 ID，库存锁定 |
| API-002 | /api/v1/orders | POST | 缺少 product_id | `{quantity:2, address_id:100}` | 400 | 错误码：MISSING_PRODUCT_ID |
| API-003 | /api/v1/orders | POST | 缺少 quantity | `{product_id:1, address_id:100}` | 400 | 错误码：MISSING_QUANTITY |
| API-004 | /api/v1/orders | POST | 缺少 address_id | `{product_id:1, quantity:2}` | 400 | 错误码：MISSING_ADDRESS |
| **契约测试 - Header 校验** |
| API-005 | /api/v1/orders | POST | 缺少 Authorization | Header 无 token | 401 | 错误码：UNAUTHORIZED |
| API-006 | /api/v1/orders | POST | Token 过期 | Expired token | 401 | 错误码：TOKEN_EXPIRED |
| API-007 | /api/v1/orders | POST | 缺少 Content-Type | 无 Content-Type | 415 | 错误码：UNSUPPORTED_MEDIA_TYPE |
| **字段类型破坏测试** |
| API-008 | /api/v1/orders | POST | product_id 为字符串 | `{product_id:"abc", ...}` | 400 | 错误码：INVALID_PRODUCT_ID_TYPE |
| API-009 | /api/v1/orders | POST | quantity 为负数 | `{quantity:-1, ...}` | 400 | 错误码：QUANTITY_MUST_BE_POSITIVE |
| API-010 | /api/v1/orders | POST | quantity 为 0 | `{quantity:0, ...}` | 400 | 错误码：QUANTITY_MUST_BE_POSITIVE |
| API-011 | /api/v1/orders | POST | quantity 为浮点数 | `{quantity:1.5, ...}` | 400 | 错误码：INVALID_QUANTITY_TYPE |
| API-012 | /api/v1/orders | POST | coupon_code 超长 | `{coupon_code:"A"...(1000 字符)}` | 400 | 错误码：COUPON_CODE_TOO_LONG |
| **业务逻辑测试** |
| API-013 | /api/v1/orders | POST | 库存不足 | 商品库存=5，下单 quantity=10 | 400 | 错误码：INSUFFICIENT_STOCK |
| API-014 | /api/v1/orders | POST | 优惠券已使用 | 使用已核销的 coupon_code | 400 | 错误码：COUPON_ALREADY_USED |
| API-015 | /api/v1/orders | POST | 优惠券不存在 | `{coupon_code:"INVALID"}` | 400 | 错误码：COUPON_NOT_FOUND |
| API-016 | /api/v1/orders | POST | 重复下单（防重） | 相同 product_id+address_id，1 秒内重复请求 | 429 | 错误码：DUPLICATE_ORDER |
| API-017 | /api/v1/orders | POST | 积分抵扣超限 | 积分抵扣 60% 订单金额 | 400 | 错误码：POINTS_EXCEED_LIMIT |
| **幂等性测试** |
| API-018 | /api/v1/orders | POST | 同一请求发送 2 次 | 相同 body，间隔 5 秒 | 201+409 | 第一次成功，第二次返回冲突 |
| API-019 | /api/v1/orders | POST | 并发下单 | 同一用户，10 个并发请求 | 201×1 或 409×9 | 只有一个成功 |
| **权限测试** |
| API-020 | /api/v1/orders | POST | 普通用户越权访问商家接口 | 使用用户 token 访问商家端点 | 403 | 错误码：FORBIDDEN |

---

### 示例 2：用户积分变更接口测试

**输入变量**：

```json
{{api_spec}} = {
  "path": "/api/v1/users/{user_id}/points",
  "method": "POST",
  "headers": {
    "Content-Type": "application/json",
    "Authorization": "Bearer {admin_token}"
  },
  "body": {
    "change_type": "string, required, enum: [earn, spend, adjust, expire]",
    "amount": "integer, required",
    "reason": "string, required, max_length=200",
    "order_id": "string, optional"
  }
}
```

```
{{business_rules}} =
1. 积分不能为负数
2. 消费积分必须有 order_id
3. 单次调整上限 10000 分
4. 需要管理员权限
5. 必须记录操作日志
```

**预期输出**：

| 用例编号 | 接口路径 | 方法 | 测试场景 | 输入参数 (JSON) | 预期响应码 | 断言逻辑 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **正常场景** |
| API-021 | /api/v1/users/123/points | POST | 获得积分 | `{change_type:"earn", amount:100, reason:"签到"}` | 200 | 积分增加 100，日志记录 |
| API-022 | /api/v1/users/123/points | POST | 消费积分 | `{change_type:"spend", amount:50, reason:"兑换", order_id:"ORD001"}` | 200 | 积分减少 50，关联订单 |
| **参数校验** |
| API-023 | /api/v1/users/123/points | POST | change_type 非法值 | `{change_type:"invalid", ...}` | 400 | 错误码：INVALID_CHANGE_TYPE |
| API-024 | /api/v1/users/123/points | POST | amount 为负数 | `{amount:-100, ...}` | 400 | 错误码：AMOUNT_MUST_BE_POSITIVE |
| API-025 | /api/v1/users/123/points | POST | reason 为空 | `{reason:"", ...}` | 400 | 错误码：REASON_REQUIRED |
| API-026 | /api/v1/users/123/points | POST | reason 超长 | `{reason:"A"...(300 字符)}` | 400 | 错误码：REASON_TOO_LONG |
| **业务规则校验** |
| API-027 | /api/v1/users/123/points | POST | 消费积分无 order_id | `{change_type:"spend", amount:50, reason:"兑换"}` | 400 | 错误码：ORDER_ID_REQUIRED_FOR_SPEND |
| API-028 | /api/v1/users/123/points | POST | 积分扣减后为负 | 用户积分=30，消费 50 | 400 | 错误码：INSUFFICIENT_POINTS |
| API-029 | /api/v1/users/123/points | POST | 单次调整超限 | `{change_type:"adjust", amount:15000, ...}` | 400 | 错误码：ADJUSTMENT_EXCEED_LIMIT |
| **权限测试** |
| API-030 | /api/v1/users/123/points | POST | 普通用户调用 | 使用用户 token | 403 | 错误码：ADMIN_ONLY |
| API-031 | /api/v1/users/123/points | POST | 无 Token | 无 Authorization | 401 | 错误码：UNAUTHORIZED |

---

## 测试覆盖度检查清单

- [ ] **HTTP 状态码覆盖**: 200, 201, 400, 401, 403, 404, 409, 429, 500
- [ ] **Header 校验**: Content-Type, Authorization, Accept
- [ ] **必填字段缺失**: 每个必填字段单独缺失
- [ ] **类型破坏**: string→int, int→string, null, array→object
- [ ] **边界值**: min, max, 0, -1, 空字符串，超长字符串
- [ ] **业务规则**: 每条业务规则至少 1 个正向 +1 个负向用例
- [ ] **幂等性**: 重复请求、并发请求
- [ ] **权限**: 未认证、已认证无权限、越权访问

---

## 变更记录

| 版本 | 日期 | 作者 | 变更说明 |
| :--- | :--- | :--- | :--- |
| v1.0 | 2026-03-22 | QA Team | 初始版本 |
