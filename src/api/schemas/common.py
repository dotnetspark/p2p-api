from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)


class HealthResponse(APIModel):
    status: str


class MoneyAmount(APIModel):
    amount: Decimal = Field(..., decimal_places=2)
