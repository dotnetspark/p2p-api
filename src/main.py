from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.dependencies.error_handlers import register_error_handlers
from src.api.dependencies.request_context import CorrelationIdMiddleware
from src.core.settings import get_settings
from src.api.router import build_router
from src.persistence.database import Base, get_engine, session_scope
from src.persistence.seed.bootstrap import seed_initial_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=get_engine())
    settings = get_settings()
    if settings.seed_on_startup:
        with session_scope() as session:
            seed_initial_data(session)
    yield


app = FastAPI(title="p2p-api", lifespan=lifespan)
app.add_middleware(CorrelationIdMiddleware)
register_error_handlers(app)
app.include_router(build_router())
