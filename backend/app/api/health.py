"""Health check endpoint.

Used by Docker healthchecks, load balancers, and uptime monitors to verify
the service (and its database connection) is alive.
"""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Report service liveness and database connectivity.

    Returns HTTP 200 with `status: "ok"` when the API and its database
    connection are healthy, or `status: "degraded"` if the database is
    unreachable (the endpoint itself still returns 200 so orchestrators
    can distinguish "process is up" from "process is fully healthy").
    """
    db_status = "ok"
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001 - we want to report any failure
        logger.error("Health check database probe failed: %s", exc)
        db_status = "unreachable"

    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
    )
