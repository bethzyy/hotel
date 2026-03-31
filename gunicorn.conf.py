"""
Gunicorn configuration for production.
Usage: gunicorn -c gunicorn.conf.py "run:create_app()"
"""
import multiprocessing

# Server socket
bind = '0.0.0.0:5000'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
worker_connections = 1000
timeout = 120  # External API calls (RollingGo/Tuniu/Tavily) can be slow
keepalive = 5

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# Security
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190
