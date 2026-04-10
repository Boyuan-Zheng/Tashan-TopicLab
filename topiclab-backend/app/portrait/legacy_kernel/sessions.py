"""Adapter-backed session management for the migrated portrait legacy kernel."""

from __future__ import annotations

import os
import re
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import date
from pathlib import Path
from typing import Any, Protocol

from app.portrait.legacy_kernel.tools import load_template

_sessions: dict[str, dict[str, Any]] = {}
_runtime_adapter_var: ContextVar["LegacyKernelRuntimeAdapter | None"] = ContextVar(
    "portrait_legacy_kernel_runtime_adapter",
    default=None,
)

SESSION_TTL_SECONDS = max(60, int(os.getenv("PROFILE_HELPER_SESSION_TTL_SECONDS", "3600")))
SESSION_MAX_COUNT = max(10, int(os.getenv("PROFILE_HELPER_SESSION_MAX_COUNT", "1000")))
PLACEHOLDER_IDENTIFIERS = {"[姓名/标识]", "姓名/标识"}
PROFILE_TITLE_PREFIXES = ("# 科研人员画像 — ", "# 科研数字分身 — ")


class LegacyKernelRuntimeAdapter(Protocol):
    def load_session(self, session_id: str | None, user_id: int | str | None) -> dict[str, Any] | None: ...
    def save_session(self, session: dict[str, Any]) -> None: ...


def _now() -> float:
    return time.time()


def _current_adapter() -> LegacyKernelRuntimeAdapter | None:
    return _runtime_adapter_var.get()


@contextmanager
def use_runtime_adapter(adapter: LegacyKernelRuntimeAdapter):
    token = _runtime_adapter_var.set(adapter)
    try:
        yield
    finally:
        _runtime_adapter_var.reset(token)


def _persist(session: dict[str, Any]) -> None:
    adapter = _current_adapter()
    if adapter is not None:
        adapter.save_session(session)


def _load_template_with_date() -> str:
    today_str = date.today().strftime("%Y-%m-%d")
    return load_template().replace("YYYY-MM-DD", today_str)


def _today_unnamed() -> str:
    return f"unnamed-{date.today().strftime('%Y-%m-%d')}"


def _sanitize_identifier(identifier: str) -> str:
    cleaned = identifier.strip()
    if cleaned in PLACEHOLDER_IDENTIFIERS or not cleaned:
        return _today_unnamed()
    cleaned = re.sub(r'[\\/:*?"<>|]+', "-", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or _today_unnamed()


def _extract_profile_identifier(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        for prefix in PROFILE_TITLE_PREFIXES:
            if stripped.startswith(prefix):
                return _sanitize_identifier(stripped[len(prefix) :])
        if stripped.startswith("# "):
            return _sanitize_identifier(stripped[2:])
        break
    return _today_unnamed()


def _session_suffix(session: dict[str, Any]) -> str:
    sid = session.get("session_id") or ""
    if sid:
        return str(sid).replace("-", "")[:8]
    return uuid.uuid4().hex[:8]


def _target_profile_path(content: str, session: dict[str, Any]) -> Path:
    identifier = _extract_profile_identifier(content)
    if session.get("user_id"):
        return Path("profile.md")
    suffix = _session_suffix(session)
    return Path(f"{identifier}-{suffix}.md")


def _target_forum_profile_path(session: dict[str, Any]) -> Path:
    if session.get("user_id"):
        return Path("forum_profile.md")
    profile_path = Path(session.get("profile_path") or _target_profile_path(session.get("profile", ""), session))
    return profile_path.with_name(f"{profile_path.stem}-论坛画像.md")


def _new_session(session_id: str, user_id: int | str | None = None) -> dict[str, Any]:
    now = _now()
    return {
        "session_id": session_id,
        "user_id": user_id,
        "messages": [],
        "profile": _load_template_with_date(),
        "forum_profile": "",
        "profile_path": None,
        "forum_profile_path": None,
        "scales": {},
        "created_at": now,
        "updated_at": now,
    }


def _touch(session: dict[str, Any]) -> None:
    session["updated_at"] = _now()
    _persist(session)


def _is_expired(session: dict[str, Any], now: float) -> bool:
    updated = float(session.get("updated_at") or 0)
    return (now - updated) > SESSION_TTL_SECONDS


def _cleanup() -> None:
    now = _now()
    expired = [sid for sid, session in _sessions.items() if _is_expired(session, now)]
    for sid in expired:
        _sessions.pop(sid, None)

    overflow = len(_sessions) - SESSION_MAX_COUNT
    if overflow > 0:
        oldest = sorted(_sessions.items(), key=lambda item: float(item[1].get("updated_at") or 0))
        for sid, _session in oldest[:overflow]:
            _sessions.pop(sid, None)


def get_or_create(
    session_id: str | None = None,
    user_id: int | str | None = None,
) -> tuple[str, dict[str, Any]]:
    """Get or create session. Returns (session_id, session_data)."""
    _cleanup()
    adapter = _current_adapter()

    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        session["session_id"] = session_id
        if user_id and not session.get("user_id"):
            session["user_id"] = user_id
        session.setdefault("forum_profile", "")
        session.setdefault("profile_path", None)
        session.setdefault("forum_profile_path", None)
        session.setdefault("scales", {})
        _touch(session)
        return session_id, session

    if adapter is not None:
        loaded = adapter.load_session(session_id, user_id)
        if loaded:
            loaded.setdefault("forum_profile", "")
            loaded.setdefault("profile_path", None)
            loaded.setdefault("forum_profile_path", None)
            loaded.setdefault("scales", {})
            loaded["session_id"] = str(loaded.get("session_id") or session_id or uuid.uuid4().hex)
            if user_id and not loaded.get("user_id"):
                loaded["user_id"] = user_id
            _sessions[str(loaded["session_id"])] = loaded
            _touch(loaded)
            return str(loaded["session_id"]), loaded

    sid = session_id or f"lks_{uuid.uuid4().hex[:16]}"
    _sessions[sid] = _new_session(sid, user_id=user_id)
    _persist(_sessions[sid])
    _cleanup()
    return sid, _sessions[sid]


def save_profile(session: dict[str, Any], content: str) -> Path:
    """Persist the development profile to session memory and adapter storage."""
    target_path = _target_profile_path(content, session)
    session["profile"] = content
    session["profile_path"] = str(target_path)
    _touch(session)
    return target_path


def save_forum_profile(session: dict[str, Any], content: str) -> Path:
    """Persist the forum profile to session memory and adapter storage."""
    target_path = _target_forum_profile_path(session)
    session["forum_profile"] = content
    session["forum_profile_path"] = str(target_path)
    _touch(session)
    return target_path


def save_scales(session: dict[str, Any], scale_name: str, data: dict[str, Any]) -> None:
    """Persist scale results to session memory and adapter storage."""
    if "scales" not in session:
        session["scales"] = {}
    payload = dict(data)
    payload["completed_at"] = date.today().strftime("%Y-%m-%d")
    session["scales"][scale_name] = payload
    _touch(session)


def get(session_id: str) -> dict[str, Any] | None:
    """Get session by id, or None if not found."""
    session = _sessions.get(session_id)
    if not session:
        adapter = _current_adapter()
        if adapter is not None:
            session = adapter.load_session(session_id, None)
            if session:
                _sessions[session_id] = session
        if not session:
            return None
    if _is_expired(session, _now()):
        _sessions.pop(session_id, None)
        return None
    _touch(session)
    return session


def list_ids() -> list[str]:
    """List active session IDs."""
    _cleanup()
    return list(_sessions.keys())


def reset(session_id: str) -> dict[str, Any]:
    """Reset session: clear messages and restore template profile."""
    existing = _sessions.get(session_id) or {}
    user_id = existing.get("user_id")
    _sessions[session_id] = _new_session(session_id, user_id=user_id)
    _persist(_sessions[session_id])
    return _sessions[session_id]
