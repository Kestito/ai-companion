FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install all required packages including Azure
RUN pip install --no-cache-dir -r requirements.txt \
    azure-identity \
    azure-keyvault-secrets \
    azure-monitor-opentelemetry \
    opencensus-ext-azure \
    fastapi \
    uvicorn \
    pydantic-settings \
    pydantic

# Create logs directory
RUN mkdir -p logs

# Create proper Python package structure
RUN mkdir -p /app/src
COPY src /app/src/

# Create entrypoint script
RUN echo '#!/bin/bash\n\
export PYTHONPATH=/app\n\
python -m src.ai_companion.modules.scheduled_messaging.processor\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Make sure directories exist
RUN mkdir -p /app/src/ai_companion/modules/scheduled_messaging/handlers

# Expose port for health API
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Use entrypoint script to ensure correct environment
ENTRYPOINT ["/app/entrypoint.sh"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1 