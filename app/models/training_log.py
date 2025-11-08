"""
TrainingLog Model - Stores model training history
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class TrainingLog(Base):
    __tablename__ = "training_logs"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Model Information
    model_version = Column(String(50), nullable=False, comment="Model version (e.g., v1.0.0)")

    # Performance Metrics
    accuracy = Column(Float, nullable=False, comment="Model accuracy score")
    f1_score = Column(Float, nullable=False, comment="Model F1-score")

    # Metadata
    trained_at = Column(DateTime, nullable=False, server_default=func.now(), index=True,
                        comment="Training completion time")
    notes = Column(Text, nullable=True, comment="Additional notes about training")

    def __repr__(self):
        return f"<TrainingLog(id={self.id}, version={self.model_version}, accuracy={self.accuracy:.4f}, f1={self.f1_score:.4f})>"

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'model_version': self.model_version,
            'accuracy': self.accuracy,
            'f1_score': self.f1_score,
            'trained_at': self.trained_at.isoformat() if self.trained_at else None,
            'notes': self.notes
        }