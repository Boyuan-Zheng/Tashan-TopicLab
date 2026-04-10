"""Publish current portrait projection into twin runtime and legacy-compatible twin storage."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from app.portrait.services.portrait_artifact_service import portrait_artifact_service
from app.portrait.services.portrait_export_service import portrait_export_service
from app.portrait.services.portrait_forum_service import portrait_forum_service
from app.portrait.services.portrait_projection_service import portrait_projection_service
from app.services.twin_runtime import create_or_update_active_twin_for_user
from app.storage.database.postgres_client import get_db_session


class PortraitPublishService:
    """Materialize the current portrait into TopicLab's twin runtime."""

    def _upsert_legacy_digital_twin(
        self,
        *,
        user_id: int,
        agent_name: str,
        display_name: str,
        expert_name: str,
        visibility: str,
        exposure: str,
        source: str,
        role_content: str,
    ) -> None:
        now = datetime.now(timezone.utc)
        with get_db_session() as db_session:
            db_session.execute(
                text(
                    """
                    INSERT INTO digital_twins (
                        user_id, agent_name, display_name, expert_name,
                        visibility, exposure, session_id, source, role_content, updated_at
                    ) VALUES (
                        :user_id, :agent_name, :display_name, :expert_name,
                        :visibility, :exposure, NULL, :source, :role_content, :updated_at
                    )
                    ON CONFLICT (user_id, agent_name)
                    DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        expert_name = EXCLUDED.expert_name,
                        visibility = EXCLUDED.visibility,
                        exposure = EXCLUDED.exposure,
                        source = EXCLUDED.source,
                        role_content = EXCLUDED.role_content,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "user_id": user_id,
                    "agent_name": agent_name,
                    "display_name": display_name,
                    "expert_name": expert_name,
                    "visibility": visibility,
                    "exposure": exposure,
                    "source": source,
                    "role_content": role_content,
                    "updated_at": now,
                },
            )

    def publish(
        self,
        *,
        user_id: int,
        display_name: str | None = None,
        visibility: str = "private",
        exposure: str = "brief",
        source_session_id: str | None = None,
        forum_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if visibility not in {"private", "public"}:
            raise ValueError("visibility must be private or public")
        if exposure not in {"brief", "full"}:
            raise ValueError("exposure must be brief or full")

        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        effective_name = projection["structured_profile"]["display_name"]
        if exposure == "brief":
            forum_export = portrait_forum_service.generate_forum_profile(
                user_id=user_id,
                display_name=effective_name,
                source_session_id=source_session_id,
                **(forum_options or {}),
            )
            role_content = forum_export["forum_profile_markdown"]
            source_artifact_id = forum_export["artifact"]["artifact_id"]
        else:
            profile_export = portrait_export_service.export_profile_markdown(
                user_id=user_id,
                display_name=effective_name,
                source_session_id=source_session_id,
            )
            role_content = profile_export["profile_markdown"]
            source_artifact_id = profile_export["artifact"]["artifact_id"]

        agent_name = "my_twin"
        expert_name = effective_name
        source = "portrait_publish"
        self._upsert_legacy_digital_twin(
            user_id=user_id,
            agent_name=agent_name,
            display_name=effective_name,
            expert_name=expert_name,
            visibility=visibility,
            exposure=exposure,
            source=source,
            role_content=role_content,
        )
        twin = create_or_update_active_twin_for_user(
            user_id,
            source_agent_name=agent_name,
            display_name=effective_name,
            expert_name=expert_name,
            visibility=visibility,
            exposure=exposure,
            base_profile_markdown=role_content,
            source=source,
        )
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="publish_twin",
            format="json",
            title=f"{effective_name} published twin",
            content_json={
                "twin_id": twin.get("twin_id"),
                "version": twin.get("version"),
                "visibility": visibility,
                "exposure": exposure,
                "display_name": effective_name,
                "agent_name": agent_name,
            },
            metadata_json={"source_artifact_id": source_artifact_id},
        )
        return {"projection": projection, "twin": twin, "artifact": artifact, "role_content": role_content}


portrait_publish_service = PortraitPublishService()
