"""Pydantic schemas for the health check endpoint."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response body for GET /health."""

    status: str = Field(..., examples=["ok"])
    database: str = Field(..., examples=["ok"])
