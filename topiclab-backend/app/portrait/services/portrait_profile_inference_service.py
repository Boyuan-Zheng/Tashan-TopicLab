"""Deterministic old-product-compatible profile dimension inference."""

from __future__ import annotations

from typing import Any


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round1(value: float) -> float:
    return round(value, 1)


def _score_to_level(score: float, *, high: float, medium: float) -> str:
    if score >= high:
        return "高"
    if score >= medium:
        return "中"
    return "低"


class PortraitProfileInferenceService:
    """Rebuild old infer-profile-dimensions semantics above canonical portrait state."""

    process_dimension_map = {
        "problem_definition": "问题定义",
        "literature": "文献整合",
        "design": "方案设计",
        "execution": "实验执行",
        "writing": "论文写作",
        "management": "项目管理",
    }

    def _extract_inputs(self, current_state: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
        state_json = current_state.get("state_json") or {}
        profile = state_json.get("profile") or {}
        basic_info = profile.get("basic_info") or {}
        capability = profile.get("capability") or {}
        current_needs = profile.get("current_needs") or {}
        return state_json, basic_info, capability, current_needs

    def _infer_cognitive_style(self, basic_info: dict[str, Any], capability: dict[str, Any]) -> dict[str, Any]:
        method = str(basic_info.get("method_paradigm") or basic_info.get("method_statement") or "")
        cross = str(basic_info.get("cross_discipline") or "")
        academic_network = str(basic_info.get("academic_network") or "")
        tech_stack_text = str(capability.get("tech_stack_text") or "")
        outputs = str(capability.get("representative_outputs") or "")
        process = capability.get("process") or {}

        integration = 14.0
        depth = 14.0
        evidence: list[str] = []

        if "计算" in method or "数据" in method:
            integration += 3
            evidence.append("研究方法偏计算/数据驱动")
        if "实验" in method or "理论" in method:
            depth += 3
            evidence.append("研究方法包含实验/理论推导")
        if cross:
            integration += 4
            evidence.append("明确存在交叉学科方向")
        if any(token in academic_network for token in ["跨机构", "跨学科", "合作"]):
            integration += 2
            evidence.append("合作网络具有跨机构/跨学科特征")
        if tech_stack_text:
            separators = tech_stack_text.count("、") + tech_stack_text.count(",") + tech_stack_text.count("，") + tech_stack_text.count("/")
            if separators >= 2:
                integration += 2
                evidence.append("技术栈呈现多工具/多框架组合")
            if any(token in tech_stack_text for token in ["调优", "推导", "贝叶斯", "数学", "实验"]):
                depth += 1
        if outputs:
            depth += 1
            evidence.append("已有代表性产出支撑纵深积累")

        design_score = float((process.get("design") or {}).get("score") or 0)
        literature_score = float((process.get("literature") or {}).get("score") or 0)
        execution_score = float((process.get("execution") or {}).get("score") or 0)
        if design_score >= 4 or literature_score >= 4:
            depth += 1
        if execution_score >= 4:
            depth += 1

        integration = _clamp(integration, 4, 28)
        depth = _clamp(depth, 4, 28)
        csi = integration - depth

        if csi >= 7:
            style_type = "倾向整合型"
        elif csi <= -7:
            style_type = "倾向深度型"
        else:
            style_type = "相对平衡型"

        confidence = "高" if len(evidence) >= 4 else "中" if len(evidence) >= 2 else "低"
        return {
            "integration": _round1(integration),
            "depth": _round1(depth),
            "csi": _round1(csi),
            "type": style_type,
            "confidence": confidence,
            "evidence": evidence[:6],
        }

    def _infer_motivation(
        self,
        basic_info: dict[str, Any],
        capability: dict[str, Any],
        current_needs: dict[str, Any],
    ) -> dict[str, Any]:
        stage = str(basic_info.get("research_stage") or "")
        outputs = str(capability.get("representative_outputs") or "")
        process = capability.get("process") or {}
        pain_points = str(current_needs.get("pain_points") or "")
        desired_change = str(current_needs.get("desired_change") or "")
        tech_stack = str(capability.get("tech_stack_text") or "")
        cross = str(basic_info.get("cross_discipline") or "")

        writing = float((process.get("writing") or {}).get("score") or 0)
        execution = float((process.get("execution") or {}).get("score") or 0)
        management = float((process.get("management") or {}).get("score") or 0)

        know = 4.8
        accomplishment = 4.5
        stimulation = 4.1
        identified = 4.7
        introjected = 3.2
        external = 2.3
        amotivation = 1.8
        evidence: list[str] = []

        if outputs:
            know += 0.6
            accomplishment += 0.8
            evidence.append("已有代表性产出")
        if cross or any(token in tech_stack for token in ["Python", "PyTorch", "JAX", "MATLAB", "MNE", "SPM"]):
            know += 0.4
            stimulation += 0.3
            evidence.append("存在跨领域技术探索")
        if "博士生" in stage or "博士后" in stage:
            introjected += 0.2
            evidence.append("当前处于高竞争研究阶段")
        if writing and writing < 3.5 and execution >= 4:
            stimulation += 0.3
            external += 0.2
            evidence.append("执行力较高但写作压力仍在")
        if management >= 4:
            identified += 0.2
        if pain_points:
            introjected += 0.3
            amotivation += 0.1
        if desired_change:
            identified += 0.2

        scores = {
            "to_know": _round1(_clamp(know, 1, 7)),
            "toward_accomplishment": _round1(_clamp(accomplishment, 1, 7)),
            "to_experience_stimulation": _round1(_clamp(stimulation, 1, 7)),
            "identified": _round1(_clamp(identified, 1, 7)),
            "introjected": _round1(_clamp(introjected, 1, 7)),
            "external": _round1(_clamp(external, 1, 7)),
            "amotivation": _round1(_clamp(amotivation, 1, 7)),
        }
        rai = _round1(
            3 * scores["to_know"]
            + 3 * scores["toward_accomplishment"]
            + 3 * scores["to_experience_stimulation"]
            + 2 * scores["identified"]
            - scores["introjected"]
            - 2 * scores["external"]
            - 3 * scores["amotivation"]
        )
        scores["rai"] = rai
        scores["confidence"] = "高" if len(evidence) >= 4 else "中" if len(evidence) >= 2 else "低"
        scores["evidence"] = evidence[:6]
        return scores

    def _infer_personality(
        self,
        basic_info: dict[str, Any],
        capability: dict[str, Any],
        current_needs: dict[str, Any],
    ) -> dict[str, Any]:
        academic_network = str(basic_info.get("academic_network") or "")
        cross = str(basic_info.get("cross_discipline") or "")
        tech_stack = str(capability.get("tech_stack_text") or "")
        process = capability.get("process") or {}
        pain_points = str(current_needs.get("pain_points") or "")

        openness = 3.8
        extraversion = 2.8
        agreeableness = 3.1
        conscientiousness = 3.0
        neuroticism = 2.8
        evidence: list[str] = []

        if cross or any(token in tech_stack for token in ["Python", "PyTorch", "JAX", "MATLAB", "统计", "贝叶斯"]):
            openness += 0.8
            evidence.append("跨领域方向与多样技术栈提升开放性估计")
        if any(token in academic_network for token in ["跨机构", "跨学科", "合作", "团队"]):
            extraversion += 0.5
            agreeableness += 0.3
            evidence.append("合作网络存在外部协作信号")

        execution = float((process.get("execution") or {}).get("score") or 0)
        writing = float((process.get("writing") or {}).get("score") or 0)
        management = float((process.get("management") or {}).get("score") or 0)
        if execution >= 4 or writing >= 4 or management >= 4:
            conscientiousness += 0.8
            evidence.append("科研流程能力中执行/写作/管理较强")
        if pain_points:
            neuroticism += 0.4
        if management >= 4 and any(token in academic_network for token in ["合作", "团队"]):
            extraversion += 0.2

        values = {
            "extraversion": _round1(_clamp(extraversion, 1, 5)),
            "agreeableness": _round1(_clamp(agreeableness, 1, 5)),
            "conscientiousness": _round1(_clamp(conscientiousness, 1, 5)),
            "neuroticism": _round1(_clamp(neuroticism, 1, 5)),
            "openness": _round1(_clamp(openness, 1, 5)),
        }
        values["levels"] = {
            key: _score_to_level(score, high=4.1, medium=3.0)
            for key, score in values.items()
            if isinstance(score, (int, float))
        }
        values["confidence"] = "高" if len(evidence) >= 3 else "中" if len(evidence) >= 2 else "低"
        values["evidence"] = evidence[:6]
        return values

    def _build_interpretation(
        self,
        *,
        basic_info: dict[str, Any],
        capability: dict[str, Any],
        current_needs: dict[str, Any],
        cognitive_style: dict[str, Any],
        motivation: dict[str, Any],
        personality: dict[str, Any],
    ) -> dict[str, Any]:
        stage = str(basic_info.get("research_stage") or "科研阶段")
        field = str(basic_info.get("primary_field") or "当前研究方向")
        change = str(current_needs.get("desired_change") or "提升当前核心工作的推进效率")
        pain = str(current_needs.get("pain_points") or "")
        process = capability.get("process") or {}
        weaker_dims = [
            self.process_dimension_map[key]
            for key, value in process.items()
            if isinstance(value, dict) and float(value.get("score") or 0) and float(value.get("score") or 0) <= 3
        ]

        core_driver = (
            f"你当前更像一位以{field}为主轴、在 {stage} 阶段持续推进的研究者。"
            f" 从推断结果看，你的核心驱动力来自 {cognitive_style['type']} 的认知取向，"
            f"以及较强的自主学术动机（RAI={motivation['rai']}）。"
        )
        risks = []
        if pain:
            risks.append(f"当前最明显的风险是：{pain}")
        if weaker_dims:
            risks.append(f"在科研流程上，{ '、'.join(weaker_dims[:3]) } 可能是更容易形成瓶颈的环节。")
        if personality["neuroticism"] >= 3.4:
            risks.append("在关键节点前后的压力反应可能偏高，建议增加进度拆分和外部反馈节奏。")
        if not risks:
            risks.append("当前未发现明显结构性短板，但仍建议定期用量表或回顾校准画像。")

        paths = [
            f"围绕“{change}”设置接下来三个月的阶段性目标，并把它拆成可执行的小里程碑。",
            "优先把当前画像中的推断维度逐步用正式量表或真实产出记录校准。",
        ]
        return {
            "core_driver": core_driver,
            "risks": risks[:3],
            "paths": paths[:2],
        }

    def infer_from_current_state(self, current_state: dict[str, Any]) -> dict[str, Any]:
        state_json, basic_info, capability, current_needs = self._extract_inputs(current_state)
        cognitive_style = self._infer_cognitive_style(basic_info, capability)
        motivation = self._infer_motivation(basic_info, capability, current_needs)
        personality = self._infer_personality(basic_info, capability, current_needs)
        interpretation = self._build_interpretation(
            basic_info=basic_info,
            capability=capability,
            current_needs=current_needs,
            cognitive_style=cognitive_style,
            motivation=motivation,
            personality=personality,
        )

        source = "混合" if state_json.get("scales") else "AI推断"
        patch = {
            "profile": {
                "meta": {
                    "collection_stage": "inferred_done",
                    "data_source": source,
                },
                "inferred_dimensions": {
                    "source": "AI推断",
                    "cognitive_style": cognitive_style,
                    "motivation": motivation,
                    "personality": personality,
                    "interpretation": interpretation,
                },
            }
        }
        return {
            "state_patch_json": patch,
            "change_summary_json": {
                "source_type": "manual",
                "source_id": "legacy_skill:infer-profile-dimensions:auto",
                "skill_id": "infer-profile-dimensions",
                "fields_written": ["profile.inferred_dimensions", "profile.meta.collection_stage", "profile.meta.data_source"],
                "source_label": "legacy_skill_inference",
            },
            "observation_json": {
                "kind": "legacy_skill_inferred_dimensions",
                "cognitive_style_type": cognitive_style["type"],
                "motivation_rai": motivation["rai"],
                "personality_openness": personality["openness"],
            },
            "summary": {
                "cognitive_style": cognitive_style,
                "motivation": motivation,
                "personality": personality,
                "interpretation": interpretation,
            },
        }


portrait_profile_inference_service = PortraitProfileInferenceService()
