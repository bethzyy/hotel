# Hotel Search Application

多平台酒店搜索、比价与预订助手，支持 RollingGo（全球）和途牛（国内）双数据源。

## 功能特性

- **多平台搜索**: RollingGo（全球酒店）+ 途牛（国内酒店）
- **跨平台比价**: 自动匹配同一酒店在不同平台的价格
- **在线预订**: 支持途牛平台直接预订（国内酒店）
- **高级筛选**: 星级、价格、距离、标签筛选
- **收藏功能**: 本地保存喜欢的酒店
- **搜索历史**: 记录最近搜索的目的地
- **响应式设计**: 支持桌面和移动设备

## 技术栈

- **后端**: Python Flask
- **前端**: Bootstrap 5 + Vanilla JavaScript
- **数据存储**: SQLite
- **酒店数据**:
  - RollingGo MCP API（全球酒店搜索）
  - 途牛 MCP API（国内酒店搜索与预订）

## 安装

### 1. 安装 Python 依赖

```bash
cd hotel
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# RollingGo API Key（全球酒店搜索）
AIGOHOTEL_API_KEY=your-rollinggo-api-key

# 途牛 API Key（国内酒店搜索与预订）
TUNIU_API_KEY=your-tuniu-api-key

# 默认数据源: rollinggo 或 tuniu
DEFAULT_PROVIDER=rollinggo
```

**获取 API Key**:
- RollingGo: https://mcp.aigohotel.com/apply
- 途牛: https://open.tuniu.com/mcp/apikeys

## 运行

```bash
python run.py
```

应用将在 http://localhost:5000 启动。

## API 端点

### 搜索与详情

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/search` | POST | 搜索酒店（支持 rollinggo/tuniu） |
| `/api/hotel/<id>` | GET | 获取酒店详情 |
| `/api/providers` | GET | 获取可用数据源列表 |
| `/api/tags` | GET | 获取标签列表（RollingGo） |
| `/api/place-types` | GET | 获取地点类型列表 |

### 比价功能

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/compare/<provider>/<hotel_id>` | GET | 跨平台比价 |
| `/api/compare/batch` | POST | 批量比价 |
| `/api/compare/status` | GET | 比价功能状态 |

### 预订功能（途牛）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/booking/create-order` | POST | 创建预订订单 |

### 用户功能

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/favorites` | GET | 获取收藏列表 |
| `/api/favorites` | POST | 添加收藏 |
| `/api/favorites/<id>` | DELETE | 删除收藏 |
| `/api/favorites/toggle` | POST | 切换收藏状态 |
| `/api/history` | GET | 获取搜索历史 |
| `/api/history` | DELETE | 清空搜索历史 |

## 项目结构

```
hotel/
├── app/
│   ├── __init__.py          # Flask 应用初始化
│   ├── routes/              # API 路由
│   │   ├── search.py        # 搜索 API
│   │   ├── hotel.py         # 酒店详情 API
│   │   ├── comparison.py    # 比价 API
│   │   ├── booking.py       # 预订 API
│   │   └── user.py          # 用户相关 API
│   ├── services/            # 业务逻辑
│   │   ├── hotel_provider.py # Provider 抽象层
│   │   ├── rollinggo.py     # RollingGo MCP 客户端
│   │   ├── tuniu.py         # 途牛 MCP 客户端
│   │   ├── hotel_matcher.py # 跨平台酒店匹配
│   │   └── cache.py         # 缓存服务
│   ├── static/              # 静态资源
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/           # HTML 模板
│       ├── index.html       # 搜索页
│       ├── results.html     # 结果页（含比价）
│       ├── detail.html      # 详情页
│       ├── booking.html     # 预订页
│       └── order.html       # 订单页
├── rollinggo-hotel/         # RollingGo skill (英文)
├── rollinggo-hotel-cn/      # RollingGo skill (中文)
├── tuniu-hotel-SKILL.md     # 途牛 MCP 文档
├── config.py                # 配置文件
├── requirements.txt         # Python 依赖
├── run.py                   # 启动入口
└── README.md                # 本文档
```

## Provider 对比

| 特性 | RollingGo | 途牛 |
|------|-----------|------|
| 覆盖范围 | 全球 | 国内 |
| 搜索 | ✅ | ✅ |
| 比价 | ✅ | ✅ |
| 预订 | ❌ | ✅ |
| 分页 | ❌ | ✅ |

## 使用流程

1. **搜索酒店**: 输入目的地、日期、人数
2. **查看结果**: 浏览酒店列表，点击「比价」查看跨平台价格
3. **查看详情**: 点击酒店查看详细信息、房型、价格
4. **预订酒店**: （国内酒店）选择房型，填写入住人信息，完成预订
5. **支付订单**: 跳转到途牛完成支付

## 注意事项

1. **RollingGo**: 仅提供全球酒店搜索和比价，不支持直接预订
2. **途牛**: 支持国内酒店搜索、比价和预订
3. **比价匹配**: 基于酒店名称相似度和地址距离自动匹配
4. **缓存**: 搜索结果默认缓存 1 小时，比价结果缓存 30 分钟

## License

MIT
