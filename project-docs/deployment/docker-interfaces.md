# AI Companion Docker Interfaces

This document explains how to use the Docker container which provides a unified solution for running all available interfaces for the AI Companion.

## Available Interfaces

The AI Companion supports the following interfaces:

1. **WhatsApp** - Allows interaction via WhatsApp messaging
2. **Chainlit** - Provides a web-based chat interface
3. **Telegram** - Enables interaction through Telegram messaging
4. **Monitoring** - Provides metrics and performance monitoring
5. **Web UI** - Modern Next.js-based web interface for enhanced user experience

## Building the Docker Image

To build the Docker image with support for all interfaces:

```bash
docker build -t ai-companion:latest .
```

## Running the Container

You can run the container in different modes by setting the `INTERFACE` environment variable:

### Running All Interfaces

```bash
docker run -p 8000:8000 -e INTERFACE=all ai-companion:latest
```

This will start all interfaces simultaneously:
- Main FastAPI application on port 8000, which includes:
  - WhatsApp webhook at `/whatsapp`
  - Chainlit web interface at `/chat`
  - Monitoring interface at `/health`
  - Telegram bot (no external port needed)

### Running with Unified Interface

```bash
docker run -p 8000:8000 -e INTERFACE=unified ai-companion:latest
```

This runs all interfaces through the unified path-based routing system.

### Running Specific Interfaces

#### WhatsApp Only

```bash
docker run -p 8000:8000 -e INTERFACE=whatsapp ai-companion:latest
```

#### Chainlit Web Interface Only

```bash
docker run -p 8000:8000 -e INTERFACE=chainlit ai-companion:latest
```

#### Telegram Bot Only

```bash
docker run -e INTERFACE=telegram ai-companion:latest
```

#### Monitoring Interface Only

```bash
docker run -p 8090:8090 -e INTERFACE=monitor ai-companion:latest
```

#### Next.js Web UI Only

```bash
# Build the web-ui image separately
docker build -t ai-companion-web-ui:latest -f src/ai_companion/interfaces/web-ui/Dockerfile src/ai_companion/interfaces/web-ui

# Run the web-ui container
docker run -p 3000:3000 ai-companion-web-ui:latest
```

## Environment Variables

The container requires the following key environment variables:

- `INTERFACE`: Determines which interface(s) to run. Valid options:
  - `whatsapp` - Run only the WhatsApp interface
  - `chainlit` - Run only the Chainlit web interface
  - `telegram` - Run only the Telegram bot
  - `monitor` - Run only the Monitoring interface
  - `web-ui` - Run only the Next.js Web UI
  - `all` - Run all interfaces on separate ports
  - `unified` - Run all interfaces with path-based routing (recommended)

## Supplying Environment Variables

### Using an .env File (Recommended)

Mount an .env file as a volume:

```bash
docker run -p 8000:8000 -v /path/to/.env:/app/.env ai-companion:latest
```

### Using Command-Line Variables

Pass environment variables directly:

```bash
docker run -p 8000:8000 \
  -e INTERFACE=unified \
  -e OPENAI_API_KEY=your_key \
  -e TELEGRAM_BOT_TOKEN=your_token \
  ai-companion:latest
```

## Volumes

You can mount volumes for persistent data:

```bash
docker run -p 8000:8000 -v ./data:/app/data ai-companion:latest
```

## Health Checks

Check the status of the application:

```bash
curl http://localhost:8000/health
```

## Using Docker Compose

Here's an example `docker-compose.yml` file:

```yaml
version: '3.8'

services:
  ai-companion:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - INTERFACE=unified
    volumes:
      - ./data:/app/data
      - ./.env:/app/.env
    restart: unless-stopped
```

## Troubleshooting Docker Container Issues

If you encounter issues with the container:

1. **Check the container logs**:
   ```bash
   docker logs <container_id>
   ```

2. **Verify Docker is running**:
   ```bash
   docker info
   ```

3. **Inspect container environment variables**:
   ```bash
   docker inspect <container_id> | grep -A 20 "Env"
   ```

4. **Check container health (if defined)**:
   ```bash
   docker inspect --format "{{.State.Health.Status}}" <container_id>
   ```

5. **Verify port bindings**:
   ```bash
   docker port <container_id>
   ```

See the [Troubleshooting Guide](./troubleshooting.md) for more detailed information. 