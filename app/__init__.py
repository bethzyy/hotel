"""
Flask Application Factory
Multi-MCP hotel search and booking application
"""
import os
import logging
import logging.handlers
from pathlib import Path
from flask import Flask, jsonify


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configure logging
    from config import DEBUG, BASE_DIR
    log_level = logging.DEBUG if DEBUG else logging.INFO
    log_format = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'

    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        force=True
    )

    # File logging in production
    if not DEBUG:
        logs_dir = Path(BASE_DIR / 'logs')
        logs_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / 'app.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        file_handler.setLevel(logging.INFO)
        logging.getLogger().addHandler(file_handler)

    # Debug-only loggers
    if DEBUG:
        logging.getLogger('app.routes.comparison').setLevel(logging.DEBUG)
        logging.getLogger('app.services.tavily').setLevel(logging.DEBUG)

    # Suppress verbose third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    logging.info(f"[App] Logging configured: level={'DEBUG' if DEBUG else 'INFO'}")

    # Load default configuration
    from config import (
        SECRET_KEY, DEBUG, DATABASE_PATH,
        CACHE_ENABLED, CACHE_TTL, RESULTS_PER_PAGE,
        MAX_FAVORITES, MAX_HISTORY, PLACE_TYPES,
        ROLLINGGO_API_KEY, ROLLINGGO_TIMEOUT,
        TUNIU_API_KEY, TUNIU_MCP_URL, TUNIU_TIMEOUT,
        DEFAULT_PROVIDER, PROVIDERS,
        SERPER_API_KEY, SERPER_TIMEOUT, SERPER_ENABLED,
        TAVILY_API_KEY, TAVILY_TIMEOUT, TAVILY_ENABLED
    )

    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = DEBUG
    app.config['DATABASE_PATH'] = DATABASE_PATH
    app.config['CACHE_ENABLED'] = CACHE_ENABLED
    app.config['CACHE_TTL'] = CACHE_TTL
    app.config['RESULTS_PER_PAGE'] = RESULTS_PER_PAGE
    app.config['MAX_FAVORITES'] = MAX_FAVORITES
    app.config['MAX_HISTORY'] = MAX_HISTORY
    app.config['PLACE_TYPES'] = PLACE_TYPES
    app.config['ROLLINGGO_API_KEY'] = ROLLINGGO_API_KEY
    app.config['ROLLINGGO_TIMEOUT'] = ROLLINGGO_TIMEOUT
    app.config['TUNIU_API_KEY'] = TUNIU_API_KEY
    app.config['TUNIU_MCP_URL'] = TUNIU_MCP_URL
    app.config['TUNIU_TIMEOUT'] = TUNIU_TIMEOUT
    app.config['DEFAULT_PROVIDER'] = DEFAULT_PROVIDER
    app.config['PROVIDERS'] = PROVIDERS
    app.config['SERPER_API_KEY'] = SERPER_API_KEY
    app.config['SERPER_TIMEOUT'] = SERPER_TIMEOUT
    app.config['SERPER_ENABLED'] = SERPER_ENABLED
    app.config['TAVILY_API_KEY'] = TAVILY_API_KEY
    app.config['TAVILY_TIMEOUT'] = TAVILY_TIMEOUT
    app.config['TAVILY_ENABLED'] = TAVILY_ENABLED

    # Override with custom config if provided
    if config:
        app.config.update(config)

    # Ensure data directory exists
    data_dir = Path(app.config['DATABASE_PATH']).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize database
    from app.services.cache import CacheService
    cache_service = CacheService(app.config['DATABASE_PATH'])
    cache_service.init_db()
    app.cache_service = cache_service

    # Register blueprints
    from app.routes.search import search_bp
    from app.routes.hotel import hotel_bp
    from app.routes.user import user_bp
    from app.routes.booking import booking_bp
    from app.routes.comparison import comparison_bp
    from app.routes.click import click_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(hotel_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(booking_bp, url_prefix='/api')
    app.register_blueprint(comparison_bp, url_prefix='/api')
    app.register_blueprint(click_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')

    # Health check endpoint (for monitoring and load balancer)
    @app.route('/health')
    def health():
        from datetime import datetime, timezone
        checks = {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}
        # Check database connectivity
        try:
            cache_service.conn.execute('SELECT 1')
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'error: {str(e)}'
            checks['status'] = 'degraded'
        return jsonify(checks)

    # Robots.txt
    @app.route('/robots.txt')
    def robots_txt():
        from flask import send_from_directory
        return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')

    # Main page routes
    @app.route('/')
    def index():
        from flask import render_template
        return render_template('index.html')

    @app.route('/results')
    def results():
        from flask import render_template, request
        return render_template('results.html')

    @app.route('/detail/<hotel_id>')
    def detail(hotel_id):
        from flask import render_template
        return render_template('detail.html', hotel_id=hotel_id)

    @app.route('/booking')
    def booking():
        from flask import render_template
        return render_template('booking.html')

    @app.route('/order')
    def order():
        from flask import render_template
        return render_template('order.html')

    return app
