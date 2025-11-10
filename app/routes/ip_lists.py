"""
IP Lists Endpoints
Whitelist and Blacklist management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from pydantic import BaseModel, field_validator
import re

from app.dependencies import get_db, get_detection_service
from app.database.crud import (
    get_all_whitelist,
    add_to_whitelist,
    remove_from_whitelist,
    get_all_blacklist,
    add_to_blacklist,
    remove_from_blacklist
)
from app.models import Whitelist, Blacklist
from app.detection.detection_service import DetectionService

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================
# REQUEST MODELS
# ============================================================

class IPAddressRequest(BaseModel):
    """Request model for adding IP to whitelist/blacklist"""
    ip_address: str
    description: str = ""

    @field_validator('ip_address')
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IP address format"""
        # Simple IPv4 validation
        ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(ipv4_pattern, v):
            raise ValueError('Invalid IP address format')

        # Check each octet is 0-255
        octets = v.split('.')
        for octet in octets:
            if int(octet) > 255:
                raise ValueError('Invalid IP address: octet > 255')

        return v


# ============================================================
# WHITELIST ENDPOINTS
# ============================================================

@router.get("/whitelist")
async def get_whitelist(
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all whitelisted IPs

    Returns:
        JSON with whitelist entries
    """
    try:
        whitelist = get_all_whitelist(db=db)
        whitelist_data = [entry.to_dict() for entry in whitelist]

        return {
            "whitelist": whitelist_data,
            "count": len(whitelist_data)
        }

    except Exception as e:
        logger.error(f"Failed to get whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get whitelist: {str(e)}"
        )


@router.post("/whitelist", status_code=status.HTTP_201_CREATED)
async def add_ip_to_whitelist(
        request: IPAddressRequest,
        db: Session = Depends(get_db),
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Add IP address to whitelist

    Request Body:
    - ip_address: IP address to whitelist (required)
    - description: Reason for whitelisting (optional)

    Returns:
        JSON with created whitelist entry
    """
    try:
        # Add to database
        whitelist_entry = add_to_whitelist(
            db=db,
            ip_address=request.ip_address,
            description=request.description
        )

        if not whitelist_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IP address {request.ip_address} is already in whitelist"
            )

        # Reload whitelist in DetectionService
        detection_service.reload_whitelist()

        logger.info(f"Added {request.ip_address} to whitelist")

        return {
            "status": "success",
            "message": f"IP {request.ip_address} added to whitelist",
            "whitelist": whitelist_entry.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to whitelist: {str(e)}"
        )


@router.delete("/whitelist/{whitelist_id}")
async def remove_ip_from_whitelist(
        whitelist_id: int,
        db: Session = Depends(get_db),
        detection_service: DetectionService = Depends(get_detection_service)
) -> Dict[str, Any]:
    """
    Remove IP address from whitelist by ID

    Path Parameters:
    - whitelist_id: Whitelist entry ID

    Returns:
        JSON with success message
    """
    try:
        # Get whitelist entry by ID
        whitelist_entry = db.query(Whitelist).filter(Whitelist.id == whitelist_id).first()

        if not whitelist_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Whitelist entry with ID {whitelist_id} not found"
            )

        ip_address = whitelist_entry.ip_address

        # Remove from database (by IP address)
        success = remove_from_whitelist(db=db, ip_address=ip_address)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove from whitelist"
            )

        # Reload whitelist in DetectionService
        detection_service.reload_whitelist()

        logger.info(f"Removed {ip_address} from whitelist")

        return {
            "status": "success",
            "message": f"IP {ip_address} removed from whitelist"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from whitelist: {str(e)}"
        )


# ============================================================
# BLACKLIST ENDPOINTS
# ============================================================

@router.get("/blacklist")
async def get_blacklist(
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get all blacklisted IPs

    Returns:
        JSON with blacklist entries
    """
    try:
        blacklist = get_all_blacklist(db=db)
        blacklist_data = [entry.to_dict() for entry in blacklist]

        return {
            "blacklist": blacklist_data,
            "count": len(blacklist_data)
        }

    except Exception as e:
        logger.error(f"Failed to get blacklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get blacklist: {str(e)}"
        )


@router.post("/blacklist", status_code=status.HTTP_201_CREATED)
async def add_ip_to_blacklist(
        request: IPAddressRequest,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Add IP address to blacklist

    Request Body:
    - ip_address: IP address to blacklist (required)
    - description: Reason for blacklisting (optional)

    Returns:
        JSON with created blacklist entry
    """
    try:
        # Add to database
        blacklist_entry = add_to_blacklist(
            db=db,
            ip_address=request.ip_address,
            description=request.description
        )

        if not blacklist_entry:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IP address {request.ip_address} is already in blacklist"
            )

        logger.info(f"Added {request.ip_address} to blacklist")

        return {
            "status": "success",
            "message": f"IP {request.ip_address} added to blacklist",
            "blacklist": blacklist_entry.to_dict()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add to blacklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add to blacklist: {str(e)}"
        )


@router.delete("/blacklist/{blacklist_id}")
async def remove_ip_from_blacklist(
        blacklist_id: int,
        db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Remove IP address from blacklist by ID

    Path Parameters:
    - blacklist_id: Blacklist entry ID

    Returns:
        JSON with success message
    """
    try:
        # Get blacklist entry by ID
        blacklist_entry = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()

        if not blacklist_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Blacklist entry with ID {blacklist_id} not found"
            )

        ip_address = blacklist_entry.ip_address

        # Remove from database (by IP address)
        success = remove_from_blacklist(db=db, ip_address=ip_address)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove from blacklist"
            )

        logger.info(f"Removed {ip_address} from blacklist")

        return {
            "status": "success",
            "message": f"IP {ip_address} removed from blacklist"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to remove from blacklist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove from blacklist: {str(e)}"
        )