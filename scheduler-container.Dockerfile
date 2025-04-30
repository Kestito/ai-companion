# Build stage
FROM mcr.microsoft.com/azure-functions/python:3.9-python3.9 AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (for better caching)
COPY requirements.txt .

# Install dependencies with proper cleanup
RUN pip install --no-cache-dir -r requirements.txt \
    azure-identity \
    azure-keyvault-secrets \
    azure-monitor-opentelemetry \
    opencensus-ext-azure \
    fastapi \
    uvicorn \
    pydantic-settings \
    pydantic \
    && find /usr/local/lib/python3.9/site-packages -name "__pycache__" -type d -exec rm -rf {} +

# Create Python package structure
RUN mkdir -p /app/src
COPY src /app/src/

# Create entrypoint script
RUN echo '#!/bin/bash\n\
export PYTHONPATH=/app\n\
python -m src.ai_companion.modules.scheduled_messaging.processor\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Create necessary directories
RUN mkdir -p /app/src/ai_companion/modules/scheduled_messaging/handlers /app/logs

# Runtime stage with minimal dependencies
FROM mcr.microsoft.com/azure-functions/python:3.9-python3.9-slim

WORKDIR /app

# Set environment variables for Azure compatibility
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITE_HOSTNAME=scheduler.azurewebsites.net \
    AZURE_FUNCTIONS_ENVIRONMENT=Production

# Copy only necessary files from builder stage
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /app/src /app/src
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh
COPY --from=builder /app/logs /app/logs

# Create health check endpoint
RUN mkdir -p /app/src/health && \
    echo 'from fastapi import FastAPI\n\
app = FastAPI()\n\
\n\
@app.get("/health")\n\
def health_check():\n\
    return {"status": "ok"}\n\
\n\
if __name__ == "__main__":\n\
    import uvicorn\n\
    uvicorn.run(app, host="0.0.0.0", port=8080)\n\
' > /app/src/health/app.py && \
    echo '#!/bin/bash\n\
python -m src.health.app &\n\
exec /app/entrypoint.sh\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port for health API
EXPOSE 8080

# Health check for Azure App Service
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Use startup script that includes health endpoint
CMD ["/app/start.sh"] 