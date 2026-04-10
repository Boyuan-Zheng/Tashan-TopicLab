from __future__ import annotations

import json
import sys
import types
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


def _install_test_shims(monkeypatch):
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
    monkeypatch.setitem(sys.modules, "app.services.content_moderation", fake_moderation)

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
    monkeypatch.setitem(sys.modules, "app.services.oss_upload", fake_oss)


def _register_and_login(client: TestClient, *, phone: str, username: str, password: str = "password123") -> dict:
    from app.storage.database.postgres_client import get_db_session

    code = "123456"
    with get_db_session() as session:
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

    response = client.post(
        "/auth/register",
        json={
            "phone": phone,
            "code": code,
            "password": password,
            "username": username,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _legacy_profile_markdown(*, stage: str) -> str:
    return f"""# 科研人员画像 — 测试智能体

## 元信息

- **创建时间**：2026-04-11
- **最后更新**：2026-04-11
- **采集阶段**：{stage}
- **数据来源**：混合

---

## 一、基础身份

- **研究阶段**：博士生
- **一级领域**：认知科学
- **二级领域**：计算神经科学
- **交叉方向**：交叉 AI 与脑科学
- **方法范式**：计算建模
- **所在机构**：中国科学院国家天文台
- **学术网络**：导师刘老师，团队做黑洞与致密天体。

---

## 二、能力

### 2.1 技术能力

| 类别 | 具体技术 | 熟练程度（★☆） |
|:---|:---|:---:|
| 编程 | Python | ★★★★ |

**代表性产出**：科研工具原型

### 2.2 科研流程能力

| 环节 | 评分 | 简要说明 |
|:---|:---:|:---|
| 问题定义 | 4 | 擅长梳理研究问题 |
| 文献整合 | 4 | 能快速整合跨学科资料 |
| 方案设计 | 4 | 计算建模方案清晰 |
| 实验执行 | 3 |  |
| 论文写作 | 3 | 需要提升故事线 |
| 项目管理 | 3 |  |

---

## 三、当前需求

### 3.1 主要时间占用

| 事项 | 描述 | 感受 |
|:---|:---|:---|
| 论文写作 | 正在集中整理结果 | 疲惫 |

### 3.2 核心难点与卡点

| 难点 | 具体表现 | 期望获得的帮助类型 |
|:---|:---|:---|
| 论文故事线 | 如何把模型结果组织得更有说服力 | 写作发表突破 |

### 3.3 近期最想改变的一件事

写作发表突破

---

## 八、审核记录

| 日期 | 审核字段 | 用户反馈 | 处理方式 |
|:---|:---|:---|:---|
| 2026-04-11 | 基础画像 | 首版 | 自动写入 |
"""


def _legacy_forum_profile_markdown() -> str:
    return """# 测试智能体

## Identity
You are a doctoral researcher working at the intersection of cognitive science, computational neuroscience, and AI for brain science.

## Expertise
- Python-based research tooling
- Cross-disciplinary literature synthesis

## Thinking Style
- 喜欢把不同学科的概念连接起来理解问题

## Discussion Style
- 倾向先搭框架，再逐步补细节
"""


def _legacy_kernel_response(*, content: str | None = None, tool_calls: list[tuple[str, dict]] | None = None):
    wrapped_calls = []
    for index, (name, arguments) in enumerate(tool_calls or [], start=1):
        wrapped_calls.append(
            types.SimpleNamespace(
                id=f"call_{index}",
                type="function",
                function=types.SimpleNamespace(
                    name=name,
                    arguments=json.dumps(arguments, ensure_ascii=False),
                ),
            )
        )
    return types.SimpleNamespace(
        choices=[
            types.SimpleNamespace(
                message=types.SimpleNamespace(
                    content=content,
                    tool_calls=wrapped_calls,
                )
            )
        ]
    )


def _install_fake_legacy_kernel_llm(monkeypatch) -> None:
    import app.portrait.legacy_kernel.agent as legacy_agent

    class _FakeLegacyKernelCompletions:
        def create(self, *, model, messages, tools=None, tool_choice=None):
            _ = model, tools, tool_choice
            convo = messages[1:]
            last_user = next((item.get("content", "") for item in reversed(convo) if item.get("role") == "user"), "")
            last_message = convo[-1] if convo else {}

            if last_user == "帮我开始建立科研数字分身。":
                if last_message.get("role") == "user":
                    return _legacy_kernel_response(tool_calls=[("read_skill", {"skill_name": "collect-basic-info"})])
                return _legacy_kernel_response(content="我们先开始建立科研数字分身。你可以回复 A 使用 AI 记忆导入，或回复 B 直接逐步填写。")

            if last_user == "B":
                if last_message.get("role") == "user":
                    return _legacy_kernel_response(tool_calls=[("write_profile", {"content": _legacy_profile_markdown(stage="basic_info_done")})])
                return _legacy_kernel_response(content="已记录你的基础身份信息。你可以继续补充，或让我生成论坛画像。")

            if "论坛画像" in last_user:
                if last_message.get("role") == "user":
                    return _legacy_kernel_response(tool_calls=[("write_forum_profile", {"content": _legacy_forum_profile_markdown()})])
                return _legacy_kernel_response(content="论坛画像已生成，你可以继续查看或确认。")

            if "确认当前画像" in last_user or "完成最终画像" in last_user:
                if last_message.get("role") == "user":
                    return _legacy_kernel_response(tool_calls=[("write_profile", {"content": _legacy_profile_markdown(stage="review_done")})])
                return _legacy_kernel_response(content="画像已确认并完成。")

            if "提示词" in last_user:
                if last_message.get("role") == "user":
                    return _legacy_kernel_response(tool_calls=[("read_skill", {"skill_name": "generate-ai-memory-prompt"})])
                return _legacy_kernel_response(
                    content="请复制下面的提示词：\n```markdown\n【科研数字分身信息提取请求】\nA1. 我目前处于哪个研究阶段？\n```"
                )

            return _legacy_kernel_response(content="我已收到，请继续。")

    class _FakeLegacyKernelClient:
        def __init__(self) -> None:
            self.chat = types.SimpleNamespace(completions=_FakeLegacyKernelCompletions())

    monkeypatch.setattr(legacy_agent, "create_client", lambda: _FakeLegacyKernelClient())
    monkeypatch.setattr(legacy_agent, "get_default_model", lambda: "fake-legacy-model")


def _complete_legacy_basic_info_flow(client: TestClient, headers: dict[str, str], session_id: str) -> dict:
    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"choice": "direct"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"choice": "博士生"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "认知科学；计算神经科学；交叉 AI 与脑科学"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"choice": "计算建模"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "中国科学院国家天文台"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "导师刘老师，团队做黑洞与致密天体。"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "合作以实验室内部和跨机构合作为主。"},
    )
    assert response.status_code == 200, response.text

    for value in [4, 5, 4, 3, 4, 3]:
        response = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": value},
        )
        assert response.status_code == 200, response.text
        response = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"text": "跳过"},
        )
        assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "Python（熟练）、PyTorch（日常使用）、MATLAB（入门）"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "跳过"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "论文写作、数据分析、组会沟通"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"choice": "疲惫"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"text": "最大卡点是如何把模型结果组织成更有说服力的故事线。"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"choice": "方法支持"},
    )
    assert response.status_code == 200, response.text

    response = client.post(
        f"/api/v1/portrait/sessions/{session_id}/respond",
        headers=headers,
        json={"choice": "写作发表突破"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_portrait_session_runtime_closed_loop(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_runtime.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router
    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def fake_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state
        return {
            "content": "好的，我已经记录了你的方向。接下来请补充你最常用的工作方式。",
            "model": model or "fake-dialogue-model",
        }

    monkeypatch.setattr(dialogue_generation_service, "generate_assistant_reply", fake_generate_assistant_reply)

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072001", username="portrait-session-user")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/portrait/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "portrait-session-test"},
        )
        assert start.status_code == 200, start.text
        start_payload = start.json()
        session_id = start_payload["session"]["session_id"]
        assert start_payload["stage"] == "dialogue"
        assert start_payload["input_kind"] == "text"
        assert "respond" in start_payload["allowed_actions"]

        status = client.get(f"/api/v1/portrait/sessions/{session_id}", headers=headers)
        assert status.status_code == 200, status.text
        assert status.json()["session"]["session_id"] == session_id

        respond = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"text": "我主要在做 AI agent 工作流、科研工具开发和学术写作。"},
        )
        assert respond.status_code == 200, respond.text
        respond_payload = respond.json()
        assert respond_payload["last_response"]["generation_status"] == "completed"
        assert "dialogue_session" in respond_payload["runtime_refs"]
        assert "portrait_state" in respond_payload["runtime_refs"]
        assert respond_payload["current_state"]["portrait_state_id"].startswith("pst_")
        assert respond_payload["current_state"]["state_json"]["dialogue"]["latest_session"]["session_id"] == respond_payload["runtime_refs"]["dialogue_session"]["ref_value"]
        assert respond_payload["result_preview"]["portrait_state_id"] == respond_payload["runtime_refs"]["portrait_state"]["ref_value"]

        forum = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "forum:generate"},
        )
        assert forum.status_code == 200, forum.text
        forum_payload = forum.json()
        assert forum_payload["runtime_refs"]["forum_artifact"]["ref_value"].startswith("par_")
        assert forum_payload["last_response"]["product_action"]["artifact"]["artifact_kind"] == "forum_profile_markdown"
        assert any(block["type"] == "copyable" for block in forum_payload["blocks"])

        scientist = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "scientist:famous"},
        )
        assert scientist.status_code == 200, scientist.text
        scientist_payload = scientist.json()
        assert scientist_payload["runtime_refs"]["scientist_famous_artifact"]["ref_value"].startswith("par_")
        assert scientist_payload["last_response"]["product_action"]["artifact"]["artifact_kind"] == "scientist_famous_match"

        exported = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "export:profile_markdown"},
        )
        assert exported.status_code == 200, exported.text
        exported_payload = exported.json()
        assert exported_payload["runtime_refs"]["export_profile_markdown_artifact"]["ref_value"].startswith("par_")
        assert exported_payload["last_response"]["product_action"]["artifact"]["artifact_kind"] == "export_profile_markdown"

        result = client.get(f"/api/v1/portrait/sessions/{session_id}/result", headers=headers)
        assert result.status_code == 200, result.text
        result_payload = result.json()
        assert result_payload["result"]["current_state"]["portrait_state_id"] == respond_payload["current_state"]["portrait_state_id"]

        confirm = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"confirm": True},
        )
        assert confirm.status_code == 200, confirm.text
        confirm_payload = confirm.json()
        assert confirm_payload["status"] == "completed"
        assert confirm_payload["stage"] == "completed"
        assert confirm_payload["input_kind"] == "none"


def test_portrait_session_runtime_rejects_unsupported_first_batch_inputs(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_unsupported.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072002", username="portrait-session-unsupported")
        headers = _auth_headers(auth["token"])

        start = client.post("/api/v1/portrait/sessions", headers=headers, json={})
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        response = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": 3},
        )
        assert response.status_code == 400, response.text
        detail = response.json()["detail"]
        assert detail["code"] == "unsupported_portrait_session_choice"
        assert detail["choice"] == "3"


def test_portrait_session_runtime_routes_scale_choices(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_scale.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072003", username="portrait-session-scale")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/portrait/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "portrait-session-scale"},
        )
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        choose_scale = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "scale:rcss"},
        )
        assert choose_scale.status_code == 200, choose_scale.text
        choose_payload = choose_scale.json()
        assert choose_payload["stage"] == "scale_question"
        assert choose_payload["input_kind"] == "choice"
        assert choose_payload["runtime_refs"]["scale_session"]["metadata_json"]["scale_id"] == "rcss"

        latest = choose_payload
        for _ in range(8):
            answered = client.post(
                f"/api/v1/portrait/sessions/{session_id}/respond",
                headers=headers,
                json={"choice": 7},
            )
            assert answered.status_code == 200, answered.text
            latest = answered.json()

        assert latest["stage"] == "dialogue"
        assert latest["runtime_refs"]["portrait_state"]["ref_value"].startswith("pst_")
        assert latest["last_response"]["scale_finalize"]["result"]["scale_id"] == "rcss"


def test_portrait_session_runtime_routes_prompt_import_flow(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_prompt_import.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router
    from app.portrait.services.dialogue_generation_service import dialogue_generation_service

    async def fake_generate_assistant_reply(messages, derived_state, *, model=None):
        _ = messages, derived_state
        return {
            "content": "好的，我已经有了你的主线。接下来如有需要，你也可以选择导出外部提示词。",
            "model": model or "fake-dialogue-model",
        }

    monkeypatch.setattr(dialogue_generation_service, "generate_assistant_reply", fake_generate_assistant_reply)

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072004", username="portrait-session-prompt")
        headers = _auth_headers(auth["token"])

        start = client.post("/api/v1/portrait/sessions", headers=headers, json={})
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        seed = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"text": "我最近主要在做科研工具开发、AI 代理工作流和学术写作。"},
        )
        assert seed.status_code == 200, seed.text
        seed_payload = seed.json()
        assert "dialogue_session" in seed_payload["runtime_refs"]
        assert "portrait_state" in seed_payload["runtime_refs"]

        handoff = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "prompt_handoff"},
        )
        assert handoff.status_code == 200, handoff.text
        handoff_payload = handoff.json()
        assert handoff_payload["stage"] == "import_result"
        assert handoff_payload["runtime_refs"]["prompt_handoff"]["ref_value"].startswith("phf_")
        assert handoff_payload["payload"]["prompt_text"]

        imported = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={
                "external_text": "# Summary\n你在科研工具和 AI agent 上有长期积累。\n# Open Questions\n还需要确认组织协作风格。",
            },
        )
        assert imported.status_code == 200, imported.text
        imported_payload = imported.json()
        assert imported_payload["stage"] == "dialogue"
        assert imported_payload["runtime_refs"]["import_result"]["ref_value"].startswith("pir_")
        assert imported_payload["last_response"]["state_update"]["current_state"]["portrait_state_id"].startswith("pst_")


def test_portrait_session_runtime_lists_and_resets_sessions(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_history.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072005", username="portrait-session-history")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/portrait/sessions",
            headers=headers,
            json={"actor_type": "internal", "actor_id": "portrait-session-history"},
        )
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        listed = client.get("/api/v1/portrait/sessions?limit=10", headers=headers)
        assert listed.status_code == 200, listed.text
        listed_payload = listed.json()
        assert listed_payload["count"] == 1
        assert listed_payload["current_active_session_id"] == session_id
        assert listed_payload["sessions"][0]["session"]["session_id"] == session_id

        reset = client.post(f"/api/v1/portrait/sessions/{session_id}/reset", headers=headers)
        assert reset.status_code == 200, reset.text
        reset_payload = reset.json()
        assert reset_payload["status"] == "reset"
        assert reset_payload["stage"] == "reset"
        assert reset_payload["input_kind"] == "none"
        assert reset_payload["last_response"]["status"] == "reset"

        listed_after = client.get("/api/v1/portrait/sessions?limit=10", headers=headers)
        assert listed_after.status_code == 200, listed_after.text
        assert listed_after.json()["current_active_session_id"] is None


def test_portrait_session_legacy_product_runs_migrated_legacy_kernel_loop(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_legacy_product_kernel.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)
    _install_fake_legacy_kernel_llm(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072006", username="portrait-session-legacy-product")
        headers = _auth_headers(auth["token"])

        start = client.post(
            "/api/v1/portrait/sessions",
            headers=headers,
            json={"mode": "legacy_product", "actor_type": "internal", "actor_id": "legacy-product-agent"},
        )
        assert start.status_code == 200, start.text
        start_payload = start.json()
        session_id = start_payload["session"]["session_id"]
        assert start_payload["stage"] == "legacy_kernel"
        assert start_payload["input_kind"] == "text"
        assert start_payload["interactive_block"]["type"] == "text_input"
        assert "legacy_kernel_session" in start_payload["runtime_refs"]
        assert "portrait_state" in start_payload["runtime_refs"]
        assert "A 使用 AI 记忆导入" in start_payload["message"]

        direct = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "direct"},
        )
        assert direct.status_code == 200, direct.text
        direct_payload = direct.json()
        assert direct_payload["stage"] in {"legacy_kernel", "basic_info_done"}
        current_state = direct_payload["current_state"]["state_json"]
        assert current_state["profile"]["basic_info"]["research_stage"] == "博士生"
        assert current_state["profile"]["basic_info"]["institution"] == "中国科学院国家天文台"
        assert current_state["profile"]["capability"]["tech_stack_text"].startswith("Python")
        assert current_state["profile"]["current_needs"]["desired_change"] == "写作发表突破"
        assert current_state["legacy_kernel"]["legacy_session_id"] == direct_payload["runtime_refs"]["legacy_kernel_session"]["ref_value"]
        assert "科研人员画像" in current_state["legacy_kernel"]["profile_markdown"]

        forum = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "forum:generate"},
        )
        assert forum.status_code == 200, forum.text
        forum_payload = forum.json()
        assert forum_payload["runtime_refs"]["legacy_kernel_session"]["ref_value"] == direct_payload["runtime_refs"]["legacy_kernel_session"]["ref_value"]
        assert forum_payload["current_state"]["state_json"]["legacy_kernel"]["forum_profile_markdown"].startswith("# 测试智能体")
        assert any(block["type"] == "copyable" for block in forum_payload["blocks"])

        confirm = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"confirm": True},
        )
        assert confirm.status_code == 200, confirm.text
        confirm_payload = confirm.json()
        assert confirm_payload["status"] == "completed"
        assert confirm_payload["current_state"]["state_json"]["profile"]["meta"]["collection_stage"] == "review_done"

        history = client.get(f"/api/v1/portrait/sessions/{session_id}/history?limit=20", headers=headers)
        assert history.status_code == 200, history.text
        history_payload = history.json()
        event_types = {item["event_type"] for item in history_payload["events"]}
        assert "legacy_kernel_bootstrap" in event_types
        assert "legacy_kernel_turn" in event_types
        assert history_payload["runtime_refs"]["legacy_kernel_session"]["ref_value"].startswith("lks_")


def test_portrait_session_legacy_product_routes_prompt_request_through_legacy_kernel(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_session_legacy_prompt.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)
    _install_fake_legacy_kernel_llm(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_session as portrait_session_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_session_router.router, prefix="/api/v1", tags=["portrait-session-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800072007", username="portrait-session-legacy-ai-memory")
        headers = _auth_headers(auth["token"])

        start = client.post("/api/v1/portrait/sessions", headers=headers, json={"mode": "legacy_product"})
        assert start.status_code == 200, start.text
        session_id = start.json()["session"]["session_id"]

        prompt = client.post(
            f"/api/v1/portrait/sessions/{session_id}/respond",
            headers=headers,
            json={"choice": "prompt_handoff"},
        )
        assert prompt.status_code == 200, prompt.text
        prompt_payload = prompt.json()
        assert prompt_payload["stage"] == "legacy_kernel"
        copyables = [block for block in prompt_payload["blocks"] if block["type"] == "copyable"]
        assert copyables
        assert "科研数字分身信息提取请求" in copyables[0]["content"]
        assert "prompt_handoff" not in prompt_payload["runtime_refs"]
