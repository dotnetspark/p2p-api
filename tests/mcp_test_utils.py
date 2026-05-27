from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from src.main import create_app


@asynccontextmanager
async def mcp_client_session() -> AsyncIterator[ClientSession]:
    app = create_app()
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://localhost:8000",
            follow_redirects=True,
        ) as http_client:
            async with streamable_http_client("http://localhost:8000/mcp/", http_client=http_client) as streams:
                read_stream, write_stream = streams[0], streams[1]
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    yield session


def is_error(result) -> bool:
    if hasattr(result, "isError"):
        return result.isError
    return result.is_error


def structured_content(result):
    if hasattr(result, "structuredContent"):
        return result.structuredContent
    return result.structured_content