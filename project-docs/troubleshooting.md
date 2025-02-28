# AI Companion Troubleshooting Guide

This document provides solutions for common issues encountered when running the AI Companion application.

## Common Issues

### 1. 404 Not Found for `/chat/` Endpoint

**Symptoms:**
- Accessing `http://localhost:8000/chat/` returns a 404 Not Found error
- Error logs show `"GET /chat/ HTTP/1.1" 404 Not Found`

**Causes:**
- The Chainlit service is not running on port 8080
- The main application is running but cannot connect to the Chainlit service

**Solutions:**
1. Check if the Chainlit service is running:
   ```bash
   curl http://localhost:8000/chat/status
   ```

2. If the status shows "unavailable", ensure the application was started with the `INTERFACE=all` environment variable:
   ```bash
   docker run -p 8000:8000 -e INTERFACE=all ai-companion:latest
   ```

3. Check the application logs for any errors related to starting Chainlit:
   ```bash
   docker logs <container_id>
   ```

4. If running locally, start the Chainlit service manually:
   ```bash
   cd src
   python -m ai_companion.interfaces.chainlit.app --host 0.0.0.0 --port 8080
   ```

### 2. Monitoring Endpoints Return 404 Not Found

**Symptoms:**
- Accessing `/health/metrics`, `/health/report`, or `/health/reset` returns a 404 Not Found error
- Error logs show `"GET /health/metrics HTTP/1.1" 404 Not Found`

**Causes:**
- The monitoring service is not running on port 8090
- The main application is running but cannot connect to the monitoring service

**Solutions:**
1. Check if the monitoring service is running:
   ```bash
   curl http://localhost:8000/health
   ```

2. If the monitoring status shows "unavailable", ensure the application was started with the `INTERFACE=all` environment variable:
   ```bash
   docker run -p 8000:8000 -e INTERFACE=all ai-companion:latest
   ```

3. Check the application logs for any errors related to starting the monitoring service:
   ```bash
   docker logs <container_id>
   ```

4. If running locally, start the monitoring service manually:
   ```bash
   cd src
   python -m ai_companion.interfaces.monitor.app
   ```

### 3. Connection Refused Errors

**Symptoms:**
- Error logs show "Connection refused" when trying to connect to services
- Health checks show services as "unavailable"

**Causes:**
- Services are not running on the expected ports
- Firewall or network issues preventing connections

**Solutions:**
1. Check if the services are running and listening on the expected ports:
   ```bash
   # On Linux/macOS
   netstat -tuln | grep 8080  # Check Chainlit
   netstat -tuln | grep 8090  # Check Monitoring
   
   # On Windows
   netstat -an | findstr 8080  # Check Chainlit
   netstat -an | findstr 8090  # Check Monitoring
   ```

2. Ensure no firewall rules are blocking the connections

3. If running in Docker, ensure the ports are properly exposed:
   ```bash
   docker run -p 8000:8000 -p 8080:8080 -p 8090:8090 -e INTERFACE=all ai-companion:latest
   ```

### 4. Services Start But Are Not Accessible

**Symptoms:**
- Logs show that services started successfully
- But accessing the endpoints still returns errors

**Causes:**
- Services are binding to localhost/127.0.0.1 instead of 0.0.0.0
- Port conflicts with other applications

**Solutions:**
1. Ensure services are binding to all interfaces (0.0.0.0):
   ```bash
   # For Chainlit
   python -m ai_companion.interfaces.chainlit.app --host 0.0.0.0 --port 8080
   
   # For Monitoring
   python -m ai_companion.interfaces.monitor.app --host 0.0.0.0 --port 8090
   ```

2. Check for port conflicts and use different ports if needed:
   ```bash
   # On Linux/macOS
   lsof -i :8080
   lsof -i :8090
   
   # On Windows
   netstat -ano | findstr 8080
   netstat -ano | findstr 8090
   ```

## Checking Service Status

You can check the status of all services using the health endpoint:

```bash
curl http://localhost:8000/health
```

This will return information about all services, including their status and availability.

For specific services:

- Chainlit: `curl http://localhost:8000/chat/status`
- Monitoring: `curl http://localhost:8000/health`

## Restarting Services

If you need to restart services:

1. If running in Docker, restart the container:
   ```bash
   docker restart <container_id>
   ```

2. If running locally, stop the current processes and start them again:
   ```bash
   # Start main application
   python -m ai_companion.main
   
   # Start Chainlit
   python -m ai_companion.interfaces.chainlit.app --host 0.0.0.0 --port 8080
   
   # Start Monitoring
   python -m ai_companion.interfaces.monitor.app --host 0.0.0.0 --port 8090
   ```

## Getting Help

If you continue to experience issues after trying these solutions, please:

1. Check the application logs for detailed error messages
2. Review the project documentation for any configuration requirements
3. Open an issue in the project repository with detailed information about the problem

## Chainlit Interface Not Working

### Symptoms
- The `/chat/` endpoint returns a 307 Temporary Redirect to `/chat/error`
- The error page shows "The Chainlit service is currently unavailable"
- Logs show: `Error checking service at localhost:8080: All connection attempts failed`

### Cause
The issue is related to the file path in the Docker container. The Chainlit service is trying to run the file at `ai_companion/interfaces/chainlit/app.py`, but in the container, the file structure is different. The file should be at `/app/src/ai_companion/interfaces/chainlit/app.py` instead.

### Solution
There are two ways to fix this issue:

#### Option 1: Update the Dockerfile
Modify the Dockerfile to use the correct path for the Chainlit app:

```dockerfile
# Change this line in the Dockerfile
/app/.venv/bin/chainlit run ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \
```

to:

```dockerfile
/app/.venv/bin/chainlit run src/ai_companion/interfaces/chainlit/app.py --host 0.0.0.0 --port 8080 & \
```

#### Option 2: Create a Symbolic Link
Add a command to the Dockerfile to create a symbolic link:

```dockerfile
# Add this before the startup script
RUN ln -sf /app/src/ai_companion /app/ai_companion
```

### Implementation Steps
1. Update the Dockerfile with one of the solutions above
2. Rebuild the Docker image
3. Push the new image to the Azure Container Registry
4. Update the Azure Container App to use the new image

```powershell
# Rebuild and push the image
docker build -t evelinaai247acr.azurecr.io/ai-companion:v1.0.2 .
az acr login --name evelinaai247acr
docker push evelinaai247acr.azurecr.io/ai-companion:v1.0.2

# Update the container app
az containerapp update --name evelina-vnet-app --resource-group evelina-ai-rg --image evelinaai247acr.azurecr.io/ai-companion:v1.0.2
```

## Monitoring Endpoints Working but Chainlit Not Working

If the monitoring endpoints (`/health/metrics`, `/health/report`, etc.) are working but the Chainlit interface is not, it indicates that the main application and monitoring service are running correctly, but there's an issue with the Chainlit service specifically.

This is expected behavior with the current implementation, as the main application is designed to handle the absence of the Chainlit service gracefully by redirecting to an error page.

## Checking Service Status

You can check the status of all services using the health endpoint:

```
curl https://evelina-vnet-app.ambitiousglacier-13171220.eastus.azurecontainerapps.io/health
```

This will show the status of all services, including Chainlit. 