# Use an appropriate base image
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install the project into `/app`
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    INTERFACE=all

# Install system dependencies for building libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the dependency management files and README first
COPY uv.lock pyproject.toml README.md /app/

# Install the application dependencies - this can be cached if uv.lock doesn't change
RUN uv sync --frozen --no-cache

# Copy your application code into the container
# (This is done after installing dependencies to leverage Docker layer caching)
COPY src/ /app/src/

# Set the virtual environment environment variables
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

# Install the package in development mode
RUN uv pip install -e .

# Create utils directory if it doesn't exist
RUN mkdir -p /app/src/ai_companion/utils

# Fix import issue - create a logging.py file with the get_logger function
RUN echo 'import logging\n\
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
    return logger\n' > /app/src/ai_companion/utils/logging.py

# Create __init__.py in utils directory if it doesn't exist
RUN touch /app/src/ai_companion/utils/__init__.py

# Note: .env file should be mounted as a volume or environment variables passed directly
# Example: docker run -v /path/to/.env:/app/.env -p 8000:8000 -p 8080:8080 ai-companion:all

# Define volumes for persistent data
VOLUME ["/app/data"]

# Create healthcheck script
# Note: Make sure your interfaces implement these health endpoints
RUN echo '#!/bin/sh\n\
if [ "$INTERFACE" = "whatsapp" ] || [ "$INTERFACE" = "all" ]; then\n\
  curl -f http://localhost:8000/whatsapp/health 2>/dev/null || exit 1\n\
fi\n\
if [ "$INTERFACE" = "chainlit" ] || [ "$INTERFACE" = "all" ]; then\n\
  curl -f http://localhost:8000/health 2>/dev/null || exit 1\n\
fi\n\
if [ "$INTERFACE" = "monitor" ] || [ "$INTERFACE" = "all" ]; then\n\
  curl -f http://localhost:8090/monitor/health 2>/dev/null || exit 1\n\
fi\n\
exit 0' > /app/healthcheck.sh && chmod +x /app/healthcheck.sh

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 CMD ["/app/healthcheck.sh"]

# Expose ports for all interfaces
EXPOSE 8000 8080 8090

# Create startup script to run the selected interface(s)
RUN echo '#!/bin/sh\n\
# Create .env file if mounted as volume but not found\n\
touch /app/.env 2>/dev/null || true\n\
\n\
case "$INTERFACE" in\n\
  "whatsapp")\n\
    echo "Starting WhatsApp interface..."\n\
    /app/.venv/bin/uvicorn ai_companion.interfaces.whatsapp.webhook_endpoint:app --host 0.0.0.0 --port 8000\n\
    ;;\n\
  "chainlit")\n\
    echo "Starting Chainlit interface..."\n\
    /app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8000\n\
    ;;\n\
  "telegram")\n\
    echo "Starting Telegram interface..."\n\
    /app/.venv/bin/python -m ai_companion.interfaces.telegram.telegram_bot\n\
    ;;\n\
  "monitor")\n\
    echo "Starting Monitoring interface..."\n\
    /app/.venv/bin/uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090\n\
    ;;\n\
  "all")\n\
    echo "Starting all interfaces..."\n\
    /app/.venv/bin/uvicorn ai_companion.interfaces.whatsapp.webhook_endpoint:app --host 0.0.0.0 --port 8000 & \\\n\
    /app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \\\n\
    /app/.venv/bin/python -m ai_companion.interfaces.telegram.telegram_bot & \\\n\
    /app/.venv/bin/uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090 & \\\n\
    wait\n\
    ;;\n\
  *)\n\
    echo "Unknown interface: $INTERFACE. Valid options are: whatsapp, chainlit, telegram, monitor, all"\n\
    exit 1\n\
    ;;\n\
esac' > /app/start.sh && chmod +x /app/start.sh

# Note: .env file should be mounted as a volume or environment variables passed directly
# Example: docker run -v /path/to/.env:/app/.env -p 8000:8000 -p 8080:8080 ai-companion:latest

# Set the default command to run the startup script
CMD ["/app/start.sh"]
