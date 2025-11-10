"""
Model Information Endpoints
ML model metadata and training metrics
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
import json
from pathlib import Path

from app.dependencies import get_detection_service
from app.detection.detection_service import DetectionService
from app.config import MODELS_DIR, REPORTS_DIR

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/info")
async def get_model_info(
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Get ML model information and metadata

    Returns:
        JSON with model information:
        - Model version
        - Number of features
        - Supported attack classes
        - Training date
        - Model accuracy
    """
    try:
        # Get model info from ModelLoader
        if detection_service.model_loader is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Model not loaded"
            )

        model_info = detection_service.model_loader.get_model_info()

        # Add additional system info
        response = {
            "model": {
                "version": model_info.get("version", "1.0.0"),
                "algorithm": "XGBoost",
                "features_count": model_info.get("n_features", 25),
                "classes": model_info.get("classes", []),
                "classes_count": model_info.get("n_classes", 4)
            },
            "performance": {
                "accuracy": model_info.get("accuracy"),
                "f1_score": model_info.get("f1_score")
            },
            "training": {
                "trained_at": model_info.get("trained_at", "Unknown"),
                "dataset": "CICIDS2017",
                "samples_trained": model_info.get("samples_trained", "Unknown")
            },
            "configuration": {
                "alert_threshold": detection_service.alert_threshold,
                "deduplication_window": 60  # seconds
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model info: {str(e)}"
        )


@router.get("/metrics")
async def get_model_metrics() -> Dict[str, Any]:
    """
    Get detailed training metrics

    Returns:
        JSON with detailed training metrics:
        - Accuracy, Precision, Recall, F1-score
        - Per-class performance
        - Confusion matrix
        - Training history
    """
    try:
        # Path to training metrics file
        metrics_file = REPORTS_DIR / "training_metrics.json"

        if not metrics_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training metrics file not found at {metrics_file}"
            )

        # Load metrics from file
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)

        return metrics

    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse metrics file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse training metrics file"
        )
    except Exception as e:
        logger.error(f"Failed to get model metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model metrics: {str(e)}"
        )


@router.get("/status")
async def get_model_status(
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Get current model status and usage statistics

    Returns:
        JSON with model status and runtime statistics
    """
    try:
        # Get detection statistics
        stats = detection_service.get_statistics()

        # Model loaded status
        model_loaded = detection_service.model_loader is not None

        response = {
            "model_loaded": model_loaded,
            "detection_active": detection_service.is_running(),
            "statistics": {
                "total_predictions": stats.get("total_predictions", 0),
                "alerts_created": stats.get("alerts_created", 0),
                "benign_filtered": stats.get("benign_filtered", 0),
                "duplicates_blocked": stats.get("duplicates_blocked", 0),
                "whitelist_skipped": stats.get("whitelist_skipped", 0),
                "low_confidence_skipped": stats.get("low_confidence_skipped", 0)
            },
            "attacks_detected": stats.get("attacks_by_type", {}),
            "cache_performance": stats.get("cache_stats", {})
        }

        return response

    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get model status: {str(e)}"
        )