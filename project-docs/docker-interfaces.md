# AI Companion Docker Interfaces

This document explains how to use the Docker container which provides a unified solution for running all available interfaces for the AI Companion.

## Available Interfaces

The AI Companion supports the following interfaces:

1. **WhatsApp** - Allows interaction via WhatsApp messaging
2. **Chainlit** - Provides a web-based chat interface
3. **Telegram** - Enables interaction through Telegram messaging
4. **Monitoring** - Provides metrics and performance monitoring

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
docker run -p 8000:8000 -v /path/to/.env:/app/.env ai-companion:latest
```

### Using Environment Variables Directly

Alternatively, you can pass environment variables directly:

```bash
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e TELEGRAM_BOT_TOKEN=your_token \
  -e OTHER_VARIABLE=value \
  ai-companion:latest
```

## Volumes

You can mount a volume for persistent data storage:

```bash
docker run -p 8000:8000 -v ./data:/app/data ai-companion:latest
```

## Health Checks

You can check the health of the application using the health endpoint:

```bash
curl http://localhost:8000/health
```

## Accessing the Interfaces

Once the container is running, you can access the interfaces at:

- **Main API**: http://localhost:8000
- **Chainlit**: http://localhost:8000/chat
  - Status: http://localhost:8000/chat/status
- **WhatsApp Webhook**: http://localhost:8000/whatsapp
- **Monitoring Interface**: http://localhost:8000/health
  - Metrics: http://localhost:8000/health/metrics
  - Performance Report: http://localhost:8000/health/report
  - Reset Metrics: http://localhost:8000/health/reset (POST)

## Troubleshooting

If you encounter issues with the container:

1. Check the container logs:
   ```bash
   docker logs <container_id>
   ```

2. Check the status of services:
   - Chainlit: http://localhost:8000/chat/status
   - Monitoring: http://localhost:8000/health

3. Ensure all required environment variables are set correctly
4. Verify that ports are not already in use on your host machine
5. Check that the necessary API keys and tokens are valid

## Example docker-compose.yml

Here's an example `docker-compose.yml` file for running the AI Companion with all interfaces:

```yaml
version: '3.8'

services:
  ai-companion:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"  # Main application port
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
```

You can choose either to mount the .env file or specify environment variables directly in the docker-compose.yml file, depending on your security preferences and deployment setup.

## Azure Container App Deployment

When deploying to Azure Container Apps, the application will be available at:

- **Main API**: https://your-app-name.azurecontainerapps.io
- **Chainlit**: https://your-app-name.azurecontainerapps.io/chat
  - Status: https://your-app-name.azurecontainerapps.io/chat/status
- **WhatsApp Webhook**: https://your-app-name.azurecontainerapps.io/whatsapp
- **Monitoring Interface**: https://your-app-name.azurecontainerapps.io/health
  - Metrics: https://your-app-name.azurecontainerapps.io/health/metrics
  - Performance Report: https://your-app-name.azurecontainerapps.io/health/report
  - Reset Metrics: https://your-app-name.azurecontainerapps.io/health/reset (POST)

For the AI Companion deployment, the URLs are:

- **Main API**: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io
- **Chainlit**: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/chat
  - Status: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/chat/status
- **WhatsApp Webhook**: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/whatsapp
- **Monitoring Interface**: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health
  - Metrics: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health/metrics
  - Performance Report: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health/report
  - Reset Metrics: https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health/reset (POST) 