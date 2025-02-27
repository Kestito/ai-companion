# AI Companion Docker Interfaces

This document explains how to use the `Dockerfile.allinterfaces` which provides a unified container for running all available interfaces for the AI Companion.

## Available Interfaces

The AI Companion supports the following interfaces:

1. **WhatsApp** - Allows interaction via WhatsApp messaging
2. **Chainlit** - Provides a web-based chat interface
3. **Telegram** - Enables interaction through Telegram messaging
4. **Monitoring** - Provides metrics and performance monitoring

## Building the Docker Image

To build the Docker image with support for all interfaces:

```bash
docker build -t ai-companion:all -f Dockerfile.allinterfaces .
```

## Running the Container

You can run the container in different modes by setting the `INTERFACE` environment variable:

### Running All Interfaces

```bash
docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 -e INTERFACE=all ai-companion:all
```

This will start all interfaces simultaneously:
- WhatsApp interface on port 8080
- Chainlit web interface on port 8000
- Telegram bot (no port needed)
- Monitoring interface on port 8090

### Running Specific Interfaces

#### WhatsApp Only

```bash
docker run -p 8080:8080 -e INTERFACE=whatsapp ai-companion:all
```

#### Chainlit Web Interface Only

```bash
docker run -p 8000:8000 -e INTERFACE=chainlit ai-companion:all
```

#### Telegram Bot Only

```bash
docker run -e INTERFACE=telegram ai-companion:all
```

#### Monitoring Interface Only

```bash
docker run -p 8090:8090 -e INTERFACE=monitor ai-companion:all
```

## Environment Variables

The container uses the following environment variables:

- `INTERFACE`: Determines which interface(s) to run. Valid options are:
  - `whatsapp` - Run only the WhatsApp interface
  - `chainlit` - Run only the Chainlit web interface
  - `telegram` - Run only the Telegram bot
  - `monitor` - Run only the Monitoring interface
  - `all` - Run all interfaces (default)

- All other environment variables required by the specific interfaces should be provided either through:
  - An `.env` file mounted into the container (recommended)
  - Environment variables passed directly to the container

### Mounting an .env File

To use an .env file with your container, mount it as a volume:

```bash
docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 -v /path/to/.env:/app/.env ai-companion:all
```

### Using Environment Variables Directly

Alternatively, you can pass environment variables directly:

```bash
docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 \
  -e OPENAI_API_KEY=your_key \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OTHER_VARIABLE=value \
  ai-companion:all
```

## Volumes

The container defines a volume at `/app/data` for persistent data storage. You can mount this to a local directory:

```bash
docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 -v ./data:/app/data ai-companion:all
```

## Health Checks

The container includes health checks for the HTTP-based interfaces (WhatsApp, Chainlit, and Monitoring). You can monitor the container health using:

```bash
docker inspect --format='{{.State.Health.Status}}' <container_id>
```

## Accessing the Interfaces

Once the container is running, you can access the interfaces at:

- **Chainlit**: http://localhost:8000
- **WhatsApp Webhook**: http://localhost:8080
- **Monitoring API**: http://localhost:8090
  - API Documentation: http://localhost:8090/docs
  - Metrics: http://localhost:8090/monitor/metrics
  - Performance Report: http://localhost:8090/monitor/report

## Troubleshooting

If you encounter issues with the container:

1. Check the container logs:
   ```bash
   docker logs <container_id>
   ```

2. Ensure all required environment variables are set correctly
3. Verify that ports are not already in use on your host machine
4. Check that the necessary API keys and tokens are valid

## Known Issues and Solutions

### Missing Health Endpoints

The health check script looks for `/health` endpoints on the WhatsApp, Chainlit, and Monitoring interfaces. If these endpoints are not implemented in your application, the health check may fail. You can:

1. Implement the health endpoints in your application
2. Modify the Dockerfile to remove or adjust the health check

### Import Issues

The Dockerfile includes a fix for a common import issue with the logging module. If you encounter other import issues, you may need to:

1. Check the container logs for specific import errors
2. Modify the Dockerfile to create any missing modules or symbolic links

## Example docker-compose.yml

Here's an example `docker-compose.yml` file for running the AI Companion with all interfaces:

```yaml
version: '3.8'

services:
  ai-companion:
    build:
      context: .
      dockerfile: Dockerfile.allinterfaces
    ports:
      - "8000:8000"  # Chainlit web interface
      - "8080:8080"  # WhatsApp webhook
      - "8090:8090"  # Monitoring API
    environment:
      - INTERFACE=all
      # You can specify environment variables directly here
      # - OPENAI_API_KEY=your_key_here
      # - TELEGRAM_BOT_TOKEN=your_token_here
    volumes:
      - ./data:/app/data
      # Mount your .env file (recommended approach)
      - ./.env:/app/.env
    restart: unless-stopped
    healthcheck:
      test: ["/app/healthcheck.sh"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

You can choose either to mount the .env file or specify environment variables directly in the docker-compose.yml file, depending on your security preferences and deployment setup. 