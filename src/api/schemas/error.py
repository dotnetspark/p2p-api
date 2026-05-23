from __future__ import annotations

from pydantic import Field

from src.api.schemas.common import APIModel


class ErrorDetails(APIModel):
    code: str
    category: str
    retryable: bool
    message: str
    correlation_id: str = Field(alias="correlation_id")


class ErrorResponse(APIModel):
    error: ErrorDetails
