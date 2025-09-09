"""
Health check routes
"""

from fastapi import APIRouter, Request
from typing import Dict, Any

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "cqrs-api"
    }


@router.get("/api/cqrs/status")
async def cqrs_status(request: Request):
    """Get CQRS service status"""
    cqrs_service = request.app.state.cqrs_service
    status = await cqrs_service.get_service_status()
    return status
