from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class SystemConfig(Base):
    __tablename__ = "system_config"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Config Key-Value
    key = Column(String(100), nullable=False, unique=True, index=True, comment="Configuration key")
    value = Column(Text, nullable=False, comment="Configuration value")

    # Metadata
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(),
                        comment="Last update time")

    def __repr__(self):
        return f"<SystemConfig(key={self.key}, value={self.value})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }