# Hotel Search Application

基于 RollingGo CLI 的酒店搜索与比价助手。

## 功能特性

- 酒店搜索：按目的地、日期、人数搜索酒店
- 高级筛选：星级、价格、距离、标签筛选
- 收藏功能：本地保存喜欢的酒店
- 搜索历史：记录最近搜索的目的地
- 响应式设计：支持桌面和移动设备

## 技术栈

- **后端**: Python Flask
- **前端**: Bootstrap 5 + Vanilla JavaScript
- **数据存储**: SQLite
- **酒店数据**: RollingGo CLI (AigoHotel API)

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

```
AIGOHOTEL_API_KEY=your-api-key-here
```

获取 API Key: https://mcp.agentichotel.cn/apply

### 3. 确保 Node.js 和 npx 可用

RollingGo CLI 通过 npx 运行：

```bash
# 验证 npx 可用
npx --version
```

## 运行

```bash
cd hotel
python run.py
```

应用将在 http://localhost:5000 启动。

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/search` | POST | 搜索酒店 |
| `/api/hotel/<id>` | GET | 获取酒店详情 |
| `/api/tags` | GET | 获取标签列表 |
| `/api/place-types` | GET | 获取地点类型列表 |
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
│   │   └── user.py          # 用户相关 API
│   ├── services/            # 业务逻辑
│   │   ├── rollinggo.py     # RollingGo CLI 封装
│   │   └── cache.py         # 缓存服务
│   ├── models/              # 数据模型
│   │   └── schema.py        # Pydantic 模型
│   ├── static/              # 静态资源
│   │   ├── css/style.css
│   │   └── js/app.js
│   └── templates/           # HTML 模板
│       ├── index.html       # 搜索页
│       ├── results.html     # 结果页
│       └── detail.html      # 详情页
├── rollinggo-hotel/         # RollingGo skill (英文)
├── rollinggo-hotel-cn/      # RollingGo skill (中文)
├── config.py                # 配置文件
├── requirements.txt         # Python 依赖
├── run.py                   # 启动入口
└── README.md                # 本文档
```

## 注意事项

1. **不支持预订**: 本应用仅提供酒店搜索和比价功能，不支持直接预订。用户需前往 Booking.com、Agoda 等平台完成预订。

2. **API Key**: 需要有效的 AigoHotel API Key 才能使用搜索功能。

3. **缓存**: 搜索结果默认缓存 1 小时，可在 `.env` 中调整 `CACHE_TTL`。

## License

MIT
