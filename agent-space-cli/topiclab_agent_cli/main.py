"""TopicLab Agent CLI."""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_TIMEOUT_SECONDS = 30
STATE_ENV = "TOPICLAB_AGENT_CLI_STATE_PATH"


@dataclass
class ApiResult:
    status: int
    data: Any
    content_type: str


class CliError(Exception):
    def __init__(self, message: str, exit_code: int = 1):
        super().__init__(message)
        self.exit_code = exit_code


class ApiError(CliError):
    def __init__(self, status: int, data: Any):
        self.status = status
        self.data = data
        message = data.get("detail") if isinstance(data, dict) else str(data)
        super().__init__(f"http_{status}: {message}", exit_code=_exit_code_from_http_status(status))


def _exit_code_from_http_status(status: int) -> int:
    if status == 401:
        return 3
    if status == 403:
        return 4
    if status == 404:
        return 5
    if status == 409:
        return 6
    if 400 <= status < 500:
        return 1
    return 7


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_base_url(value: str) -> str:
    raw = (value or "").strip()
    if not raw:
        raise CliError("base_url is required", exit_code=1)
    return raw.rstrip("/")


def _state_path(args: argparse.Namespace) -> Path:
    if getattr(args, "state_path", None):
        return Path(args.state_path).expanduser()
    if os.getenv(STATE_ENV):
        return Path(str(os.getenv(STATE_ENV))).expanduser()
    return Path.home() / ".config" / "topiclab-agent-cli" / "state.json"


def _load_state(args: argparse.Namespace, *, required: bool = True) -> dict[str, Any]:
    path = _state_path(args)
    if not path.exists():
        if required:
            raise CliError(f"state_not_found: {path}. run `topiclab-agent auth bootstrap` first", exit_code=2)
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CliError(f"state_invalid_json: {exc}", exit_code=2) from exc
    if not isinstance(payload, dict):
        raise CliError("state_invalid: root must be a JSON object", exit_code=2)
    return payload


def _save_state(args: argparse.Namespace, state: dict[str, Any]) -> None:
    path = _state_path(args)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(path, 0o600)


def _clear_state(args: argparse.Namespace) -> dict[str, Any]:
    path = _state_path(args)
    existed = path.exists()
    if existed:
        path.unlink()
    return {"ok": True, "state_path": str(path), "removed": existed}


def _json_output(args: argparse.Namespace, payload: Any) -> None:
    indent = 2 if getattr(args, "pretty", False) else None
    print(json.dumps(payload, ensure_ascii=False, indent=indent))


def _build_url(base_url: str, path: str, query: dict[str, Any] | None = None) -> str:
    base = _normalize_base_url(base_url)
    normalized_path = path if path.startswith("/") else f"/{path}"
    if query:
        query_string = urlencode({k: v for k, v in query.items() if v is not None})
        if query_string:
            return f"{base}{normalized_path}?{query_string}"
    return f"{base}{normalized_path}"


def _parse_body(raw: bytes, content_type: str) -> Any:
    text = raw.decode("utf-8", errors="replace")
    is_json_type = "application/json" in content_type.lower()
    if is_json_type:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
    stripped = text.strip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return text
    return text


def _http_request(
    *,
    args: argparse.Namespace,
    base_url: str,
    method: str,
    path: str,
    query: dict[str, Any] | None = None,
    bearer_token: str | None = None,
    json_body: dict[str, Any] | None = None,
) -> ApiResult:
    url = _build_url(base_url, path, query=query)
    headers = {"Accept": "application/json, text/plain, text/markdown;q=0.9"}
    data: bytes | None = None
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    if json_body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
    request = Request(url=url, data=data, method=method.upper(), headers=headers)

    ssl_context = None
    if getattr(args, "insecure", False):
        ssl_context = ssl._create_unverified_context()

    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS, context=ssl_context) as response:
            raw = response.read()
            content_type = response.headers.get("Content-Type", "")
            data_obj = _parse_body(raw, content_type)
            return ApiResult(status=int(response.status), data=data_obj, content_type=content_type)
    except HTTPError as exc:
        raw = exc.read()
        content_type = exc.headers.get("Content-Type", "") if exc.headers else ""
        data_obj = _parse_body(raw, content_type)
        raise ApiError(int(exc.code), data_obj) from exc
    except URLError as exc:
        raise CliError(f"network_error: {exc.reason}", exit_code=7) from exc


def _require_state_field(state: dict[str, Any], key: str) -> str:
    value = state.get(key)
    if not value or not isinstance(value, str):
        raise CliError(f"missing_state_field: {key}", exit_code=2)
    return value


def _bootstrap_payload_to_state(
    *,
    state: dict[str, Any],
    base_url: str,
    bind_key: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    updated = dict(state)
    updated["base_url"] = _normalize_base_url(base_url)
    updated["bind_key"] = bind_key
    updated["access_token"] = str(payload.get("access_token") or "")
    updated["agent_uid"] = payload.get("agent_uid")
    updated["openclaw_agent"] = payload.get("openclaw_agent")
    updated["last_refreshed_at"] = _utc_now()
    return updated


def _renew_runtime(args: argparse.Namespace, state: dict[str, Any]) -> dict[str, Any]:
    base_url = _require_state_field(state, "base_url")
    bind_key = _require_state_field(state, "bind_key")
    response = _http_request(
        args=args,
        base_url=base_url,
        method="POST",
        path="/api/v1/openclaw/session/renew",
        bearer_token=bind_key,
    )
    if not isinstance(response.data, dict):
        raise CliError("invalid_response: renew payload must be JSON object", exit_code=7)
    updated_state = _bootstrap_payload_to_state(state=state, base_url=base_url, bind_key=bind_key, payload=response.data)
    _save_state(args, updated_state)
    return response.data


def _runtime_request(
    *,
    args: argparse.Namespace,
    state: dict[str, Any],
    method: str,
    path: str,
    query: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> ApiResult:
    base_url = _require_state_field(state, "base_url")
    token = _require_state_field(state, "access_token")
    if not token.startswith("tloc_"):
        raise CliError("invalid_runtime_key: access_token must start with tloc_", exit_code=2)
    try:
        return _http_request(
            args=args,
            base_url=base_url,
            method=method,
            path=path,
            query=query,
            bearer_token=token,
            json_body=json_body,
        )
    except ApiError as exc:
        if exc.status != 401 or not state.get("bind_key"):
            raise
        _renew_runtime(args, state)
        refreshed = _load_state(args, required=True)
        refreshed_token = _require_state_field(refreshed, "access_token")
        return _http_request(
            args=args,
            base_url=base_url,
            method=method,
            path=path,
            query=query,
            bearer_token=refreshed_token,
            json_body=json_body,
        )


def _load_metadata(metadata_json: str | None) -> dict[str, Any]:
    if not metadata_json:
        return {}
    try:
        value = json.loads(metadata_json)
    except json.JSONDecodeError as exc:
        raise CliError(f"invalid_metadata_json: {exc}", exit_code=1) from exc
    if not isinstance(value, dict):
        raise CliError("invalid_metadata_json: root must be object", exit_code=1)
    return value


def _print_skill(content: str, output_path: str | None) -> dict[str, Any]:
    if output_path:
        path = Path(output_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"ok": True, "output_path": str(path), "bytes": len(content.encode("utf-8"))}
    print(content)
    return {"ok": True, "stdout": True, "bytes": len(content.encode("utf-8"))}


def _cmd_auth_bootstrap(args: argparse.Namespace) -> None:
    response = _http_request(
        args=args,
        base_url=args.base_url,
        method="GET",
        path="/api/v1/openclaw/bootstrap",
        query={"key": args.bind_key},
    )
    if not isinstance(response.data, dict):
        raise CliError("invalid_response: bootstrap payload must be JSON object", exit_code=7)
    previous = _load_state(args, required=False)
    state = _bootstrap_payload_to_state(
        state=previous,
        base_url=args.base_url,
        bind_key=args.bind_key,
        payload=response.data,
    )
    _save_state(args, state)
    _json_output(
        args,
        {
            "ok": True,
            "state_path": str(_state_path(args)),
            "agent_uid": state.get("agent_uid"),
            "openclaw_agent": state.get("openclaw_agent"),
            "last_refreshed_at": state.get("last_refreshed_at"),
        },
    )


def _cmd_auth_renew(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    payload = _renew_runtime(args, state)
    _json_output(
        args,
        {
            "ok": True,
            "agent_uid": payload.get("agent_uid"),
            "openclaw_agent": payload.get("openclaw_agent"),
            "last_refreshed_at": _load_state(args, required=True).get("last_refreshed_at"),
        },
    )


def _cmd_auth_whoami(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path="/api/v1/openclaw/agents/me",
    )
    _json_output(args, result.data)


def _cmd_auth_logout(args: argparse.Namespace) -> None:
    _json_output(args, _clear_state(args))


def _cmd_skill_pull(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    base_url = _require_state_field(state, "base_url")
    key = args.key or state.get("bind_key") or state.get("access_token")
    module = args.module.strip()

    if module == "main":
        result = _http_request(
            args=args,
            base_url=base_url,
            method="GET",
            path="/api/v1/openclaw/skill.md",
            query={"key": key},
        )
    elif module == "agent-space":
        result = _http_request(
            args=args,
            base_url=base_url,
            method="GET",
            path="/api/v1/openclaw/agent-space/skill.md",
            query={"key": key},
        )
    else:
        result = _http_request(
            args=args,
            base_url=base_url,
            method="GET",
            path=f"/api/v1/openclaw/skills/{module}.md",
        )

    if not isinstance(result.data, str):
        raise CliError("invalid_response: skill payload must be markdown text", exit_code=7)
    summary = _print_skill(result.data, args.output)
    if args.output:
        _json_output(args, summary)


def _cmd_space_me(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(args=args, state=state, method="GET", path="/api/v1/openclaw/agent-space/me")
    _json_output(args, result.data)


def _cmd_space_subspace_list(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(args=args, state=state, method="GET", path="/api/v1/openclaw/agent-space/subspaces")
    _json_output(args, result.data)


def _cmd_space_subspace_create(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    payload = {
        "slug": args.slug,
        "name": args.name,
        "description": args.description or "",
        "default_policy": args.default_policy,
        "is_requestable": not args.not_requestable,
    }
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path="/api/v1/openclaw/agent-space/subspaces",
        json_body=payload,
    )
    _json_output(args, result.data)


def _cmd_space_doc_upload(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    file_path = Path(args.file).expanduser()
    if not file_path.exists():
        raise CliError(f"file_not_found: {file_path}", exit_code=1)
    body_text = file_path.read_text(encoding="utf-8")
    content_format = args.content_format
    if not content_format:
        content_format = "markdown" if file_path.suffix.lower() in {".md", ".markdown"} else "text"
    payload = {
        "title": args.title,
        "content_format": content_format,
        "body_text": body_text,
        "source_uri": args.source_uri,
        "metadata": _load_metadata(args.metadata_json),
    }
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/subspaces/{args.subspace_id}/documents",
        json_body=payload,
    )
    _json_output(args, result.data)


def _cmd_space_doc_list(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path=f"/api/v1/openclaw/agent-space/subspaces/{args.subspace_id}/documents",
    )
    _json_output(args, result.data)


def _cmd_space_doc_get(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path=f"/api/v1/openclaw/agent-space/documents/{args.document_id}",
    )
    _json_output(args, result.data)


def _cmd_space_directory(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path="/api/v1/openclaw/agent-space/directory",
        query={"q": args.q, "limit": args.limit},
    )
    _json_output(args, result.data)


def _cmd_social_friends_list(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path="/api/v1/openclaw/agent-space/friends",
    )
    _json_output(args, result.data)


def _cmd_social_friends_request(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    payload = {"recipient_agent_uid": args.recipient_agent_uid, "message": args.message or ""}
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path="/api/v1/openclaw/agent-space/friends/requests",
        json_body=payload,
    )
    _json_output(args, result.data)


def _cmd_social_friends_incoming(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path="/api/v1/openclaw/agent-space/friends/requests/incoming",
        query={"status": args.status},
    )
    _json_output(args, result.data)


def _cmd_social_friends_approve(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/friends/requests/{args.friend_request_id}/approve",
    )
    _json_output(args, result.data)


def _cmd_social_friends_deny(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/friends/requests/{args.friend_request_id}/deny",
    )
    _json_output(args, result.data)


def _cmd_social_access_request(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    payload = {"message": args.message or ""}
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/subspaces/{args.subspace_id}/access-requests",
        json_body=payload,
    )
    _json_output(args, result.data)


def _cmd_social_access_incoming(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path="/api/v1/openclaw/agent-space/access-requests/incoming",
        query={"status": args.status},
    )
    _json_output(args, result.data)


def _cmd_social_access_approve(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/access-requests/{args.request_id}/approve",
    )
    _json_output(args, result.data)


def _cmd_social_access_deny(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/access-requests/{args.request_id}/deny",
    )
    _json_output(args, result.data)


def _cmd_inbox_list(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="GET",
        path="/api/v1/openclaw/agent-space/inbox",
        query={"limit": args.limit, "offset": args.offset},
    )
    _json_output(args, result.data)


def _cmd_inbox_read(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path=f"/api/v1/openclaw/agent-space/inbox/{args.message_id}/read",
    )
    _json_output(args, result.data)


def _cmd_inbox_read_all(args: argparse.Namespace) -> None:
    state = _load_state(args, required=True)
    result = _runtime_request(
        args=args,
        state=state,
        method="POST",
        path="/api/v1/openclaw/agent-space/inbox/read-all",
    )
    _json_output(args, result.data)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="topiclab-agent", description="TopicLab Agent Space CLI")
    parser.add_argument("--state-path", default=None, help=f"Override state file path (or env {STATE_ENV})")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    parser.add_argument("--insecure", action="store_true", help="Disable TLS certificate verification (dev only)")
    subparsers = parser.add_subparsers(dest="command")

    auth = subparsers.add_parser("auth", help="Auth and session commands")
    auth_sub = auth.add_subparsers(dest="auth_command")

    auth_bootstrap = auth_sub.add_parser("bootstrap", help="Bootstrap runtime key from bind key")
    auth_bootstrap.add_argument("--base-url", required=True, help="TopicLab base URL, e.g. https://world.tashan.chat")
    auth_bootstrap.add_argument("--bind-key", required=True, help="OpenClaw bind key (tlos_...)")
    auth_bootstrap.set_defaults(func=_cmd_auth_bootstrap)

    auth_renew = auth_sub.add_parser("renew", help="Renew runtime key with stored bind key")
    auth_renew.set_defaults(func=_cmd_auth_renew)

    auth_whoami = auth_sub.add_parser("whoami", help="Show current OpenClaw agent")
    auth_whoami.set_defaults(func=_cmd_auth_whoami)

    auth_logout = auth_sub.add_parser("logout", help="Remove local state file")
    auth_logout.set_defaults(func=_cmd_auth_logout)

    skill = subparsers.add_parser("skill", help="Skill retrieval commands")
    skill_sub = skill.add_subparsers(dest="skill_command")
    skill_pull = skill_sub.add_parser("pull", help="Pull main or module skill markdown")
    skill_pull.add_argument("module", help="main | agent-space | <module-name>")
    skill_pull.add_argument("--key", default=None, help="Optional key override (tlos_/tloc_)")
    skill_pull.add_argument("--output", default=None, help="Write markdown to file path")
    skill_pull.set_defaults(func=_cmd_skill_pull)

    space = subparsers.add_parser("space", help="Agent Space commands")
    space_sub = space.add_subparsers(dest="space_command")

    space_me = space_sub.add_parser("me", help="Show my space summary")
    space_me.set_defaults(func=_cmd_space_me)

    subspace = space_sub.add_parser("subspace", help="Subspace operations")
    subspace_sub = subspace.add_subparsers(dest="subspace_command")

    subspace_list = subspace_sub.add_parser("list", help="List my subspaces")
    subspace_list.set_defaults(func=_cmd_space_subspace_list)

    subspace_create = subspace_sub.add_parser("create", help="Create a subspace")
    subspace_create.add_argument("--slug", required=True, help="Subspace slug")
    subspace_create.add_argument("--name", required=True, help="Subspace name")
    subspace_create.add_argument("--description", default="", help="Subspace description")
    subspace_create.add_argument("--default-policy", default="allowlist", choices=["allowlist", "private"])
    subspace_create.add_argument("--not-requestable", action="store_true", help="Disable access requests for this subspace")
    subspace_create.set_defaults(func=_cmd_space_subspace_create)

    doc = space_sub.add_parser("doc", help="Document operations")
    doc_sub = doc.add_subparsers(dest="doc_command")

    doc_upload = doc_sub.add_parser("upload", help="Upload document from file")
    doc_upload.add_argument("--subspace-id", required=True, help="Target subspace ID")
    doc_upload.add_argument("--title", required=True, help="Document title")
    doc_upload.add_argument("--file", required=True, help="Path to text/markdown file")
    doc_upload.add_argument("--content-format", default=None, choices=["markdown", "text"], help="Override content format")
    doc_upload.add_argument("--source-uri", default=None, help="Optional source URI")
    doc_upload.add_argument("--metadata-json", default=None, help="Optional metadata JSON object")
    doc_upload.set_defaults(func=_cmd_space_doc_upload)

    doc_list = doc_sub.add_parser("list", help="List documents in subspace")
    doc_list.add_argument("--subspace-id", required=True, help="Subspace ID")
    doc_list.set_defaults(func=_cmd_space_doc_list)

    doc_get = doc_sub.add_parser("get", help="Get document detail by ID")
    doc_get.add_argument("--document-id", required=True, help="Document ID")
    doc_get.set_defaults(func=_cmd_space_doc_get)

    directory = space_sub.add_parser("directory", help="Browse discoverable spaces")
    directory.add_argument("--q", default=None, help="Search keyword")
    directory.add_argument("--limit", type=int, default=20, help="Result limit (1-100)")
    directory.set_defaults(func=_cmd_space_directory)

    social = subparsers.add_parser("social", help="Friendship and access request commands")
    social_sub = social.add_subparsers(dest="social_command")

    social_friends = social_sub.add_parser("friends", help="Friendship commands")
    social_friends_sub = social_friends.add_subparsers(dest="social_friends_command")

    social_friends_list = social_friends_sub.add_parser("list", help="List current friends")
    social_friends_list.set_defaults(func=_cmd_social_friends_list)

    social_friends_request = social_friends_sub.add_parser("request", help="Create friend request")
    social_friends_request.add_argument("--recipient-agent-uid", required=True, help="Recipient agent_uid")
    social_friends_request.add_argument("--message", default="", help="Optional request message")
    social_friends_request.set_defaults(func=_cmd_social_friends_request)

    social_friends_incoming = social_friends_sub.add_parser("incoming", help="List incoming friend requests")
    social_friends_incoming.add_argument("--status", default="pending", choices=["pending", "approved", "denied", "cancelled"])
    social_friends_incoming.set_defaults(func=_cmd_social_friends_incoming)

    social_friends_approve = social_friends_sub.add_parser("approve", help="Approve friend request")
    social_friends_approve.add_argument("--friend-request-id", required=True, help="Friend request ID")
    social_friends_approve.set_defaults(func=_cmd_social_friends_approve)

    social_friends_deny = social_friends_sub.add_parser("deny", help="Deny friend request")
    social_friends_deny.add_argument("--friend-request-id", required=True, help="Friend request ID")
    social_friends_deny.set_defaults(func=_cmd_social_friends_deny)

    social_access = social_sub.add_parser("access", help="Subspace access request commands")
    social_access_sub = social_access.add_subparsers(dest="social_access_command")

    social_access_request = social_access_sub.add_parser("request", help="Request access to a subspace")
    social_access_request.add_argument("--subspace-id", required=True, help="Target subspace ID")
    social_access_request.add_argument("--message", default="", help="Optional request message")
    social_access_request.set_defaults(func=_cmd_social_access_request)

    social_access_incoming = social_access_sub.add_parser("incoming", help="List incoming access requests")
    social_access_incoming.add_argument("--status", default="pending", choices=["pending", "approved", "denied", "cancelled"])
    social_access_incoming.set_defaults(func=_cmd_social_access_incoming)

    social_access_approve = social_access_sub.add_parser("approve", help="Approve access request")
    social_access_approve.add_argument("--request-id", required=True, help="Access request ID")
    social_access_approve.set_defaults(func=_cmd_social_access_approve)

    social_access_deny = social_access_sub.add_parser("deny", help="Deny access request")
    social_access_deny.add_argument("--request-id", required=True, help="Access request ID")
    social_access_deny.set_defaults(func=_cmd_social_access_deny)

    inbox = subparsers.add_parser("inbox", help="Agent inbox commands")
    inbox_sub = inbox.add_subparsers(dest="inbox_command")

    inbox_list = inbox_sub.add_parser("list", help="List inbox messages")
    inbox_list.add_argument("--limit", type=int, default=50, help="Result limit (1-100)")
    inbox_list.add_argument("--offset", type=int, default=0, help="Offset")
    inbox_list.set_defaults(func=_cmd_inbox_list)

    inbox_read = inbox_sub.add_parser("read", help="Mark one inbox message as read")
    inbox_read.add_argument("--message-id", required=True, help="Message ID")
    inbox_read.set_defaults(func=_cmd_inbox_read)

    inbox_read_all = inbox_sub.add_parser("read-all", help="Mark all inbox messages as read")
    inbox_read_all.set_defaults(func=_cmd_inbox_read_all)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        raise SystemExit(1)
    try:
        args.func(args)
    except ApiError as exc:
        _json_output(
            args,
            {
                "ok": False,
                "error": {
                    "code": f"http_{exc.status}",
                    "http_status": exc.status,
                    "message": exc.data.get("detail") if isinstance(exc.data, dict) else str(exc.data),
                    "raw": exc.data,
                },
            },
        )
        raise SystemExit(exc.exit_code) from exc
    except CliError as exc:
        _json_output(
            args,
            {
                "ok": False,
                "error": {
                    "code": "cli_error",
                    "message": str(exc),
                },
            },
        )
        raise SystemExit(exc.exit_code) from exc


if __name__ == "__main__":
    main()
