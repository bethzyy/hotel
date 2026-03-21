"""
Configuration for Hotel Search Application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Flask Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'hotel-search-secret-key-2024')
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# Database Configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', str(BASE_DIR / 'data' / 'hotel.db'))

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
