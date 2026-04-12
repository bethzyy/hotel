# ---- Stage 1: Build Nuxt frontend ----
FROM node:20-alpine AS frontend

WORKDIR /web
COPY web/package*.json ./
RUN npm ci --prefer-offline
COPY web/ ./
RUN npm run generate

# ---- Stage 2: Python runtime ----
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn gevent

# Copy application code
COPY . .

# Copy Nuxt build output from frontend stage
COPY --from=frontend /web/.output/public /app/web/dist

# Create data directory for SQLite
RUN mkdir -p /app/data

# Non-root user for security
RUN useradd --create-home appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:create_app()"]
