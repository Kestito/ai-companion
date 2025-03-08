#!/bin/bash
set -e

# Get the interface type from environment variable
INTERFACE=${INTERFACE:-all}

# Function to check if a port is open/service is running
check_service() {
    local host=$1
    local port=$2
    local max_attempts=$3
    local attempt=1
    
    echo "Checking if service is running at $host:$port..."
    while [ $attempt -le $max_attempts ]; do
        if nc -z $host $port >/dev/null 2>&1; then
            echo "✅ Service is running at $host:$port"
            return 0
        fi
        echo "⏳ Waiting for service to start at $host:$port (attempt $attempt/$max_attempts)"
        sleep 2
        attempt=$((attempt+1))
    done
    
    echo "❌ Service failed to start at $host:$port after $max_attempts attempts"
    return 1
}

# Function to start Chainlit
start_chainlit() {
    echo "🚀 Starting Chainlit on port 8080..."
    /app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 &
    CHAINLIT_PID=$!
    
    # Check if Chainlit is running
    if ! check_service localhost 8080 15; then
        echo "❌ Failed to start Chainlit service"
        kill $CHAINLIT_PID 2>/dev/null || true
        exit 1
    fi
}

# Function to clean up processes on exit
cleanup() {
    echo "Cleaning up processes..."
    jobs -p | xargs -r kill
    wait
    exit 0
}

# Set up trap for cleanup
trap cleanup SIGTERM SIGINT

case "$INTERFACE" in
  "whatsapp")
    echo "Starting WhatsApp interface..."
    /app/.venv/bin/uvicorn ai_companion.main:app --host 0.0.0.0 --port 8000
    ;;
    
  "chainlit")
    echo "Starting Chainlit interface..."
    /app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8000
    ;;
    
  "telegram")
    echo "Starting Telegram interface..."
    /app/.venv/bin/python -m ai_companion.interfaces.telegram.telegram_bot
    ;;
    
  "monitor")
    echo "Starting Monitoring interface..."
    /app/.venv/bin/uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090
    ;;
    
  "web-ui")
    echo "Starting Next.js Web UI interface..."
    # The web-ui is expected to be started by its own Dockerfile with CMD ["node", "server.js"]
    # This case is here to prevent the entrypoint script from starting other interfaces
    # when running the web-ui container
    exec "$@"
    ;;
    
  "all")
    echo "Starting all interfaces..."
    
    # Start Chainlit first
    start_chainlit
    
    # Start Telegram bot
    echo "🚀 Starting Telegram bot..."
    /app/.venv/bin/python -m ai_companion.interfaces.telegram.telegram_bot &
    
    # Start monitoring interface
    echo "🚀 Starting monitoring interface on port 8090..."
    /app/.venv/bin/uvicorn ai_companion.interfaces.monitor.app:app --host 0.0.0.0 --port 8090 &
    
    # Start main FastAPI app
    echo "🚀 Starting main FastAPI app on port 8000..."
    /app/.venv/bin/uvicorn ai_companion.main:app --host 0.0.0.0 --port 8000 &
    
    # Wait for all background processes
    wait
    ;;
    
  *)
    echo "Unknown interface: $INTERFACE. Valid options are: whatsapp, chainlit, telegram, monitor, web-ui, all"
    exit 1
    ;;
esac 