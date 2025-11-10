"""
Statistics Endpoints
Dashboard statistics and analytics
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from app.dependencies import get_db, get_detection_service
from app.database.crud import count_alerts, get_alert_statistics
from app.models import Alert
from app.detection.detection_service import DetectionService

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def get_statistics(
        db: Session = Depends(get_db),
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Get overall statistics for dashboard

    Returns:
        JSON with comprehensive statistics:
        - Total alerts count
        - Alerts by attack type
        - Alerts by severity
        - Top 10 attacked destination IPs
        - System monitoring status
    """
    try:
        # 1. Total alerts count
        total_alerts = count_alerts(db=db)

        # 2. Count by attack type
        dos_hulk_count = count_alerts(db=db, attack_type="DoS Hulk")
        portscan_count = count_alerts(db=db, attack_type="PortScan")
        ddos_count = count_alerts(db=db, attack_type="DDoS")

        # 3. Count by severity
        critical_count = count_alerts(db=db, severity="critical")
        low_count = count_alerts(db=db, severity="low")

        # 4. Top 10 attacked destination IPs (custom query)
        top_attacked_ips = db.query(
            Alert.dest_ip,
            func.count(Alert.id).label('attack_count')
        ).group_by(
            Alert.dest_ip
        ).order_by(
            desc('attack_count')
        ).limit(10).all()

        # Convert to list of dicts
        top_attacked_list = [
            {"ip": ip, "count": count}
            for ip, count in top_attacked_ips
        ]

        # 5. Monitoring status
        is_monitoring = detection_service.is_running()

        # 6. Get 24h statistics
        stats_24h = get_alert_statistics(db=db, hours=24)

        return {
            "overview": {
                "total_alerts": total_alerts,
                "critical_alerts": critical_count,
                "low_alerts": low_count,
                "monitoring_active": is_monitoring
            },
            "attack_types": {
                "DoS Hulk": dos_hulk_count,
                "PortScan": portscan_count,
                "DDoS": ddos_count
            },
            "severity": {
                "critical": critical_count,
                "low": low_count
            },
            "top_attacked_ips": top_attacked_list,
            "last_24h": {
                "total_alerts": stats_24h["total_alerts"],
                "critical_alerts": stats_24h["critical_alerts"],
                "low_alerts": stats_24h["low_alerts"],
                "by_attack_type": stats_24h["attack_types"]
            }
        }

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )


@router.get("/timeline")
async def get_timeline_statistics(
        period: str = Query("hour", description="Time period: hour, day, or week"),
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get time-series statistics for charts

    Query Parameters:
    - period: Time period (hour, day, week)
        - hour: Last 1 hour, grouped by minute
        - day: Last 24 hours, grouped by hour
        - week: Last 7 days, grouped by day

    Returns:
        JSON with time-series data for visualization
    """
    try:
        # Validate period
        valid_periods = ["hour", "day", "week"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )

        # Map period to hours and grouping
        period_config = {
            "hour": {"hours": 1, "interval_minutes": 5, "group_by": "minute"},
            "day": {"hours": 24, "interval_minutes": 60, "group_by": "hour"},
            "week": {"hours": 168, "interval_minutes": 1440, "group_by": "day"}  # 24*7=168
        }

        config = period_config[period]
        hours_back = config["hours"]
        interval_minutes = config["interval_minutes"]

        # Get start time
        now = datetime.now()
        start_time = now - timedelta(hours=hours_back)

        # Query alerts in time range
        alerts = db.query(Alert).filter(
            Alert.timestamp >= start_time
        ).order_by(Alert.timestamp).all()

        # Group alerts by time intervals
        timeline_data = []
        current_time = start_time

        while current_time <= now:
            interval_end = current_time + timedelta(minutes=interval_minutes)

            # Count alerts in this interval
            interval_alerts = [
                a for a in alerts
                if current_time <= a.timestamp < interval_end
            ]

            # Count by attack type
            dos_count = sum(1 for a in interval_alerts if a.attack_type == "DoS Hulk")
            port_count = sum(1 for a in interval_alerts if a.attack_type == "PortScan")
            ddos_count = sum(1 for a in interval_alerts if a.attack_type == "DDoS")

            # Count by severity
            critical = sum(1 for a in interval_alerts if a.severity == "critical")
            low = sum(1 for a in interval_alerts if a.severity == "low")

            timeline_data.append({
                "time": current_time.isoformat(),
                "total": len(interval_alerts),
                "attack_types": {
                    "DoS Hulk": dos_count,
                    "PortScan": port_count,
                    "DDoS": ddos_count
                },
                "severity": {
                    "critical": critical,
                    "low": low
                }
            })

            current_time = interval_end

        # Get summary statistics
        total_in_period = len(alerts)
        critical_in_period = sum(1 for a in alerts if a.severity == "critical")

        return {
            "period": period,
            "start_time": start_time.isoformat(),
            "end_time": now.isoformat(),
            "interval_minutes": interval_minutes,
            "summary": {
                "total_alerts": total_in_period,
                "critical_alerts": critical_in_period,
                "low_alerts": total_in_period - critical_in_period
            },
            "timeline": timeline_data
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timeline statistics: {str(e)}"
        )