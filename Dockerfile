# Dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# SO deps (certs, tz, build)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates tzdata \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# melhor cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn uvicorn

# código
COPY . .

# porta do Cloud Run
ENV PORT=8080

# entrypoint (FastAPI em app.app:app)
CMD exec gunicorn app.app:app -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT} --workers 2 --timeout 300
