# ============================================================
# ClassPulse Backend — Dockerfile
# ============================================================
FROM python:3.11-slim

WORKDIR /app

# System deps for psycopg2 (libpq) and bcrypt compilation (gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps (prefer pre-built wheels to avoid compilation)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

# Copy application source
COPY . .

# Default command (overridden per service in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
