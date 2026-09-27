"""Settings loaded from environment variables."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

_TRUTHY = {"true", "1", "yes"}
_COUNTRY = re.compile(r"[A-Z]{2}")


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    email: str
    password: str = field(repr=False)
    country: str
    langfuse_enabled: bool
    langfuse_capture_data: bool


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    """Build Settings from `env` (defaults to os.environ). Raises ConfigError."""
    env = os.environ if env is None else env

    email = env.get("EUFYLIFE_EMAIL", "").strip()
    password = env.get("EUFYLIFE_PASSWORD", "")
    missing = [
        name
        for name, value in (("EUFYLIFE_EMAIL", email), ("EUFYLIFE_PASSWORD", password))
        if not value
    ]
    if missing:
        raise ConfigError(f"Missing required environment variable(s): {', '.join(missing)}")

    raw_country = env.get("EUFYLIFE_COUNTRY", "").strip()
    country = raw_country.upper() or "US"
    if not _COUNTRY.fullmatch(country):
        raise ConfigError(
            f"Invalid EUFYLIFE_COUNTRY {raw_country!r}. Use a two-letter code such as US or GB."
        )

    langfuse_enabled = bool(
        env.get("LANGFUSE_PUBLIC_KEY", "").strip() and env.get("LANGFUSE_SECRET_KEY", "").strip()
    )
    capture = env.get("LANGFUSE_CAPTURE_DATA", "").strip().lower() in _TRUTHY

    return Settings(
        email=email,
        password=password,
        country=country,
        langfuse_enabled=langfuse_enabled,
        langfuse_capture_data=capture,
    )
