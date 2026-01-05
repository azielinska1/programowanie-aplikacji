from __future__ import annotations

from dataclasses import dataclass
import os

from dotenv import load_dotenv


# On Windows it's common to have an old value set in OS env vars.
# By default python-dotenv does NOT override existing variables, which can
# lead to using a stale/invalid key even when .env is correct.
load_dotenv(override=True)


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    sqlite_path: str
    debug_tool_trace: bool


def _get_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _get_str(name: str, default: str = "") -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip()
    # Be tolerant to values copied with surrounding quotes.
    if (len(value) >= 2) and ((value[0] == value[-1]) and value[0] in {'"', "'"}):
        value = value[1:-1].strip()
    return value


def get_settings() -> Settings:
    return Settings(
        gemini_api_key=_get_str("GEMINI_API_KEY", ""),
        gemini_model=_get_str("GEMINI_MODEL", "gemini-2.5-flash"),
        sqlite_path=_get_str("SQLITE_PATH", "./app.db"),
        debug_tool_trace=_get_bool("DEBUG_TOOL_TRACE", False),
    )
