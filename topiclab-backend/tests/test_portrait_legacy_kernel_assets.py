from app.portrait.legacy_kernel import list_doc_names, list_skill_names, load_template, read_doc, read_skill


def test_legacy_kernel_assets_are_packaged_locally():
    skills = list_skill_names()
    docs = list_doc_names()

    assert "collect-basic-info" in skills
    assert "review-profile" in skills
    assert "academic-motivation-scale" in docs
    assert "tashan-profile-outline" in docs


def test_legacy_kernel_reads_copied_skill_and_doc_content():
    skill_text = read_skill("generate-ai-memory-prompt")
    doc_text = read_doc("researcher-cognitive-style")
    template_text = load_template()

    assert "生成 AI 记忆提取提示词" in skill_text
    assert "RCSS" in doc_text
    assert "科研人员画像" in template_text
