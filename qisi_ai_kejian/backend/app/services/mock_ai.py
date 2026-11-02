"""Mock teacher-agent + outline + 6-page preview. No real model calls."""

from __future__ import annotations

from typing import Any

STYLES: list[dict[str, Any]] = [
    {
        "id": "clean_academic",
        "name": "清学术风",
        "description": "白板底、深蓝点缀，适合高校课堂",
        "palette": ["#F7F9FC", "#1B3A57", "#4A90A4"],
    },
    {
        "id": "warm_classroom",
        "name": "暖课堂风",
        "description": "米白底、墨绿标题，亲和讲授感",
        "palette": ["#FBF7F0", "#2F4F3E", "#C4A35A"],
    },
    {
        "id": "exam_focus",
        "name": "考场聚焦",
        "description": "高对比黑白，题型分区清晰",
        "palette": ["#FFFFFF", "#111111", "#E4572E"],
    },
    {
        "id": "story_visual",
        "name": "图文叙事",
        "description": "大图配要点，适合案例课",
        "palette": ["#0F172A", "#E2E8F0", "#38BDF8"],
    },
]

MODELS: list[dict[str, Any]] = [
    {
        "id": "mock-qisi-lite",
        "name": "奇思 Lite（Mock）",
        "provider": "qisi_mock",
        "description": "本地 mock，响应快，适合联调",
        "recommended": True,
    },
    {
        "id": "mock-hunyuan",
        "name": "混元（Mock）",
        "provider": "tencent_mock",
        "description": "腾讯云混元占位，不发起真实请求",
        "recommended": False,
    },
    {
        "id": "mock-deepseek",
        "name": "DeepSeek（Mock）",
        "provider": "deepseek_mock",
        "description": "第三方模型占位，不发起真实请求",
        "recommended": False,
    },
]


def list_styles() -> list[dict[str, Any]]:
    return STYLES


def list_models() -> list[dict[str, Any]]:
    return MODELS


def teacher_reply(
    content_type: str,
    history: list[dict[str, str]],
    user_text: str,
) -> dict[str, Any]:
    """Rule-based clarifying dialogue. Returns teacher turn + optional outline."""
    turns = len([m for m in history if m["role"] == "user"]) + 1
    kind = "课件" if content_type == "courseware" else "试卷"
    lower = user_text.lower()

    if turns == 1:
        return {
            "content": (
                f"好的，我们先把这份{kind}说清楚再生成。"
                f"你希望面向什么学段/对象？课时大概多久？有没有指定教材或章节？"
            ),
            "clarifying_done": False,
            "suggested_replies": [
                "高一，45 分钟，人教版必修一",
                "初三复习课，两课时",
                "大学通识课，90 分钟",
            ],
            "outline": None,
        }

    if turns == 2:
        return {
            "content": (
                f"明白。这份{kind}最想突出的 2～3 个内容要点是什么？"
                f"有没有必须避开或强调的注意事项（难度、敏感点、考试范围）？"
            ),
            "clarifying_done": False,
            "suggested_replies": [
                "强调概念辨析 + 例题，避开超纲",
                "重难点是公式推导，注意单位换算",
                "覆盖选择题与简答，难度中等",
            ],
            "outline": None,
        }

    # After enough clarification, produce outline
    outline = _build_outline(content_type, history + [{"role": "user", "content": user_text}])
    return {
        "content": (
            f"大纲已经整理好了。请确认「内容要点 / 大纲 / 注意事项」；"
            f"确认后可进入约 6 页预览，并筛选风格与生成模型。"
            + ("（你提到了考试/题目，已按试卷结构整理。）" if "题" in user_text or "exam" in lower else "")
        ),
        "clarifying_done": True,
        "suggested_replies": ["确认大纲，去预览", "再改一下重难点"],
        "outline": outline,
    }


def _build_outline(content_type: str, history: list[dict[str, str]]) -> dict[str, Any]:
    user_bits = "；".join(m["content"] for m in history if m["role"] == "user")
    if content_type == "courseware":
        return {
            "key_points": [
                "明确学习目标与先修知识",
                "核心概念分层讲解",
                "例题 / 互动巩固",
            ],
            "outline": [
                {"section": "导入与目标", "items": ["情境导入", "本节目标"]},
                {"section": "核心知识", "items": ["概念 A", "概念 B", "对比辨析"]},
                {"section": "例题示范", "items": ["基础例", "变式例"]},
                {"section": "小结与作业", "items": ["知识结构图", "课后练习"]},
            ],
            "notes": [
                "控制单页信息密度，口语化讲解",
                "避开超纲内容；单位与符号统一",
                f"教师补充语境：{user_bits[:120]}",
            ],
            "raw_summary": f"课件澄清摘要：{user_bits[:200]}",
        }

    return {
        "key_points": [
            "覆盖目标知识点",
            "题型比例合理",
            "难度梯度清晰",
        ],
        "outline": [
            {"section": "选择题", "items": ["基础概念 4 题", "应用辨析 2 题"]},
            {"section": "填空题", "items": ["公式 / 单位 3 题"]},
            {"section": "简答 / 计算", "items": ["综合题 2 题"]},
            {"section": "参考答案与评分点", "items": ["采分点", "常见错因"]},
        ],
        "notes": [
            "标注预计用时与分值",
            "敏感题干避免超纲表述",
            f"教师补充语境：{user_bits[:120]}",
        ],
        "raw_summary": f"试卷澄清摘要：{user_bits[:200]}",
    }


def build_preview(
    content_type: str,
    outline: dict[str, Any],
    style_id: str,
    model_id: str,
) -> list[dict[str, Any]]:
    """Generate ~6 mock preview pages from outline + style."""
    style = next((s for s in STYLES if s["id"] == style_id), STYLES[0])
    sections = outline.get("outline") or []
    key_points = outline.get("key_points") or []
    notes = outline.get("notes") or []

    pages: list[dict[str, Any]] = [
        {
            "page_no": 1,
            "title": "封面 · " + ("课件预览" if content_type == "courseware" else "试卷预览"),
            "bullets": [
                f"风格：{style['name']}",
                f"模型：{model_id}",
                "（Mock 内容，未调用真实生成接口）",
            ],
            "speaker_note": "开场问候，说明本节安排",
            "mock_image_hint": f"palette={','.join(style['palette'])}",
        },
        {
            "page_no": 2,
            "title": "内容要点",
            "bullets": key_points or ["（待补充要点）"],
            "speaker_note": "用 30 秒过一遍要点",
            "mock_image_hint": "key_points_card",
        },
    ]

    # Map up to 3 outline sections into pages 3–5
    for i, sec in enumerate(sections[:3]):
        pages.append(
            {
                "page_no": 3 + i,
                "title": sec.get("section", f"章节 {i + 1}"),
                "bullets": list(sec.get("items") or ["要点"]),
                "speaker_note": f"讲解「{sec.get('section', '')}」",
                "mock_image_hint": f"section_{i + 1}_{style_id}",
            }
        )

    while len(pages) < 5:
        n = len(pages) + 1
        pages.append(
            {
                "page_no": n,
                "title": f"扩展页 {n}",
                "bullets": ["根据大纲自动补齐的 mock 页"],
                "speaker_note": None,
                "mock_image_hint": "filler",
            }
        )

    pages.append(
        {
            "page_no": 6,
            "title": "注意事项与收尾",
            "bullets": notes[:4] or ["检查符号与难度", "留足互动时间"],
            "speaker_note": "提醒作业与答疑渠道",
            "mock_image_hint": "closing",
        }
    )

    # Ensure exactly 6 pages with sequential numbers
    pages = pages[:6]
    for i, p in enumerate(pages, start=1):
        p["page_no"] = i
    return pages
