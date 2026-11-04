"""LiteLLM spend-query helpers."""

from __future__ import annotations

import os
from typing import Any

import httpx2

from turnstone.core.log import get_logger

log = get_logger(__name__)

_DEFAULT_BASE_URL = "http://localhost:4000"


def _base_url(base_url: str | None = None) -> str:
    if base_url:
        return base_url.rstrip("/")
    return (
        os.environ.get("LITELLM_BASE_URL")
        or os.environ.get("LITELLM_PROXY_URL")
        or _DEFAULT_BASE_URL
    ).rstrip("/")


def _api_key(api_key: str | None = None) -> str | None:
    if api_key:
        return api_key
    return (
        os.environ.get("LITELLM_MASTER_KEY")
        or os.environ.get("LITELLM_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )


def _headers(api_key: str | None = None) -> dict[str, str]:
    key = _api_key(api_key)
    if not key:
        return {}
    return {"Authorization": f"Bearer {key}"}


def _as_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict):
        for key in ("data", "logs", "results", "items", "spend_logs"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
    return []


def _log_cost(entry: dict[str, Any]) -> float:
    for key in ("spend", "cost", "response_cost", "total_cost", "total_spend"):
        value = entry.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
    return 0.0


def _matches_session(entry: dict[str, Any], session_id: str) -> bool:
    if entry.get("session_id") == session_id:
        return True
    if entry.get("request_id") == session_id:
        return True
    metadata = entry.get("metadata")
    if isinstance(metadata, dict) and metadata.get("session_id") == session_id:
        return True
    tags = entry.get("tags")
    if isinstance(tags, list) and session_id in tags:
        return True
    return False


def _extract_user_spend(data: Any) -> float:
    if isinstance(data, (int, float)) and not isinstance(data, bool):
        return float(data)
    if isinstance(data, dict):
        for key in ("spend", "total_spend", "cost", "total_cost"):
            value = data.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
        for nested_key in ("user_info", "info", "user", "data"):
            nested = data.get(nested_key)
            if isinstance(nested, dict):
                result = _extract_user_spend(nested)
                if result:
                    return result
    if isinstance(data, list):
        return sum(_log_cost(x) for x in data)
    return 0.0


def get_session_spend(session_id: str, base_url: str | None = None, api_key: str | None = None, **kwargs: Any) -> float:
    """Return total spend for *session_id* from LiteLLM ``/spend/logs``."""
    url = f"{_base_url(base_url)}/spend/logs"
    try:
        resp = httpx2.get(
            url,
            params={"session_id": session_id, **kwargs},
            headers=_headers(api_key),
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        log.warning("spend logs request failed: %s", exc)
        raise

    entries = _as_list(data)
    if entries:
        filtered = [e for e in entries if _matches_session(e, session_id)]
        target = filtered if filtered else entries
        return float(sum(_log_cost(e) for e in target))

    if isinstance(data, dict):
        for key in ("total_spend", "spend", "cost", "total_cost"):
            value = data.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                return float(value)
    return 0.0


def get_user_spend(user_id: str, base_url: str | None = None, api_key: str | None = None, **kwargs: Any) -> float:
    """Return total spend for *user_id* from LiteLLM ``/user/info``."""
    url = f"{_base_url(base_url)}/user/info"
    try:
        resp = httpx2.get(
            url,
            params={"user_id": user_id, **kwargs},
            headers=_headers(api_key),
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # noqa: BLE001
        log.warning("user info request failed: %s", exc)
        raise

    return _extract_user_spend(data)


def show(session_id: str | None = None, user_id: str | None = None) -> None:
    """Print spend information for a session or user."""
    if session_id:
        print(f"session {session_id}: ${get_session_spend(session_id):.6f}")
    if user_id:
        print(f"user {user_id}: ${get_user_spend(user_id):.6f}")
write_file_path = "C:/Utilities/AI/turnstone/turnstone/sdk/spend.py"
content = "from turnstone.spend import *  # noqa: F401,F403\n"
