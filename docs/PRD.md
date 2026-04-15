# 酒店搜索与比价平台 - 产品需求文档 (PRD)

**版本**: 3.0.2
**更新日期**: 2026-04-15
**状态**: Phase 8 双供应商统一搜索整合（已实施）

---

## 1. 项目概述

### 1.1 项目名称
酒店搜索与比价平台

### 1.2 项目目标
提供统一的酒店搜索、比价和预订服务，通过 **CPS 联盟佣金 + 订阅制会员** 混合模式实现商业变现。核心差异化价值在于跨平台比价——帮助用户在 8+ 预订平台中找到最低价格。

### 1.3 商业模式

| 收入来源 | 比重 | 说明 |
|---------|------|------|
| CPS 联盟佣金 | 60% | 用户点击预订链接跳转至途牛/Booking 等平台，按成交获得佣金 |
| 订阅制会员 | 30% | 月费 ¥19.9 / 年费 ¥199，享无限搜索、价格提醒等高级功能 |
| 增长工具 | 10% | 推荐奖励、优惠券等运营工具驱动用户获取和留存 |

### 1.4 目标用户
- 价格敏感型旅行者（比价需求强，转化率高）
- 出境游旅客（RollingGo 全球搜索）
- 国内旅行者（途牛搜索 + 预订）
- 无明确平台偏好的比价用户

### 1.5 用户权限模型

| 权限 | 免费用户 | 匿名用户 | 付费会员 |
|------|---------|---------|---------|
| 每日搜索次数 | 10 次 | 5 次 | 无限 |
| 跨平台比价 | ✅ | ✅ | ✅ |
| 收藏上限 | 50 家 | 50 家 | 50 家 |
| 价格变动提醒 | ❌ | ❌ | ✅ |
| 历史价格分析 | ❌ | ❌ | ✅ |
| 优先客服 | ❌ | ❌ | ✅ |

---

## 2. 功能规格

### 2.1 酒店搜索

#### 2.1.1 多供应商支持

| 供应商 | 覆盖范围 | 支持预订 | 支持分页 |
|--------|----------|----------|----------|
| RollingGo | 全球酒店 | 否（跳转外部） | 否 |
| 途牛 (Tuniu) | 国内酒店 | 是 | 是 |

#### 2.1.2 搜索参数

**RollingGo 供应商:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 搜索关键词 |
| place | string | 是 | 目的地名称 |
| place_type | string | 是 | 地点类型：城市/机场/景点/火车站/地铁站/酒店/区/县/详细地址 |
| check_in_date | string | 否 | 入住日期 (YYYY-MM-DD) |
| stay_nights | int | 否 | 入住晚数 (默认: 1) |
| adult_count | int | 否 | 成人数量 (默认: 2) |
| child_count | int | 否 | 儿童数量 (默认: 0) |
| child_ages | array | 否 | 儿童年龄列表 |
| star_ratings | string | 否 | 星级范围，如 "4.0,5.0" |
| max_price | float | 否 | 每晚最高价格 |
| distance | int | 否 | 最大距离（米） |
| required_tags | array | 否 | 必须包含的标签 |
| preferred_tags | array | 否 | 优先标签 |
| size | int | 否 | 每页结果数 (默认: 20) |

**途牛供应商:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city_name | string | 是 | 城市名称 |
| check_in | string | 是 | 入住日期 (YYYY-MM-DD) |
| check_out | string | 是 | 离店日期 (YYYY-MM-DD) |
| adult_count | int | 否 | 成人数量 (默认: 2) |
| child_count | int | 否 | 儿童数量 (默认: 0) |
| keyword | string | 否 | 酒店名称或品牌关键词 |
| page_num | int | 否 | 页码 (默认: 1) |
| query_id | string | 否 | 分页查询 ID |

#### 2.1.3 搜索次数限制

搜索 API 在返回响应时会附带 `X-Search-Remaining` 响应头，告知用户剩余搜索次数。免费用户每日 10 次，匿名用户每日 5 次，会员无限制。前端搜索结果页顶部展示剩余次数和升级引导。

#### 2.1.4 统一搜索模式（v3.0）

从 v3.0 开始，搜索 API 支持统一搜索模式，后端自动路由到最佳供应商组合。

##### 智能路由
- 用户输入目的地 -> 城市列表匹配判断国内/港澳台/国际 -> AI 意图解析（GLM-4-flash）提取 RollingGo 参数
- **国内目的地**: 双源并行查询（Tuniu + RollingGo）-> 结果融合去重
- **国际目的地**: 仅 RollingGo

##### 请求格式
```json
{
  "destination": "上海陆家嘴",
  "check_in": "2026-04-16",
  "check_out": "2026-04-17",
  "adult_count": 2,
  "keyword": "万豪"
}
```

`destination` 字段同时替代原来的 `city_name`（Tuniu）和 `place`（RollingGo）。提供 `destination` 时自动启用统一模式；提供 `provider` 时走原有单供应商模式（向后兼容）。

##### 双源融合策略

后端通过 `SearchMerger` 服务将两个供应商的结果合并：

1. 优先 Tuniu 结果（有房型详情+价格+预订能力）
2. 用 `HotelMatcher` 匹配 RollingGo 中的同一家酒店（名称相似度 60% + 坐标距离 40%，坐标缺失时用地址文本相似度兜底）
3. 匹配到的酒店进行字段级合并
4. 未匹配的 RollingGo 酒店追加到列表末尾

##### 字段合并规则

| 字段 | 主来源 | 补充来源 | 说明 |
|------|--------|----------|------|
| hotel_id | Tuniu | - | 预订需要 Tuniu ID |
| name | Tuniu | - | Tuniu 名称更完整 |
| price_per_night | Tuniu | RollingGo | Tuniu 实时价格优先 |
| distance | RollingGo | - | 仅 RollingGo 提供距离 |
| latitude/longitude | RollingGo | Tuniu | RollingGo 坐标更精确 |
| amenities | RollingGo | - | 仅 RollingGo 返回设施 |
| booking_url | RollingGo | - | CPS 跳转链接 |
| business/brand_name | Tuniu | - | 商圈/品牌信息 |
| room_name/meal/refund | Tuniu | - | 房型/餐食/退款信息 |
| comment_digest | Tuniu | - | 点评摘要 |

##### 响应格式

融合响应新增 `merged` 字段标识：
```json
{
  "success": true,
  "data": {
    "hotels": [...],
    "total": 15,
    "provider": "auto",
    "merged": true,
    "sources": {
      "tuniu": 8,
      "rollinggo": 12,
      "merged_pairs": 5
    },
    "supports_booking": true
  }
}
```

### 2.2 多平台比价

#### 2.2.1 支持的外部平台
- Booking.com、KAYAK、Expedia、Agoda、TripAdvisor、Hotels.com、携程/Trip.com、Priceline、Hotwire

#### 2.2.2 价格搜索服务

| 服务 | 优先级 | 特点 |
|------|--------|------|
| Tavily | 首选 | AI 优化搜索，URL 内容提取 |
| Serper | 备用 | Google 搜索 API |

#### 2.2.3 价格提取
- 支持货币：CNY, USD, EUR, GBP, HKD, TWD
- 正则匹配提取价格，价格区间取最低价
- 多币种自动转换为 CNY 展示

### 2.3 酒店详情

- 基本信息：名称、地址、星级、评分、品牌、描述
- 图片画廊（缩略图 + 主图切换）
- 设施列表、位置坐标
- 房型方案：房型名、床型、面积、入住人数、价格、早餐、可用性
- 预订跳转按钮（通过 CPS 点击追踪）

#### 详情页数据融合（v3.0）

详情页展示主供应商完整数据，融合酒店显示双入口预订：

- **主数据**: 主供应商的完整详情（房型+价格+政策+图片）
- **来源标识**: SourceBadge 组件显示数据来源（途牛/全球/双源）
- **双入口预订**: 融合酒店同时显示"在线预订"（途牛直连）和"全球预订"（外部链接）
- **第三方比价**: Tavily/Serper 搜索携程/Agoda/Expedia 等平台价格

### 2.4 预订系统（仅途牛）

1. **准备预订**：`POST /api/book/prepare` -- 验证房间可用性
2. **创建订单**：`POST /api/book/create` -- 提交预订，填写入住人信息

#### 统一预订路径（v3.0）

| 场景 | 预订方式 | 实现 |
|------|----------|------|
| Tuniu 酒店 | 直连预订 API | `create_order()` -> 预订弹窗 |
| RollingGo 酒店 | 跳转外部链接 | `booking_url` -> CPS 点击追踪 |
| 融合酒店 | 双入口 | "直订 680" + "更多平台比价" |

### 2.5 用户系统

#### 2.5.1 认证
- 手机号 + 短信验证码登录
- JWT Token 认证（24 小时有效期）
- 设备指纹识别匿名用户（localStorage + User-Agent + IP）

#### 2.5.2 收藏管理
- 添加/移除/切换收藏状态
- 最多 50 个收藏（免费用户），支持登录和匿名用户

#### 2.5.3 搜索历史
- 自动记录搜索历史（最多 20 条）
- 支持单条删除和清空

### 2.6 会员体系

#### 2.6.1 会员计划

| 计划 | 价格 | 有效期 | 权益 |
|------|------|--------|------|
| 月度会员 | ¥19.9 | 30 天 | 无限搜索 + 价格提醒 + 历史价格 + 优先客服 |
| 年度会员 | ¥199 | 365 天 | 同月度会员，省 ¥40 |

#### 2.6.2 会员状态
- 自动续期：到期后自动降级为免费用户
- 会员延期：续费时若当前会员未过期，在到期日基础上延长
- 状态查询：`GET /api/membership/info` 返回 tier、到期时间、剩余搜索次数

### 2.7 支付系统

#### 2.7.1 支付流程
1. 用户选择计划 → `POST /api/payment/create` 创建支付订单
2. 前端跳转至支付页面（微信支付/支付宝）
3. 支付成功 → 支付平台回调 → 自动激活会员
4. 开发模式支持 Mock 支付（`GET /api/payment/mock/{provider}/{id}`）

#### 2.7.2 支付安全
- 回调验签（HMAC-SHA256）
- 幂等处理（payment_trade_no 去重）
- 金额比对防篡改

### 2.8 价格监控（会员专属）

- 用户为收藏的酒店设置目标价格
- 系统定期检查价格（APScheduler，每 6 小时）
- 价格达到目标时标记触发，记录追踪事件
- 管理界面：创建/查看/删除提醒

### 2.9 推荐奖励

- 每位用户自动生成 6 位推荐码
- 邀请好友注册：双方各获得 7 天会员
- 推荐记录和统计查询

### 2.10 优惠券系统

- 管理员创建优惠券（折扣类型：百分比 / 固定天数）
- 用户领取和使用优惠券
- 支付时核销优惠券

### 2.11 数据埋点与分析

#### 2.11.1 前端埋点 SDK
- 自动 pageview 追踪（路由变化）
- 手动事件上报：search、view_hotel、compare、click_book、favorite
- 批量缓冲（累积 10 条或 5 秒发送）
- sendBeacon 兜底（页面关闭时发送）

#### 2.11.2 管理后台分析
- **总览** (`GET /api/admin/analytics/overview`)：DAU、搜索量、点击量、收藏量、每日趋势
- **转化漏斗** (`GET /api/admin/analytics/funnel`)：搜索 → 查看 → 比价 → 预订 → 收藏
- **用户分析** (`GET /api/admin/analytics/users`)：注册率、活跃率、转化率、Top 用户

### 2.12 个性化推荐

- **个性化建议** (`GET /api/recommend/personalized`)：基于用户搜索历史和收藏偏好
- **相似酒店** (`GET /api/recommend/similar/{hotel_id}`)：基于协同过滤（收藏了相同酒店的用户也收藏了哪些酒店）

### 2.13 CPS 联盟点击追踪

- 预订链接通过 `/api/click/track` 中转
- 记录：hotel_id、hotel_name、provider、user_id、source_page、IP、User-Agent
- 302 重定向至目标预订平台

---

## 3. API 文档

### 3.1 搜索 API

#### POST /api/search
搜索酒店。响应头包含 `X-Search-Remaining`（剩余搜索次数，会员为 -1）。

**请求体 (RollingGo):**
```json
{
  "provider": "rollinggo",
  "query": "万豪",
  "place": "上海",
  "place_type": "城市",
  "check_in_date": "2026-04-01",
  "stay_nights": 2,
  "adult_count": 2,
  "size": 20
}
```

**请求体 (途牛):**
```json
{
  "provider": "tuniu",
  "city_name": "上海",
  "check_in": "2026-04-01",
  "check_out": "2026-04-03",
  "adult_count": 2,
  "keyword": "万豪"
}
```

**请求体 (统一模式 - v3.0):**
```json
{
  "destination": "上海陆家嘴",
  "check_in": "2026-04-16",
  "check_out": "2026-04-17",
  "adult_count": 2,
  "keyword": "万豪"
}
```

**说明**: 提供 `destination` 时启用统一模式，后端自动选择供应商。提供 `provider` 时走单供应商模式（向后兼容）。

**响应:**
```json
{
  "success": true,
  "data": {
    "hotels": [...],
    "total": 50,
    "provider": "tuniu",
    "supports_booking": true,
    "supports_pagination": true,
    "query_id": "xxx",
    "page_num": 1,
    "has_more": true
  },
  "cached": false
}
```

#### GET /api/tags
获取可用筛选标签（仅 RollingGo）。

#### GET /api/place-types
获取可用地点类型。

#### GET /api/providers
获取可用供应商列表。

### 3.2 酒店详情 API

#### GET /api/hotel/{hotel_id}
获取酒店详情，包含 is_favorite 状态。

**查询参数:** provider, check_in, check_out, adult_count

### 3.3 比价 API

#### GET /api/compare/{provider}/{hotel_id}
跨平台价格比较。查询参数：check_in, check_out, hotel_name, hotel_address。

### 3.4 预订 API

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | /api/book/prepare | 准备预订（验证房型） |
| POST | /api/book/create | 创建预订订单 |

### 3.5 认证 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| POST | /api/auth/send-code | 否 | 发送短信验证码（限 5次/分钟） |
| POST | /api/auth/login | 否 | 手机号 + 验证码登录/注册 |
| GET | /api/auth/me | Optional | 获取当前用户信息（含会员状态） |
| POST | /api/auth/anonymous | 否 | 获取匿名会话标识 |

### 3.6 用户 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/favorites | Optional | 获取收藏列表 |
| POST | /api/favorites | Optional | 添加收藏 |
| DELETE | /api/favorites/{hotel_id} | Optional | 移除收藏 |
| GET | /api/favorites/{hotel_id} | Optional | 检查收藏状态 |
| POST | /api/favorites/toggle | Optional | 切换收藏 |
| GET | /api/history | Optional | 搜索历史 |
| DELETE | /api/history | Optional | 清空历史 |
| DELETE | /api/history/{id} | Optional | 删除单条历史 |

### 3.7 会员 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/membership/info | 是 | 获取会员信息（tier、到期时间、剩余搜索次数） |
| POST | /api/membership/check | Optional | 检查功能权限（是否可用） |

### 3.8 支付 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/payment/plans | 否 | 获取会员计划列表 |
| POST | /api/payment/create | 是 | 创建支付订单 |
| POST | /api/payment/wechat/callback | 否 | 微信支付回调 |
| POST | /api/payment/alipay/callback | 否 | 支付宝回调 |
| GET | /api/payment/status/{id} | 是 | 查询支付状态 |
| GET | /api/payment/mock/{provider}/{id} | 是 | Mock 支付（仅开发模式） |

### 3.9 价格提醒 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| POST | /api/alerts | 是 | 创建价格提醒 |
| GET | /api/alerts | 是 | 获取提醒列表 |
| DELETE | /api/alerts/{id} | 是 | 删除提醒 |

### 3.10 推荐奖励 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/referral/code | 是 | 获取我的推荐码 |
| POST | /api/referral/apply | 是 | 使用推荐码 |
| GET | /api/referral/records | 是 | 推荐记录 |

### 3.11 优惠券 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/coupons/available | 否 | 可领取的优惠券 |
| POST | /api/coupons/{id}/claim | 是 | 领取优惠券 |
| POST | /api/coupons/redeem | 是 | 使用优惠券 |
| GET | /api/coupons/mine | 是 | 我的优惠券（支持 status 过滤） |

### 3.12 数据追踪 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| POST | /api/events/track | Optional | 批量事件上报（最多 50 条/次） |

### 3.13 推荐 API

| 方法 | 端点 | 认证 | 说明 |
|------|------|------|------|
| GET | /api/recommend/personalized | 是 | 个性化推荐 |
| GET | /api/recommend/similar/{hotel_id} | 否 | 相似酒店推荐 |

### 3.14 管理后台 API

所有管理 API 需要 HTTP Basic Auth 认证。

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/admin/ | 管理后台页面 |
| GET | /api/admin/stats | 点击统计 |
| GET | /api/admin/clicks | 最近点击记录 |
| GET | /api/admin/analytics/overview | 数据总览（DAU、搜索量、趋势） |
| GET | /api/admin/analytics/funnel | 转化漏斗 |
| GET | /api/admin/analytics/users | 用户分析 |

### 3.15 点击追踪 API

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/click/track | CPS 点击追踪 + 302 重定向 |

---

## 4. 技术架构

### 4.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nuxt.js 3 前端                            │
│  Vue 3 + TypeScript + Pinia + Bootstrap 5                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │ 搜索/结果 │ │ 酒店详情  │ │ 会员中心  │ │ 价格提醒/推荐奖励 │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                       │
│  │ 优惠券中心 │ │ 收藏管理  │ │ 埋点 SDK  │                       │
│  └──────────┘ └──────────┘ └──────────┘                       │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Flask 后端                                │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │搜索路由 │ │酒店路由 │ │比价路由 │ │预订路由 │ │认证路由     │  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │用户路由 │ │会员路由 │ │支付路由 │ │推荐路由 │ │追踪路由     │  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐  │
│  │点击追踪 │ │优惠券   │ │推荐奖励 │ │管理后台 │ │推荐服务     │  │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │               │               │
    ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴─────┐
    │  SQLite/  │  │   Redis   │  │ 外部 API   │
    │ PostgreSQL│  │ (限流/缓存)│  │            │
    └───────────┘  └───────────┘  │ RollingGo  │
                                   │ 途牛 MCP   │
                                   │ Tavily     │
                                   │ Serper     │
                                   └────────────┘
```

#### 4.1.1 数据流架构（v3.0）

```
+-------------------------------------------------------------+
|                      统一搜索入口                             |
|                  POST /api/search                            |
|              destination + check_in + check_out              |
+-----------------------------+-------------------------------+
                              |
                              v
                  +-------------------+
                  |  意图解析器        |
                  |  (GLM-4-flash)    |
                  |  国内/国际判断      |
                  +--------+----------+
                           |
              +------------+------------+
              v                         v
       +-------------+          +-------------+
       |  国内模式    |          |  国际模式    |
       | 双源并行查询  |          | 仅RollingGo  |
       +------+------+          +------+------+
              |                         |
       +------+------+                 |
       v             v                 v
 +-------+    +----------+      +----------+
 |Tuniu  |    |RollingGo |      |RollingGo |
 |MCP API|    |MCP API   |      |MCP API   |
 +---+---+    +----+-----+      +----+-----+
     |             |                  |
     +------+------+                  |
            v                          |
    +-------------+                    |
    |SearchMerger |                    |
    |合并+去重     |                    |
    +------+------+                    |
           |                           |
           +------------+--------------+
                        v
              +------------------+
              |  统一响应格式     |
              |  + 第三方比价     |
              |  (Tavily/Serper) |
              +------------------+
```

### 4.2 前端技术栈

| 技术 | 用途 |
|------|------|
| Nuxt.js 3 | SPA 框架（ssr: false）|
| Vue 3 + TypeScript | UI 框架 |
| Pinia | 状态管理（auth, favorites, membership） |
| Bootstrap 5 + Bootstrap Icons | UI 组件和图标 |
| useApi composable | 统一 API 调用层（Token + 设备指纹） |
| useTracking composable | 数据埋点 SDK |

### 4.3 后端技术栈

| 技术 | 用途 |
|------|------|
| Flask 2.3+ | Web 框架 |
| SQLAlchemy 2.0 + Flask-Migrate | ORM + 数据库迁移 |
| Flask-JWT-Extended | JWT 认证 |
| Flask-Limiter | API 限流（Redis 存储） |
| Flask-CORS | 跨域支持 |
| APScheduler | 定时任务（价格监控） |

### 4.4 数据库模型

**用户相关：**

| 模型 | 说明 |
|------|------|
| User | 用户账户（含会员字段：tier, expires_at, search_count_today） |
| Favorite | 收藏（支持 user_id 和 device_fingerprint） |
| SearchHistory | 搜索历史 |
| Subscription | 订阅记录（plan, amount, status, payment_provider, trade_no） |
| ReferralCode | 推荐码（每用户一个） |
| ReferralRecord | 推荐记录 |

**业务相关：**

| 模型 | 说明 |
|------|------|
| Click | CPS 点击追踪（含 user_id 关联） |
| PriceAlert | 价格提醒 |
| Coupon | 优惠券模板 |
| UserCoupon | 用户已领优惠券 |
| TrackingEvent | 用户行为事件（埋点） |
| AuditLog | 操作审计日志 |

### 4.5 项目结构

```
hotel/
├── app/
│   ├── __init__.py              # Flask 应用工厂
│   ├── extensions.py             # Flask-Limiter (Redis)
│   ├── models/
│   │   ├── database.py           # SQLAlchemy 核心模型 (User, Favorite, SearchHistory, Click, Subscription, PriceAlert)
│   │   ├── tracking.py           # TrackingEvent 模型
│   │   ├── referral.py           # ReferralCode + ReferralRecord
│   │   ├── coupon.py             # Coupon + UserCoupon
│   │   ├── audit_log.py          # AuditLog
│   │   └── schema.py             # Pydantic 验证模型
│   ├── routes/
│   │   ├── search.py             # 搜索 API（含次数限制）
│   │   ├── hotel.py              # 酒店详情
│   │   ├── comparison.py         # 跨平台比价
│   │   ├── booking.py            # 预订流程
│   │   ├── auth.py               # 认证（含会员信息返回）
│   │   ├── user.py               # 收藏 + 搜索历史
│   │   ├── click.py              # CPS 点击追踪
│   │   ├── admin.py              # 管理后台 + 数据分析
│   │   ├── membership.py         # 会员管理 + 权限检查
│   │   ├── payment.py            # 支付创建 + 回调
│   │   ├── tracking.py           # 事件追踪上报
│   │   ├── referral.py           # 推荐奖励
│   │   ├── coupon.py             # 优惠券
│   │   └── recommendation.py     # 个性化推荐
│   ├── services/
│   │   ├── hotel_provider.py     # 供应商抽象层
│   │   ├── rollinggo.py          # RollingGo MCP 客户端
│   │   ├── tuniu.py              # 途牛 MCP 客户端
│   │   ├── tavily.py             # Tavily 搜索服务
│   │   ├── serper.py             # Serper 搜索服务
│   │   ├── hotel_matcher.py      # 酒店名称匹配（含英文后缀剥离+地址兜底）
│   │   ├── search_merger.py       # 双源搜索融合服务
│   │   ├── intent_parser.py      # AI 意图解析（GLM-4-flash）
│   │   ├── currency.py           # 多币种转换
│   │   ├── cache.py              # SQLite 缓存服务
│   │   ├── payment.py            # 支付服务抽象层
│   │   ├── price_monitor.py      # 价格监控服务
│   │   ├── recommendation.py     # 推荐服务（基于规则）
│   │   └── security.py           # 安全工具（AES 加密、HMAC 签名）
│   └── utils.py
├── web/                          # Nuxt.js 3 前端
│   ├── pages/
│   │   ├── index.vue             # 搜索首页
│   │   ├── results.vue           # 搜索结果（含 SearchLimit）
│   │   ├── detail/[hotelId].vue  # 酒店详情
│   │   ├── booking.vue           # 预订页
│   │   ├── order.vue             # 订单页
│   │   ├── favorites.vue         # 收藏页
│   │   ├── login.vue             # 登录页
│   │   ├── membership.vue        # 会员中心
│   │   ├── alerts.vue            # 价格提醒
│   │   ├── referral.vue          # 推荐奖励
│   │   └── coupons.vue           # 优惠券中心
│   ├── stores/
│   │   ├── auth.ts               # 认证状态
│   │   ├── favorites.ts          # 收藏状态
│   │   └── membership.ts         # 会员状态
│   ├── composables/
│   │   ├── useApi.ts             # 统一 API 调用
│   │   └── useTracking.ts        # 埋点 SDK
│   ├── components/
│   │   ├── layout/               # AppNavbar, MobileTabBar
│   │   ├── hotel/                # HotelCard, ComparisonSection, FavoriteButton, PriceBadge, SourceBadge
│   │   ├── search/               # SearchForm, SearchHistory
│   │   ├── membership/           # PlanCard, SearchLimit, UpgradeModal
│   │   ├── common/               # EmptyState, SkeletonCard
│   │   └── growth/               # ShareButton
│   ├── types/api.ts              # TypeScript 类型定义
│   └── utils/
│       ├── storage.ts            # 设备指纹
│       ├── session.ts            # Session ID 管理
│       └── currency.ts           # 货币格式化
├── data/                         # SQLite 数据库
├── logs/                         # 日志文件
├── config.py                     # 配置
├── docker-compose.yml            # Docker 编排（API + Web + Redis）
├── requirements.txt
├── run.py                        # 应用入口
└── .env                          # 环境变量
```

---

## 5. 配置说明

### 5.1 环境变量

```env
# === 基础配置 ===
SECRET_KEY=your-secret-key
FLASK_DEBUG=True
DATABASE_URL=sqlite:///data/hotel.db      # SQLite 开发 / PostgreSQL 生产
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_EXPIRES=86400           # 24h

# === 供应商配置 ===
AIGOHOTEL_API_KEY=your-rollinggo-key    # RollingGo 全球搜索
ROLLINGGO_TIMEOUT=60
TUNIU_API_KEY=your-tuniu-key            # 途牛国内搜索+预订
TUNIU_MCP_URL=https://openapi.tuniu.cn/mcp/hotel
TUNIU_TIMEOUT=60
DEFAULT_PROVIDER=tuniu

# === 比价服务 ===
TAVILY_API_KEY=your-tavily-key           # 首选
TAVILY_TIMEOUT=15
SERPER_API_KEY=your-serper-key           # 备用
SERPER_TIMEOUT=10

# === 缓存 ===
CACHE_ENABLED=True
CACHE_TTL=3600

# === Redis ===
REDIS_URL=redis://localhost:6379/0       # 限流和缓存

# === 会员配置 ===
FREE_SEARCH_LIMIT=10                     # 免费用户每日搜索次数
ANONYMOUS_SEARCH_LIMIT=5                 # 匿名用户每日搜索次数

# === 支付配置 ===
WECHAT_PAY_APP_ID=                       # 微信支付（待接入）
WECHAT_PAY_MCH_ID=
WECHAT_PAY_API_KEY=
WECHAT_PAY_NOTIFY_URL=
ALIPAY_APP_ID=                           # 支付宝（待接入）
ALIPAY_PRIVATE_KEY=
ALIPAY_PUBLIC_KEY=
ALIPAY_NOTIFY_URL=

# === 管理后台 ===
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password

# === 应用设置 ===
RESULTS_PER_PAGE=20
MAX_FAVORITES=50
MAX_HISTORY=20
```

---

## 6. 部署

### 6.1 Docker Compose

```bash
# 启动所有服务（API + Web + Redis）
docker compose up -d

# 查看日志
docker compose logs -f
```

三个服务：
- **api**: Flask 后端 (port 5000)，依赖 Redis
- **web**: Nuxt.js 前端 (port 3000)，依赖 API
- **redis**: Redis 7 Alpine (port 6379)

### 6.2 开发模式

```bash
# 后端
python run.py

# 前端
cd web && npm run dev
```

---

## 7. 版本历史

| 版本 | 日期 | 阶段 | 变更 |
|------|------|------|------|
| 1.0.0 | 2026-03-20 | 初始版本 | 基础搜索比价功能 |
| 1.1.0 | 2026-04-01 | Phase 1 | 生产化部署 + CPS 联盟追踪 + 管理后台 + SEO |
| 1.2.0 | 2026-04-01 | Phase 2 | 手机号认证 + ORM 迁移 + API 限流 |
| 1.3.0 | 2026-04-01 | Phase 3 | Nuxt.js 3 前端迁移 |
| 2.0.0 | 2026-04-01 | Phase 4 | 数据埋点与分析基础（TrackingEvent + 管理后台分析 API） |
| 2.1.0 | 2026-04-01 | Phase 5 | 会员体系 + 搜索限制 + 支付集成（微信/支付宝） |
| 2.2.0 | 2026-04-01 | Phase 6 | 价格监控 + 推荐奖励 + 优惠券系统 |
| 2.3.0 | 2026-04-01 | Phase 7 | Redis 基础设施 + 安全加固 + 个性化推荐 + 审计日志 |
| 3.0.0 | 2026-04-15 | Phase 8 | 双供应商统一搜索整合 -- 智能路由 + 双源融合 + 详情页增强 |
| 3.0.1 | 2026-04-15 | Phase 8 实施 | 后端: destination统一搜索 + ThreadPoolExecutor双源并行 + SearchMerger融合 + HotelMatcher阈值修复 + placeType纠正 + TimeoutError容错. 前端: SearchForm统一搜索框 + results.vue来源统计 + SourceBadge来源标签 + 详情页双入口预订 |
| 3.0.2 | 2026-04-15 | Bugfix | HotelMatcher剥离英文括号后缀 + 地址文本相似度兜底(坐标缺失时) + RollingGo query组合place+keyword + PRD与代码同步修正 |

---

*文档基于代码库分析生成，最后更新 2026-04-15 (v3.0.2)*
