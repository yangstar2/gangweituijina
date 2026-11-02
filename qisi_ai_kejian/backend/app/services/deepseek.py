"""DeepSeek OpenAI-compatible client for PPT thinking + structured outline.

Uses deepseek-reasoner when configured; falls back to deepseek-chat with
explicit chain-of-thought, then to local mock if no API key or on failure.
Never log or return the API key.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..config import settings
from . import mock_ai, teacher_prep


@dataclass
class ThinkResult:
    provider: str  # deepseek | mock
    model: str
    thinking: str
    thinking_steps: list[dict[str, str]] = field(default_factory=list)
    outline: dict[str, Any] = field(default_factory=dict)
    raw_content: str | None = None
    used_mock_fallback: bool = False
    error: str | None = None
    skill_slug: str | None = None
    skill_path: str | None = None
    skill_context: dict[str, Any] = field(default_factory=dict)


def is_configured() -> bool:
    return bool((settings.deepseek_api_key or "").strip())


def _steps_from_thinking(thinking: str) -> list[dict[str, str]]:
    """Split reasoning into short UI steps."""
    text = (thinking or "").strip()
    if not text:
        return [
            {"title": "锚定学情", "detail": "年级、班级水平与先修薄弱点"},
            {"title": "设定目标", "detail": "写出可检测的课堂学习目标"},
            {"title": "编排节段", "detail": "导入→概念→例题→练习→小结"},
        ]
    chunks = re.split(r"\n{2,}|(?<=[。！？\n])\s*(?=\d+[\.、．]|\*|•|- )", text)
    chunks = [c.strip() for c in chunks if c and c.strip()]
    labels = ["锚定学情", "设定目标", "设计钩子", "编排节段", "课标校准", "整理大纲"]
    steps: list[dict[str, str]] = []
    for i, chunk in enumerate(chunks[:6]):
        title = labels[i] if i < len(labels) else f"思考 {i + 1}"
        detail = chunk.replace("\n", " ")
        if len(detail) > 160:
            detail = detail[:157] + "…"
        steps.append({"title": title, "detail": detail})
    if not steps:
        steps.append({"title": "教学推理", "detail": text[:160]})
    return steps


def _extract_json_object(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    cleaned = text.strip()
    # Strip common markdown fences
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", cleaned, re.I)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        obj = json.loads(cleaned)
        return obj if isinstance(obj, dict) else None
    except json.JSONDecodeError:
        pass
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(cleaned[start : end + 1])
            return obj if isinstance(obj, dict) else None
        except json.JSONDecodeError:
            return None
    return None


def _normalize_outline(raw: dict[str, Any] | None, fallback: dict[str, Any]) -> dict[str, Any]:
    src = raw or {}
    key_points = src.get("key_points") or fallback.get("key_points") or []
    outline = src.get("outline") or fallback.get("outline") or []
    notes = src.get("notes") or fallback.get("notes") or []
    raw_summary = src.get("raw_summary") or fallback.get("raw_summary")

    norm_sections: list[dict[str, Any]] = []
    for sec in outline:
        if not isinstance(sec, dict):
            continue
        section = str(sec.get("section") or sec.get("title") or "章节").strip()
        items = sec.get("items") or sec.get("bullets") or []
        if isinstance(items, str):
            items = [items]
        items = [str(x).strip() for x in items if str(x).strip()]
        phase = sec.get("phase")
        if section:
            entry: dict[str, Any] = {"section": section, "items": items or ["要点"]}
            if phase:
                entry["phase"] = str(phase).strip()
            norm_sections.append(entry)

    return {
        "key_points": [str(x).strip() for x in key_points if str(x).strip()][:8]
        or fallback.get("key_points")
        or ["明确可检测的学习目标"],
        "outline": norm_sections
        or fallback.get("outline")
        or [{"section": "导入与目标", "items": ["情境钩子", "目标说明"], "phase": "导入"}],
        "notes": [str(x).strip() for x in notes if str(x).strip()][:8]
        or fallback.get("notes")
        or ["控制单页信息密度", "紧扣课标不超纲"],
        "raw_summary": (str(raw_summary).strip() if raw_summary else None)
        or fallback.get("raw_summary"),
    }


def _build_messages(
    content_type: str,
    history: list[dict[str, str]],
    existing_outline: dict[str, Any] | None,
    title: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Prefer teacher-prep-skill template; fall back to legacy ad-hoc prompt."""
    if teacher_prep.is_available():
        return teacher_prep.build_think_messages(
            content_type, history, existing_outline, title=title
        )
    kind = "课件 PPT" if content_type == "courseware" else "试卷"
    sys = (
        "你是资深教研助手。根据师生对话澄清结果，先深度推理，再输出结构化"
        f"{kind}大纲 JSON。最终回复必须是单个 JSON 对象，字段："
        "key_points (string[]), outline ({section, items[]}[]), notes (string[]), "
        "raw_summary (string)。不要包裹多余说明。"
    )
    lines = []
    for m in history:
        role = m.get("role") or "user"
        label = "教师助手" if role == "teacher" else "用户"
        lines.append(f"{label}: {m.get('content', '')}")
    user_blob = "\n".join(lines) if lines else "（尚无对话，请给通用培训课件大纲）"
    if existing_outline:
        user_blob += "\n\n已有草稿大纲（可 refining）:\n" + json.dumps(
            existing_outline, ensure_ascii=False
        )
    user_blob += (
        "\n\n请输出适合课堂教学的大纲；章节 3～6 个，每节 2～4 个要点。"
    )
    return [
        {"role": "system", "content": sys},
        {"role": "user", "content": user_blob},
    ], {}


def _mock_think(
    content_type: str,
    history: list[dict[str, str]],
    existing_outline: dict[str, Any] | None,
    error: str | None = None,
    title: str | None = None,
) -> ThinkResult:
    skill_ctx: dict[str, Any] = {}
    if existing_outline and existing_outline.get("outline"):
        outline = _normalize_outline(existing_outline, existing_outline)
        if teacher_prep.is_available():
            skill_ctx = teacher_prep.resolve_skill_context(history, title)
    elif teacher_prep.is_available():
        raw = teacher_prep.outline_from_skill_fallback(content_type, history, title)
        skill_ctx = raw.pop("_skill_context", {}) or {}
        outline = _normalize_outline(raw, raw)
    else:
        outline = mock_ai._build_outline(content_type, history)  # noqa: SLF001 — shared stub
    bits = "；".join(m["content"] for m in history if m.get("role") == "user")[:120]
    skill_line = ""
    if teacher_prep.is_available():
        skill_line = (
            f"\n0. 加载 teacher-prep-skill（{teacher_prep.skill_install_path()}），"
            f"匹配教材 {skill_ctx.get('version_id') or '通用'} / "
            f"知识点 {len(skill_ctx.get('knowledge_points') or [])} 个\n"
        )
    thinking = (
        "（Mock 教学推理，未调用 DeepSeek；大纲由 teacher-prep-skill 驱动）\n"
        if teacher_prep.is_available()
        else "（Mock 教学推理，未调用 DeepSeek）\n"
    )
    kps = skill_ctx.get("knowledge_points") or []
    thinking += (
        f"{skill_line}"
        f"1. 锚定学情：对话线索「{bits or '通用课堂'}」；"
        f"班级约 {skill_ctx.get('hints', {}).get('student_count') or 40} 人，"
        f"风格 {skill_ctx.get('hints', {}).get('teaching_style') or '讲练结合'}。\n"
        f"2. 设定目标：落实「{(kps[0] if kps else '本节核心概念')}」可检测掌握。\n"
        f"3. 设计钩子：用生活情境唤醒先修「{('、'.join(kps[:2]) if kps else '旧知')}」。\n"
        "4. 编排节段：导入(5′)→概念建构(12′)→例题精讲(15′)→变式练习(10′)→小结(3′)。\n"
        f"5. 课标校准：严格限定 {(('、'.join(kps[:4])) if kps else '本节知识点')}，不超纲。\n"
        "6. 整理大纲：产出可直接生成课堂 PPT 的结构化章节。"
    )
    return ThinkResult(
        provider="mock",
        model="mock-qisi-lite",
        thinking=thinking,
        thinking_steps=_steps_from_thinking(thinking),
        outline=outline,
        used_mock_fallback=True,
        error=error,
        skill_slug=teacher_prep.SKILL_ORG_SLUG if teacher_prep.is_available() else None,
        skill_path=teacher_prep.skill_install_path(),
        skill_context=skill_ctx,
    )


def _chat_completions(model: str, messages: list[dict[str, str]]) -> dict[str, Any]:
    base = (settings.deepseek_api_base or "https://api.deepseek.com").rstrip("/")
    url = f"{base}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.deepseek_api_key.strip()}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    with httpx.Client(timeout=settings.deepseek_timeout_sec) as client:
        resp = client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        return resp.json()


def _parse_completion(data: dict[str, Any]) -> tuple[str, str]:
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    thinking = (
        message.get("reasoning_content")
        or message.get("reasoning")
        or ""
    )
    content = message.get("content") or ""
    # deepseek-chat CoT: optional <think>...</think>
    if not thinking and content:
        m = re.search(r"<think>([\s\S]*?)</think>", content, re.I)
        if m:
            thinking = m.group(1).strip()
            content = (content[: m.start()] + content[m.end() :]).strip()
        else:
            m2 = re.search(r"<thinking>([\s\S]*?)</thinking>", content, re.I)
            if m2:
                thinking = m2.group(1).strip()
                content = (content[: m2.start()] + content[m2.end() :]).strip()
    return str(thinking or ""), str(content or "")


def think_ppt_content(
    content_type: str,
    history: list[dict[str, str]],
    existing_outline: dict[str, Any] | None = None,
    title: str | None = None,
) -> ThinkResult:
    """Run DeepSeek reasoning + structured outline; mock if unconfigured."""
    if teacher_prep.is_available() and not (existing_outline and existing_outline.get("outline")):
        fallback_outline = teacher_prep.outline_from_skill_fallback(
            content_type, history, title
        )
        fallback_outline.pop("_skill_context", None)
    else:
        fallback_outline = existing_outline or mock_ai._build_outline(  # noqa: SLF001
            content_type, history
        )

    if not is_configured():
        return _mock_think(content_type, history, existing_outline, title=title)

    messages, skill_ctx = _build_messages(
        content_type, history, existing_outline, title=title
    )
    preferred = (settings.deepseek_model or "deepseek-reasoner").strip()
    fallback_model = (settings.deepseek_fallback_model or "deepseek-chat").strip()
    models_to_try = [preferred]
    if fallback_model and fallback_model != preferred:
        models_to_try.append(fallback_model)

    last_err: str | None = None
    for idx, model in enumerate(models_to_try):
        try:
            msgs = list(messages)
            if model == fallback_model and model != "deepseek-reasoner":
                msgs = [
                    msgs[0],
                    {
                        "role": "user",
                        "content": (
                            msgs[1]["content"]
                            + "\n\n请先在 <think>…</think> 中按"
                            "「学情→目标→钩子→节段→课标」写出教学推理，"
                            "禁止空泛套话，然后再输出最终 JSON。"
                        ),
                    },
                ]
            data = _chat_completions(model, msgs)
            thinking, content = _parse_completion(data)
            parsed = _extract_json_object(content)
            outline = _normalize_outline(parsed, fallback_outline)
            if not thinking:
                thinking = (
                    f"已使用 {model} + teacher-prep-skill 完成结构化推理，并生成课件大纲。"
                    if content
                    else f"模型 {model} 返回为空，已合并草稿大纲。"
                )
            return ThinkResult(
                provider="deepseek",
                model=model,
                thinking=thinking,
                thinking_steps=_steps_from_thinking(thinking),
                outline=outline,
                raw_content=content,
                used_mock_fallback=False,
                skill_slug=teacher_prep.SKILL_ORG_SLUG if teacher_prep.is_available() else None,
                skill_path=teacher_prep.skill_install_path(),
                skill_context={
                    "version_id": skill_ctx.get("version_id"),
                    "knowledge_points": skill_ctx.get("knowledge_points") or [],
                    "template_filled": bool(skill_ctx.get("template_filled")),
                },
            )
        except Exception as exc:  # noqa: BLE001 — soft-fallback to next model / mock
            last_err = f"{type(exc).__name__}: {exc}"
            continue

    return _mock_think(
        content_type, history, existing_outline, error=last_err, title=title
    )


def generate_ppt_content(
    outline: dict[str, Any],
    style_id: str,
    model_id: str,
    title: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build full slide JSON via teacher-prep-skill (+ DeepSeek when configured)."""
    history = history or []
    if not teacher_prep.is_available():
        content = mock_ai.generate_ppt(outline, style_id, model_id, title)
        content["preview_pages"] = teacher_prep.slides_to_preview_pages(
            content.get("slides") or []
        )
        return content

    messages, skill_ctx = teacher_prep.build_ppt_messages(
        outline, history, title, style_id, model_id
    )
    if not is_configured():
        return teacher_prep.local_skill_slides(
            outline, style_id, model_id, title, skill_ctx
        )

    preferred = (settings.deepseek_model or "deepseek-reasoner").strip()
    fallback_model = (settings.deepseek_fallback_model or "deepseek-chat").strip()
    models_to_try = [preferred]
    if fallback_model and fallback_model != preferred:
        models_to_try.append(fallback_model)

    for model in models_to_try:
        try:
            data = _chat_completions(model, messages)
            _thinking, content = _parse_completion(data)
            parsed = _extract_json_object(content)
            result = teacher_prep.parse_ppt_completion(
                parsed,
                outline=outline,
                style_id=style_id,
                model_id=model_id,
                title=title,
                context=skill_ctx,
            )
            result["llm_model"] = model
            result["llm_provider"] = "deepseek"
            return result
        except Exception:  # noqa: BLE001
            continue

    return teacher_prep.local_skill_slides(
        outline, style_id, model_id, title, skill_ctx
    )
