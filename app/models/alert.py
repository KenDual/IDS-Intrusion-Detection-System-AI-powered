"""
Alert Model - Stores detected attack alerts
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Alert Information
    timestamp = Column(DateTime, nullable=False, index=True, comment="Time when alert was detected")
    source_ip = Column(String(45), nullable=False, index=True, comment="Source IP address (attacker)")
    dest_ip = Column(String(45), nullable=False, comment="Destination IP address (victim)")

    # Attack Details
    attack_type = Column(String(50), nullable=False, index=True, comment="Attack type: DoS Hulk, PortScan, DDoS")
    confidence = Column(Float, nullable=False, comment="Model confidence score (0-1)")
    severity = Column(String(20), nullable=False, comment="Severity level: low or critical")

    # Metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment="Record creation time")

    # Composite indexes for common queries
    __table_args__ = (
        Index('idx_timestamp_attack_type', 'timestamp', 'attack_type'),
        Index('idx_source_ip_timestamp', 'source_ip', 'timestamp'),
        Index('idx_severity_timestamp', 'severity', 'timestamp'),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, type={self.attack_type}, src={self.source_ip}, confidence={self.confidence:.2f})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source_ip': self.source_ip,
            'dest_ip': self.dest_ip,
            'attack_type': self.attack_type,
            'confidence': self.confidence,
            'severity': self.severity,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }