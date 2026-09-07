# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATA_MODEL_OUTPUT_DIR=/app/docs

# Security: Create non-root user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

WORKDIR /app

# Install build dependencies
COPY pyproject.toml README.md requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir .

# Copy application source
COPY src/ ./src/

# Ensure output directory exists and is owned by appuser
RUN mkdir -p /app/docs && chown -R appuser:appgroup /app

USER appuser

VOLUME ["/app/docs"]

ENTRYPOINT ["data-model-architect"]
CMD ["--help"]
