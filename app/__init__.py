"""
Flask Application Factory
Multi-MCP hotel search and booking application
"""
import os
import logging
import logging.handlers
from pathlib import Path
from flask import Flask, jsonify, send_from_directory


def create_app(config=None):
    """Create and configure the Flask application."""
    # Nuxt SPA static files directory
    dist_dir = str(Path(__file__).resolve().parent.parent / 'web' / 'dist')

    app = Flask(__name__, static_folder=dist_dir)

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
        SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS,
        JWT_SECRET_KEY, JWT_ACCESS_TOKEN_EXPIRES,
        CACHE_ENABLED, CACHE_TTL, RESULTS_PER_PAGE,
        MAX_FAVORITES, MAX_HISTORY, PLACE_TYPES,
        ROLLINGGO_API_KEY, ROLLINGGO_TIMEOUT,
        TUNIU_API_KEY, TUNIU_MCP_URL, TUNIU_TIMEOUT,
        DEFAULT_PROVIDER, PROVIDERS,
        SERPER_API_KEY, SERPER_TIMEOUT, SERPER_ENABLED,
        TAVILY_API_KEY, TAVILY_TIMEOUT, TAVILY_ENABLED,
        REDIS_URL
    )

    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['DEBUG'] = DEBUG
    app.config['DATABASE_PATH'] = DATABASE_PATH
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS
    app.config['JWT_SECRET_KEY'] = JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = JWT_ACCESS_TOKEN_EXPIRES
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
    app.config['REDIS_URL'] = REDIS_URL

    # Override with custom config if provided
    if config:
        app.config.update(config)

    # Ensure data directory exists
    data_dir = Path(app.config['DATABASE_PATH']).parent
    data_dir.mkdir(parents=True, exist_ok=True)

    # Initialize SQLAlchemy + Flask-Migrate
    from app.models.database import db
    db.init_app(app)

    from flask_migrate import Migrate
    Migrate(app, db)

    # Initialize JWT
    from flask_jwt_extended import JWTManager
    jwt = JWTManager(app)

    # Initialize API Limiter
    from app.extensions import limiter
    limiter.init_app(app)
    app.limiter = limiter

    # Initialize CORS — restrict origins, never wildcard with credentials
    from flask_cors import CORS
    from config import CORS_ORIGINS
    allowed_origins = [o.strip() for o in CORS_ORIGINS.split(',') if o.strip()]
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)

    # Initialize cache service (Redis when available, SQLite fallback)
    from app.services.cache import CacheService
    cache_service = CacheService(
        app.config['DATABASE_PATH'],
        redis_url=app.config.get('REDIS_URL', '')
    )
    cache_service.init_db()
    app.cache_service = cache_service

    # Create all database tables (SQLAlchemy models)
    # Import all models before create_all to ensure all tables are created
    # Note: use 'from ... import' to avoid shadowing the local 'app' variable
    from app.models import tracking as _m_tracking  # noqa: F401
    from app.models import referral as _m_referral  # noqa: F401
    from app.models import coupon as _m_coupon  # noqa: F401
    from app.models import audit_log as _m_audit_log  # noqa: F401

    with app.app_context():
        # Auto-migrate: drop old tables that conflict with new SQLAlchemy models
        if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
            inspector = db.inspect(db.engine)
            existing = inspector.get_table_names()
            for table in ['favorites', 'search_history', 'clicks']:
                if table in existing:
                    columns = [c['name'] for c in inspector.get_columns(table)]
                    needs_recreate = False
                    if table == 'favorites' and 'user_id' not in columns:
                        needs_recreate = True
                    elif table == 'search_history' and 'device_fingerprint' not in columns:
                        needs_recreate = True
                    elif table == 'clicks' and 'hotel_name' not in columns:
                        needs_recreate = True
                    if needs_recreate:
                        db.session.execute(db.text(f'DROP TABLE IF EXISTS {table}'))
                        app.logger.info(f"[Migrate] Dropped old table: {table}")
                        db.session.commit()
        db.create_all()

    # Register blueprints
    from app.routes.search import search_bp
    from app.routes.hotel import hotel_bp
    from app.routes.user import user_bp
    from app.routes.booking import booking_bp
    from app.routes.comparison import comparison_bp
    from app.routes.click import click_bp
    from app.routes.admin import admin_bp
    from app.routes.auth import auth_bp
    from app.routes.tracking import tracking_bp
    from app.routes.payment import payment_bp
    from app.routes.membership import membership_bp
    from app.routes.referral import referral_bp
    from app.routes.coupon import coupon_bp
    from app.routes.recommendation import recommendation_bp

    app.register_blueprint(search_bp, url_prefix='/api')
    app.register_blueprint(hotel_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(booking_bp, url_prefix='/api')
    app.register_blueprint(comparison_bp, url_prefix='/api')
    app.register_blueprint(click_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(tracking_bp, url_prefix='/api')
    app.register_blueprint(payment_bp, url_prefix='/api')
    app.register_blueprint(membership_bp, url_prefix='/api')
    app.register_blueprint(referral_bp, url_prefix='/api')
    app.register_blueprint(coupon_bp, url_prefix='/api')
    app.register_blueprint(recommendation_bp, url_prefix='/api')

    # Health check endpoint (for monitoring and load balancer)
    @app.route('/health')
    def health():
        from datetime import datetime, timezone
        checks = {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'error: {str(e)}'
            checks['status'] = 'degraded'
        return jsonify(checks)

    # Robots.txt
    @app.route('/robots.txt')
    def robots_txt():
        return send_from_directory(app.static_folder, 'robots.txt', mimetype='text/plain')

    # SPA catch-all: serve Nuxt static files, fallback to index.html for client-side routing
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def spa_catch_all(path):
        """Serve Nuxt SPA static files. Non-file routes fall back to index.html."""
        if path:
            # Try to serve the exact file first (e.g., _nuxt/xxx.js, favicon.svg)
            file_path = Path(app.static_folder) / path
            if file_path.is_file():
                return send_from_directory(app.static_folder, path)

        # Fallback to index.html for SPA client-side routing
        index_path = Path(app.static_folder) / 'index.html'
        if index_path.is_file():
            return send_from_directory(app.static_folder, 'index.html')

        # No Nuxt build found — return helpful message
        return jsonify({
            'success': False,
            'error': 'Frontend not built. Run: cd web && npm run generate',
            'api_docs': '/api/search, /api/hotel/<id>, /health',
        }), 503

    return app
