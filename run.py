"""
Hotel Search Application Entry Point
"""
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Load environment variables from .env file BEFORE importing config
from dotenv import load_dotenv
load_dotenv()

from app import create_app

app = create_app()

if __name__ == '__main__':
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))

    # Run the application
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', True),
        use_reloader=False  # 禁用 Watchdog 防止频繁重启导致 ERR_CONNECTION_RESET
    )
