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


def _seed_portrait_state(client: TestClient, headers: dict[str, str]) -> dict:
    response = client.post(
        "/api/v1/portrait/state/updates",
        headers=headers,
        json={
            "source_type": "manual",
            "source_id": "seed_products",
            "state_patch_json": {
                "profile": {
                    "basic_info": {
                        "research_stage": "博士生",
                        "primary_field": "认知科学",
                        "secondary_field": "人工智能",
                        "cross_discipline": "AI 与脑科学",
                        "method_paradigm": "计算建模",
                        "institution": "中国科学院国家天文台",
                        "advisor_team": "导师刘老师，团队做黑洞与致密天体。",
                        "academic_network": "跨机构合作与实验室内协作并行",
                    },
                    "capability": {
                        "tech_stack_text": "Python, PyTorch, JAX",
                        "representative_outputs": "论文写作、数据分析工具、agent 工作流原型",
                        "process": {
                            "problem_definition": {"score": 4, "description": "能较快定位关键问题"},
                            "literature": {"score": 4, "description": "能整合多学科材料"},
                            "design": {"score": 5, "description": "方案设计相对稳定"},
                            "execution": {"score": 4, "description": "计算实验推进较稳"},
                            "writing": {"score": 3, "description": "写作表达仍需加强"},
                            "management": {"score": 4, "description": "能够维护长期项目节奏"},
                        },
                    },
                    "current_needs": {
                        "major_time_occupation": "agent 工作流与科研写作",
                        "pain_points": "如何把模型结果组织成更有说服力的故事线",
                        "desired_change": "写作发表突破",
                    },
                    "inferred_dimensions": {
                        "source": "AI推断",
                        "cognitive_style": {"integration": 22.0, "depth": 14.0, "csi": 8.0, "type": "倾向整合型"},
                        "motivation": {
                            "to_know": 5.4,
                            "toward_accomplishment": 5.2,
                            "to_experience_stimulation": 4.9,
                            "identified": 5.0,
                            "introjected": 3.0,
                            "external": 2.2,
                            "amotivation": 1.7,
                            "rai": 31.4,
                        },
                        "personality": {
                            "openness": 4.5,
                            "conscientiousness": 3.8,
                            "extraversion": 3.1,
                            "agreeableness": 3.4,
                            "neuroticism": 2.7,
                        },
                        "interpretation": {
                            "core_driver": "更像一位以认知科学为主轴、重视整合与系统搭建的研究者。",
                            "risks": ["容易在整合过多线索后延迟收束"],
                            "paths": ["先固定一条主线，再让跨域材料服务主线"],
                        },
                    },
                },
                "dialogue": {
                    "latest_session": {
                        "session_id": "dgs_seeded",
                        "status": "active",
                        "actor_type": "internal",
                        "actor_id": "test",
                        "derived_state": {
                            "message_count": 4,
                            "summary": {"summary_text": "长期关注 agent 工作流、科研工具和学术写作。"},
                        },
                    }
                },
            },
            "change_summary_json": {"source_type": "manual", "source_id": "seed_products"},
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_portrait_products_closed_loop(tmp_path, monkeypatch):
    database_path = tmp_path / "portrait_products.sqlite3"
    monkeypatch.setenv("TOPICLAB_TESTING", "1")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{database_path}")
    _install_test_shims(monkeypatch)

    import app.storage.database.postgres_client as postgres_client
    import app.api.auth as auth_router
    import app.api.portrait_state as portrait_state_router
    import app.api.portrait_products as portrait_products_router

    postgres_client.reset_db_state()
    postgres_client.init_auth_tables()

    app = FastAPI()
    app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
    app.include_router(portrait_state_router.router, prefix="/api/v1", tags=["portrait-state-v1"])
    app.include_router(portrait_products_router.router, prefix="/api/v1", tags=["portrait-products-v1"])

    with TestClient(app) as client:
        auth = _register_and_login(client, phone="13800083001", username="portrait-products-user")
        headers = _auth_headers(auth["token"])
        seeded = _seed_portrait_state(client, headers)
        portrait_state_id = seeded["current_state"]["portrait_state_id"]

        structured = client.get("/api/v1/portrait/export/structured", headers=headers)
        assert structured.status_code == 200, structured.text
        structured_payload = structured.json()
        assert structured_payload["projection"]["portrait_state_id"] == portrait_state_id
        assert structured_payload["structured_profile"]["basic_info"]["primary_field"] == "认知科学"
        assert structured_payload["artifact"]["artifact_kind"] == "export_structured_profile"

        forum = client.post(
            "/api/v1/portrait/forum/generate",
            headers=headers,
            json={"display_name": "认知结构测试智能体", "institution_mode": "omit"},
        )
        assert forum.status_code == 200, forum.text
        forum_payload = forum.json()
        assert "## Identity" in forum_payload["forum_profile_markdown"]
        assert forum_payload["artifact"]["artifact_kind"] == "forum_profile_markdown"

        famous = client.get("/api/v1/portrait/scientists/famous", headers=headers)
        assert famous.status_code == 200, famous.text
        famous_payload = famous.json()
        assert len(famous_payload["match"]["top3"]) == 3
        assert famous_payload["artifact"]["artifact_kind"] == "scientist_famous_match"

        field = client.get("/api/v1/portrait/scientists/field", headers=headers)
        assert field.status_code == 200, field.text
        field_payload = field.json()
        assert field_payload["artifact"]["artifact_kind"] == "scientist_field_recommendations"
        assert isinstance(field_payload["recommendations"], list)

        markdown = client.get("/api/v1/portrait/export/profile-markdown", headers=headers)
        assert markdown.status_code == 200, markdown.text
        markdown_payload = markdown.json()
        assert markdown_payload["profile_markdown"].startswith("# ")
        assert markdown_payload["artifact"]["artifact_kind"] == "export_profile_markdown"

        html_export = client.get("/api/v1/portrait/export/profile-html", headers=headers)
        assert html_export.status_code == 200, html_export.text
        html_payload = html_export.json()
        assert "<html" in html_payload["profile_html"].lower()
        assert html_payload["artifact"]["artifact_kind"] == "export_profile_html"

        publish = client.post(
            "/api/v1/portrait/publish",
            headers=headers,
            json={"display_name": "认知结构测试智能体", "visibility": "private", "exposure": "brief"},
        )
        assert publish.status_code == 200, publish.text
        publish_payload = publish.json()
        assert publish_payload["twin"]["twin_id"].startswith("twin_")
        assert publish_payload["artifact"]["artifact_kind"] == "publish_twin"
        assert publish_payload["role_content"].startswith("# 认知结构测试智能体")

        artifacts = client.get("/api/v1/portrait/artifacts?limit=20", headers=headers)
        assert artifacts.status_code == 200, artifacts.text
        artifact_payload = artifacts.json()
        assert len(artifact_payload["artifacts"]) >= 6
        artifact_id = forum_payload["artifact"]["artifact_id"]
        detail = client.get(f"/api/v1/portrait/artifacts/{artifact_id}", headers=headers)
        assert detail.status_code == 200, detail.text
        assert detail.json()["artifact"]["artifact_id"] == artifact_id
