"""
Alert Endpoints
CRUD operations for alerts
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime

from app.dependencies import get_db
from app.database.crud import (
    get_alerts,
    count_alerts,
    get_recent_alerts,
    get_alert_by_id,
    delete_alert
)

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_alerts_endpoint(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    attack_type: Optional[str] = Query(None, description="Filter by attack type"),
    severity: Optional[str] = Query(None, description="Filter by severity (low/critical)"),
    source_ip: Optional[str] = Query(None, description="Filter by source IP"),
    date_from: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    date_to: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get alerts with pagination and filters

    Query Parameters:
    - page: Page number (default: 1)
    - limit: Items per page (default: 50, max: 200)
    - attack_type: Filter by attack type (DoS Hulk, PortScan, DDoS)
    - severity: Filter by severity (low, critical)
    - source_ip: Filter by source IP address
    - date_from: Filter alerts from this date (ISO format)
    - date_to: Filter alerts to this date (ISO format)

    Returns:
        JSON with alerts list and pagination info
    """
    try:
        # Parse date filters
        start_date = None
        end_date = None

        if date_from:
            try:
                start_date = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date_from format. Use ISO format (e.g., 2025-11-10T08:00:00)"
                )

        if date_to:
            try:
                end_date = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date_to format. Use ISO format (e.g., 2025-11-10T18:00:00)"
                )

        # Get alerts from database (match crud.py parameters)
        alerts = get_alerts(
            db=db,
            skip=(page - 1) * limit,
            limit=limit,
            attack_type=attack_type,
            severity=severity,
            source_ip=source_ip,
            start_date=start_date,
            end_date=end_date
        )

        # Get total count for pagination (match crud.py parameters)
        total = count_alerts(
            db=db,
            attack_type=attack_type,
            severity=severity,
            start_date=start_date,
            end_date=end_date
        )

        # Calculate total pages
        total_pages = (total + limit - 1) // limit if total > 0 else 1

        # Convert alerts to dict
        alerts_data = [alert.to_dict() for alert in alerts]

        return {
            "alerts": alerts_data,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/recent")
async def get_recent_alerts_endpoint(
    n: int = Query(10, ge=1, le=100, description="Number of recent alerts"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get N most recent alerts

    Query Parameters:
    - n: Number of alerts to retrieve (default: 10, max: 100)

    Returns:
        JSON with recent alerts list
    """
    try:
        # Match crud.py parameter name (limit instead of n)
        alerts = get_recent_alerts(db=db, limit=n)
        alerts_data = [alert.to_dict() for alert in alerts]

        return {
            "alerts": alerts_data,
            "count": len(alerts_data)
        }

    except Exception as e:
        logger.error(f"Failed to get recent alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent alerts: {str(e)}"
        )


@router.get("/{alert_id}")
async def get_alert_by_id_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get alert by ID

    Path Parameters:
    - alert_id: Alert ID

    Returns:
        JSON with alert details
    """
    try:
        alert = get_alert_by_id(db=db, alert_id=alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )

        return alert.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert: {str(e)}"
        )


@router.delete("/{alert_id}")
async def delete_alert_endpoint(
    alert_id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Delete alert by ID

    Path Parameters:
    - alert_id: Alert ID

    Returns:
        JSON with success message
    """
    try:
        # Check if alert exists
        alert = get_alert_by_id(db=db, alert_id=alert_id)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found"
            )

        # Delete alert
        success = delete_alert(db=db, alert_id=alert_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete alert"
            )

        logger.info(f"Alert {alert_id} deleted")

        return {
            "status": "success",
            "message": f"Alert {alert_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete alert {alert_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete alert: {str(e)}"
        )