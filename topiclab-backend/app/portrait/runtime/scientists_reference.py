"""Reference scientist set for portrait matching, with legacy fallback when available."""

from __future__ import annotations

from pathlib import Path


_FALLBACK_SCIENTISTS = [
    {
        "name": "理查德·费曼",
        "name_en": "Richard Feynman",
        "field": "理论物理",
        "era": "1918-1988",
        "csi": 18,
        "rai": 55,
        "openness": 4.8,
        "conscientiousness": 2.8,
        "extraversion": 4.5,
        "agreeableness": 2.8,
        "neuroticism": 2.0,
        "signature": "以好奇心为核心驱动，用物理直觉跨越学科边界",
        "match_reason_template": "你们都偏向跨领域整合，并且科研动力更接近内在好奇心。",
    },
    {
        "name": "列奥纳多·达芬奇",
        "name_en": "Leonardo da Vinci",
        "field": "博学家（艺术/工程/解剖/光学）",
        "era": "1452-1519",
        "csi": 24,
        "rai": 52,
        "openness": 5.0,
        "conscientiousness": 2.2,
        "extraversion": 3.5,
        "agreeableness": 3.0,
        "neuroticism": 3.0,
        "signature": "极致跨领域探索者，在艺术与科学之间自由穿行",
        "match_reason_template": "你们都具有极强的跨领域好奇心，喜欢在不同领域间发现隐藏联系。",
    },
    {
        "name": "赫伯特·西蒙",
        "name_en": "Herbert Simon",
        "field": "人工智能/认知科学/管理学",
        "era": "1916-2001",
        "csi": 20,
        "rai": 48,
        "openness": 4.7,
        "conscientiousness": 4.2,
        "extraversion": 3.8,
        "agreeableness": 3.5,
        "neuroticism": 2.0,
        "signature": "在多个学科建立理论框架的系统思想家",
        "match_reason_template": "你们都善于把不同领域的方法组装成系统性框架。",
    },
    {
        "name": "钱学森",
        "name_en": "Qian Xuesen",
        "field": "航天工程/系统科学",
        "era": "1911-2009",
        "csi": 16,
        "rai": 45,
        "openness": 4.5,
        "conscientiousness": 4.5,
        "extraversion": 3.0,
        "agreeableness": 3.2,
        "neuroticism": 2.5,
        "signature": "从工程实践到系统论，连接具体与宏观",
        "match_reason_template": "你们都在保持工程深度的同时追求系统性的宏观建构。",
    },
    {
        "name": "玛丽·居里",
        "name_en": "Marie Curie",
        "field": "放射化学/物理学",
        "era": "1867-1934",
        "csi": 10,
        "rai": 50,
        "openness": 4.3,
        "conscientiousness": 4.8,
        "extraversion": 2.5,
        "agreeableness": 3.5,
        "neuroticism": 3.0,
        "signature": "以极致的实验毅力推动跨物理-化学的新领域",
        "match_reason_template": "你们都兼具跨领域视野和很强的执行韧性。",
    },
    {
        "name": "约翰·冯·诺依曼",
        "name_en": "John von Neumann",
        "field": "数学/计算机/博弈论/量子力学",
        "era": "1903-1957",
        "csi": 22,
        "rai": 42,
        "openness": 4.9,
        "conscientiousness": 3.5,
        "extraversion": 4.0,
        "agreeableness": 2.5,
        "neuroticism": 2.0,
        "signature": "在纯数学和应用之间自如切换的整合者",
        "match_reason_template": "你们都具备在理论与应用之间快速切换的整合能力。",
    },
    {
        "name": "安德鲁·怀尔斯",
        "name_en": "Andrew Wiles",
        "field": "数论",
        "era": "1953-",
        "csi": -20,
        "rai": 56,
        "openness": 4.0,
        "conscientiousness": 4.8,
        "extraversion": 1.8,
        "agreeableness": 3.5,
        "neuroticism": 3.0,
        "signature": "在一个问题上长时间深耕到极致的专精者",
        "match_reason_template": "你们都更愿意在关键问题上持续深挖，而不是快速切换题目。",
    },
    {
        "name": "拉马努金",
        "name_en": "Srinivasa Ramanujan",
        "field": "纯数学",
        "era": "1887-1920",
        "csi": -18,
        "rai": 58,
        "openness": 4.5,
        "conscientiousness": 3.5,
        "extraversion": 1.5,
        "agreeableness": 4.0,
        "neuroticism": 3.5,
        "signature": "凭直觉深入数学核心、独创性极强的天才",
        "match_reason_template": "你们都拥有对核心问题的强直觉和高内驱深耕倾向。",
    },
    {
        "name": "芭芭拉·麦克林托克",
        "name_en": "Barbara McClintock",
        "field": "细胞遗传学",
        "era": "1902-1992",
        "csi": -14,
        "rai": 54,
        "openness": 4.2,
        "conscientiousness": 4.5,
        "extraversion": 2.0,
        "agreeableness": 3.0,
        "neuroticism": 2.5,
        "signature": "在学界质疑中坚持独立研究的深耕者",
        "match_reason_template": "你们都具有在垂直领域长期坚持独立判断的特质。",
    },
    {
        "name": "桑提亚哥·拉蒙-卡哈尔",
        "name_en": "Santiago Ramon y Cajal",
        "field": "神经解剖学",
        "era": "1852-1934",
        "csi": -12,
        "rai": 48,
        "openness": 4.3,
        "conscientiousness": 4.8,
        "extraversion": 2.5,
        "agreeableness": 3.0,
        "neuroticism": 2.5,
        "signature": "用精密观察和手绘揭示神经结构的现代神经科学先驱",
        "match_reason_template": "你们都具备在细分方向中追求极致精确的专注力。",
    },
    {
        "name": "埃米·诺特",
        "name_en": "Emmy Noether",
        "field": "抽象代数/理论物理",
        "era": "1882-1935",
        "csi": -10,
        "rai": 52,
        "openness": 4.4,
        "conscientiousness": 4.0,
        "extraversion": 2.8,
        "agreeableness": 4.2,
        "neuroticism": 2.0,
        "signature": "在抽象结构中发现深层统一性的数学家",
        "match_reason_template": "你们都倾向于在抽象层面深入挖掘，追求理论的内在统一。",
    },
    {
        "name": "托马斯·爱迪生",
        "name_en": "Thomas Edison",
        "field": "发明/工程",
        "era": "1847-1931",
        "csi": 16,
        "rai": 5,
        "openness": 4.0,
        "conscientiousness": 4.5,
        "extraversion": 4.0,
        "agreeableness": 2.0,
        "neuroticism": 2.5,
        "signature": "以目标和落地为导向的系统化发明家",
        "match_reason_template": "你们都善于跨领域整合技术，并关注实际产出与落地。",
    },
]


def _legacy_scientists_path() -> Path:
    return (
        Path(__file__).resolve().parents[5]
        / "Resonnet"
        / "app"
        / "services"
        / "profile_helper"
        / "scientists_db.py"
    )


def load_scientists() -> list[dict]:
    legacy_path = _legacy_scientists_path()
    namespace: dict[str, object] = {}
    if legacy_path.exists() and legacy_path.is_file():
        try:
            exec(legacy_path.read_text(encoding="utf-8"), namespace)
            scientists = namespace.get("SCIENTISTS")
            if isinstance(scientists, list) and scientists:
                return scientists
        except Exception:
            pass
    return list(_FALLBACK_SCIENTISTS)
