from __future__ import annotations

import uuid
from typing import Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


CORRELATION_HEADER = "X-Correlation-ID"


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        correlation_id = request.headers.get(CORRELATION_HEADER, str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers[CORRELATION_HEADER] = correlation_id
        return response


def get_correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")
