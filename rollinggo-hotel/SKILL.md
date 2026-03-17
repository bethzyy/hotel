---
name: rollinggo-hotel
description: Use the RollingGo CLI to find hotels, narrow results with destination, date, tag, distance, star, and budget filters, inspect hotel tags, and fetch hotel pricing and detail. This skill is primarily about the hotel search workflow; package distribution choice is secondary and defaults to npm/npx unless uv is explicitly required. Trigger this skill when the user asks how to search hotels, compare hotel candidates, filter hotel results, inspect hotel detail, or use the RollingGo CLI for hotel lookup.
---
# RollingGo CLI

## Overview

Use the `rollinggo` command as the primary interface for hotel search workflows.

Prefer explicit subcommands and structured flags. Keep output in JSON unless a human explicitly asks for a table.

Use this skill to do four things:

1. Explain how to search hotels with the CLI.
2. Execute real hotel search, tag, and hotel-detail commands from the terminal.
3. Help users narrow results and interpret hotel output.
4. Validate parity between the Python and Node distributions when needed.

## Primary Workflow

Treat hotel lookup as the main task. Use this sequence unless the user has already narrowed the task to a later step.

1. Clarify the search target: destination, date, nights, budget, star range, tags, distance, and occupancy.
2. If tag-based filtering is needed, run `hotel-tags` first.
3. Run `search-hotels` with structured filters.
4. Read the JSON result and extract one or more `hotelId` values.
5. Run `hotel-detail --hotel-id <id>` for the selected hotel.
6. Interpret room plans, pricing, or business-level no-availability results.
7. If results are weak, loosen filters and search again.

## Hotel Search Priorities

When helping users search hotels, keep the emphasis on these tasks first:

1. Getting the right destination and place type.
2. Setting dates and occupancy correctly.
3. Applying only the necessary filters.
4. Searching first and drilling into detail second.
5. Using JSON output so AI or scripts can continue processing.

Package or runtime discussion should only appear when the user needs to know how to execute the command.

## Execution Environment References

Load only the reference file that matches the runtime environment being discussed.

- For the Node `npm` or `npx` package, read [references/rollinggo-npx.md](references/rollinggo-npx.md).
- For the Python `uv` or `uvx` package, read [references/rollinggo-uv.md](references/rollinggo-uv.md).
- For parity checks, release comparisons, or "make npm behave like uv" requests, read both reference files.

## Distribution Selection

Choose one distribution and keep the session consistent unless the user explicitly asks to compare them.

- If the user does not express a packaging preference, default to the `npm` reference first because the npm/npx distribution has better cross-environment compatibility.
- Use the `npm` reference when the user mentions `npm`, `npx`, npm publish, Node packaging, wants the most compatible default path, or is working in the `rollinggo-npx` local project.
- Use the `uv` reference when the user explicitly mentions `uv`, `uvx`, PyPI, Python packaging, or the `rollinggo-uv` local project.
- If the user says "the CLI should work the same in both places", use both references and compare command surface, help output, exit codes, and real request behavior.

## Shared Workflow

Apply this sequence unless the user already narrowed the task to a later step.

1. Confirm the user's hotel-search goal.
2. Confirm how the user plans to run the CLI only if execution environment matters.
3. If there is no explicit ecosystem constraint, choose the npm/npx distribution first.
4. Confirm API key availability through `--api-key` or `AIGOHOTEL_API_KEY`. If the user does not have a key yet, direct them to apply at https://mcp.agentichotel.cn/apply.
5. Inspect `rollinggo --help` or `rollinggo <command> --help` if parameter meaning is uncertain.
6. Use `hotel-tags` if tags are needed before building filters.
7. Use `search-hotels` to obtain candidate hotels.
8. Extract `hotelId`.
9. Use `hotel-detail --hotel-id <id>` for pricing and room detail.
10. Interpret stdout, stderr, and exit codes.

## Output Rules

- Treat stdout as result payload only.
- Treat stderr as error output only.
- Prefer JSON for AI and automation.
- Allow `--format table` only for `search-hotels`.
- Expect exit code `0` for success, `1` for HTTP or network failure, and `2` for CLI validation failure.

## How To Answer Users

When the user is new to the CLI:

1. Start with the hotel-search task, not the packaging discussion.
2. Show the exact hotel-search command for the requested task.
3. Explain what output to inspect next.
4. Only then explain install or temporary run if the user still needs an execution path.
5. Show API key setup if required.

When the user is an AI operator or automation engineer:

- Prefer compact commands.
- Prefer JSON output.
- Prefer `hotelId` over hotel name.
- Prefer deterministic flags over prose.
- Prefer one shell command per task.

## Parity Checklist

When comparing Python and Node distributions, verify these items explicitly:

1. Top-level command name is `rollinggo`.
2. Subcommands are `search-hotels`, `hotel-detail`, and `hotel-tags`.
3. API key resolution order is `--api-key` then `AIGOHOTEL_API_KEY`.
4. `search-hotels` supports `--format table`.
5. `hotel-detail` and `hotel-tags` reject `--format table`.
6. Missing required parameters return exit code `2`.
7. HTTP failures return exit code `1`.
8. Responses remove `bookingUrl` recursively before printing.
9. Real hotel search and detail calls still succeed against the live API.

## Local Paths

Use these repo paths when working from local source:

- Python package project: `rollinggo-uv/`
- Node package project: `rollinggo-npx/`
- Skill root: `skills/rollinggo-hotel/`

## Good Defaults

- Prefer explaining how to search hotels over explaining package distribution choice.
- Prefer the npm/npx distribution by default because it is more compatible across environments.
- Prefer installed `rollinggo ...` over longer wrappers when available.
- Prefer the uv distribution only when the user explicitly wants Python packaging, uv tooling, or the `rollinggo-uv` source tree.
- Prefer `search-hotels` followed by `hotel-detail`.
- Prefer help inspection before guessing enum values or date formats.
- Prefer reading the matching reference file instead of repeating long instructions in this file.
