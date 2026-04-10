"""Copied old-kernel asset registry, retargeted to local portrait assets."""

from __future__ import annotations

from pathlib import Path

_DEFAULT_SKILL_NAMES = [
    "collect-basic-info",
    "administer-ams",
    "administer-rcss",
    "administer-mini-ipip",
    "infer-profile-dimensions",
    "review-profile",
    "update-profile",
    "generate-forum-profile",
    "generate-ai-memory-prompt",
    "import-ai-memory",
    "modify-profile-schema",
]

_DEFAULT_DOC_NAMES = [
    "academic-motivation-scale",
    "mini-ipip-scale",
    "researcher-cognitive-style",
    "tashan-profile-outline",
    "tashan-profile-examples",
    "multidimensional-work-motivation-scale",
    "implementation-guide",
]


def _assets_root() -> Path:
    return Path(__file__).resolve().parent / "assets"


def _skills_dir() -> Path:
    return _assets_root() / "skills"


def _docs_dir() -> Path:
    return _assets_root() / "docs"


def _template_path() -> Path:
    return _assets_root() / "_template.md"


def list_skill_names() -> list[str]:
    skills_dir = _skills_dir()
    if skills_dir.exists() and skills_dir.is_dir():
        names = sorted(
            path.name
            for path in skills_dir.iterdir()
            if path.is_dir() and (path / "SKILL.md").exists()
        )
        if names:
            return names
    return _DEFAULT_SKILL_NAMES.copy()


def list_doc_names() -> list[str]:
    docs_dir = _docs_dir()
    if docs_dir.exists() and docs_dir.is_dir():
        names = sorted(path.stem for path in docs_dir.glob("*.md") if path.is_file())
        if names:
            return names
    return _DEFAULT_DOC_NAMES.copy()


SKILL_NAMES = list_skill_names()
DOC_NAMES = list_doc_names()


def read_skill(skill_name: str) -> str:
    """Read the copied old skill markdown from the local portrait package."""
    skill_names = list_skill_names()
    if skill_name not in skill_names:
        return f"错误：未知的 skill 名称 '{skill_name}'。可用：{', '.join(skill_names)}"
    path = _skills_dir() / skill_name / "SKILL.md"
    if not path.exists():
        return f"错误：文件不存在 {path}"
    return path.read_text(encoding="utf-8")


def read_doc(doc_name: str) -> str:
    """Read copied old helper docs from the local portrait package."""
    doc_names = list_doc_names()
    if doc_name not in doc_names:
        return f"错误：未知的 doc 名称 '{doc_name}'。可用：{', '.join(doc_names)}"
    path = _docs_dir() / f"{doc_name}.md"
    if not path.exists():
        return f"错误：文件不存在 {path}"
    return path.read_text(encoding="utf-8")


def load_template() -> str:
    """Load the copied old profile markdown template."""
    template_path = _template_path()
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "# 科研数字分身\n\n（空白模板）\n"
