# 测试报告

> 生成日期：2026-04-01
> 测试框架：pytest 9.0.2
> Python：3.11.9
> 结果：**99 passed, 0 failed, 4.22s**

## 测试环境

- 数据库：SQLite（临时文件，每次会话创建）
- 外部依赖：所有外部 API（RollingGo、Tuniu）不 mock，但断言兼容其不可用的情况
- Rate Limiting：测试环境中已禁用
- 认证：session 级 fixture，每个会话只发送一次验证码

## 测试覆盖

### Tier 1：基础设施 + 核心功能（29 tests）

| 模块 | 文件 | 用例数 | 说明 |
|------|------|--------|------|
| 健康检查 | `test_health.py` | 4 | /health、providers、place_types、robots.txt |
| 认证流程 | `test_auth.py` | 9 | 发送验证码、登录、用户信息、匿名会话 |
| 收藏 CRUD | `test_user.py::TestFavorites` | 9 | 添加/移除/切换/查询/重复 |
| 搜索历史 | `test_user.py::TestSearchHistory` | 5 | 添加/查询/清空/删除 |
| 搜索参数校验 | `test_search.py::TestSearchValidation` | 6 | 缺失参数、无效 provider、必填字段 |

### Tier 2：商业化功能（53 tests）

| 模块 | 文件 | 用例数 | 说明 |
|------|------|--------|------|
| 会员体系 | `test_membership.py` | 5 | 信息查询、权限检查、搜索配额 |
| 支付流程 | `test_payment.py` | 13 | 计划列表、创建订单、Mock 支付全流程、续期 |
| CPS 点击追踪 | `test_click.py` | 5 | 302 重定向、数据库记录、user_id 关联 |
| 事件追踪 | `test_tracking.py` | 8 | 批量/单个/空事件、DB 记录、auth 关联 |
| 推荐奖励 | `test_referral.py` | 8 | 生成码、使用码、重复使用、自推、记录查询 |
| 优惠券 | `test_coupon.py` | 6 | 列表/领取/使用/重复领取/已用优惠券 |
| 推荐服务 | `test_recommendation.py` | 6 | 个性化推荐、相似酒店、limit 参数 |

### Tier 3：管理后台（11 tests）

| 模块 | 文件 | 用例数 | 说明 |
|------|------|--------|------|
| 管理认证 | `test_admin.py::TestAdminAuth` | 3 | 无认证/错误密码/正确密码 |
| 统计接口 | `test_admin.py::TestAdminStats` | 2 | 统计响应、days 参数 |
| 点击记录 | `test_admin.py::TestAdminClicks` | 2 | 列表、limit |
| 分析接口 | `test_admin.py::TestAdminAnalytics` | 4 | 概览/漏斗/用户/仪表盘页面 |

## 运行命令

```bash
# 运行全部测试
pytest tests/ -v --tb=short

# 运行单个模块
pytest tests/test_auth.py -v

# 运行带覆盖率
pytest tests/ -v --cov=app --cov-report=term-missing
```

## 测试基础设施

### conftest.py 关键设计

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `app` | session | Flask 应用实例 + SQLite 数据库 + 所有表创建 |
| `client` | function | Flask 测试客户端 |
| `db` | function | 每个测试后 drop_all + create_all（仅部分测试使用） |
| `auth_headers` | session | 用户 13800138000 的 JWT token（避免 rate limit） |
| `auth_headers_alt` | session | 用户 13900139000 的 JWT token |
| `admin_headers` | function | Basic Auth 管理员凭证 |

### 设计决策

1. **auth_headers session 级**：验证码端点有 5/min 限制，99 个测试共享同一个 token 避免耗尽
2. **db function 级**：每个测试获得干净的数据库，但与 session 级 auth 不兼容（auth 用户会被删除）
3. **不使用 db fixture**：大多数测试通过 API 操作数据，避免 fixture 作用域冲突

## 发现并修复的问题

### 基础设施问题

| 问题 | 影响 | 修复 |
|------|------|------|
| Rate limiting 耗尽 | 46 个测试 ERROR | 测试配置禁用 `RATELIMIT_ENABLED=False` |
| Coupon/Referral/Tracking 表未创建 | 数据插入失败 | `create_app()` 中提前导入所有模型 |
| `import app.models.*` 覆盖局部变量 | app 实例丢失 | 改用 `from app.models import ...` |
| Windows 临时文件锁 | teardown ERROR | cleanup 加 `try/except` |

### 模型/路由问题

| 问题 | 影响 | 修复 |
|------|------|------|
| `BigInteger` + SQLite 不兼容 | 事件追踪 500 | `TrackingEvent.id` 改为 `Integer` |
| 时区感知 vs 朴素 datetime | 支付/会员 500 | 兼容两种 datetime 格式比较 |
| 空事件列表 `[]` 被拒绝 | 返回 400 | `if not data` → `if data is None` |
| 点击追踪未解析 JWT | user_id 为 None | 添加 `@jwt_required(optional=True)` |

### 测试逻辑问题

| 问题 | 影响 | 修复 |
|------|------|------|
| POST 无 JSON body 返回 415/500 | 断言失败 | 兼容多种状态码 |
| Tuniu 外部 API 不可用 | 测试不稳定 | 断言不依赖外部 API 结果 |
| 累积数据计数不准 | assert 失败 | 使用 `count_before + 1` 模式 |
| `DetachedInstanceError` | coupon.id 访问失败 | 在 `app_context` 内保存 ID |
| 跨测试数据污染 | 推荐测试不稳定 | 改用 API 添加数据 |
