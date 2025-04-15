"""Main FastAPI application for AI Companion."""

import logging
import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
import httpx

from ai_companion.interfaces.whatsapp.whatsapp_response import whatsapp_router
from ai_companion.interfaces.monitor.api import monitor_router
from ai_companion.api.web_handler import router as web_chat_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True  # Force override any existing logging config
)

# Disable problematic loggers
logging.getLogger("langgraph_api").setLevel(logging.WARNING)
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Companion",
    description="AI Companion with WhatsApp, Chainlit, and Monitoring interfaces",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with path-based routing
app.include_router(whatsapp_router)
# Include the monitor router with a different prefix
monitor_router.prefix = "/health"  # Change the prefix from /monitor to /health
app.include_router(monitor_router)
# Include the web chat router
app.include_router(web_chat_router)

# Chainlit proxy configuration
CHAINLIT_HOST = "localhost"
CHAINLIT_PORT = 8080

# Monitoring proxy configuration
MONITOR_HOST = "localhost"
MONITOR_PORT = 8090

# Mount Chainlit static assets
# This path should point to the Chainlit frontend dist directory
CHAINLIT_ASSETS_PATH = "/app/.venv/lib/python3.12/site-packages/chainlit/frontend/dist"
if os.path.exists(CHAINLIT_ASSETS_PATH):
    # Mount the assets directory
    app.mount("/assets", StaticFiles(directory=f"{CHAINLIT_ASSETS_PATH}/assets"), name="assets")
    logger.info(f"Mounted Chainlit assets from {CHAINLIT_ASSETS_PATH}/assets")
else:
    logger.warning(f"Chainlit assets directory not found at {CHAINLIT_ASSETS_PATH}")

# Function to check if a service is running
async def is_service_running(host: str, port: int, path: str = "/") -> dict:
    """Check if a service is running at the specified host and port."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{host}:{port}{path}", timeout=2.0)
            return {
                "status": "healthy" if response.status_code < 400 else "unhealthy",
                "status_code": response.status_code
            }
    except Exception as e:
        logger.error(f"Error checking service at {host}:{port}: {e}")
        return {"status": "unavailable", "error": str(e)}

@app.get("/chat/status")
async def chainlit_status():
    """Check the status of the Chainlit service."""
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    return {
        "service": "chainlit",
        "status": status["status"],
        "details": status
    }

@app.get("/chat/error", response_class=HTMLResponse)
async def chainlit_error():
    """Return an error page when Chainlit is not running."""
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    
    if status["status"] == "healthy":
        return RedirectResponse(url="/chat/")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Chainlit Service Error</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .error-container {{
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                border-radius: 5px;
                padding: 20px;
                margin-bottom: 20px;
            }}
            .info-container {{
                background-color: #e2f0fb;
                border: 1px solid #b8daff;
                border-radius: 5px;
                padding: 20px;
            }}
            h1 {{
                color: #721c24;
            }}
            h2 {{
                color: #0c5460;
            }}
            pre {{
                background-color: #f8f9fa;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
            }}
            .btn {{
                display: inline-block;
                padding: 10px 15px;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin-top: 10px;
            }}
            .btn:hover {{
                background-color: #0069d9;
            }}
        </style>
    </head>
    <body>
        <div class="error-container">
            <h1>Chainlit Service Error</h1>
            <p>The Chainlit service is currently unavailable. This service provides the chat interface for the AI Companion.</p>
            <p><strong>Status:</strong> {status["status"]}</p>
            {f'<p><strong>Error:</strong> {status.get("error", "Unknown error")}</p>' if "error" in status else ""}
        </div>
        
        <div class="info-container">
            <h2>Troubleshooting Steps</h2>
            <ol>
                <li>Make sure the Chainlit service is running on {CHAINLIT_HOST}:{CHAINLIT_PORT}</li>
                <li>Check the application logs for any errors related to Chainlit</li>
                <li>Restart the application with the INTERFACE=all environment variable</li>
                <li>If running in Docker, make sure the container has the correct ports exposed</li>
            </ol>
            
            <h2>Docker Command to Start All Interfaces</h2>
            <pre>docker run -p 8000:8000 -e INTERFACE=all ai-companion:latest</pre>
            
            <h2>Check Status</h2>
            <a href="/health" class="btn">Check System Health</a>
            <a href="/chat/status" class="btn">Check Chainlit Status</a>
        </div>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content, status_code=503)

@app.get("/chat", response_class=HTMLResponse)
async def chat_redirect():
    """Redirect /chat to root to ensure all Chainlit access goes through root URL"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        return RedirectResponse(url="/chat/error")
    
    # Redirect to root instead of /chat/
    return RedirectResponse(url="/")

@app.api_route("/chat/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit(request: Request, path: str):
    """Proxy requests to Chainlit running on port 8080"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        return RedirectResponse(url="/chat/error")
    
    client = httpx.AsyncClient(base_url=f"http://{CHAINLIT_HOST}:{CHAINLIT_PORT}")
    
    # Construct the target URL - handle empty path case
    url = "/" if path == "" else f"/{path}"
    
    # Get headers from the incoming request
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove the host header
    
    # Get the request body if it exists
    body = await request.body()
    
    try:
        # Log the proxy attempt
        logger.info(f"Proxying request to Chainlit: {request.method} {url}")
        
        # Forward the request to Chainlit
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params,
            follow_redirects=True,
            timeout=10.0  # Add a timeout to prevent hanging requests
        )
        
        # Log the response status
        logger.info(f"Chainlit response: {response.status_code}")
        
        # Return the response from Chainlit
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.ConnectError as e:
        logger.error(f"Connection error to Chainlit service: {e}")
        return RedirectResponse(url="/chat/error")
    except httpx.TimeoutException as e:
        logger.error(f"Timeout connecting to Chainlit service: {e}")
        return RedirectResponse(url="/chat/error")
    except Exception as e:
        logger.error(f"Error proxying to Chainlit: {e}")
        return RedirectResponse(url="/chat/error")
    finally:
        await client.aclose()

# Add routes for additional Chainlit API endpoints
@app.api_route("/auth/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_auth(request: Request, path: str):
    """Handle auth-related requests from Chainlit frontend (authentication is disabled)"""
    # For /auth/config, always return a response indicating auth is disabled
    # This is required by the Chainlit frontend even though we don't use authentication
    if path == "config":
        logger.info("Returning no-auth configuration for Chainlit frontend")
        return Response(
            content='{"auth_type":null,"providers":[],"session_duration_seconds":3600}',
            status_code=200,
            media_type="application/json"
        )
    
    # For all other auth endpoints, return empty JSON
    logger.info(f"Returning empty response for unused auth endpoint: {path}")
    return Response(content="{}", status_code=200, media_type="application/json")

@app.api_route("/project/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_project(request: Request, path: str):
    """Handle project-related requests from Chainlit frontend"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    
    # If Chainlit is healthy, proxy the request
    if status["status"] == "healthy":
        client = httpx.AsyncClient(base_url=f"http://{CHAINLIT_HOST}:{CHAINLIT_PORT}")
        url = f"/project/{path}"
        
        # Get headers from the incoming request
        headers = dict(request.headers)
        headers.pop("host", None)  # Remove the host header
        
        # Get the request body if it exists
        body = await request.body()
        
        try:
            # Log the proxy attempt
            logger.info(f"Proxying project request to Chainlit: {request.method} {url}")
            
            # Forward the request to Chainlit
            response = await client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                params=request.query_params,
                follow_redirects=True,
                timeout=5.0
            )
            
            # Log the response status
            logger.info(f"Chainlit project response: {response.status_code}")
            
            # Return the response from Chainlit
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except Exception as e:
            logger.error(f"Error proxying project to Chainlit: {e}")
            # Fall through to default responses below
        finally:
            await client.aclose()
    
    # If Chainlit is not healthy or there was an error, return default responses
    # These are required by the Chainlit frontend to function properly
    if path.startswith("translations"):
        logger.info("Returning empty translations for Chainlit frontend")
        return Response(
            content='{"translations":{}}',
            status_code=200,
            media_type="application/json"
        )
    
    # For all other project endpoints, return empty JSON
    logger.info(f"Returning empty response for project endpoint: {path}")
    return Response(content="{}", status_code=200, media_type="application/json")

# Add WebSocket proxy route for Chainlit
@app.api_route("/ws/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_ws(request: Request, path: str):
    """Proxy WebSocket requests to Chainlit"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        return Response(content="{}", status_code=404, media_type="application/json")
    
    client = httpx.AsyncClient(base_url=f"http://{CHAINLIT_HOST}:{CHAINLIT_PORT}")
    url = f"/ws/{path}"
    
    # Get headers from the incoming request
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove the host header
    
    # Get the request body if it exists
    body = await request.body()

    try:
        # Log the proxy attempt
        logger.info(f"Proxying WebSocket request to Chainlit: {request.method} {url}")

        # Forward the request to Chainlit
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params,
            follow_redirects=True,
            timeout=60.0  # Increase timeout for WebSocket connections
        )

        # Log the response status
        logger.info(f"Chainlit WebSocket response: {response.status_code}")

        # Handle WebSocket upgrade requests (Socket.IO polling)
        if "content-type" in response.headers:
            content_type = response.headers["content-type"]
        else:
            # Default to application/json for socket.io polling
            content_type = "application/json"
        
        # Return the response from Chainlit with explicit content type
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=content_type
        )
    except Exception as e:
        logger.error(f"Error proxying WebSocket to Chainlit: {e}")
        # Return 404 for WebSocket errors
        return Response(content="{}", status_code=404, media_type="application/json")
    finally:
        await client.aclose()

# Add WebSocket support for the root path to handle Socket.IO at the root URL
@app.api_route("/socket.io/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_socketio_root(request: Request, path: str):
    """Proxy Socket.IO requests to Chainlit for the root URL"""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        return Response(content="{}", status_code=404, media_type="application/json")
    
    client = httpx.AsyncClient(base_url=f"http://{CHAINLIT_HOST}:{CHAINLIT_PORT}")
    url = f"/socket.io/{path}"
    
    # Get headers from the incoming request
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove the host header
    
    # Get the request body if it exists
    body = await request.body()

    try:
        # Log the proxy attempt
        logger.info(f"Proxying Socket.IO request to Chainlit: {request.method} {url}")

        # Forward the request to Chainlit
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params,
            follow_redirects=True,
            timeout=60.0  # Increase timeout for Socket.IO connections
        )

        # Log the response status
        logger.info(f"Chainlit Socket.IO response: {response.status_code}")

        # Handle Socket.IO responses with proper content type
        if "content-type" in response.headers:
            content_type = response.headers["content-type"]
        else:
            # Default to application/json for socket.io polling
            content_type = "application/json"
        
        # Return the response from Chainlit with explicit content type
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=content_type
        )
    except Exception as e:
        logger.error(f"Error proxying Socket.IO to Chainlit: {e}")
        return Response(content="{}", status_code=404, media_type="application/json")
    finally:
        await client.aclose()

@app.get("/health")
async def health_check():
    """Root health check endpoint."""
    # Check the monitoring service health
    try:
        async with httpx.AsyncClient() as client:
            monitor_health = await client.get(f"http://{MONITOR_HOST}:{MONITOR_PORT}/health")
            monitor_status = monitor_health.json() if monitor_health.status_code == 200 else {"status": "unavailable"}
    except Exception as e:
        logger.error(f"Error checking monitoring health: {e}")
        monitor_status = {"status": "unavailable", "error": str(e)}
    
    # Check the Chainlit service health
    chainlit_status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    
    return {
        "status": "healthy",
        "service": "ai-companion",
        "monitoring": monitor_status,
        "chainlit": chainlit_status,
        "interfaces": {
            "whatsapp": "/whatsapp/health",
            "monitor": "/health",
            "chainlit": "/chat/"
        },
        "monitoring_endpoints": {
            "metrics": "/health/metrics",
            "report": "/health/report",
            "reset": "/health/reset"
        }
    }

@app.get("/health/metrics")
async def monitor_metrics():
    """Proxy to the monitoring service metrics endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{MONITOR_HOST}:{MONITOR_PORT}/monitor/metrics")
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except Exception as e:
        logger.error(f"Error proxying to monitoring metrics: {e}")
        return {"status": "error", "message": f"Failed to connect to monitoring service: {str(e)}"}

@app.get("/health/report")
async def monitor_report():
    """Proxy to the monitoring service report endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"http://{MONITOR_HOST}:{MONITOR_PORT}/monitor/report")
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except Exception as e:
        logger.error(f"Error proxying to monitoring report: {e}")
        return {"status": "error", "message": f"Failed to connect to monitoring service: {str(e)}"}

@app.post("/health/reset")
async def monitor_reset():
    """Proxy to the monitoring service reset endpoint."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"http://{MONITOR_HOST}:{MONITOR_PORT}/monitor/reset")
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
    except Exception as e:
        logger.error(f"Error proxying to monitoring reset: {e}")
        return {"status": "error", "message": f"Failed to connect to monitoring service: {str(e)}"}

@app.get("/")
async def root():
    """Root endpoint for the AI Companion."""
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] == "healthy":
        # Proxy to Chainlit directly instead of redirecting to /chat/
        client = httpx.AsyncClient(base_url=f"http://{CHAINLIT_HOST}:{CHAINLIT_PORT}")
        try:
            # Forward the request to Chainlit
            logger.info(f"Proxying root request to Chainlit")
            response = await client.get(
                "/",
                follow_redirects=True,
                timeout=10.0
            )
            
            # Log the response status
            logger.info(f"Chainlit root response: {response.status_code}")
            
            # Return the response from Chainlit
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except Exception as e:
            logger.error(f"Error proxying to Chainlit root: {e}")
            return RedirectResponse(url="/chat/error")
        finally:
            await client.aclose()
    
    # Otherwise show the API information
    return {
        "message": "AI Companion API",
        "docs_url": "/docs",
        "whatsapp_url": "/whatsapp/webhook",
        "monitoring": {
            "metrics": "/health/metrics",
            "report": "/health/report",
            "reset": "/health/reset"
        },
        "chainlit_url": "/chat/"
    }

# Add direct access to Chainlit at the root level
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_chainlit_root(request: Request, path: str):
    """Proxy requests to Chainlit running on port 8080 for paths not handled by other routes"""
    # This route has the lowest priority and will only be used if no other route matches
    
    # Skip paths that should be handled by other routes
    if path.startswith(("docs", "openapi.json", "whatsapp", "health", "auth", "project", "chat", "ws")):
        # Let other routes handle these paths
        raise HTTPException(status_code=404, detail="Not found")
    
    # Check if Chainlit is running first
    status = await is_service_running(CHAINLIT_HOST, CHAINLIT_PORT)
    if status["status"] != "healthy":
        # If Chainlit is not running, show an error
        return RedirectResponse(url="/chat/error")
    
    client = httpx.AsyncClient(base_url=f"http://{CHAINLIT_HOST}:{CHAINLIT_PORT}")
    
    # Construct the target URL
    url = f"/{path}"
    
    # Get headers from the incoming request
    headers = dict(request.headers)
    headers.pop("host", None)  # Remove the host header
    
    # Get the request body if it exists
    body = await request.body()
    
    try:
        # Log the proxy attempt
        logger.info(f"Proxying request to Chainlit root: {request.method} {url}")
        
        # Forward the request to Chainlit
        response = await client.request(
            method=request.method,
            url=url,
            headers=headers,
            content=body,
            params=request.query_params,
            follow_redirects=True,
            timeout=10.0
        )
        
        # Log the response status
        logger.info(f"Chainlit root response: {response.status_code}")
        
        # Return the response from Chainlit
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except Exception as e:
        logger.error(f"Error proxying to Chainlit root: {e}")
        return RedirectResponse(url="/chat/error")
    finally:
        await client.aclose()

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 