"""
Monitor Control Endpoints
Start/Stop monitoring and get system status
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.dependencies import get_db, get_capture_service, get_detection_service
from app.capture.capture_service import CaptureService
from app.detection.detection_service import DetectionService
from app.capture.config import INTERFACE

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/start")
async def start_monitoring(
        db: Session = Depends(get_db),
        capture_service: CaptureService = Depends(get_capture_service),
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Start network monitoring and attack detection

    Steps:
    1. Check if already running
    2. Start CaptureService (packet capture)
    3. Initialize DetectionService with db and capture service
    4. Start DetectionService (detection loop)

    Returns:
        JSON with status and message
    """
    try:
        # Check if already running
        if capture_service.is_monitoring_active():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring is already active"
            )

        if detection_service.is_running():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Detection service is already running"
            )

        logger.info("Starting monitoring...")

        # Step 1: Start CaptureService
        logger.info(f"Starting packet capture on interface: {INTERFACE}")
        capture_started = await capture_service.start_monitoring()

        if not capture_started:
            error_msg = capture_service.sniffer.error_message or "Unknown error"
            logger.error(f"Failed to start capture: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start packet capture: {error_msg}"
            )

        # Step 2: Initialize DetectionService with dependencies
        logger.info("Initializing detection service...")
        detection_service.initialize_components(
            capture_service=capture_service,
            db_session=db
        )

        # Step 3: Start DetectionService
        logger.info("Starting detection service...")
        await detection_service.start()

        logger.info("Monitoring started successfully")

        return {
            "status": "success",
            "message": "Monitoring started successfully",
            "interface": INTERFACE,
            "services": {
                "capture_active": capture_service.is_monitoring_active(),
                "detection_active": detection_service.is_running()
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/stop")
async def stop_monitoring(
        capture_service: CaptureService = Depends(get_capture_service),
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Stop network monitoring and attack detection

    Steps:
    1. Check if running
    2. Stop DetectionService
    3. Stop CaptureService
    4. Return final statistics

    Returns:
        JSON with status, message, and statistics
    """
    try:
        # Check if not running
        if not capture_service.is_monitoring_active() and not detection_service.is_running():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Monitoring is not active"
            )

        logger.info("Stopping monitoring...")

        # Step 1: Stop DetectionService first
        if detection_service.is_running():
            logger.info("Stopping detection service...")
            await detection_service.stop()

        # Step 2: Stop CaptureService
        if capture_service.is_monitoring_active():
            logger.info("Stopping packet capture...")
            capture_stats = await capture_service.stop_monitoring()
        else:
            capture_stats = capture_service.get_statistics()

        # Step 3: Get final statistics
        detection_stats = detection_service.get_statistics()

        logger.info("Monitoring stopped successfully")

        return {
            "status": "success",
            "message": "Monitoring stopped successfully",
            "statistics": {
                "capture": {
                    "packets_captured": capture_stats['packets_captured'],
                    "flows_created": capture_stats['total_flows_created'],
                    "flows_expired": capture_stats['total_flows_expired'],
                    "features_extracted": capture_stats['features_extracted']
                },
                "detection": {
                    "total_predictions": detection_stats['total_predictions'],
                    "alerts_created": detection_stats['alerts_created'],
                    "benign_filtered": detection_stats['benign_filtered'],
                    "duplicates_blocked": detection_stats['duplicates_blocked'],
                    "whitelist_skipped": detection_stats['whitelist_skipped'],
                    "low_confidence_skipped": detection_stats['low_confidence_skipped'],
                    "attacks_by_type": detection_stats['attacks_by_type']
                }
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.get("/status")
async def get_monitoring_status(
        capture_service: CaptureService = Depends(get_capture_service),
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Get current monitoring status and statistics

    Returns:
        JSON with monitoring status and real-time statistics
    """
    try:
        # Get capture statistics
        capture_stats = capture_service.get_statistics()

        # Get detection statistics
        detection_stats = detection_service.get_statistics()

        return {
            "status": "active" if capture_service.is_monitoring_active() else "inactive",
            "interface": INTERFACE,
            "capture": {
                "monitoring_active": capture_stats['monitoring_active'],
                "packets_captured": capture_stats['packets_captured'],
                "active_flows": capture_stats['active_flows'],
                "total_flows_created": capture_stats['total_flows_created'],
                "total_flows_expired": capture_stats['total_flows_expired'],
                "features_extracted": capture_stats['features_extracted'],
                "queue_size": capture_stats['queue_size'],
                "error_message": capture_stats.get('error_message')
            },
            "detection": {
                "detection_running": detection_stats.get('total_predictions', 0) > 0 or detection_service.is_running(),
                "total_predictions": detection_stats['total_predictions'],
                "alerts_created": detection_stats['alerts_created'],
                "benign_filtered": detection_stats['benign_filtered'],
                "duplicates_blocked": detection_stats['duplicates_blocked'],
                "whitelist_skipped": detection_stats['whitelist_skipped'],
                "low_confidence_skipped": detection_stats['low_confidence_skipped'],
                "attacks_by_type": detection_stats['attacks_by_type']
            },
            "alert_cache": detection_stats.get('cache_stats', {}),
            "websocket": detection_stats.get('websocket_stats', {})
        }

    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get status: {str(e)}"
        )