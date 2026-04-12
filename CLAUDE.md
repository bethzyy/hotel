# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hotel search and comparison application with multi-provider MCP architecture. Supports global hotel search (RollingGo) and domestic booking (Tuniu). Uses AI (GLM-4-flash) for intelligent search parameter extraction.

## Commands

```bash
# Run development server
python run.py                    # http://localhost:5000

# Install dependencies
pip install -r requirements.txt

# Install MCP runtime dependencies (required for RollingGo)
pip install mcp httpx httpx-sse
```

## Environment Setup

Copy `.env.example` to `.env` and configure:

```
AIGOHOTEL_API_KEY=your-key-here    # Required for RollingGo
ZHIPU_API_KEY=your-key-here        # Required for AI intent parsing
DEFAULT_PROVIDER=rollinggo          # or 'tuniu'
```

## Architecture

### Single Server (Flask + Nuxt SPA)

Nuxt generates static SPA (`ssr: false`) → Flask serves static files + API routes. One server handles everything.

### Multi-Provider Pattern

```
HotelProvider (ABC)
├── RollingGoProvider    # Global search, no booking
└── TuniuProvider        # Domestic search + booking
```

**Key files:**
- `app/services/hotel_provider.py` - Abstract interface + implementations
- `app/services/rollinggo.py` - RollingGo CLI/MCP wrapper
- `app/services/tuniu.py` - Tuniu MCP HTTP client
- `app/services/intent_parser.py` - AI search intent parser (GLM-4-flash)

### Request Flow

```
Frontend → Flask Route → [LLM Intent Parser] → get_provider(name) → Provider.search_hotels() → Normalized response
```

### AI Intent Parser

When user provides city + landmark, the system uses GLM-4-flash to:
1. Extract structured params: city, place, placeType, minStar, maxPrice
2. Determine optimal `placeType` (城市/机场/景点/火车站/地铁站/酒店/区/县/详细地址)
3. Fallback to keyword matching if LLM unavailable

RollingGo API's `placeType` significantly affects result accuracy (e.g., 机场 type returns hotels 6x closer than 详细地址).

### RollingGo Dual Mode

RollingGo service has two execution modes with automatic fallback:
1. **MCP API** (primary) - Returns `bookingUrl` for direct booking
2. **CLI** (fallback) - `npx rollinggo` subprocess

### Configuration

All config via environment variables loaded in `config.py`:
- `AIGOHOTEL_API_KEY` - RollingGo API key
- `ZHIPU_API_KEY` - ZhipuAI API key (for intent parsing)
- `TUNIU_API_KEY` - Tuniu API key (optional)
- `DEFAULT_PROVIDER` - 'rollinggo' or 'tuniu' (default: tuniu)

### Data Normalization

Each provider has `normalize_hotel()` and `normalize_hotel_detail()` methods that transform API responses to a standard format. This ensures frontend compatibility regardless of provider.

## API Endpoints

| Endpoint | Provider | Notes |
|----------|----------|-------|
| `POST /api/search` | Both | Provider-specific params, AI intent parsing |
| `GET /api/hotel/<id>` | Both | Detail + room plans |
| `POST /api/booking/create-order` | Tuniu only | Create booking order |
| `GET /api/tags` | RollingGo only | Filter tags |
| `GET /api/providers` | - | List available providers |

## RollingGo API Notes

- `placeType` values: 城市、机场、景点、火车站、地铁站、酒店、区/县、详细地址
- Combine city + landmark for better recognition: `place="北京香山"` not `place="香山"`
- `starRatings` and `distanceInMeter` params are accepted but **not enforced** by API
- Post-filter star ratings locally in `search.py`
- Maximum 20 results per request (API hard limit)

## RollingGo Skill

The `rollinggo-hotel/` and `rollinggo-hotel-cn/` directories contain Claude Code skills for CLI usage. Read `references/rollinggo-npx.md` for command details.

## Notes

- **Windows paths**: Use forward slashes (`C:/path`) or quoted backslashes in bash commands
- **API Key**: Get RollingGo API key from https://mcp.agentichotel.cn/apply
