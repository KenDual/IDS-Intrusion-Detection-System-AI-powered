"""
FastAPI Dependencies
Shared dependencies for routes
"""
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.capture.capture_service import get_capture_service
from app.detection.detection_service import get_detection_service

# Export dependencies
__all__ = [
    'get_db',
    'get_capture_service',
    'get_detection_service'
]