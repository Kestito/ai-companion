FROM mcr.microsoft.com/azure-functions/python:3.9-python3.9 AS builder

# Set working directory
WORKDIR /app

# Install build dependencies 
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files first for better layer caching
COPY uv.lock pyproject.toml README.md /app/

# Copy application code
COPY src/ /app/src/

# Install dependencies
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-cache && \
    pip install -e .

# Create necessary files and directories
RUN mkdir -p /app/src/ai_companion/utils /app/.chainlit /app/public && \
    echo 'import logging\n\
\n\
def get_logger(name):\n\
    """Get a logger with the given name."""\n\
    logger = logging.getLogger(name)\n\
    if not logger.handlers:\n\
        handler = logging.StreamHandler()\n\
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")\n\
        handler.setFormatter(formatter)\n\
        logger.addHandler(handler)\n\
        logger.setLevel(logging.INFO)\n\
    return logger' > /app/src/ai_companion/utils/logging.py && \
    echo "# AI Companion\n\nWelcome to the AI Companion chat interface." > /app/chainlit.md && \
    ln -sf /app/src/ai_companion /app/ai_companion

# Create startup script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    echo '#!/bin/bash\n\
\n\
# Get the interface type from environment variable\n\
INTERFACE=${INTERFACE:-all}\n\
\n\
case "$INTERFACE" in\n\
  "whatsapp")\n\
    echo "Starting WhatsApp interface..."\n\
    uvicorn ai_companion.main:app --host 0.0.0.0 --port 8000\n\
    ;;\n\
  "chainlit")\n\
    echo "Starting Chainlit interface..."\n\
    # Use chainlit command with our custom app\n\
    chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8000\n\
    ;;\n\
  "telegram")\n\
    echo "Starting Telegram interface separately (legacy mode)..."\n\
    python -m ai_companion.interfaces.telegram.telegram_bot\n\
    ;;\n\
  "monitor")\n\
    echo "Starting Monitoring interface..."\n\
    uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090\n\
    ;;\n\
  "all")\n\
    echo "Starting all interfaces with integrated Telegram bot..."\n\
    # Start Chainlit on port 8080\n\
    chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \\\n\
    # Wait for Chainlit to be ready\n\
    echo "Waiting for Chainlit to start..." && sleep 5 && \\\n\
    # Start monitoring interface on port 8090\n\
    uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090 & \\\n\
    # Start main FastAPI app on port 8000 (handles WhatsApp and now also runs Telegram bot)\n\
    uvicorn ai_companion.main:app --host 0.0.0.0 --port 8000 & \\\n\
    wait\n\
    ;;\n\
  *)\n\
    echo "Unknown interface: $INTERFACE. Valid options are: whatsapp, chainlit, telegram, monitor, all"\n\
    exit 1\n\
    ;;\n\
esac' > /app/start.sh && chmod +x /app/start.sh

# Runtime stage with minimal dependencies
FROM mcr.microsoft.com/azure-functions/python:3.9-python3.9-slim

WORKDIR /app

# Set environment variables for Azure compatibility
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    INTERFACE=all \
    AZURE_FUNCTIONS_ENVIRONMENT=Production \
    AzureWebJobsScriptRoot=/app \
    WEBSITES_ENABLE_APP_SERVICE_STORAGE=false

# Copy only necessary files from builder stage
COPY --from=builder /app/src /app/src
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/start.sh /app/start.sh
COPY --from=builder /app/entrypoint.sh /app/entrypoint.sh
COPY --from=builder /app/chainlit.md /app/chainlit.md
COPY --from=builder /app/.chainlit /app/.chainlit
COPY --from=builder /app/public /app/public
COPY --from=builder /app/ai_companion /app/ai_companion

# Update PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Create symbolic link required for Azure Functions
RUN ln -sf /app/src/ai_companion /app/ai_companion && \
    mkdir -p /home/site/wwwroot

# Health check for Azure App Service
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/monitor/health || exit 1

# ENTRYPOINT for Azure compatibility
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden by Azure)
CMD []
