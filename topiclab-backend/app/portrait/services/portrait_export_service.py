"""Export current portrait projections into structured, markdown, HTML, PDF, and image artifacts."""

from __future__ import annotations

import html
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from app.portrait.services.portrait_artifact_service import portrait_artifact_service
from app.portrait.services.portrait_forum_service import portrait_forum_service
from app.portrait.services.portrait_projection_service import portrait_projection_service
from app.portrait.services.portrait_scientist_service import portrait_scientist_service


_BROWSER_CANDIDATES = [
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/usr/bin/google-chrome-stable",
    "/usr/bin/google-chrome",
    "/usr/bin/microsoft-edge",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
]


def _find_browser() -> str | None:
    for candidate in _BROWSER_CANDIDATES:
        if Path(candidate).exists():
            return candidate
    return None


def _escape(text_value: Any) -> str:
    return html.escape(str(text_value or ""))


class PortraitExportService:
    """Generate durable exports from current portrait state."""

    def _render_profile_html(
        self,
        *,
        structured_profile: dict[str, Any],
        profile_markdown: str,
        famous_match: dict[str, Any] | None,
        field_recommendations: list[dict[str, Any]] | None,
    ) -> str:
        sections_html = []
        for section_name in [
            "Identity",
            "Capability",
            "Current Needs",
            "Cognitive Style",
            "Motivation",
            "Personality",
            "Interpretation",
            "Dialogue Snapshot",
        ]:
            anchor = f"## {section_name}"
            body = ""
            capture = False
            lines: list[str] = []
            for raw_line in profile_markdown.splitlines():
                if raw_line.startswith("## "):
                    capture = raw_line.strip() == anchor
                    continue
                if capture:
                    lines.append(raw_line)
            if lines:
                body = "<br/>".join(_escape(line) for line in lines if line.strip())
                sections_html.append(f"<section><h2>{_escape(section_name)}</h2><p>{body}</p></section>")

        scientist_html = ""
        if famous_match:
            top3_html = "".join(
                [
                    "<li><strong>{name}</strong> ({field}) - {similarity}%<br/>{reason}</li>".format(
                        name=_escape(item.get("name")),
                        field=_escape(item.get("field")),
                        similarity=_escape(item.get("similarity")),
                        reason=_escape(item.get("reason")),
                    )
                    for item in famous_match.get("top3") or []
                ]
            )
            scientist_html += f"<section><h2>Scientist Match</h2><ul>{top3_html}</ul></section>"
        if field_recommendations:
            rec_html = "".join(
                [
                    "<li><strong>{name}</strong> - {field}<br/>{reason}</li>".format(
                        name=_escape(item.get("name")),
                        field=_escape(item.get("field")),
                        reason=_escape(item.get("reason")),
                    )
                    for item in field_recommendations
                ]
            )
            scientist_html += f"<section><h2>Field Recommendations</h2><ul>{rec_html}</ul></section>"

        return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>{_escape(structured_profile.get('display_name'))}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 40px auto; max-width: 920px; color: #111827; line-height: 1.75; padding: 0 24px; }}
    h1 {{ font-size: 32px; margin-bottom: 8px; }}
    h2 {{ font-size: 20px; margin: 28px 0 10px; border-left: 4px solid #111827; padding-left: 10px; }}
    .meta {{ color: #6b7280; margin-bottom: 24px; }}
    section {{ margin-bottom: 24px; }}
    ul {{ padding-left: 20px; }}
    li {{ margin-bottom: 12px; }}
  </style>
</head>
<body>
  <h1>{_escape(structured_profile.get('display_name'))}</h1>
  <div class="meta">由 TopicLab portrait export runtime 生成</div>
  {''.join(sections_html)}
  {scientist_html}
</body>
</html>
"""

    def _render_binary(self, *, html_content: str, mode: str) -> bytes:
        browser = _find_browser()
        if not browser:
            raise RuntimeError("No browser runtime found for PDF/image export")

        with tempfile.TemporaryDirectory() as temp_dir:
            html_path = Path(temp_dir) / "portrait.html"
            html_path.write_text(html_content, encoding="utf-8")
            output_path = Path(temp_dir) / ("portrait.pdf" if mode == "pdf" else "portrait.png")
            last_error: str | None = None

            for headless_flag in ("--headless=new", "--headless"):
                command = [
                    browser,
                    headless_flag,
                    "--disable-gpu",
                    "--no-sandbox",
                    f"file://{html_path}",
                ]
                if mode == "pdf":
                    command.append(f"--print-to-pdf={output_path}")
                else:
                    command.extend([f"--screenshot={output_path}", "--window-size=1440,2600"])

                try:
                    subprocess.run(command, check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as exc:
                    last_error = (exc.stderr or exc.stdout or str(exc)).strip() or str(exc)
                    continue

                if output_path.exists():
                    return output_path.read_bytes()
                last_error = f"browser command succeeded but no output file was produced: {output_path}"

            raise RuntimeError(f"Browser render failed for {mode} export: {last_error or 'unknown error'}")

    def export_structured(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="export_structured_profile",
            format="json",
            title=f"{projection['structured_profile']['display_name']} structured profile",
            content_json=projection["structured_profile"],
        )
        return {"projection": projection, "structured_profile": projection["structured_profile"], "artifact": artifact}

    def export_profile_markdown(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="export_profile_markdown",
            format="markdown",
            title=f"{projection['structured_profile']['display_name']} profile markdown",
            content_text=projection["profile_markdown"],
        )
        return {"projection": projection, "profile_markdown": projection["profile_markdown"], "artifact": artifact}

    def export_forum_markdown(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None, **forum_options) -> dict[str, Any]:
        return portrait_forum_service.generate_forum_profile(
            user_id=user_id,
            display_name=display_name,
            source_session_id=source_session_id,
            **forum_options,
        )

    async def export_profile_html(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        projection = portrait_projection_service.build_projection(user_id, display_name=display_name)
        famous = portrait_scientist_service.build_famous_match(projection)
        field_recommendations = portrait_scientist_service._fallback_field_recommendations(projection["structured_profile"])
        html_content = self._render_profile_html(
            structured_profile=projection["structured_profile"],
            profile_markdown=projection["profile_markdown"],
            famous_match=famous,
            field_recommendations=field_recommendations,
        )
        artifact = portrait_artifact_service.record_artifact(
            user_id=user_id,
            portrait_state_id=projection["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="export_profile_html",
            format="html",
            title=f"{projection['structured_profile']['display_name']} profile html",
            content_text=html_content,
        )
        return {"projection": projection, "profile_html": html_content, "artifact": artifact}

    async def export_profile_pdf(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        html_export = await self.export_profile_html(user_id=user_id, display_name=display_name, source_session_id=source_session_id)
        pdf_bytes = self._render_binary(html_content=html_export["profile_html"], mode="pdf")
        display_label = html_export["projection"]["structured_profile"]["display_name"]
        artifact = portrait_artifact_service.record_binary_artifact(
            user_id=user_id,
            portrait_state_id=html_export["projection"]["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="export_profile_pdf",
            format="pdf",
            title=f"{display_label} profile pdf",
            file_name=f"{display_label}-profile.pdf",
            content_type="application/pdf",
            payload=pdf_bytes,
            metadata_json={"source_html_artifact_id": html_export["artifact"]["artifact_id"], "byte_length": len(pdf_bytes)},
        )
        return {
            "projection": html_export["projection"],
            "artifact": artifact,
            "media_bytes": pdf_bytes,
            "media_type": "application/pdf",
            "filename": artifact["artifact_filename"] or "profile.pdf",
        }

    async def export_profile_image(self, *, user_id: int, display_name: str | None = None, source_session_id: str | None = None) -> dict[str, Any]:
        html_export = await self.export_profile_html(user_id=user_id, display_name=display_name, source_session_id=source_session_id)
        image_bytes = self._render_binary(html_content=html_export["profile_html"], mode="image")
        display_label = html_export["projection"]["structured_profile"]["display_name"]
        artifact = portrait_artifact_service.record_binary_artifact(
            user_id=user_id,
            portrait_state_id=html_export["projection"]["portrait_state_id"],
            source_session_id=source_session_id,
            artifact_kind="export_profile_image",
            format="png",
            title=f"{display_label} profile image",
            file_name=f"{display_label}-profile.png",
            content_type="image/png",
            payload=image_bytes,
            metadata_json={"source_html_artifact_id": html_export["artifact"]["artifact_id"], "byte_length": len(image_bytes)},
        )
        return {
            "projection": html_export["projection"],
            "artifact": artifact,
            "media_bytes": image_bytes,
            "media_type": "image/png",
            "filename": artifact["artifact_filename"] or "profile.png",
        }


portrait_export_service = PortraitExportService()
