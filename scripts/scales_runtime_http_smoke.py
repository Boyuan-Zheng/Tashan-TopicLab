#!/usr/bin/env python3
"""HTTP smoke test for the portrait scales runtime.

This script talks to a running TopicLab backend over HTTP and validates the
authenticated scales flow end-to-end:

- health
- optional register-config probe
- register or reuse existing account
- login
- /auth/me
- /api/v1/scales
- /api/v1/scales/{scale_id}
- start session
- answer-batch
- finalize
- result

It is intended for staging or canary validation after the in-process smoke has
already passed.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "scales-runtime" / "fixtures" / "rcss-strong-integration.json"


def _request(base_url: str, method: str, path: str, *, data=None, token: str | None = None, timeout: float = 10.0):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(f"{base_url}{path}", data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _request_allow_http_error(
    base_url: str,
    method: str,
    path: str,
    *,
    data=None,
    token: str | None = None,
    timeout: float = 10.0,
):
    try:
        return _request(base_url, method, path, data=data, token=token, timeout=timeout)
    except HTTPError as exc:
        payload = exc.read().decode("utf-8")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            parsed = {"raw": payload}
        return exc.code, parsed


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run an end-to-end authenticated HTTP smoke against a running TopicLab scales runtime."
    )
    parser.add_argument("--base-url", required=True, help="Backend base URL, for example http://127.0.0.1:18000")
    parser.add_argument("--phone", default="13800138001", help="Phone number for the smoke user")
    parser.add_argument("--password", default="StagePass123", help="Password for the smoke user")
    parser.add_argument("--username", default="stage-smoke-user", help="Username to use during registration")
    parser.add_argument("--actor-type", default="internal", choices=["human", "agent", "internal"])
    parser.add_argument("--actor-id", default="http-smoke", help="Actor ID stored on the scale session")
    parser.add_argument("--fixture", default=str(DEFAULT_FIXTURE), help="Fixture JSON with scale_id and answers")
    parser.add_argument("--skip-register", action="store_true", help="Skip register and only perform login")
    parser.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds")
    args = parser.parse_args()

    fixture_path = Path(args.fixture).expanduser().resolve()
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    scale_id = fixture["scale_id"]

    summary: dict[str, object] = {"base_url": args.base_url, "fixture": str(fixture_path)}

    _, health = _request(args.base_url, "GET", "/health", timeout=args.timeout)
    summary["health"] = health

    register_config_status, register_config = _request_allow_http_error(
        args.base_url,
        "GET",
        "/auth/register-config",
        timeout=args.timeout,
    )
    summary["register_config"] = {"status": register_config_status, "payload": register_config}

    if not args.skip_register:
        register_status, register_payload = _request_allow_http_error(
            args.base_url,
            "POST",
            "/auth/register",
            data={
                "username": args.username,
                "phone": args.phone,
                "code": "",
                "password": args.password,
            },
            timeout=args.timeout,
        )
        summary["register"] = {"status": register_status, "payload": register_payload}
        if register_status >= 400 and "已注册" not in json.dumps(register_payload, ensure_ascii=False):
            print(json.dumps(summary, ensure_ascii=False, indent=2))
            return 1

    _, login = _request(
        args.base_url,
        "POST",
        "/auth/login",
        data={"phone": args.phone, "password": args.password},
        timeout=args.timeout,
    )
    token = login["token"]
    summary["login"] = {
        "user_id": login["user"]["id"],
        "phone": login["user"]["phone"],
        "username": login["user"]["username"],
    }

    _, me = _request(args.base_url, "GET", "/auth/me", token=token, timeout=args.timeout)
    _, listing = _request(args.base_url, "GET", "/api/v1/scales", token=token, timeout=args.timeout)
    _, definition = _request(args.base_url, "GET", f"/api/v1/scales/{scale_id}", token=token, timeout=args.timeout)
    _, session = _request(
        args.base_url,
        "POST",
        "/api/v1/scales/sessions",
        data={"scale_id": scale_id, "actor_type": args.actor_type, "actor_id": args.actor_id},
        token=token,
        timeout=args.timeout,
    )
    session_id = session["session"]["session_id"]
    _, answered = _request(
        args.base_url,
        "POST",
        f"/api/v1/scales/sessions/{session_id}/answer-batch",
        data={"answers": fixture["answers"]},
        token=token,
        timeout=args.timeout,
    )
    _, finalized = _request(
        args.base_url,
        "POST",
        f"/api/v1/scales/sessions/{session_id}/finalize",
        token=token,
        timeout=args.timeout,
    )
    _, result = _request(
        args.base_url,
        "GET",
        f"/api/v1/scales/sessions/{session_id}/result",
        token=token,
        timeout=args.timeout,
    )

    summary["me"] = me
    summary["scales"] = {
        "registry_version": listing["registry_version"],
        "count": len(listing["list"]),
        "scale_ids": [item["scale_id"] for item in listing["list"]],
    }
    summary["definition"] = {
        "scale_id": definition["scale_id"],
        "question_count": len(definition["questions"]),
        "definition_version": definition["definition_version"],
    }
    summary["session"] = {
        "session_id": session_id,
        "status_after_answers": answered["session"]["status"],
        "status_after_finalize": finalized["session"]["status"],
    }
    summary["result"] = result["result"]

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
