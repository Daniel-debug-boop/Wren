# Wren - Production Dockerfile
# Multi-stage build: frontend builder -> backend builder -> runtime

# Stage 1: Build frontend
FROM node:22-slim AS frontend-builder
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --prefer-offline
COPY frontend ./
RUN npm run build

# Stage 2: Build backend
FROM python:3.12-slim AS backend-builder
WORKDIR /app
ENV PYTHONPATH='/app'
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install --no-cache-dir poetry
COPY pyproject.toml poetry.lock ./
RUN touch README.md && poetry install --only main --no-root && rm -rf $POETRY_CACHE_DIR

# Stage 3: Runtime
FROM python:3.12-slim AS runtime
WORKDIR /app

# Install system dependencies for PTY and terminal
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends \
        bash \
        git \
        curl \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Copy backend from builder
COPY --from=backend-builder /app/.venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH='/app'

# Copy application code
COPY backend/ ./backend/
COPY skills/ ./skills/
COPY pyproject.toml poetry.lock README.md LICENSE ./

# Copy frontend build
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# Create workspace directory
RUN mkdir -p /workspace

# Environment defaults
ENV WORKSPACE_BASE=/workspace \
    BACKEND_HOST=0.0.0.0 \
    BACKEND_PORT=3000 \
    RUNTIME=local \
    ENABLE_DOCS=false

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000/api/v1/alive || exit 1

# Serve both frontend (static) and backend from one process
CMD ["sh", "-c", "python -m uvicorn backend.main:app --host $BACKEND_HOST --port $BACKEND_PORT"]
