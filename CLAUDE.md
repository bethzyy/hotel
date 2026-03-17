# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Hotel search and comparison application with multi-provider MCP architecture. Supports global hotel search (RollingGo) and domestic booking (Tuniu).

## Commands

```bash
# Run development server
python run.py                    # http://localhost:5000

# Install dependencies
pip install -r requirements.txt
```

## Architecture

### Multi-Provider Pattern

The application uses a provider abstraction pattern for hotel services:

```
HotelProvider (ABC)
├── RollingGoProvider    # Global search, no booking
└── TuniuProvider        # Domestic search + booking
```

**Key files:**
- `app/services/hotel_provider.py` - Abstract interface + implementations
- `app/services/rollinggo.py` - RollingGo CLI/MCP wrapper
- `app/services/tuniu.py` - Tuniu MCP HTTP client

### Request Flow

```
Flask Route → get_provider(name) → Provider.search_hotels() → Normalized response
```

### RollingGo Dual Mode

RollingGo service has two execution modes with automatic fallback:
1. **MCP API** (primary) - Returns `bookingUrl` for direct booking
2. **CLI** (fallback) - `npx rollinggo` subprocess

### Configuration

All config via environment variables loaded in `config.py`:
- `AIGOHOTEL_API_KEY` - RollingGo API key
- `TUNIU_API_KEY` - Tuniu API key (optional)
- `DEFAULT_PROVIDER` - 'rollinggo' or 'tuniu' (default: tuniu)

### Data Normalization

Each provider has `normalize_hotel()` and `normalize_hotel_detail()` methods that transform API responses to a standard format. This ensures frontend compatibility regardless of provider.

## API Endpoints

| Endpoint | Provider | Notes |
|----------|----------|-------|
| `POST /api/search` | Both | Provider-specific params |
| `GET /api/hotel/<id>` | Both | Detail + room plans |
| `POST /api/booking/create-order` | Tuniu only | Create booking order |
| `GET /api/tags` | RollingGo only | Filter tags |
| `GET /api/providers` | - | List available providers |

## RollingGo Skill

The `rollinggo-hotel/` and `rollinggo-hotel-cn/` directories contain Claude Code skills for CLI usage. Read `references/rollinggo-npx.md` for command details.
