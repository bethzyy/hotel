# RollingGo NPX Reference

## Table of Contents

1. Overview
2. Package and command naming
3. Run modes
4. API key setup
5. Help and parameter discovery
6. Command guide
7. End-to-end workflows
8. Output and exit codes
9. Troubleshooting
10. Local development and validation

## Overview

Use this reference when the user is working with the Node distribution of `rollinggo`.

This is the preferred default distribution when the user has no ecosystem constraint, because npm/npx is generally more compatible across environments.

This file explains how to execute the hotel-search workflow in the npm/npx environment. The main hotel-search logic still lives in `SKILL.md`.

This includes:

- `npx rollinggo ...`
- `npm install -g rollinggo`
- local source validation inside `rollinggo-npx/`

The npm package and the exposed command are both named `rollinggo`.

## Package and Command Naming

There are two names involved:

- package name: `rollinggo`
- command name: `rollinggo`

Temporary execution from the npm registry is:

```bash
npx rollinggo --help
```

If the package is already installed globally or otherwise on PATH, the shorter form is:

```bash
rollinggo --help
```

## Run Modes

### Temporary run with `npx`

Use when:

- the user does not want permanent installation
- an AI agent needs temporary execution

Command:

```bash
npx rollinggo --help
```

Example:

```bash
npx rollinggo search-hotels --origin-query "Find hotels near Tokyo Disneyland" --place "Tokyo Disneyland" --place-type "<supported-value-from-help>"
```

### Installed global mode

Use when:

- the machine will run the CLI repeatedly
- the user wants `rollinggo ...` directly
- an AI agent should use the shortest stable command

This is the recommended long-term setup when the user asks which distribution should be preferred.

Commands:

```bash
npm install -g rollinggo
rollinggo --help
```

### Local source mode

Use when:

- validating unpublished Node changes
- working inside this repository

Commands:

```bash
npm install
npm run build
node dist/cli.js --help
node dist/cli.js search-hotels --help
```

## API Key Setup

Resolution order is always:

1. `--api-key`
2. `AIGOHOTEL_API_KEY`

Preferred setup for repeated usage:

PowerShell:

```powershell
$env:AIGOHOTEL_API_KEY="YOUR_API_KEY"
```

Command Prompt:

```cmd
set AIGOHOTEL_API_KEY=YOUR_API_KEY
```

Bash or zsh:

```bash
export AIGOHOTEL_API_KEY="YOUR_API_KEY"
```

Single-command override:

```bash
rollinggo hotel-tags --api-key YOUR_API_KEY
```

If the user does not yet have an API key, direct them to:

https://mcp.agentichotel.cn/apply

If no API key is available, the command fails before sending the request.

## Help and Parameter Discovery

Use these commands when the user does not know parameters:

```bash
rollinggo --help
rollinggo search-hotels --help
rollinggo hotel-detail --help
rollinggo hotel-tags --help
```

The help output should be used to answer:

- which subcommand to run
- which flags are required
- accepted date and numeric formats
- exact values accepted by `--place-type`
- minimal command examples

Recommended AI flow:

1. inspect top-level help
2. inspect subcommand help
3. build one structured command
4. parse stdout as JSON

## Command Guide

### `search-hotels`

Purpose:

- search hotels by destination
- apply structured filters
- return candidate hotels for comparison

Required options:

- `--origin-query`
- `--place`
- `--place-type`

Core syntax:

```bash
rollinggo search-hotels --origin-query "<text>" --place "<destination>" --place-type "<supported-value-from-help>"
```

Common optional flags:

- `--country-code <ISO2>`
- `--size <int>`
- `--check-in-date YYYY-MM-DD`
- `--stay-nights <int>`
- `--adult-count <int>`
- `--distance-in-meter <int>`
- `--star-ratings min,max`
- `--preferred-tag <value>` repeated
- `--required-tag <value>` repeated
- `--excluded-tag <value>` repeated
- `--preferred-brand <value>` repeated
- `--max-price-per-night <number>`
- `--min-room-size <number>`
- `--format json|table`

Rules:

- Use the exact `--place-type` values shown by `rollinggo search-hotels --help`.
- Use `--star-ratings` in `min,max` format such as `4.0,5.0`.
- `table` is allowed only on `search-hotels`.

Minimal example:

```bash
rollinggo search-hotels --api-key <key> --origin-query "Find hotels near Tokyo Disneyland" --place "Tokyo Disneyland" --place-type "<supported-value-from-help>"
```

Human-readable example:

```bash
rollinggo search-hotels --origin-query "Hotels in Tokyo" --place "Tokyo" --place-type "<supported-value-from-help>" --format table
```

AI-friendly example:

```bash
rollinggo search-hotels --origin-query "Find hotels near Shanghai Disneyland" --place "Shanghai Disneyland" --place-type "<supported-value-from-help>" --check-in-date 2026-04-01 --stay-nights 2 --adult-count 2 --size 5
```

Interpretation notes:

- `--origin-query` helps semantic ranking.
- `--place` is the location anchor.
- `--place-type` disambiguates the kind of place.
- repeated tag and brand flags can be used more than once.
- JSON is the default and should be preferred for automation.

### `hotel-detail`

Purpose:

- fetch detail and rate plans for one hotel
- follow up after a search result already identified the hotel

Identifier rule:

- pass exactly one of `--hotel-id` or `--name`
- prefer `--hotel-id` whenever possible

Common flags:

- `--check-in-date YYYY-MM-DD`
- `--check-out-date YYYY-MM-DD`
- `--adult-count <int>`
- `--child-count <int>`
- `--child-age <int>` repeated
- `--room-count <int>`
- `--country-code <ISO2>`
- `--currency <ISO4217>`

Validation rules:

- `--check-out-date` must be later than `--check-in-date`
- `--child-count` must match the number of `--child-age` flags
- `--format table` is not allowed

Example by hotel ID:

```bash
rollinggo hotel-detail --hotel-id 123456 --check-in-date 2026-04-01 --check-out-date 2026-04-03 --adult-count 2 --room-count 1
```

Example by name:

```bash
rollinggo hotel-detail --name "The Ritz-Carlton Tokyo" --check-in-date 2026-04-01 --check-out-date 2026-04-03
```

Occupancy example:

```bash
rollinggo hotel-detail --hotel-id 123456 --check-in-date 2026-04-01 --check-out-date 2026-04-03 --adult-count 2 --child-count 2 --child-age 4 --child-age 7 --room-count 1
```

Interpretation notes:

- include dates when the user wants live pricing
- include occupancy when realistic availability matters
- success can still return a business result with no available room plans

### `hotel-tags`

Purpose:

- fetch tag vocabulary before composing tag filters
- inspect available brand and attribute metadata

Syntax:

```bash
rollinggo hotel-tags
```

Example:

```bash
rollinggo hotel-tags --api-key <key>
```

Interpretation notes:

- use returned strings exactly when building `search-hotels` tag filters
- output is JSON only

## End-to-End Workflows

### Workflow 1: Search then detail

1. Search:

```bash
rollinggo search-hotels --origin-query "Find hotels near Shanghai Disneyland" --place "Shanghai Disneyland" --place-type "<supported-value-from-help>" --check-in-date 2026-04-01 --stay-nights 2 --size 3
```

2. Inspect the JSON response and extract `hotelId`.

3. Fetch detail:

```bash
rollinggo hotel-detail --hotel-id <hotelId> --check-in-date 2026-04-01 --check-out-date 2026-04-03 --adult-count 2 --room-count 1
```

### Workflow 2: User does not know parameters

1. Run:

```bash
rollinggo --help
```

2. Run:

```bash
rollinggo search-hotels --help
```

3. Build the final command from the help output.

### Workflow 3: Filter by tags

1. Run:

```bash
rollinggo hotel-tags
```

2. Find useful tag values.

3. Re-run search with repeated tag flags:

```bash
rollinggo search-hotels --origin-query "Family hotels with breakfast" --place "Tokyo Disneyland" --place-type "<supported-value-from-help>" --required-tag "breakfast included" --preferred-tag "family friendly"
```

## Output and Exit Codes

- stdout contains successful result payloads only
- stderr contains errors only
- exit code `0` means success
- exit code `1` means HTTP or network failure
- exit code `2` means CLI validation failure

The CLI strips `bookingUrl` fields before printing.

Default format is JSON.

Only `search-hotels` accepts `--format table`.

## Troubleshooting

### `rollinggo` command not found

Possible causes:

- the package was not installed globally
- the terminal cannot find npm global binaries
- the user intended to use `npx`

Fix with temporary execution:

```bash
npx rollinggo --help
```

Or install globally:

```bash
npm install -g rollinggo
rollinggo --help
```

### Missing API key

Fix by passing `--api-key` or setting `AIGOHOTEL_API_KEY`.

### Validation failure

Common causes:

- missing required flags
- wrong date format
- invalid `--star-ratings`
- both `--hotel-id` and `--name`
- mismatched `--child-count` and `--child-age`

Next step:

- rerun the same subcommand with `--help`

### No hotels returned

Common causes:

- restrictive dates
- too many filters
- wrong `--place-type`
- budget too low
- distance too small

Loosen filters by:

- increasing `--size`
- increasing `--distance-in-meter`
- removing tags
- removing `--star-ratings`
- widening dates or budget

### No room plans returned by `hotel-detail`

This may be a valid business result, not a CLI failure.

Next steps:

- try another hotel from search results
- try another date range
- verify occupancy inputs
- verify market and currency inputs

## Local Development and Validation

If the user asks which local package to favor by default, favor `rollinggo-npx/` unless there is a Python-specific reason to work in `rollinggo-uv/`.

Run local help:

```bash
npm install
npm run build
node dist/cli.js --help
```

Run tests:

```bash
npm test
```

Useful parity checks against the Python build:

- top-level help output
- `search-hotels --help`
- exit code `2` for missing required parameters
- JSON-only behavior for `hotel-detail` and `hotel-tags`
- live API success for tags, search, and detail
