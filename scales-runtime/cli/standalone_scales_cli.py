#!/usr/bin/env python3
"""Standalone CLI for TopicLab scales runtime.

This CLI intentionally lives under `scales-runtime/` instead of `TopicLab-CLI`.
It proves the full runtime loop locally before the same command surface is
migrated into the shared CLI infrastructure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import types
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "topiclab-backend"
DEFAULT_STATE_DIR = Path.home() / ".topiclab-scales-runtime"
DEFAULT_PHONE = "13800052001"
DEFAULT_USERNAME = "standalone-scales"
DEFAULT_PASSWORD = "password123"
AUTH_MODE_LOCAL = "local_password"
AUTH_MODE_BIND_KEY = "bind_key"


class CLIHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    """Readable argparse formatter with defaults + preserved line breaks."""


def _emit(payload: Any, as_json: bool) -> int:
    text_payload = json.dumps(payload, ensure_ascii=False, indent=None if as_json else 2)
    sys.stdout.write(f"{text_payload}\n")
    return 0


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _session_file(state_dir: Path) -> Path:
    return state_dir / "session.json"


def _load_state(state_dir: Path) -> dict[str, Any]:
    path = _session_file(state_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(state_dir: Path, payload: dict[str, Any]) -> None:
    _ensure_dir(state_dir)
    _session_file(state_dir).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _normalize_global_args(argv: list[str]) -> list[str]:
    normalized: list[str] = []
    i = 0
    saw_json = False
    state_dir_value: str | None = None
    while i < len(argv):
        token = argv[i]
        if token == "--json":
            saw_json = True
            i += 1
            continue
        if token == "--auth-mode":
            if i + 1 >= len(argv):
                raise SystemExit("`--auth-mode` requires a value.")
            auth_mode_value = argv[i + 1]
            i += 2
            continue
        if token == "--state-dir":
            if i + 1 >= len(argv):
                raise SystemExit("`--state-dir` requires a value.")
            state_dir_value = argv[i + 1]
            i += 2
            continue
        if token == "--base-url":
            if i + 1 >= len(argv):
                raise SystemExit("`--base-url` requires a value.")
            base_url_value = argv[i + 1]
            i += 2
            continue
        if token == "--bind-key":
            if i + 1 >= len(argv):
                raise SystemExit("`--bind-key` requires a value.")
            bind_key_value = argv[i + 1]
            i += 2
            continue
        normalized.append(token)
        i += 1
    auth_mode_value = locals().get("auth_mode_value")
    base_url_value = locals().get("base_url_value")
    bind_key_value = locals().get("bind_key_value")
    if bind_key_value is not None:
        normalized = ["--bind-key", bind_key_value, *normalized]
    if base_url_value is not None:
        normalized = ["--base-url", base_url_value, *normalized]
    if auth_mode_value is not None:
        normalized = ["--auth-mode", auth_mode_value, *normalized]
    if state_dir_value is not None:
        normalized = ["--state-dir", state_dir_value, *normalized]
    if saw_json:
        normalized = ["--json", *normalized]
    return normalized


def _install_test_shims() -> None:
    fake_moderation = types.ModuleType("app.services.content_moderation")

    class ModerationDecision:
        def __init__(self, approved: bool = True, reason: str = "", suggestion: str = "", category: str = "normal"):
            self.approved = approved
            self.reason = reason
            self.suggestion = suggestion
            self.category = category

    async def moderate_post_content(content: str, *, scenario: str):
        _ = content, scenario
        return ModerationDecision()

    fake_moderation.ModerationDecision = ModerationDecision
    fake_moderation.moderate_post_content = moderate_post_content
    sys.modules["app.services.content_moderation"] = fake_moderation

    fake_oss = types.ModuleType("app.services.oss_upload")

    def get_signed_media_url(*args, **kwargs):
        _ = args, kwargs
        return "https://example.com/fake-media"

    async def upload_comment_media_to_oss(*args, **kwargs):
        _ = args, kwargs
        return {
            "url": "https://example.com/fake-media",
            "markdown": "![fake](https://example.com/fake-media)",
            "object_key": "fake-key",
            "content_type": "image/png",
            "media_type": "image",
            "width": 1,
            "height": 1,
            "size_bytes": 1,
        }

    fake_oss.get_signed_media_url = get_signed_media_url
    fake_oss.upload_comment_media_to_oss = upload_comment_media_to_oss
    sys.modules["app.services.oss_upload"] = fake_oss


class StandaloneScaleRuntime:
    def __init__(self, state_dir: Path, transport: "BaseTransport"):
        self.state_dir = _ensure_dir(state_dir)
        self.transport = transport

    def close(self) -> None:
        self.transport.close()

    def _request(self, method: str, path: str, *, headers: dict[str, str] | None = None, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.transport.request(method, path, headers=headers, json_body=json_body)

    def _register_code(self, phone: str) -> str:
        if not isinstance(self.transport, LocalAppTransport):
            raise RuntimeError("register code injection is only supported in local harness mode")
        code = "123456"
        with self.transport.postgres_client.get_db_session() as session:
            session.execute(
                text(
                    """
                    INSERT INTO verification_codes (phone, code, type, expires_at)
                    VALUES (:phone, :code, 'register', :expires_at)
                    """
                ),
                {
                    "phone": phone,
                    "code": code,
                    "expires_at": datetime.now(timezone.utc) + timedelta(minutes=5),
                },
            )
        return code


class BaseTransport:
    def request(self, method: str, path: str, *, headers: dict[str, str] | None = None, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def request_allow_http_error(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        raise NotImplementedError

    def close(self) -> None:
        return None


class LocalAppTransport(BaseTransport):
    def __init__(self, state_dir: Path):
        self.state_dir = _ensure_dir(state_dir)
        self.db_path = self.state_dir / "scales_runtime.sqlite3"
        os.environ["TOPICLAB_TESTING"] = "1"
        os.environ["DATABASE_URL"] = f"sqlite:///{self.db_path}"
        if str(BACKEND_ROOT) not in sys.path:
            sys.path.insert(0, str(BACKEND_ROOT))
        _install_test_shims()
        import app.storage.database.postgres_client as postgres_client
        import app.api.auth as auth_router
        import app.api.scales as scales_router

        self.postgres_client = postgres_client
        self.postgres_client.reset_db_state()
        self.postgres_client.init_auth_tables()
        app = FastAPI()
        app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
        app.include_router(scales_router.router, prefix="/api/v1", tags=["scales-v1"])
        self.client = TestClient(app)
        self.client.__enter__()

    def request(self, method: str, path: str, *, headers: dict[str, str] | None = None, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        response = self.client.request(method.upper(), path, headers=headers, json=json_body)
        if response.status_code >= 400:
            _emit(
                {
                    "ok": False,
                    "status_code": response.status_code,
                    "path": path,
                    "detail": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text,
                },
                True,
            )
            raise SystemExit(1)
        return response.json()

    def request_allow_http_error(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        response = self.client.request(method.upper(), path, headers=headers, json=json_body)
        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
        return response.status_code, payload

    def close(self) -> None:
        self.client.__exit__(None, None, None)
        self.postgres_client.reset_db_state()


class RemoteHTTPTransport(BaseTransport):
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def request(self, method: str, path: str, *, headers: dict[str, str] | None = None, json_body: dict[str, Any] | None = None) -> dict[str, Any]:
        status_code, payload = self.request_allow_http_error(method, path, headers=headers, json_body=json_body)
        if status_code >= 400:
            _emit({"ok": False, "status_code": status_code, "path": path, "detail": payload}, True)
            raise SystemExit(1)
        return payload if isinstance(payload, dict) else {}

    def request_allow_http_error(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> tuple[int, Any]:
        url = f"{self.base_url}{path}"
        request_headers = {"Accept": "application/json"}
        if headers:
            request_headers.update(headers)
        data = None
        if json_body is not None:
            request_headers["Content-Type"] = "application/json"
            data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(url, data=data, headers=request_headers, method=method.upper())
        try:
            with urllib.request.urlopen(request) as response:
                raw = response.read().decode("utf-8")
                return response.status, json.loads(raw) if raw else {}
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            detail: Any
            try:
                detail = json.loads(raw) if raw else exc.reason
            except json.JSONDecodeError:
                detail = raw or str(exc.reason)
            return exc.code, detail
        except urllib.error.URLError as exc:
            _emit({"ok": False, "status_code": None, "path": path, "detail": str(exc.reason)}, True)
            raise SystemExit(1)


class BaseAuthProvider:
    auth_mode: str

    def ensure_auth(self, runtime: StandaloneScaleRuntime, state: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
        raise NotImplementedError


class LocalPasswordAuthProvider(BaseAuthProvider):
    auth_mode = AUTH_MODE_LOCAL

    def ensure_auth(self, runtime: StandaloneScaleRuntime, state: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
        phone = getattr(args, "phone", None) or state.get("phone") or DEFAULT_PHONE
        username = getattr(args, "username", None) or state.get("username") or DEFAULT_USERNAME
        password = getattr(args, "password", None) or state.get("password") or DEFAULT_PASSWORD

        if isinstance(runtime.transport, LocalAppTransport):
            login_response = runtime.transport.client.post("/auth/login", json={"phone": phone, "password": password})
            if login_response.status_code == 200:
                payload = login_response.json()
            else:
                code = runtime._register_code(phone)
                register_response = runtime.transport.client.post(
                    "/auth/register",
                    json={"phone": phone, "code": code, "password": password, "username": username},
                )
                if register_response.status_code != 200:
                    detail = register_response.json() if register_response.headers.get("content-type", "").startswith("application/json") else register_response.text
                    _emit({"ok": False, "status_code": register_response.status_code, "detail": detail}, True)
                    raise SystemExit(1)
                payload = register_response.json()
        else:
            login_status, login_payload = runtime.transport.request_allow_http_error(
                "POST",
                "/auth/login",
                json_body={"phone": phone, "password": password},
            )
            if login_status == 200:
                payload = login_payload
            else:
                register_status, register_payload = runtime.transport.request_allow_http_error(
                    "POST",
                    "/auth/register",
                    json_body={"phone": phone, "code": "", "password": password, "username": username},
                )
                if register_status >= 400 and "已注册" not in json.dumps(register_payload, ensure_ascii=False):
                    _emit({"ok": False, "status_code": register_status, "detail": register_payload}, True)
                    raise SystemExit(1)
                login_status, login_payload = runtime.transport.request_allow_http_error(
                    "POST",
                    "/auth/login",
                    json_body={"phone": phone, "password": password},
                )
                if login_status != 200:
                    _emit({"ok": False, "status_code": login_status, "detail": login_payload}, True)
                    raise SystemExit(1)
                payload = login_payload

        saved = {
            **state,
            "auth_mode": self.auth_mode,
            "base_url": getattr(args, "base_url", None) or state.get("base_url"),
            "bind_key": state.get("bind_key"),
            "phone": phone,
            "username": payload["user"].get("username") or username,
            "password": password,
            "access_token": payload["token"],
            "token_type": "Bearer",
            "user": payload["user"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_state(runtime.state_dir, saved)
        return saved


class BindKeyAuthProvider(BaseAuthProvider):
    auth_mode = AUTH_MODE_BIND_KEY

    def ensure_auth(self, runtime: StandaloneScaleRuntime, state: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
        base_url = getattr(args, "base_url", None) or state.get("base_url")
        bind_key = getattr(args, "bind_key", None) or state.get("bind_key")
        if not base_url:
            _emit({"ok": False, "detail": "bind_key auth requires --base-url or a persisted base_url", "code": "missing_base_url"}, True)
            raise SystemExit(1)
        if not bind_key:
            _emit({"ok": False, "detail": "bind_key auth requires --bind-key or a persisted bind_key", "code": "missing_bind_key"}, True)
            raise SystemExit(1)

        has_existing_token = bool(state.get("access_token"))
        if has_existing_token:
            payload = runtime.transport.request(
                "POST",
                "/api/v1/openclaw/session/renew",
                headers={"Authorization": f"Bearer {bind_key}"},
            )
        else:
            key = urllib.parse.quote(bind_key, safe="")
            payload = runtime.transport.request("GET", f"/api/v1/openclaw/bootstrap?key={key}")

        saved = {
            **state,
            "auth_mode": self.auth_mode,
            "base_url": base_url,
            "bind_key": bind_key,
            "access_token": payload["access_token"],
            "token_type": payload.get("token_type", "Bearer"),
            "agent_uid": payload.get("agent_uid"),
            "openclaw_agent": payload.get("openclaw_agent") or {},
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        _save_state(runtime.state_dir, saved)
        return saved


def _resolve_auth_mode(args: argparse.Namespace, state: dict[str, Any]) -> str:
    explicit = getattr(args, "auth_mode", "auto")
    if explicit and explicit != "auto":
        return explicit
    if getattr(args, "bind_key", None) or state.get("bind_key"):
        return AUTH_MODE_BIND_KEY
    if state.get("auth_mode") in {AUTH_MODE_LOCAL, AUTH_MODE_BIND_KEY}:
        return state["auth_mode"]
    return AUTH_MODE_LOCAL


def _build_transport(state_dir: Path, args: argparse.Namespace, auth_mode: str, state: dict[str, Any]) -> BaseTransport:
    base_url = getattr(args, "base_url", None) or state.get("base_url")
    if base_url:
        if auth_mode == AUTH_MODE_BIND_KEY and not base_url:
            _emit({"ok": False, "detail": "bind_key mode requires --base-url or a persisted base_url", "code": "missing_base_url"}, True)
            raise SystemExit(1)
        return RemoteHTTPTransport(base_url)
    return LocalAppTransport(state_dir)


def _build_auth_provider(auth_mode: str) -> BaseAuthProvider:
    if auth_mode == AUTH_MODE_BIND_KEY:
        return BindKeyAuthProvider()
    return LocalPasswordAuthProvider()


def _auth_headers_from_state(state: dict[str, Any]) -> dict[str, str]:
    token = state.get("access_token")
    if not token:
        _emit({"ok": False, "detail": "missing access_token after auth ensure", "code": "missing_access_token"}, True)
        raise SystemExit(1)
    return {"Authorization": f"Bearer {token}"}


def _load_answers_payload(raw_json: str | None, file_path: str | None) -> dict[str, float]:
    if raw_json:
        payload = json.loads(raw_json)
    elif file_path:
        payload = json.loads(Path(file_path).read_text(encoding="utf-8"))
    else:
        raise ValueError("Either --answers-json or --answers-file is required.")

    if isinstance(payload, dict) and "answers" in payload and isinstance(payload["answers"], dict):
        payload = payload["answers"]
    if not isinstance(payload, dict):
        raise ValueError("Answers payload must be a JSON object or a fixture with top-level `answers`.")
    return {str(question_id): float(value) for question_id, value in payload.items()}


def _interactive_answers(runtime: StandaloneScaleRuntime, headers: dict[str, str], session_id: str) -> dict[str, Any]:
    state = runtime._request("GET", f"/api/v1/scales/sessions/{session_id}", headers=headers)
    definition = runtime._request("GET", f"/api/v1/scales/{state['session']['scale_id']}", headers=headers)
    question_by_id = {question["id"]: question for question in definition["questions"]}

    while state["progress"]["remaining_count"] > 0:
        question_id = state["progress"]["missing_question_ids"][0]
        question = question_by_id[question_id]
        while True:
            prompt = f"[{question_id}] {question['text']} ({definition['min_val']}-{definition['max_val']}): "
            raw = input(prompt).strip()
            try:
                value = float(raw)
            except ValueError:
                print("请输入数字。", file=sys.stderr)
                continue
            if value < float(definition["min_val"]) or value > float(definition["max_val"]):
                print("超出量表范围，请重试。", file=sys.stderr)
                continue
            runtime._request(
                "POST",
                f"/api/v1/scales/sessions/{session_id}/answers",
                headers=headers,
                json_body={"question_id": question_id, "value": value},
            )
            break
        state = runtime._request("GET", f"/api/v1/scales/sessions/{session_id}", headers=headers)
    return state


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Standalone local CLI for TopicLab scales runtime.",
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py --json auth ensure\n"
            "  standalone_scales_cli.py list --json\n"
            "  standalone_scales_cli.py session start --scale rcss --json\n"
            "  standalone_scales_cli.py run --scale rcss\n"
            "  standalone_scales_cli.py --auth-mode bind_key --base-url https://world.tashan.chat --bind-key tlos_xxx list --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    parser.add_argument(
        "--state-dir",
        default=str(DEFAULT_STATE_DIR),
        help="Persistent local state directory for sqlite + auth session.",
    )
    parser.add_argument(
        "--auth-mode",
        choices=["auto", AUTH_MODE_LOCAL, AUTH_MODE_BIND_KEY],
        default="auto",
        help=(
            "Authentication mode.\n"
            "`auto` prefers bind_key when one is present in args/state."
        ),
    )
    parser.add_argument("--base-url", help="Remote TopicLab base URL for remote local_password or bind_key mode.")
    parser.add_argument("--bind-key", help="OpenClaw bind key for bind-key mode.")
    parser.add_argument("--json", action="store_true", help="Emit compact JSON instead of pretty JSON.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    auth_parser = subparsers.add_parser(
        "auth",
        help="Bootstrap or refresh the standalone local auth session.",
        description="Authentication commands for the standalone scales CLI.",
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py auth ensure --json\n"
            "  standalone_scales_cli.py --auth-mode bind_key --base-url https://world.tashan.chat --bind-key tlos_xxx auth ensure --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    auth_subparsers = auth_parser.add_subparsers(dest="auth_command", required=True)
    ensure_parser = auth_subparsers.add_parser(
        "ensure",
        help="Ensure auth state exists and save a reusable token.",
        description=(
            "Bootstrap authentication for the current auth provider.\n\n"
            "- local_password mode: logs in or registers a local or remote test user\n"
            "- bind_key mode: bootstraps or renews against OpenClaw bind-key endpoints"
        ),
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py auth ensure --phone 13800052001 --username demo --password password123 --json\n"
            "  standalone_scales_cli.py --auth-mode bind_key --base-url https://world.tashan.chat --bind-key tlos_xxx auth ensure --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    ensure_parser.add_argument("--phone", help="Phone number for local_password mode.")
    ensure_parser.add_argument("--username", help="Username for local_password mode.")
    ensure_parser.add_argument("--password", help="Password for local_password mode.")

    subparsers.add_parser(
        "list",
        help="List available scales.",
        description="List all scale definitions currently available through the runtime.",
        epilog="Example:\n  standalone_scales_cli.py list --json",
        formatter_class=CLIHelpFormatter,
    )

    get_parser = subparsers.add_parser(
        "get",
        help="Read one scale definition.",
        description="Fetch one scale definition, including questions and scoring metadata.",
        epilog="Example:\n  standalone_scales_cli.py get rcss --json",
        formatter_class=CLIHelpFormatter,
    )
    get_parser.add_argument("scale_id", help="Scale identifier, for example `rcss`, `mini-ipip`, or `ams`.")

    session_parser = subparsers.add_parser(
        "session",
        help="Session lifecycle commands.",
        description="Create and inspect scale sessions without mutating result state.",
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py session start --scale rcss --json\n"
            "  standalone_scales_cli.py session status scs_123 --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    session_subparsers = session_parser.add_subparsers(dest="session_command", required=True)
    start_parser = session_subparsers.add_parser(
        "start",
        help="Create a new scale session.",
        description="Create a new answer session for one scale.",
        epilog="Example:\n  standalone_scales_cli.py session start --scale rcss --actor-type internal --actor-id self-check --json",
        formatter_class=CLIHelpFormatter,
    )
    start_parser.add_argument("--scale", required=True, help="Scale identifier to start.")
    start_parser.add_argument("--actor-type", default="human", choices=["human", "agent", "internal"], help="Declared caller type.")
    start_parser.add_argument("--actor-id", help="Optional caller identifier written into session metadata.")

    status_parser = session_subparsers.add_parser(
        "status",
        help="Read current session state.",
        description="Read current progress, next question, and allowed actions for one session.",
        epilog="Example:\n  standalone_scales_cli.py session status scs_123 --json",
        formatter_class=CLIHelpFormatter,
    )
    status_parser.add_argument("session_id", help="Scale session id.")

    answer_parser = subparsers.add_parser(
        "answer",
        help="Submit one answer.",
        description="Write one answer into an existing session.",
        epilog="Example:\n  standalone_scales_cli.py answer scs_123 --question-id A1 --value 6 --json",
        formatter_class=CLIHelpFormatter,
    )
    answer_parser.add_argument("session_id", help="Scale session id.")
    answer_parser.add_argument("--question-id", required=True, help="Question identifier within the selected scale.")
    answer_parser.add_argument("--value", required=True, type=float, help="Numeric answer value within the scale range.")

    batch_parser = subparsers.add_parser(
        "answer-batch",
        help="Submit multiple answers.",
        description="Write multiple answers into an existing session from inline JSON or a file.",
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py answer-batch scs_123 --answers-json '{\"A1\":6,\"A2\":5}' --json\n"
            "  standalone_scales_cli.py answer-batch scs_123 --answers-file ./answers.json --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    batch_parser.add_argument("session_id", help="Scale session id.")
    batch_parser.add_argument("--answers-json", help="Inline JSON object like '{\"A1\":6,\"A2\":5}'.")
    batch_parser.add_argument("--answers-file", help="Path to a JSON file. Can be either a plain answer object or a fixture with top-level `answers`.")

    finalize_parser = subparsers.add_parser(
        "finalize",
        help="Finalize a completed session.",
        description="Finalize scoring for a session after all required answers are present.",
        epilog="Example:\n  standalone_scales_cli.py finalize scs_123 --json",
        formatter_class=CLIHelpFormatter,
    )
    finalize_parser.add_argument("session_id", help="Scale session id.")

    result_parser = subparsers.add_parser(
        "result",
        help="Fetch a finalized result.",
        description="Read the persisted result object for one completed session.",
        epilog="Example:\n  standalone_scales_cli.py result scs_123 --json",
        formatter_class=CLIHelpFormatter,
    )
    result_parser.add_argument("session_id", help="Scale session id.")

    sessions_parser = subparsers.add_parser(
        "sessions",
        help="List or abandon sessions.",
        description="Inspect historical sessions or explicitly abandon one in-progress session.",
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py sessions list --json\n"
            "  standalone_scales_cli.py sessions abandon scs_123 --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    sessions_subparsers = sessions_parser.add_subparsers(dest="sessions_command", required=True)
    sessions_subparsers.add_parser(
        "list",
        help="List all sessions for the current auth user.",
        description="List historical sessions visible to the current auth user.",
        epilog="Example:\n  standalone_scales_cli.py sessions list --json",
        formatter_class=CLIHelpFormatter,
    )
    abandon_parser = sessions_subparsers.add_parser(
        "abandon",
        help="Abandon a session.",
        description="Mark one not-yet-completed session as abandoned.",
        epilog="Example:\n  standalone_scales_cli.py sessions abandon scs_123 --json",
        formatter_class=CLIHelpFormatter,
    )
    abandon_parser.add_argument("session_id", help="Scale session id.")

    run_parser = subparsers.add_parser(
        "run",
        help="Run one full questionnaire loop, interactively or from an answers file.",
        description=(
            "Create or resume a session, collect answers, finalize it, and return the result.\n\n"
            "- without answers input: prompts interactively in the terminal\n"
            "- with --answers-json / --answers-file: writes the provided answers directly"
        ),
        epilog=(
            "Examples:\n"
            "  standalone_scales_cli.py run --scale rcss\n"
            "  standalone_scales_cli.py run --scale rcss --answers-file ./fixtures/rcss-strong-integration.json --json\n"
            "  standalone_scales_cli.py run --scale mini-ipip --answers-json '{\"E1\":5}' --session-id scs_123 --json"
        ),
        formatter_class=CLIHelpFormatter,
    )
    run_parser.add_argument("--scale", required=True, help="Scale identifier to run.")
    run_parser.add_argument("--actor-type", default="human", choices=["human", "agent", "internal"], help="Declared caller type.")
    run_parser.add_argument("--actor-id", help="Optional caller identifier written into session metadata.")
    run_parser.add_argument("--answers-json", help="Inline JSON answer object.")
    run_parser.add_argument("--answers-file", help="Path to a JSON file containing answers or a fixture object.")
    run_parser.add_argument("--session-id", help="Resume an existing session instead of creating a new one.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    args = parser.parse_args(_normalize_global_args(raw_argv))
    state_dir = Path(args.state_dir).expanduser().resolve()
    state = _load_state(state_dir)
    auth_mode = _resolve_auth_mode(args, state)
    transport = _build_transport(state_dir, args, auth_mode, state)
    runtime = StandaloneScaleRuntime(state_dir, transport)
    try:
        provider = _build_auth_provider(auth_mode)
        authed_state = provider.ensure_auth(runtime, _load_state(state_dir), args)
        headers = _auth_headers_from_state(authed_state)

        if args.command == "auth" and args.auth_command == "ensure":
            payload = {"ok": True, "auth": authed_state, "state_dir": str(state_dir)}
            return _emit(payload, args.json)

        if args.command == "list":
            return _emit(runtime._request("GET", "/api/v1/scales", headers=headers), args.json)

        if args.command == "get":
            return _emit(runtime._request("GET", f"/api/v1/scales/{args.scale_id}", headers=headers), args.json)

        if args.command == "session":
            if args.session_command == "start":
                payload = runtime._request(
                    "POST",
                    "/api/v1/scales/sessions",
                    headers=headers,
                    json_body={"scale_id": args.scale, "actor_type": args.actor_type, "actor_id": args.actor_id},
                )
                state = _load_state(state_dir)
                state["last_session_id"] = payload["session"]["session_id"]
                _save_state(state_dir, state)
                return _emit(payload, args.json)
            if args.session_command == "status":
                return _emit(runtime._request("GET", f"/api/v1/scales/sessions/{args.session_id}", headers=headers), args.json)

        if args.command == "answer":
            payload = runtime._request(
                "POST",
                f"/api/v1/scales/sessions/{args.session_id}/answers",
                headers=headers,
                json_body={"question_id": args.question_id, "value": args.value},
            )
            return _emit(payload, args.json)

        if args.command == "answer-batch":
            answers = _load_answers_payload(args.answers_json, args.answers_file)
            payload = runtime._request(
                "POST",
                f"/api/v1/scales/sessions/{args.session_id}/answer-batch",
                headers=headers,
                json_body={"answers": answers},
            )
            return _emit(payload, args.json)

        if args.command == "finalize":
            return _emit(runtime._request("POST", f"/api/v1/scales/sessions/{args.session_id}/finalize", headers=headers), args.json)

        if args.command == "result":
            return _emit(runtime._request("GET", f"/api/v1/scales/sessions/{args.session_id}/result", headers=headers), args.json)

        if args.command == "sessions":
            if args.sessions_command == "list":
                return _emit(runtime._request("GET", "/api/v1/scales/sessions", headers=headers), args.json)
            if args.sessions_command == "abandon":
                return _emit(runtime._request("POST", f"/api/v1/scales/sessions/{args.session_id}/abandon", headers=headers), args.json)

        if args.command == "run":
            if args.session_id:
                session_id = args.session_id
            else:
                start_payload = runtime._request(
                    "POST",
                    "/api/v1/scales/sessions",
                    headers=headers,
                    json_body={"scale_id": args.scale, "actor_type": args.actor_type, "actor_id": args.actor_id},
                )
                session_id = start_payload["session"]["session_id"]
                state = _load_state(state_dir)
                state["last_session_id"] = session_id
                _save_state(state_dir, state)

            if args.answers_json or args.answers_file:
                answers = _load_answers_payload(args.answers_json, args.answers_file)
                runtime._request(
                    "POST",
                    f"/api/v1/scales/sessions/{session_id}/answer-batch",
                    headers=headers,
                    json_body={"answers": answers},
                )
            else:
                _interactive_answers(runtime, headers, session_id)

            finalize_payload = runtime._request("POST", f"/api/v1/scales/sessions/{session_id}/finalize", headers=headers)
            result_payload = runtime._request("GET", f"/api/v1/scales/sessions/{session_id}/result", headers=headers)
            return _emit(
                {
                    "ok": True,
                    "session_id": session_id,
                    "finalize": finalize_payload,
                    "result": result_payload["result"],
                },
                args.json,
            )

        raise RuntimeError(f"Unhandled command: {args.command}")
    finally:
        runtime.close()


if __name__ == "__main__":
    raise SystemExit(main())
