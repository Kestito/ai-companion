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
    return logger' > /app/src/ai_companion/utils/logging.py

# Copy Chainlit configuration and assets
COPY .chainlit/ /app/.chainlit/
COPY chainlit.md /app/chainlit.md
COPY public/ /app/public/

# Create a symbolic link to fix the Chainlit path issue
RUN ln -sf /app/src/ai_companion /app/ai_companion

# Create a startup script
RUN echo '#!/bin/bash\n\
\n\
# Get the interface type from environment variable\n\
INTERFACE=${INTERFACE:-all}\n\
\n\
case "$INTERFACE" in\n\
  "whatsapp")\n\
    echo "Starting WhatsApp interface..."\n\
    /app/.venv/bin/uvicorn ai_companion.main:app --host 0.0.0.0 --port 8000\n\
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
    # Start Chainlit on port 8080 (internal only, will be proxied through main app)\n\
    /app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \\\n\
    # Start Telegram bot\n\
    /app/.venv/bin/python -m ai_companion.interfaces.telegram.telegram_bot & \\\n\
    # Start monitoring interface on port 8090\n\
    /app/.venv/bin/uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090 & \\\n\
    # Start main FastAPI app on port 8000 (handles WhatsApp and proxies to Chainlit)\n\
    /app/.venv/bin/uvicorn ai_companion.main:app --host 0.0.0.0 --port 8000 & \\\n\
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
