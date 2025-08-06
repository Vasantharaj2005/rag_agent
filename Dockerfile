# --- Stage 1: Builder ---
FROM python:3.11 AS builder

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv $VIRTUAL_ENV

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Production Image ---
FROM python:3.11-slim AS final

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PORT=8080 \
    TRANSFORMERS_CACHE=/app/model_cache \
    SENTENCE_TRANSFORMERS_HOME=/app/model_cache

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set up working directory
WORKDIR /app

# Create necessary directories and assign permissions
RUN mkdir -p /app/model_cache /app/logs \
    && chown -R appuser:appuser /app

# Copy application code and set ownership
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user
USER appuser

# Healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD curl --fail http://localhost:${PORT}/health || exit 1

EXPOSE ${PORT}

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]