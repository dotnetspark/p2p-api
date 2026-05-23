from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    app_name: str = "p2p-api"
    database_url: str = "sqlite:///./vendor_management.db"
    echo_sql: bool = False
    seed_on_startup: bool = True


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", Settings.database_url)
    echo_sql = os.getenv("ECHO_SQL", "false").lower() == "true"
    seed_on_startup = os.getenv("SEED_ON_STARTUP", "true").lower() != "false"
    return Settings(
        database_url=database_url,
        echo_sql=echo_sql,
        seed_on_startup=seed_on_startup,
    )
