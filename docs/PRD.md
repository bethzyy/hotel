# 酒店搜索与比价平台 - 产品需求文档 (PRD)

**版本**: 1.0.0
**更新日期**: 2026-03-20
**状态**: 开发中

---

## 1. 项目概述

### 1.1 项目名称
酒店搜索与比价平台

### 1.2 项目目标
提供统一的酒店搜索、比价和预订服务，支持多供应商接入。用户可以搜索全球酒店，在多个预订平台之间比较价格，并通过国内供应商完成预订。

### 1.3 目标用户
- 需要预订酒店住宿的旅行者
- 希望在多个平台比较价格的用户
- 预订国内酒店的国内用户

### 1.4 核心功能
- 多供应商酒店搜索（RollingGo 全球、途牛国内）
- 外部平台比价（8+ 平台）
- 完整预订流程（途牛）
- 收藏夹和搜索历史管理

---

## 2. 功能规格

### 2.1 酒店搜索

#### 2.1.1 多供应商支持

| 供应商 | 覆盖范围 | 支持预订 | 支持分页 |
|--------|----------|----------|----------|
| RollingGo | 全球酒店 | 否 | 否 |
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

### 2.2 多平台比价

#### 2.2.1 支持的外部平台
- Booking.com
- KAYAK
- Expedia
- Agoda
- TripAdvisor
- Hotels.com
- 携程/Trip.com
- Priceline
- Hotwire

#### 2.2.2 价格搜索服务
| 服务 | 优先级 | 特点 |
|------|--------|------|
| Tavily | 首选 | AI 优化搜索，URL 内容提取 |
| Serper | 备用 | Google 搜索 API |

#### 2.2.3 价格提取
- 支持多种货币：CNY, USD, EUR, GBP, HKD, TWD
- 正则表达式匹配提取价格
- 价格区间处理（取最低价）
- URL 内容抓取详细定价信息

### 2.3 酒店详情

#### 2.3.1 酒店信息
- 基本信息：名称、地址、星级、描述
- 图片：缩略图画廊
- 设施：设施列表
- 位置：坐标和地图
- 联系方式：电话、邮箱

#### 2.3.2 房型方案
- 房型 and 可用性
- 每晚价格
- 房间设施
- 床型配置
- 取消政策

### 2.4 预订系统（仅途牛）

#### 2.4.1 预订流程
1. **准备预订**：验证房间可用性
2. **选择房型**：选择房间类型
3. **填写入住信息**：每间房的入住人信息
4. **创建订单**：提交预订

#### 2.4.2 预订参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| hotel_id | string | 是 | 酒店 ID |
| room_id | string | 是 | 房型 ID |
| pre_book_param | string | 是 | 预订参数 |
| check_in_date | string | 是 | 入住日期 |
| check_out_date | string | 是 | 离店日期 |
| room_count | int | 否 | 房间数量 (默认: 1) |
| room_guests | array | 是 | 每间房入住人信息 |
| contact_name | string | 是 | 联系人姓名 |
| contact_phone | string | 是 | 联系人电话 |

### 2.5 用户功能

#### 2.5.1 收藏管理
- 添加/移除收藏酒店
- 最多 50 个收藏
- 切换收藏状态
- 查看所有收藏

#### 2.5.2 搜索历史
- 自动记录搜索历史
- 最多 20 条记录
- 删除单条记录
- 清空所有历史

---

## 3. API 文档

### 3.1 搜索 API

#### POST /api/search
搜索酒店。

**请求体 (RollingGo):**
```json
{
  "provider": "rollinggo",
  "query": "万豪",
  "place": "上海",
  "place_type": "城市",
  "check_in_date": "2026-03-25",
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
  "check_in": "2026-03-25",
  "check_out": "2026-03-27",
  "adult_count": 2,
  "keyword": "万豪"
}
```

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
获取酒店详情。

**查询参数:**
- `provider`: 供应商名称 (默认: tuniu)
- `check_in`: 入住日期
- `check_out`: 离店日期
- `adult_count`: 成人数量

**响应:**
```json
{
  "success": true,
  "data": {
    "hotel_id": "xxx",
    "name": "酒店名称",
    "address": "地址",
    "star_rating": 4.5,
    "image_url": "...",
    "images": [...],
    "facilities": [...],
    "room_plans": [...],
    "latitude": 31.23,
    "longitude": 121.47,
    "provider": "tuniu",
    "supports_booking": true,
    "is_favorite": false
  },
  "cached": false
}
```

### 3.3 比价 API

#### GET /api/compare/{provider}/{hotel_id}
比较酒店在外部平台的价格。

**查询参数:**
- `check_in`: 入住日期 (必填)
- `check_out`: 离店日期 (必填)
- `hotel_name`: 酒店名称 (可选，提高匹配准确度)
- `hotel_address`: 酒店地址 (可选)

**响应:**
```json
{
  "success": true,
  "data": {
    "source_hotel": {...},
    "comparisons": [
      {
        "platform": "booking",
        "platform_name": "Booking.com",
        "price": 899.0,
        "currency": "CNY",
        "url": "https://...",
        "is_external": true
      }
    ],
    "best_price": 899.0,
    "savings": 100.0
  }
}
```

### 3.4 预订 API

#### POST /api/book/prepare
准备预订。

**请求体:**
```json
{
  "provider": "tuniu",
  "hotel_id": "xxx",
  "room_id": "yyy",
  "check_in": "2026-03-25",
  "check_out": "2026-03-27",
  "adult_count": 2
}
```

#### POST /api/book/create
创建预订订单。

**请求体:**
```json
{
  "provider": "tuniu",
  "hotel_id": "xxx",
  "room_id": "yyy",
  "pre_book_param": "...",
  "check_in_date": "2026-03-25",
  "check_out_date": "2026-03-27",
  "room_count": 1,
  "room_guests": [
    {"guest_name": "张三", "guest_phone": "13800138000"}
  ],
  "contact_name": "张三",
  "contact_phone": "13800138000"
}
```

### 3.5 用户 API

#### 收藏接口
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/favorites | 获取所有收藏 |
| POST | /api/favorites | 添加收藏 |
| DELETE | /api/favorites/{hotel_id} | 移除收藏 |
| GET | /api/favorites/{hotel_id} | 检查收藏状态 |
| POST | /api/favorites/toggle | 切换收藏状态 |

#### 搜索历史接口
| 方法 | 端点 | 说明 |
|------|------|------|
| GET | /api/history | 获取搜索历史 |
| DELETE | /api/history | 清空所有历史 |
| DELETE | /api/history/{id} | 删除历史记录 |

---

## 4. 技术架构

### 4.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                          前端层                                  │
│           Bootstrap 5 + 原生 JS + Jinja2 模板                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Flask 后端                                │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ 搜索路由      │ │ 酒店路由     │ │ 比价路由      │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │预订路由      │ │ 用户路由     │ │ 缓存服务      │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  RollingGo MCP  │ │   途牛 MCP      │ │  Tavily/Serper  │
│  (全球搜索)      │ │(国内搜索+预订)  │ │ (价格比价)      │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 4.2 供应商抽象模式

```python
HotelProvider (抽象基类)
├── name: str                    # 供应商名称
├── supports_booking: bool       # 是否支持预订
├── supports_pagination: bool    # 是否支持分页
├── search_hotels(**kwargs)      # 搜索酒店
├── get_hotel_detail(hotel_id)   # 获取详情
└── create_order(**kwargs)       # 创建订单

实现类:
├── RollingGoProvider
│   └── RollingGoService (CLI/MCP 封装)
└── TuniuProvider
    └── TuniuService (MCP HTTP 客户端)
```

### 4.3 数据流程

```
1. 搜索请求
   客户端 → POST /api/search → get_provider() → Provider.search_hotels()
   → 规范化响应 → 缓存 → 客户端

2. 酒店详情
   客户端 → GET /api/hotel/{id} → Provider.get_hotel_detail()
   → 规范化 → 缓存 → 客户端

3. 价格比价
   客户端 → GET /api/compare/{provider}/{id}
   → 获取源酒店 → Tavily.search_hotel_prices()
   → 提取价格 → 按价格排序 → 客户端

4. 预订流程
   客户端 → POST /api/book/prepare → 验证房型
   → POST /api/book/create → Provider.create_order() → 客户端
```

### 4.4 项目结构

```
hotel/
├── app/
│   ├── __init__.py          # Flask 应用工厂
│   ├── routes/
│   │   ├── search.py        # 搜索 API 端点
│   │   ├── hotel.py         # 酒店详情端点
│   │   ├── comparison.py    # 比价端点
│   │   ├── booking.py       # 预订流程端点
│   │   └── user.py          # 收藏和历史端点
│   ├── services/
│   │   ├── hotel_provider.py # 供应商抽象层
│   │   ├── rollinggo.py      # RollingGo MCP 客户端
│   │   ├── tuniu.py          # 途牛 MCP 客户端
│   │   ├── tavily.py         # Tavily 搜索服务
│   │   ├── serper.py         # Serper 搜索服务
│   │   ├── hotel_matcher.py  # 酒店名称匹配
│   │   └── cache.py          # SQLite 缓存服务
│   ├── models/
│   │   └── schema.py        # 数据库模型
│   ├── templates/
│   │   ├── index.html       # 首页
│   │   ├── results.html     # 搜索结果
│   │   ├── detail.html      # 酒店详情
│   │   ├── booking.html     # 预订表单
│   │   └── order.html       # 订单确认
│   └── static/
│       ├── css/style.css
│       └── js/app.js
├── data/
│   └── hotel.db             # SQLite 数据库
├── config.py                # 配置
├── run.py                   # 应用入口
├── requirements.txt
└── .env                     # 环境变量
```

---

## 5. 配置说明

### 5.1 环境变量

```env
# Flask 配置
SECRET_KEY=your-secret-key
FLASK_DEBUG=True
PORT=5000

# RollingGo API (全球酒店搜索)
AIGOHOTEL_API_KEY=your-rollinggo-key
ROLLINGGO_TIMEOUT=60

# 途牛 MCP (国内搜索+预订)
TUNIU_API_KEY=your-tuniu-key
TUNIU_MCP_URL=https://openapi.tuniu.cn/mcp/hotel
TUNIU_TIMEOUT=60

# Tavily API (比价 - 首选)
TAVILY_API_KEY=your-tavily-key
TAVILY_TIMEOUT=15
TAVILY_ENABLED=True

# Serper API (比价 - 备用)
SERPER_API_KEY=your-serper-key
SERPER_TIMEOUT=10
SERPER_ENABLED=True

# 缓存配置
CACHE_ENABLED=True
CACHE_TTL=3600

# 应用设置
DEFAULT_PROVIDER=rollinggo
RESULTS_PER_PAGE=20
MAX_FAVORITES=50
MAX_HISTORY=20
```

### 5.2 供应商配置

| 供应商 | API Key 变量 | 端点 | 能力 |
|--------|--------------|------|------|
| RollingGo | `AIGOHOTEL_API_KEY` | MCP API/CLI | 全球搜索 |
| 途牛 | `TUNIU_API_KEY` | MCP HTTP | 搜索+预订 |
| Tavily | `TAVILY_API_KEY` | REST API | 价格搜索 |
| Serper | `SERPER_API_KEY` | REST API | 价格搜索 |

### 5.3 默认设置

| 设置 | 默认值 | 说明 |
|------|--------|------|
| DEFAULT_PROVIDER | rollinggo | 默认搜索供应商 |
| RESULTS_PER_PAGE | 20 | 每页结果数 |
| MAX_FAVORITES | 50 | 最大收藏数 |
| MAX_HISTORY | 20 | 最大历史记录数 |
| CACHE_TTL | 3600 | 缓存时间（秒） |

---

## 6. 外部服务

### 6.1 RollingGo MCP
- **用途**：全球酒店搜索
- **API Key 申请**：https://mcp.agentichotel.cn/apply
- **模式**：MCP API（首选），CLI 备用
- **返回**：`bookingUrl` 用于直接预订

### 6.2 途牛 MCP
- **用途**：国内酒店搜索 + 预订
- **API Key**：联系途牛获取
- **特点**：支持分页、完整预订流程

### 6.3 Tavily
- **用途**：AI 优化的网页价格搜索
- **API Key**：https://tavily.com
- **特点**：结构化搜索、URL 内容提取

### 6.4 Serper
- **用途**：Google 搜索 API 备用
- **API Key**：https://serper.dev
- **特点**：快速搜索结果

---

## 7. 运行应用

### 7.1 安装

```bash
# 安装依赖
pip install -r requirements.txt

# 安装 MCP 运行时 (RollingGo 需要)
pip install mcp httpx httpx-sse
```

### 7.2 配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 填入 API Keys
```

### 7.3 启动服务

```bash
# 开发服务器
python run.py

# 访问 http://localhost:5000
```

---

## 8. 错误处理

### 8.1 错误响应格式

```json
{
  "success": false,
  "error": "错误信息描述"
}
```

### 8.2 常见错误码

| 状态码 | 说明 |
|--------|------|
| 400 | 请求错误 - 缺少或无效参数 |
| 404 | 资源未找到 |
| 500 | 服务器内部错误 |

---

## 9. 未来规划

- [ ] 用户认证系统
- [ ] 多语言支持
- [ ] 高级筛选（价格区间、设施）
- [ ] 价格提醒
- [ ] 评论聚合
- [ ] 移动端 API

---

## 10. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 1.0.0 | 2026-03-20 | 初始 PRD 文档 |

---

*文档基于代码库分析生成*
