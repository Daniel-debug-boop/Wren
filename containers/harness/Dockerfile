FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH='/app'
ENV PYTHONUNBUFFERED=1

RUN apt-get update -y \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only harness source (not the full openhands package)
# This keeps the image small and avoids heavy deps (litellm, docker, playwright)
COPY openhands/harness/ ./openhands/harness/
COPY openhands/__init__.py ./openhands/__init__.py

# Minimal runtime deps that the harness actually imports
RUN pip install --no-cache-dir \
    "fastapi>=0.115" \
    "uvicorn[standard]>=0.34" \
    "pyyaml>=6.0" \
    "prometheus-client>=0.21"

# Persistent data directory
RUN mkdir -p /data && chmod 777 /data
ENV OPENHANDS_HARNESS_DB_PATH=/data/harness.db

EXPOSE 8750

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "
import urllib.request, json
r = urllib.request.urlopen('http://127.0.0.1:8750/health')
assert json.loads(r.read())['status'] in ('healthy', 'degraded')
" || exit 1

ENTRYPOINT ["python3", "-m", "openhands.harness.cli", "serve"]
