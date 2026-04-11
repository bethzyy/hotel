"""
Configuration for Hotel Search Application
"""
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Production: loads .env.production via docker-compose env_file
# Development: loads .env
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Environment: 'development' or 'production'
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
DEBUG = os.environ.get('FLASK_DEBUG', 'True' if FLASK_ENV == 'development' else 'False').lower() == 'true'

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = secrets.token_hex(32)
    else:
        raise RuntimeError('SECRET_KEY environment variable is required in production')

# Database Configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'data' / 'hotel.db'))
# SQLAlchemy URI: SQLite for dev, PostgreSQL for production
# e.g. postgresql://user:pass@localhost:5432/hotel_db
SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f'sqlite:///{DATABASE_PATH}')
SQLALCHEMY_TRACK_MODIFICATIONS = False

# JWT Configuration
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', '86400'))  # 24h

# RollingGo CLI Configuration
ROLLINGGO_API_KEY = os.environ.get('AIGOHOTEL_API_KEY', '')
ROLLINGGO_TIMEOUT = int(os.environ.get('ROLLINGGO_TIMEOUT', '60'))

# Tuniu MCP Configuration
TUNIU_API_KEY = os.environ.get('TUNIU_API_KEY', '')
TUNIU_MCP_URL = os.environ.get('TUNIU_MCP_URL', 'https://openapi.tuniu.cn/mcp/hotel')
TUNIU_TIMEOUT = int(os.environ.get('TUNIU_TIMEOUT', '60'))

# Cache Configuration
CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'True').lower() == 'true'
CACHE_TTL = int(os.environ.get('CACHE_TTL', '3600'))  # 1 hour default

# Serper.dev API Configuration (for external platform price comparison)
SERPER_API_KEY = os.environ.get('SERPER_API_KEY', '')
SERPER_TIMEOUT = int(os.environ.get('SERPER_TIMEOUT', '10'))
SERPER_ENABLED = os.environ.get('SERPER_ENABLED', 'True').lower() == 'true'

# Tavily API Configuration (for external platform price comparison)
TAVILY_API_KEY = os.environ.get('TAVILY_API_KEY', '')
TAVILY_TIMEOUT = int(os.environ.get('TAVILY_TIMEOUT', '15'))
TAVILY_ENABLED = os.environ.get('TAVILY_ENABLED', 'True').lower() == 'true'

# Application Settings
RESULTS_PER_PAGE = int(os.environ.get('RESULTS_PER_PAGE', '10'))
MAX_FAVORITES = int(os.environ.get('MAX_FAVORITES', '50'))
MAX_HISTORY = int(os.environ.get('MAX_HISTORY', '20'))

# Place types supported by RollingGo CLI (Chinese values required)
PLACE_TYPES = [
    '城市',
    '机场',
    '景点',
    '火车站',
    '地铁站',
    '酒店',
    '区/县',
    '详细地址'
]

# English to Chinese place type mapping
PLACE_TYPE_MAP = {
    'city': '城市',
    'airport': '机场',
    'attraction': '景点',
    'station': '火车站',
    'subway': '地铁站',
    'hotel': '酒店',
    'district': '区/县',
    'address': '详细地址'
}

# Default search parameters
DEFAULT_ADULT_COUNT = 2
DEFAULT_STAY_NIGHTS = 1
DEFAULT_SIZE = 20

# Default MCP provider: 'rollinggo' or 'tuniu'
DEFAULT_PROVIDER = os.environ.get('DEFAULT_PROVIDER', 'tuniu')

# Available providers configuration
PROVIDERS = {
    'rollinggo': {
        'name': 'RollingGo',
        'description': '全球酒店搜索',
        'supports_booking': False,
        'supports_pagination': False
    },
    'tuniu': {
        'name': '途牛 MCP',
        'description': '国内酒店搜索与预订',
        'supports_booking': True,
        'supports_pagination': True
    }
}

# Membership Configuration
FREE_SEARCH_LIMIT = int(os.environ.get('FREE_SEARCH_LIMIT', '10'))
ANONYMOUS_SEARCH_LIMIT = int(os.environ.get('ANONYMOUS_SEARCH_LIMIT', '5'))

# WeChat Pay Configuration
WECHAT_PAY_APP_ID = os.environ.get('WECHAT_PAY_APP_ID', '')
WECHAT_PAY_MCH_ID = os.environ.get('WECHAT_PAY_MCH_ID', '')
WECHAT_PAY_API_KEY = os.environ.get('WECHAT_PAY_API_KEY', '')
WECHAT_PAY_NOTIFY_URL = os.environ.get('WECHAT_PAY_NOTIFY_URL', '')

# Alipay Configuration
ALIPAY_APP_ID = os.environ.get('ALIPAY_APP_ID', '')
ALIPAY_PRIVATE_KEY = os.environ.get('ALIPAY_PRIVATE_KEY', '')
ALIPAY_PUBLIC_KEY = os.environ.get('ALIPAY_PUBLIC_KEY', '')
ALIPAY_NOTIFY_URL = os.environ.get('ALIPAY_NOTIFY_URL', '')

# Redis Configuration
# Production: set REDIS_URL=redis://redis:6379/0 via docker-compose
# Development: empty string → Flask-Limiter falls back to memory://
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0' if FLASK_ENV == 'production' else '')
REDIS_AVAILABLE = bool(REDIS_URL)

# CORS Configuration
# Production: comma-separated allowed origins, e.g. "https://hotel.example.com,https://app.example.com"
# Development: defaults to localhost
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5000')
