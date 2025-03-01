# Chainlit Assets Fix

## Issue Description

The Chainlit interface was experiencing several issues:

1. Missing CSS and JavaScript assets, resulting in an unstyled interface
2. Missing API endpoints `/auth/config` and `/project/translations?language=lt`, causing errors in the browser console
3. Missing WebSocket endpoints for `/ws/socket.io/`, preventing real-time communication

## Root Cause Analysis

1. **Static Assets**: The FastAPI application was not correctly serving the static assets (CSS and JS files) from the Chainlit frontend directory.
2. **API Endpoints**: The FastAPI proxy configuration was not routing the `/auth/*` and `/project/*` endpoints to the Chainlit backend service.
3. **WebSocket Endpoints**: The FastAPI proxy configuration was not routing WebSocket connections to the Chainlit backend service.

## Solution Implemented

The solution was implemented in three parts:

### Part 1: Direct Static Asset Serving

We modified the FastAPI application to directly serve the static assets from the Chainlit frontend directory:

```python
# Mount Chainlit static assets
CHAINLIT_ASSETS_PATH = "/app/.venv/lib/python3.12/site-packages/chainlit/frontend/dist"
if os.path.exists(CHAINLIT_ASSETS_PATH):
    # Mount the assets directory
    app.mount("/assets", StaticFiles(directory=f"{CHAINLIT_ASSETS_PATH}/assets"), name="assets")
    logger.info(f"Mounted Chainlit assets from {CHAINLIT_ASSETS_PATH}/assets")
else:
    logger.warning(f"Chainlit assets directory not found at {CHAINLIT_ASSETS_PATH}")
```

### Part 2: Additional API Endpoint Proxying

We added proxy routes for the missing API endpoints:

```python
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_auth(request: Request, path: str):
    """Proxy auth requests to Chainlit"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        # Return default empty auth config to prevent frontend errors
        if path == "config":
            return Response(
                content='{"auth_type":null,"providers":[],"session_duration_seconds":3600}',
                status_code=200,
                media_type="application/json"
            )
        return Response(content="{}", status_code=200, media_type="application/json")
    
    # ... proxy implementation ...
```

```python
@app.api_route("/project/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_project(request: Request, path: str):
    """Proxy project requests to Chainlit"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        # Return default empty translations for /project/translations to prevent frontend errors
        if path.startswith("translations"):
            return Response(
                content='{"translations":{}}',
                status_code=200,
                media_type="application/json"
            )
        return Response(content="{}", status_code=200, media_type="application/json")
    
    # ... proxy implementation ...
```

### Part 3: WebSocket Endpoint Proxying

We added a proxy route for WebSocket connections:

```python
@app.api_route("/ws/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_ws(request: Request, path: str):
    """Proxy WebSocket requests to Chainlit"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        return Response(content="{}", status_code=404, media_type="application/json")
    
    # ... proxy implementation ...
```

## Deployment Steps

1. Update the `main.py` file with the changes above
2. Update the `deploy.ps1` script to use the new version tag (`v1.0.6`)
3. Run the deployment script to build and deploy the new image:
   ```
   ./deploy.ps1
   ```

## Verification

After deployment, verify that:

1. The Chainlit interface loads with proper styling (CSS)
2. The Chainlit interface has proper functionality (JavaScript)
3. The API endpoints `/auth/config` and `/project/translations?language=lt` return valid responses
4. The WebSocket connections are properly established

## Future Considerations

To prevent similar issues in the future:

1. Implement a more robust static file serving solution that can handle different environments
2. Add monitoring for 404 errors to detect missing assets or endpoints
3. Implement health checks for all critical services
4. Consider using a more comprehensive reverse proxy solution for production deployments
5. Implement robust fallback responses for all API endpoints to ensure the frontend can function even during temporary backend issues 