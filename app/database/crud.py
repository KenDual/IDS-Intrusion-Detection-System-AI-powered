"""
CRUD Operations for IDS Database
Helper functions for database operations
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from app.models import Alert, TrainingLog, Whitelist, Blacklist, SystemConfig


# ============================================================
# ALERTS CRUD OPERATIONS
# ============================================================

def create_alert(
        db: Session,
        timestamp: datetime,
        source_ip: str,
        dest_ip: str,
        attack_type: str,
        confidence: float,
        severity: str
) -> Alert:
    """
    Create a new alert

    Args:
        db: Database session
        timestamp: Alert detection time
        source_ip: Source IP address (attacker)
        dest_ip: Destination IP address (victim)
        attack_type: Attack type (DoS Hulk, PortScan, DDoS)
        confidence: Model confidence (0-1)
        severity: Severity level (low, critical)

    Returns:
        Alert: Created alert object
    """
    alert = Alert(
        timestamp=timestamp,
        source_ip=source_ip,
        dest_ip=dest_ip,
        attack_type=attack_type,
        confidence=confidence,
        severity=severity
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


def get_alert_by_id(db: Session, alert_id: int) -> Optional[Alert]:
    """
    Get alert by ID

    Args:
        db: Database session
        alert_id: Alert ID

    Returns:
        Alert or None if not found
    """
    return db.query(Alert).filter(Alert.id == alert_id).first()


def get_alerts(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        attack_type: Optional[str] = None,
        severity: Optional[str] = None,
        source_ip: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
) -> List[Alert]:
    """
    Get alerts with pagination and filters

    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        attack_type: Filter by attack type
        severity: Filter by severity
        source_ip: Filter by source IP
        start_date: Filter alerts after this date
        end_date: Filter alerts before this date

    Returns:
        List of alerts
    """
    query = db.query(Alert)

    # Apply filters
    if attack_type:
        query = query.filter(Alert.attack_type == attack_type)

    if severity:
        query = query.filter(Alert.severity == severity)

    if source_ip:
        query = query.filter(Alert.source_ip == source_ip)

    if start_date:
        query = query.filter(Alert.timestamp >= start_date)

    if end_date:
        query = query.filter(Alert.timestamp <= end_date)

    # Order by timestamp descending (newest first)
    query = query.order_by(desc(Alert.timestamp))

    # Pagination
    return query.offset(skip).limit(limit).all()


def get_recent_alerts(db: Session, limit: int = 10) -> List[Alert]:
    """
    Get most recent alerts

    Args:
        db: Database session
        limit: Number of alerts to return

    Returns:
        List of recent alerts
    """
    return db.query(Alert).order_by(desc(Alert.timestamp)).limit(limit).all()


def get_alerts_by_ip(db: Session, source_ip: str, limit: int = 100) -> List[Alert]:
    """
    Get all alerts from a specific source IP

    Args:
        db: Database session
        source_ip: Source IP address to filter
        limit: Maximum number of records

    Returns:
        List of alerts from the source IP
    """
    return db.query(Alert).filter(Alert.source_ip == source_ip).order_by(desc(Alert.timestamp)).limit(limit).all()


def delete_alert(db: Session, alert_id: int) -> bool:
    """
    Delete an alert by ID

    Args:
        db: Database session
        alert_id: Alert ID to delete

    Returns:
        True if deleted, False if not found
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        db.delete(alert)
        db.commit()
        return True
    return False


def count_alerts(
        db: Session,
        attack_type: Optional[str] = None,
        severity: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
) -> int:
    """
    Count total alerts with optional filters

    Args:
        db: Database session
        attack_type: Filter by attack type
        severity: Filter by severity
        start_date: Filter alerts after this date
        end_date: Filter alerts before this date

    Returns:
        Total count of alerts
    """
    query = db.query(Alert)

    if attack_type:
        query = query.filter(Alert.attack_type == attack_type)

    if severity:
        query = query.filter(Alert.severity == severity)

    if start_date:
        query = query.filter(Alert.timestamp >= start_date)

    if end_date:
        query = query.filter(Alert.timestamp <= end_date)

    return query.count()


def get_alert_statistics(db: Session, hours: int = 24) -> Dict[str, Any]:
    """
    Get alert statistics for the last N hours

    Args:
        db: Database session
        hours: Number of hours to look back

    Returns:
        Dictionary with statistics
    """
    since = datetime.now() - timedelta(hours=hours)

    total = db.query(Alert).filter(Alert.timestamp >= since).count()
    critical = db.query(Alert).filter(Alert.timestamp >= since, Alert.severity == "critical").count()

    # Count by attack type
    dos_hulk = db.query(Alert).filter(Alert.timestamp >= since, Alert.attack_type == "DoS Hulk").count()
    portscan = db.query(Alert).filter(Alert.timestamp >= since, Alert.attack_type == "PortScan").count()
    ddos = db.query(Alert).filter(Alert.timestamp >= since, Alert.attack_type == "DDoS").count()

    return {
        "total_alerts": total,
        "critical_alerts": critical,
        "low_alerts": total - critical,
        "attack_types": {
            "DoS Hulk": dos_hulk,
            "PortScan": portscan,
            "DDoS": ddos
        },
        "time_period_hours": hours
    }


# ============================================================
# WHITELIST CRUD OPERATIONS
# ============================================================

def add_to_whitelist(db: Session, ip_address: str, description: str) -> Optional[Whitelist]:
    """
    Add IP to whitelist

    Args:
        db: Database session
        ip_address: IP address to whitelist
        description: Reason for whitelisting

    Returns:
        Whitelist object or None if IP already exists
    """
    # Check if already exists
    existing = db.query(Whitelist).filter(Whitelist.ip_address == ip_address).first()
    if existing:
        return None

    whitelist = Whitelist(
        ip_address=ip_address,
        description=description
    )
    db.add(whitelist)
    db.commit()
    db.refresh(whitelist)
    return whitelist


def remove_from_whitelist(db: Session, ip_address: str) -> bool:
    """
    Remove IP from whitelist

    Args:
        db: Database session
        ip_address: IP address to remove

    Returns:
        True if removed, False if not found
    """
    whitelist = db.query(Whitelist).filter(Whitelist.ip_address == ip_address).first()
    if whitelist:
        db.delete(whitelist)
        db.commit()
        return True
    return False


def is_whitelisted(db: Session, ip_address: str) -> bool:
    """
    Check if IP is whitelisted

    Args:
        db: Database session
        ip_address: IP address to check

    Returns:
        True if whitelisted, False otherwise
    """
    return db.query(Whitelist).filter(Whitelist.ip_address == ip_address).first() is not None


def get_all_whitelist(db: Session) -> List[Whitelist]:
    """
    Get all whitelisted IPs

    Args:
        db: Database session

    Returns:
        List of whitelist entries
    """
    return db.query(Whitelist).order_by(desc(Whitelist.added_at)).all()


# ============================================================
# BLACKLIST CRUD OPERATIONS
# ============================================================

def add_to_blacklist(db: Session, ip_address: str, description: str) -> Optional[Blacklist]:
    """
    Add IP to blacklist

    Args:
        db: Database session
        ip_address: IP address to blacklist
        description: Reason for blacklisting

    Returns:
        Blacklist object or None if IP already exists
    """
    # Check if already exists
    existing = db.query(Blacklist).filter(Blacklist.ip_address == ip_address).first()
    if existing:
        return None

    blacklist = Blacklist(
        ip_address=ip_address,
        description=description
    )
    db.add(blacklist)
    db.commit()
    db.refresh(blacklist)
    return blacklist


def remove_from_blacklist(db: Session, ip_address: str) -> bool:
    """
    Remove IP from blacklist

    Args:
        db: Database session
        ip_address: IP address to remove

    Returns:
        True if removed, False if not found
    """
    blacklist = db.query(Blacklist).filter(Blacklist.ip_address == ip_address).first()
    if blacklist:
        db.delete(blacklist)
        db.commit()
        return True
    return False


def is_blacklisted(db: Session, ip_address: str) -> bool:
    """
    Check if IP is blacklisted

    Args:
        db: Database session
        ip_address: IP address to check

    Returns:
        True if blacklisted, False otherwise
    """
    return db.query(Blacklist).filter(Blacklist.ip_address == ip_address).first() is not None


def get_all_blacklist(db: Session) -> List[Blacklist]:
    """
    Get all blacklisted IPs

    Args:
        db: Database session

    Returns:
        List of blacklist entries
    """
    return db.query(Blacklist).order_by(desc(Blacklist.added_at)).all()


# ============================================================
# TRAINING LOG CRUD OPERATIONS
# ============================================================

def create_training_log(
        db: Session,
        model_version: str,
        accuracy: float,
        f1_score: float,
        notes: Optional[str] = None
) -> TrainingLog:
    """
    Create a new training log entry

    Args:
        db: Database session
        model_version: Model version string
        accuracy: Model accuracy
        f1_score: Model F1-score
        notes: Additional notes

    Returns:
        TrainingLog object
    """
    log = TrainingLog(
        model_version=model_version,
        accuracy=accuracy,
        f1_score=f1_score,
        notes=notes
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_latest_training_log(db: Session) -> Optional[TrainingLog]:
    """
    Get the most recent training log

    Args:
        db: Database session

    Returns:
        Latest TrainingLog or None
    """
    return db.query(TrainingLog).order_by(desc(TrainingLog.trained_at)).first()


def get_all_training_logs(db: Session, limit: int = 50) -> List[TrainingLog]:
    """
    Get all training logs

    Args:
        db: Database session
        limit: Maximum number of records

    Returns:
        List of training logs
    """
    return db.query(TrainingLog).order_by(desc(TrainingLog.trained_at)).limit(limit).all()


# ============================================================
# SYSTEM CONFIG CRUD OPERATIONS
# ============================================================

def set_config(db: Session, key: str, value: str) -> SystemConfig:
    """
    Set or update a configuration value

    Args:
        db: Database session
        key: Configuration key
        value: Configuration value

    Returns:
        SystemConfig object
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()

    if config:
        # Update existing
        config.value = value
        config.updated_at = datetime.now()
    else:
        # Create new
        config = SystemConfig(key=key, value=value)
        db.add(config)

    db.commit()
    db.refresh(config)
    return config


def get_config(db: Session, key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a configuration value

    Args:
        db: Database session
        key: Configuration key
        default: Default value if key not found

    Returns:
        Configuration value or default
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else default


def get_all_configs(db: Session) -> List[SystemConfig]:
    """
    Get all configuration entries

    Args:
        db: Database session

    Returns:
        List of all configurations
    """
    return db.query(SystemConfig).order_by(SystemConfig.key).all()


def delete_config(db: Session, key: str) -> bool:
    """
    Delete a configuration entry

    Args:
        db: Database session
        key: Configuration key to delete

    Returns:
        True if deleted, False if not found
    """
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        db.delete(config)
        db.commit()
        return True
    return False