"""
FastAPI Application - IDS Backend API
Main entry point for the web server
"""
import logging

from app.detection import get_connection_manager
from app.routes import monitor, alerts, stats, ip_lists, model
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from fastapi import Request
from fastapi import FastAPI, Request, status, WebSocket, WebSocketDisconnect
from app.routes import monitor, alerts, stats, model
from app.database.database import init_database, get_database_info
from app.detection.detection_service import get_detection_service
from app.capture.capture_service import get_capture_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # ===== STARTUP =====
    logger.info("=" * 60)
    logger.info("Starting IDS Backend API...")
    logger.info("=" * 60)

    try:
        # 1. Initialize database
        logger.info("Initializing database...")
        init_database()
        db_info = get_database_info()
        logger.info(f"Database: {db_info['database_path']}")
        logger.info(f"Database size: {db_info['database_size_mb']} MB")

        # 2. Initialize DetectionService (load ML model)
        logger.info("Loading ML model...")
        detection_service = get_detection_service()
        detection_service.initialize_components()
        logger.info("ML model loaded successfully")

        # 3. Get CaptureService instance (don't start yet)
        logger.info("Initializing CaptureService...")
        capture_service = get_capture_service()
        logger.info("CaptureService ready")

        logger.info("=" * 60)
        logger.info("IDS Backend API started successfully!")
        logger.info("API Docs: http://localhost:8000/docs")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield  # Application runs here

    # ===== SHUTDOWN =====
    logger.info("=" * 60)
    logger.info("Shutting down IDS Backend API...")
    logger.info("=" * 60)

    try:
        # Stop detection service if running
        detection_service = get_detection_service()
        if detection_service.is_running():
            logger.info("Stopping DetectionService...")
            await detection_service.stop()

        # Stop capture service if running
        capture_service = get_capture_service()
        if capture_service.is_monitoring_active():
            logger.info("Stopping CaptureService...")
            await capture_service.stop_monitoring()

        logger.info("Shutdown complete")

    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title="IDS - AI-Powered Intrusion Detection System",
    description="Real-time network intrusion detection using XGBoost ML model",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitor"])
app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(ip_lists.router, prefix="/api", tags=["IP Lists"])
app.include_router(model.router, prefix="/api/model", tags=["Model"])


# ===== WEBSOCKET ENDPOINT =====

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """
    WebSocket endpoint for real-time alert broadcasting

    Clients connect to this endpoint to receive alerts in real-time.

    Connection URL: ws://localhost:8000/ws/alerts

    Message format (JSON):
    {
        "id": 123,
        "timestamp": "2025-11-10T10:30:00",
        "source_ip": "192.168.1.100",
        "dest_ip": "10.0.0.1",
        "attack_type": "DDoS",
        "confidence": 0.98,
        "severity": "critical"
    }
    """
    from app.detection.websocket_manager import get_connection_manager

    connection_manager = get_connection_manager()

    try:
        # Accept WebSocket connection
        await websocket.accept()
        logger.info(f"WebSocket client connected: {websocket.client}")

        # Register connection with ConnectionManager (NOT async)
        connection_manager.connect(websocket)

        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (ping/pong for keep-alive)
                data = await websocket.receive_text()

                # Optional: Handle client messages
                if data == "ping":
                    await websocket.send_text("pong")

            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {websocket.client}")
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        # Disconnect and cleanup (NOT async)
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket connection closed: {websocket.client}")

# CORS Middleware (allow all for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== EXCEPTION HANDLERS =====

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Handle 404 Not Found"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": "Not found"}
    )


@app.exception_handler(400)
async def bad_request_handler(request: Request, exc):
    """Handle 400 Bad Request"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Handle 500 Internal Server Error"""
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# ===== ROOT ENDPOINT =====

@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API info
    """
    return {
        "name": "IDS - AI-Powered Intrusion Detection System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "monitor": "/api/monitor",
            "alerts": "/api/alerts",
            "statistics": "/api/stats",
            "whitelist": "/api/whitelist",
            "blacklist": "/api/blacklist",
            "model": "/api/model",
            "websocket": "/ws/alerts"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    detection_service = get_detection_service()
    capture_service = get_capture_service()
    db_info = get_database_info()

    return {
        "status": "healthy",
        "database": {
            "connected": db_info['database_exists'],
            "size_mb": db_info['database_size_mb']
        },
        "services": {
            "detection_running": detection_service.is_running(),
            "monitoring_active": capture_service.is_monitoring_active()
        }
    }

# ===== ROUTES REGISTRATION =====
# TODO: Import and register routers here when created
# Example:
# from app.routes import monitor, alerts, stats, ip_lists, model, websocket
# app.include_router(monitor.router, prefix="/api/monitor", tags=["Monitor"])
# app.include_router(alerts.router, prefix="/api/alerts", tags=["Alerts"])
# ... etc