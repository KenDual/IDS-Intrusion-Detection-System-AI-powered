"""
Whitelist Model - Stores whitelisted IP addresses
"""

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Whitelist(Base):
    __tablename__ = "whitelist"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # IP Information
    ip_address = Column(String(45), nullable=False, unique=True, index=True, comment="Whitelisted IP address")
    description = Column(Text, nullable=False, comment="Reason for whitelisting")

    # Metadata
    added_at = Column(DateTime, nullable=False, server_default=func.now(),
                      comment="Time when IP was added to whitelist")

    def __repr__(self):
        return f"<Whitelist(id={self.id}, ip={self.ip_address})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'ip_address': self.ip_address,
            'description': self.description,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }