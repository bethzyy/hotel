# RollingGo NPX 参考

## 目录

1. 概览
2. 包名与命令名
3. 运行模式
4. API Key 配置
5. 帮助与参数发现
6. 命令说明
7. 端到端流程
8. 输出与退出码
9. 故障排查
10. 本地开发与验证

## 概览

当用户使用的是 `rollinggo` 的 Node 分发版本时，读取这份参考文件。

如果用户没有明确的生态限制，这也是默认优先推荐的分发版本，因为 npm/npx 在不同环境里的兼容性通常更好。

这个文件只说明同一套酒店查询工作流在 npm/npx 环境里怎么执行；真正的酒店查询主线仍然在主 `SKILL.md` 中。

覆盖范围包括：

- `npx rollinggo ...`
- `npm install -g rollinggo`
- 在 `rollinggo-npx/` 里做本地源码验证

npm 包名和暴露出来的命令名都叫 `rollinggo`。

## 包名与命令名

这里有两个名字：

- 包名：`rollinggo`
- 命令名：`rollinggo`

从 npm registry 临时执行的形式是：

```bash
npx rollinggo --help
```

如果包已经全局安装或已经在 PATH 里，直接使用：

```bash
rollinggo --help
```

## 运行模式

### 用 `npx` 临时运行

适用场景：

- 用户不想永久安装
- AI 代理需要临时执行

命令：

```bash
npx rollinggo --help
```

示例：

```bash
npx rollinggo search-hotels --origin-query "Find hotels near Tokyo Disneyland" --place "Tokyo Disneyland" --place-type "<从帮助页读取的支持值>"
```

### 全局安装模式

适用场景：

- 机器会重复调用 CLI
- 用户想直接执行 `rollinggo ...`
- AI 代理需要最短的稳定命令

当用户询问“默认该优先哪个分发版本”时，推荐这一条长期使用路径。

命令：

```bash
npm install -g rollinggo
rollinggo --help
```

### 本地源码模式

适用场景：

- 在验证尚未发布的 Node 改动
- 正在这个仓库里开发

命令：

```bash
npm install
npm run build
node dist/cli.js --help
node dist/cli.js search-hotels --help
```

## API Key 配置

解析顺序始终是：

1. `--api-key`
2. `AIGOHOTEL_API_KEY`

重复使用时推荐配置环境变量。

PowerShell：

```powershell
$env:AIGOHOTEL_API_KEY="YOUR_API_KEY"
```

Command Prompt：

```cmd
set AIGOHOTEL_API_KEY=YOUR_API_KEY
```

Bash 或 zsh：

```bash
export AIGOHOTEL_API_KEY="YOUR_API_KEY"
```

单命令覆盖：

```bash
rollinggo hotel-tags --api-key YOUR_API_KEY
```

如果用户还没有 API Key，指向申请入口：

https://mcp.agentichotel.cn/apply

如果没有 API Key，命令会在发请求之前失败。

## 帮助与参数发现

当用户不知道参数时，先执行：

```bash
rollinggo --help
rollinggo search-hotels --help
rollinggo hotel-detail --help
rollinggo hotel-tags --help
```

帮助页应用来回答：

- 应该执行哪个子命令
- 哪些参数是必填
- 日期与数字格式要求
- `--place-type` 可接受的精确取值
- 最小可运行示例

推荐的 AI 流程：

1. 看顶层帮助
2. 看子命令帮助
3. 拼出一条结构化命令
4. 按 JSON 解析 stdout

## 命令说明

### `search-hotels`

用途：

- 按目的地搜索酒店
- 应用结构化筛选
- 返回可比较的候选酒店

必填参数：

- `--origin-query`
- `--place`
- `--place-type`

基础语法：

```bash
rollinggo search-hotels --origin-query "<文本>" --place "<目的地>" --place-type "<从帮助页读取的支持值>"
```

常用可选参数：

- `--country-code <ISO2>`
- `--size <int>`
- `--check-in-date YYYY-MM-DD`
- `--stay-nights <int>`
- `--adult-count <int>`
- `--distance-in-meter <int>`
- `--star-ratings min,max`
- `--preferred-tag <value>` 可重复
- `--required-tag <value>` 可重复
- `--excluded-tag <value>` 可重复
- `--preferred-brand <value>` 可重复
- `--max-price-per-night <number>`
- `--min-room-size <number>`
- `--format json|table`

规则：

- `--place-type` 必须使用 `rollinggo search-hotels --help` 中展示的精确值。
- `--star-ratings` 必须是 `min,max` 形式，例如 `4.0,5.0`。
- 只有 `search-hotels` 允许 `table`。

最小示例：

```bash
rollinggo search-hotels --api-key <key> --origin-query "Find hotels near Tokyo Disneyland" --place "Tokyo Disneyland" --place-type "<从帮助页读取的支持值>"
```

适合人工阅读的示例：

```bash
rollinggo search-hotels --origin-query "Hotels in Tokyo" --place "Tokyo" --place-type "<从帮助页读取的支持值>" --format table
```

适合 AI 的示例：

```bash
rollinggo search-hotels --origin-query "Find hotels near Shanghai Disneyland" --place "Shanghai Disneyland" --place-type "<从帮助页读取的支持值>" --check-in-date 2026-04-01 --stay-nights 2 --adult-count 2 --size 5
```

解释说明：

- `--origin-query` 用于语义理解与排序。
- `--place` 是位置锚点。
- `--place-type` 用于说明地点类型。
- 标签与品牌参数可重复传入。
- 自动化场景默认应优先使用 JSON。

### `hotel-detail`

用途：

- 查询单个酒店的详情和价格计划
- 作为搜索结果之后的跟进步骤

标识规则：

- `--hotel-id` 与 `--name` 只能传一个
- 优先使用 `--hotel-id`

常用参数：

- `--check-in-date YYYY-MM-DD`
- `--check-out-date YYYY-MM-DD`
- `--adult-count <int>`
- `--child-count <int>`
- `--child-age <int>` 可重复
- `--room-count <int>`
- `--country-code <ISO2>`
- `--currency <ISO4217>`

校验规则：

- `--check-out-date` 必须晚于 `--check-in-date`
- `--child-count` 必须与 `--child-age` 次数一致
- 不允许 `--format table`

按酒店 ID 查询：

```bash
rollinggo hotel-detail --hotel-id 123456 --check-in-date 2026-04-01 --check-out-date 2026-04-03 --adult-count 2 --room-count 1
```

按酒店名查询：

```bash
rollinggo hotel-detail --name "The Ritz-Carlton Tokyo" --check-in-date 2026-04-01 --check-out-date 2026-04-03
```

带入住人数的示例：

```bash
rollinggo hotel-detail --hotel-id 123456 --check-in-date 2026-04-01 --check-out-date 2026-04-03 --adult-count 2 --child-count 2 --child-age 4 --child-age 7 --room-count 1
```

解释说明：

- 用户要实时价格时必须带日期。
- 关心真实可售情况时应带入住人数。
- 即使命令执行成功，也可能出现没有可售房型的业务结果。

### `hotel-tags`

用途：

- 在构建标签筛选前读取标签词表
- 查看可用品牌和属性元数据

语法：

```bash
rollinggo hotel-tags
```

示例：

```bash
rollinggo hotel-tags --api-key <key>
```

解释说明：

- 构建 `search-hotels` 标签筛选时，直接使用返回的标签字符串。
- 输出仅支持 JSON。

## 端到端流程

### 流程 1：先搜索，再看详情

1. 搜索：

```bash
rollinggo search-hotels --origin-query "Find hotels near Shanghai Disneyland" --place "Shanghai Disneyland" --place-type "<从帮助页读取的支持值>" --check-in-date 2026-04-01 --stay-nights 2 --size 3
```

2. 从 JSON 输出里提取 `hotelId`。

3. 查看详情：

```bash
rollinggo hotel-detail --hotel-id <hotelId> --check-in-date 2026-04-01 --check-out-date 2026-04-03 --adult-count 2 --room-count 1
```

### 流程 2：用户不知道参数

1. 先执行：

```bash
rollinggo --help
```

2. 再执行：

```bash
rollinggo search-hotels --help
```

3. 根据帮助页拼最终命令。

### 流程 3：先查标签再做筛选

1. 执行：

```bash
rollinggo hotel-tags
```

2. 找到需要的标签值。

3. 用可重复标签参数重新搜索：

```bash
rollinggo search-hotels --origin-query "Family hotels with breakfast" --place "Tokyo Disneyland" --place-type "<从帮助页读取的支持值>" --required-tag "breakfast included" --preferred-tag "family friendly"
```

## 输出与退出码

- stdout 只输出成功结果
- stderr 只输出错误
- 退出码 `0` 表示成功
- 退出码 `1` 表示 HTTP 或网络失败
- 退出码 `2` 表示 CLI 参数校验失败

输出前会移除 `bookingUrl` 字段。

默认格式是 JSON。

只有 `search-hotels` 支持 `--format table`。

## 故障排查

### 找不到 `rollinggo` 命令

可能原因：

- 包还没有全局安装
- 终端找不到 npm 的全局可执行文件
- 用户本来应该走 `npx`

用临时执行修复：

```bash
npx rollinggo --help
```

或全局安装：

```bash
npm install -g rollinggo
rollinggo --help
```

### 缺少 API Key

通过 `--api-key` 或 `AIGOHOTEL_API_KEY` 提供。

### 参数校验失败

常见原因：

- 缺少必填参数
- 日期格式错误
- `--star-ratings` 格式错误
- 同时传了 `--hotel-id` 和 `--name`
- `--child-count` 与 `--child-age` 次数不一致

下一步：

- 对同一子命令重新执行 `--help`

### 没有返回酒店

常见原因：

- 日期太严格
- 筛选条件太多
- `--place-type` 不正确
- 预算太低
- 距离太小

放宽方式：

- 增加 `--size`
- 增加 `--distance-in-meter`
- 删除标签条件
- 删除 `--star-ratings`
- 放宽日期或预算

### `hotel-detail` 没有返回房价计划

这可能是业务结果，不一定是 CLI 故障。

下一步：

- 换搜索结果里的其他酒店
- 换日期范围
- 检查入住人数参数
- 检查市场与币种设置

## 本地开发与验证

如果用户询问本地默认应该优先维护哪个包，优先建议 `rollinggo-npx/`，除非任务本身明确属于 Python 或 uv 生态。

本地帮助：

```bash
npm install
npm run build
node dist/cli.js --help
```

运行测试：

```bash
npm test
```

与 Python 版做一致性检查时，重点看：

- 顶层帮助页
- `search-hotels --help`
- 缺少必填参数时是否返回 `2`
- `hotel-detail` 与 `hotel-tags` 是否只支持 JSON
- 真实 API 的标签、搜索、详情是否都成功
