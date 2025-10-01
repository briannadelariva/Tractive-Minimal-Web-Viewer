"""
Tractive Minimal Web Viewer

Build: docker build -t tractive-web .
Run: docker run --rm -p 8080:8080 tractive-web
Open: http://localhost:8080

A minimal, production-ready web app that runs entirely in a Docker container.
Presents a login page for a Tractive account, authenticates via the unofficial
Tractive API client, and displays available data (trackers, hardware info,
position data, geofences, live mode state).
"""

import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from .tractive_client import TractiveClient, TractiveClientError

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
PORT = int(os.getenv("PORT", 8080))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app setup
app = FastAPI(
    title="Tractive Minimal Web Viewer",
    description="Minimal web interface for viewing Tractive tracker data",
    version="1.0.0"
)

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=1200)  # 20 minutes

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except RuntimeError:
    # Handle case where static directory doesn't exist yet
    pass

templates = Jinja2Templates(directory="app/templates")

# Global client instance (in production, you'd use dependency injection)
tractive_clients: Dict[str, TractiveClient] = {}


def get_session_id(request: Request) -> str:
    """Generate or get session ID"""
    session_id = request.session.get("session_id")
    if not session_id:
        session_id = secrets.token_urlsafe(16)
        request.session["session_id"] = session_id
    return session_id


async def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Get current authenticated user from session"""
    return request.session.get("user")


async def require_auth(request: Request) -> Dict[str, Any]:
    """Require authentication, redirect to login if not authenticated"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


async def get_tractive_client(request: Request) -> TractiveClient:
    """Get or create Tractive client for current session"""
    session_id = get_session_id(request)
    
    if session_id not in tractive_clients:
        tractive_clients[session_id] = TractiveClient()
    
    return tractive_clients[session_id]


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect based on auth status"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    else:
        return RedirectResponse(url="/login", status_code=302)


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[str] = None):
    """Display login form"""
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    
    return templates.TemplateResponse("login.html", {
        "request": request,
        "error": error
    })


@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    """Handle login form submission"""
    try:
        client = await get_tractive_client(request)
        
        # Authenticate with Tractive
        session_data = await client.authenticate(email, password)
        
        # Store minimal session data (never store password)
        request.session["user"] = {
            "email": email,
            "user_id": session_data.get("user_id"),
            "authenticated_at": session_data.get("authenticated_at"),
            "last_activity": datetime.now().isoformat()
        }
        
        logger.info(f"User {email} successfully logged in")
        return RedirectResponse(url="/dashboard", status_code=302)
        
    except TractiveClientError as e:
        logger.warning(f"Login failed for {email}: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": f"Login failed: {str(e)}",
            "email": email
        })
    except Exception as e:
        logger.error(f"Unexpected error during login for {email}: {str(e)}")
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "An unexpected error occurred. Please try again.",
            "email": email
        })


@app.post("/logout")
async def logout(request: Request):
    """Handle logout"""
    session_id = get_session_id(request)
    
    # Clean up client
    if session_id in tractive_clients:
        try:
            await tractive_clients[session_id].close()
        except Exception as e:
            logger.error(f"Error closing client during logout: {str(e)}")
        finally:
            del tractive_clients[session_id]
    
    # Clear session
    request.session.clear()
    
    return RedirectResponse(url="/login", status_code=302)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, tracker_id: Optional[str] = None):
    """Main dashboard showing tracker data"""
    try:
        user = await require_auth(request)
        client = await get_tractive_client(request)
        
        # Update last activity
        user["last_activity"] = datetime.now().isoformat()
        request.session["user"] = user
        
        # Get trackers list
        try:
            trackers = await client.get_trackers()
        except TractiveClientError as e:
            logger.error(f"Failed to get trackers: {str(e)}")
            trackers = []
        
        if not trackers:
            return templates.TemplateResponse("dashboard.html", {
                "request": request,
                "user": user,
                "trackers": [],
                "error": "No trackers found for this account"
            })
        
        # Select tracker (first one if not specified)
        selected_tracker = None
        if tracker_id:
            selected_tracker = next((t for t in trackers if t["id"] == tracker_id), None)
        
        if not selected_tracker:
            selected_tracker = trackers[0]
            tracker_id = selected_tracker["id"]
        
        # Get detailed data for selected tracker
        dashboard_data = {
            "user": user,
            "trackers": trackers,
            "selected_tracker": selected_tracker,
            "hardware_info": None,
            "latest_position": None,
            "recent_history": None,
            "geofences": None,
            "live_tracking": None,
            "errors": []
        }
        
        # Fetch all data concurrently (in a real app, you'd use asyncio.gather)
        try:
            dashboard_data["hardware_info"] = await client.get_hardware_info(tracker_id)
        except Exception as e:
            dashboard_data["errors"].append(f"Hardware info: {str(e)}")
        
        try:
            dashboard_data["latest_position"] = await client.get_latest_position(tracker_id)
        except Exception as e:
            dashboard_data["errors"].append(f"Latest position: {str(e)}")
        
        try:
            dashboard_data["recent_history"] = await client.get_position_history(tracker_id, hours=2)
        except Exception as e:
            dashboard_data["errors"].append(f"Position history: {str(e)}")
        
        try:
            dashboard_data["geofences"] = await client.get_geofences(tracker_id)
        except Exception as e:
            dashboard_data["errors"].append(f"Geofences: {str(e)}")
        
        try:
            dashboard_data["live_tracking"] = await client.get_live_tracking_state(tracker_id)
        except Exception as e:
            dashboard_data["errors"].append(f"Live tracking: {str(e)}")
        
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            **dashboard_data
        })
        
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "error": f"An error occurred: {str(e)}"
        })


@app.get("/data/json/{kind}")
async def get_json_data(
    request: Request,
    kind: str,
    tracker_id: Optional[str] = None
):
    """Return raw JSON data for inspection"""
    try:
        user = await require_auth(request)
        client = await get_tractive_client(request)
        
        if kind == "trackers":
            data = await client.get_trackers()
        elif kind == "hw_info" and tracker_id:
            data = await client.get_hardware_info(tracker_id)
        elif kind == "latest" and tracker_id:
            data = await client.get_latest_position(tracker_id)
        elif kind == "history" and tracker_id:
            data = await client.get_position_history(tracker_id, hours=2)
        elif kind == "geofences" and tracker_id:
            data = await client.get_geofences(tracker_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid data kind or missing tracker_id")
        
        return JSONResponse(content=data)
        
    except HTTPException:
        return JSONResponse(
            content={"error": "Authentication required"},
            status_code=401
        )
    except Exception as e:
        logger.error(f"Error fetching {kind} data: {str(e)}")
        return JSONResponse(
            content={"error": str(e)},
            status_code=500
        )


@app.post("/toggle-live/{tracker_id}")
async def toggle_live_tracking(
    request: Request,
    tracker_id: str,
    enable: bool = Form(...)
):
    """Toggle live tracking for a tracker"""
    try:
        user = await require_auth(request)
        client = await get_tractive_client(request)
        
        result = await client.toggle_live_tracking(tracker_id, enable)
        
        # Redirect back to dashboard with the same tracker selected
        return RedirectResponse(
            url=f"/dashboard?tracker_id={tracker_id}",
            status_code=302
        )
        
    except HTTPException:
        return RedirectResponse(url="/login", status_code=302)
    except Exception as e:
        logger.error(f"Error toggling live tracking: {str(e)}")
        return RedirectResponse(
            url=f"/dashboard?tracker_id={tracker_id}",
            status_code=302
        )


@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(content={
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })


# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    for client in tractive_clients.values():
        try:
            await client.close()
        except Exception as e:
            logger.error(f"Error closing client during shutdown: {str(e)}")
    tractive_clients.clear()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=False)