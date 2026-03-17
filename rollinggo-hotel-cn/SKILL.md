---
name: rollinggo-hotel-cn
description: 使用 RollingGo CLI 完成酒店搜索、结果筛选、酒店标签读取，以及酒店价格与详情查询。本技能的主线是“怎么查酒店”，包分发方式只是次要执行细节；默认优先推荐 npm/npx 分发版本，因为它在不同环境里的兼容性更好，只有当用户明确要求 uv 时，才优先使用 Python uv 分发版本。当用户需要酒店推荐、结构化筛选、房型与价格详情、标签发现，或需要使用 RollingGo CLI 查酒店时触发本技能。
---
# RollingGo CLI

## 概览

使用 `rollinggo` 命令作为酒店搜索工作流的主入口。

优先使用明确的子命令和结构化参数。除非用户明确要求表格，否则输出默认保持 JSON。

这个技能主要完成四件事：

1. 解释如何用 CLI 查酒店。
2. 直接在终端执行真实酒店搜索、标签查询和详情查询命令。
3. 帮助用户收窄结果并理解酒店输出。
4. 在需要时校验 Python 与 Node 两个分发版本是否一致。

## 主要工作流

把“查酒店”当作主任务。除非用户已经把问题限定在后续某一步，否则按下面流程执行：

1. 先明确搜索目标：目的地、日期、晚数、预算、星级、标签、距离和入住人数。
2. 如果要按标签筛选，先执行 `hotel-tags`。
3. 使用结构化筛选执行 `search-hotels`。
4. 从 JSON 结果里读出一个或多个 `hotelId`。
5. 对选中的酒店执行 `hotel-detail --hotel-id <id>`。
6. 解读房型、价格，或“无可售房型”这类业务结果。
7. 如果结果不理想，就放宽筛选条件重新搜索。

## 酒店查询优先级

在帮助用户查酒店时，优先关注这些内容：

1. 目的地和 `place-type` 是否正确。
2. 日期和入住人数是否合理。
3. 是否只使用了必要的筛选条件。
4. 是否先搜索再查看详情。
5. 是否保持 JSON 输出，方便 AI 或脚本继续处理。

只有当用户需要知道“怎么执行命令”时，才把重点转到包分发方式上。

## 执行环境参考文件

只读取与当前分发方式匹配的参考文件。

- 如果用户讨论的是 Node `npm` 或 `npx` 包，读取 [references/rollinggo-npx.md](references/rollinggo-npx.md)。
- 如果用户讨论的是 Python `uv` 或 `uvx` 包，读取 [references/rollinggo-uv.md](references/rollinggo-uv.md)。
- 如果任务是做一致性检查、发布对比，或者“让 npm 行为和 uv 一样”，同时读取两个参考文件。

## 分发版本选择

除非用户明确要求对比，否则一次会话只围绕一个分发版本展开。

- 如果用户没有明确的生态偏好，默认先使用 `npm` 参考文件，因为 npm/npx 在不同环境中的兼容性更好。
- 当用户提到 `npm`、`npx`、npm publish、Node 打包，想要兼容性更好的默认路径，或正在本地 `rollinggo-npx` 项目中工作时，使用 `npm` 参考文件。
- 当用户明确提到 `uv`、`uvx`、PyPI、Python 打包，或本地 `rollinggo-uv` 项目时，使用 `uv` 参考文件。
- 如果用户说“两个地方的 CLI 都要一样工作”，同时读取两个参考文件，对比命令面、帮助页、退出码和真实请求行为。

## 共享工作流

除非用户已经把任务范围收窄到后续某一步，否则按下面顺序执行：

1. 先确认用户的酒店查询目标。
2. 只有在执行环境确实重要时，再确认用户准备如何运行 CLI，是临时执行、已安装命令，还是本地源码。
3. 如果没有明确生态约束，默认先选择 npm/npx 分发版本。
4. 确认 API Key 是否通过 `--api-key` 或 `AIGOHOTEL_API_KEY` 提供。如果用户还没有 Key，指向申请入口：https://mcp.agentichotel.cn/apply
5. 如果参数含义不确定，先查看 `rollinggo --help` 或 `rollinggo <command> --help`。
6. 如果需要标签筛选，先执行 `hotel-tags`。
7. 使用 `search-hotels` 获取候选酒店。
8. 提取 `hotelId`。
9. 使用 `hotel-detail --hotel-id <id>` 查询价格和房型详情。
10. 解释 stdout、stderr 和退出码。

## 输出规则

- 把 stdout 视为结果载荷，不要混入解释文字。
- 把 stderr 视为错误输出。
- AI 和自动化场景优先使用 JSON。
- 只允许 `search-hotels` 使用 `--format table`。
- 约定退出码 `0` 为成功，`1` 为 HTTP 或网络失败，`2` 为 CLI 参数校验失败。

## 如何回答用户

当用户不熟悉 CLI 时：

1. 先围绕“怎么查酒店”讲，不要先讲打包生态。
2. 先给完成当前查询任务的精确命令。
3. 再解释下一步要看哪一段输出。
4. 只有当用户还不知道怎么执行时，再补安装或临时运行方式。
5. 必要时再补 API Key 配置。

当用户是 AI 操作员或自动化工程师时：

- 优先给紧凑命令。
- 优先给 JSON 输出。
- 优先使用 `hotelId`，而不是酒店名称。
- 优先使用确定性的结构化参数，不要依赖模糊描述。
- 一次任务尽量保持一条完整命令。

## 一致性检查清单

在对比 Python 与 Node 分发版本时，显式核对以下项目：

1. 顶层命令名都是 `rollinggo`。
2. 子命令都是 `search-hotels`、`hotel-detail`、`hotel-tags`。
3. API Key 解析顺序都是 `--api-key` 优先，然后 `AIGOHOTEL_API_KEY`。
4. `search-hotels` 支持 `--format table`。
5. `hotel-detail` 与 `hotel-tags` 拒绝 `--format table`。
6. 缺少必填参数时返回退出码 `2`。
7. HTTP 失败时返回退出码 `1`。
8. 输出前会递归移除 `bookingUrl` 字段。
9. 对真实线上 API 的酒店搜索与详情查询仍然能成功。

## 本地路径

在本仓库中使用这些路径：

- Python 包项目：`rollinggo-uv/`
- Node 包项目：`rollinggo-npx/`
- 当前技能根目录：`skills/rollinggo-hotel-cn/`

## 默认建议

- 默认优先解释怎么查酒店，而不是先解释包分发方式。
- 默认优先推荐 npm/npx 分发版本，因为它在不同环境里的兼容性更好。
- 如果环境里已经有命令，优先使用已安装的 `rollinggo ...`，不要用更长的包装命令。
- 只有当用户明确需要 Python 打包、uv 工具链或 `rollinggo-uv` 源码时，才优先推荐 uv 分发版本。
- 默认走 `search-hotels` 再走 `hotel-detail`。
- 不确定枚举值或日期格式时，优先先看帮助页。
- 不要把过长说明继续堆在本文件里，优先读取匹配的参考文件。
