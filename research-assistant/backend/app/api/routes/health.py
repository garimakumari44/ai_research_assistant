from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.schemas.health import (
    HealthResponse,
    ComponentHealthResponse,
)

from app.services.health_service import HealthService


router = APIRouter(
    prefix="/health",
    tags=["Health"]
)


@router.get(
    "",
    response_model=HealthResponse
)
async def health_check():

    return HealthResponse(
        status="healthy",
        service="AI Research Assistant",
        version="1.0.0",
        timestamp=datetime.utcnow()
    )



@router.get(
    "/database",
    response_model=ComponentHealthResponse
)
async def database_health():

    is_healthy = await HealthService.check_database()


    if not is_healthy:

        raise HTTPException(
            status_code=503,
            detail="Database unavailable"
        )


    return ComponentHealthResponse(
        status="healthy",
        component="database",
        message="Database connection successful"
    )



@router.get(
    "/redis",
    response_model=ComponentHealthResponse
)
async def redis_health():

    is_healthy = await HealthService.check_redis()


    if not is_healthy:

        raise HTTPException(
            status_code=503,
            detail="Redis unavailable"
        )


    return ComponentHealthResponse(
        status="healthy",
        component="redis",
        message="Redis connection successful"
    )