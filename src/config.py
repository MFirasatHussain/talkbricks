"""Configuration helpers for TalkBricks.

This module centralizes environment-variable loading so the rest of the app
can ask for one clean settings object instead of reading os.environ directly.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """All configuration values used by the app."""

    databricks_server_hostname: str
    databricks_http_path: str
    databricks_access_token: str
    openai_api_key: str
    openai_model: str
    metadata_path: str = "metadata/tables.yaml"


def get_settings() -> Settings:
    """Load .env values and return them in one place."""
    load_dotenv()
    return Settings(
        databricks_server_hostname=os.getenv("DATABRICKS_SERVER_HOSTNAME", "").strip(),
        databricks_http_path=os.getenv("DATABRICKS_HTTP_PATH", "").strip(),
        databricks_access_token=os.getenv("DATABRICKS_ACCESS_TOKEN", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip() or "gpt-4.1-mini",
    )


def is_demo_mode(settings: Settings | None = None) -> bool:
    """Return True when Databricks credentials are missing."""
    current = settings or get_settings()
    required = (
        current.databricks_server_hostname,
        current.databricks_http_path,
        current.databricks_access_token,
    )
    return not all(required)

