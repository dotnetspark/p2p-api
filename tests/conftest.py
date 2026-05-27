from __future__ import annotations

import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.core.settings import get_settings
from src.main import app
from src.persistence.database import Base, get_engine, get_session_factory
import src.persistence.model_registry  # noqa: F401
from src.persistence.seed.bootstrap import seed_initial_data


TEST_DB_PATH = "./p2p_test.db"


@pytest.fixture(autouse=True)
def configure_test_database() -> Iterator[None]:
    os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"
    os.environ["SEED_ON_STARTUP"] = "true"
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = get_session_factory()()
    try:
        seed_initial_data(session)
    finally:
        session.close()
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
