"""Bridge to SkillHub `@org-3plub05j/teacher-prep-skill`.

Loads the installed skill (prompts + knowledge graph), fills the prep template,
and drives PPT outline / slide content. DeepSeek remains the LLM backend when
`DEEPSEEK_API_KEY` is set; otherwise a skill-structured local fallback is used.
"""

from __future__ import annotations

import json
import re
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

from . import mock_ai

SKILL_SLUG = "teacher-prep-skill"
SKILL_ORG_SLUG = "@org-3plub05j/teacher-prep-skill"


def skill_root() -> Path | None:
    """Resolve installed skill directory (project vendor → Cursor skills)."""
    here = Path(__file__).resolve()
    backend_dir = here.parents[2]  # .../backend
    project_dir = backend_dir.parent  # .../qisi_ai_kejian
    candidates = [
        backend_dir / "skills" / SKILL_SLUG,
        project_dir / ".cursor" / "skills" / SKILL_SLUG,
        Path.home() / ".cursor" / "skills" / SKILL_SLUG,
        Path.home() / ".claude" / "skills" / SKILL_SLUG,
        Path.home() / ".workbuddy" / "skills" / SKILL_SLUG,
    ]
    for path in candidates:
        if (path / "SKILL.md").is_file() and (path / "references" / "prep_template.md").is_file():
            return path
    return None


def skill_install_path() -> str | None:
    root = skill_root()
    return str(root) if root else None


def is_available() -> bool:
    return skill_root() is not None


@lru_cache(maxsize=1)
def _load_lookup_module():
    root = skill_root()
    if not root:
        return None
    scripts = str(root / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import knowledge_lookup  # type: ignore  # noqa: WPS433 — skill-local module

    return knowledge_lookup


def read_prep_template() -> str:
    root = skill_root()
    if not root:
        return ""
    return (root / "references" / "prep_template.md").read_text(encoding="utf-8")


def read_skill_markdown() -> str:
    root = skill_root()
    if not root:
        return ""
    return (root / "SKILL.md").read_text(encoding="utf-8")


_SUBJECT_PATTERNS = [
    ("数学", "数学"),
    ("物理", "物理"),
    ("化学", "化学"),
    ("生物", "生物"),
    ("语文", "语文"),
    ("英语", "英语"),
    ("历史", "历史"),
    ("地理", "地理"),
    ("道德与法治", "道德与法治"),
    ("科学", "科学"),
    ("信息技术", "信息技术"),
]

_PUBLISHER_PATTERNS = [
    ("人教", "pep"),
    ("苏教", "su"),
    ("北师大", "bsd"),
    ("沪科", "shk"),
    ("外研", "fltrp"),
    ("华师大", "ecnu"),
    ("浙教", "zjedu"),
    ("鲁教", "sdedu"),
]


def _history_blob(history: list[dict[str, str]]) -> str:
    return "；".join(m.get("content", "") for m in history if m.get("role") == "user")


def infer_lesson_hints(history: list[dict[str, str]], title: str | None = None) -> dict[str, Any]:
    text = _history_blob(history)
    if title:
        text = f"{title}；{text}"

    subject = "数学"
    for label, name in _SUBJECT_PATTERNS:
        if label in text:
            subject = name
            break

    publisher_label = "人教"
    publisher_code = "pep"
    for label, code in _PUBLISHER_PATTERNS:
        if label in text:
            publisher_label = label
            publisher_code = code
            break

    grade = 7
    m = re.search(r"(高[一二三]|初[一二三]|[一二三四五六七八九十]年级|\d{1,2}\s*年级)", text)
    if m:
        token = m.group(1)
        grade_map = {
            "高一": 10,
            "高二": 11,
            "高三": 12,
            "初一": 7,
            "初二": 8,
            "初三": 9,
            "一年级": 1,
            "二年级": 2,
            "三年级": 3,
            "四年级": 4,
            "五年级": 5,
            "六年级": 6,
            "七年级": 7,
            "八年级": 8,
            "九年级": 9,
            "十年级": 10,
            "十一年级": 11,
            "十二年级": 12,
        }
        if token in grade_map:
            grade = grade_map[token]
        else:
            num = re.search(r"(\d{1,2})", token)
            if num:
                grade = max(1, min(12, int(num.group(1))))

    chapter_number = 1
    cm = re.search(r"第\s*(\d+)\s*章", text)
    if cm:
        chapter_number = int(cm.group(1))

    style = "讲练结合"
    if "探究" in text or "项目" in text:
        style = "探究式 / 项目式"
    elif "小组" in text or "讨论" in text:
        style = "讲练结合 + 小组讨论"

    mastery = None
    mm = re.search(r"正确率\s*(\d{1,3})\s*%", text)
    if mm:
        mastery = int(mm.group(1))

    students = 40
    sm = re.search(r"(\d{1,3})\s*人", text)
    if sm:
        students = int(sm.group(1))

    return {
        "subject": subject,
        "grade": grade,
        "publisher_label": publisher_label,
        "publisher_code": publisher_code,
        "chapter_number": chapter_number,
        "teaching_style": style,
        "class_mastery_pct": mastery,
        "student_count": students,
        "raw_text": text[:400],
    }


def resolve_skill_context(
    history: list[dict[str, str]],
    title: str | None = None,
) -> dict[str, Any]:
    """Lookup textbook / knowledge-graph context for prompt injection."""
    hints = infer_lesson_hints(history, title)
    ctx: dict[str, Any] = {
        "skill_slug": SKILL_ORG_SLUG,
        "skill_path": skill_install_path(),
        "hints": hints,
        "version_id": None,
        "version_meta": None,
        "chapter": None,
        "knowledge_points": [],
        "template_filled": False,
    }
    lookup = _load_lookup_module()
    if not lookup:
        return ctx

    versions = lookup.list_versions(subject=hints["subject"], grade=hints["grade"]) or []
    version = None
    for v in versions:
        vid = str(v.get("version_id") or "")
        if vid.startswith(hints["publisher_code"]):
            version = v
            break
    if not version and versions:
        version = versions[0]
    if not version:
        return ctx

    version_id = version["version_id"]
    ctx["version_id"] = version_id
    ctx["version_meta"] = version
    structure = lookup.get_chapter_structure(version_id) or {}
    chapters = structure.get("chapters") or []
    chapter = None
    for ch in chapters:
        if int(ch.get("chapter_number") or 0) == hints["chapter_number"]:
            chapter = ch
            break
    if not chapter and chapters:
        chapter = chapters[0]
    ctx["chapter"] = chapter

    kps: list[str] = []
    if chapter:
        for sec in chapter.get("sections") or []:
            for kp in sec.get("knowledge_points") or []:
                name = kp.get("name") or kp.get("code")
                if name:
                    kps.append(str(name))
    ctx["knowledge_points"] = kps[:12]
    return ctx


def fill_prep_template(context: dict[str, Any], history: list[dict[str, str]]) -> str:
    template = read_prep_template()
    if not template:
        return ""
    hints = context.get("hints") or {}
    version = context.get("version_meta") or {}
    chapter = context.get("chapter") or {}
    sections = chapter.get("sections") or [{}]
    section = sections[0] if sections else {}
    kps = context.get("knowledge_points") or ["本节核心概念"]
    mastery = hints.get("class_mastery_pct")
    avg_score = mastery if mastery is not None else 70
    learned = "、".join(kps[:4]) or "先修概念"
    unlearned = "后续拓展内容"
    replacements = {
        "{{teacher_name}}": "启思",
        "{{version_publisher}}": str(
            version.get("version_name") or hints.get("publisher_label") or "人教版"
        ),
        "{{version_id}}": str(context.get("version_id") or "unknown"),
        "{{subject}}": str(hints.get("subject") or version.get("subject") or "数学"),
        "{{chapter_number}}": str(chapter.get("chapter_number") or hints.get("chapter_number") or 1),
        "{{chapter_title}}": str(chapter.get("title") or "本章"),
        "{{section_number}}": "1",
        "{{section_title}}": str(section.get("title") or "第 1 节"),
        "{{page_range}}": str(section.get("page_range") or "—"),
        "{{class_name}}": "本班",
        "{{student_count}}": str(hints.get("student_count") or 40),
        "{{avg_score}}": str(avg_score),
        "{{class_rank}}": "—",
        "{{learned_topics}}": learned,
        "{{unlearned_topics}}": unlearned,
        "{{attention_students}}": "基础薄弱学生",
        "{{knowledge_points}}": "、".join(kps) or "本节知识点",
        "{{teaching_objectives}}": "掌握本节核心概念并能完成基础与变式练习",
        "{{class_periods}}": "1 课时（45 分钟）",
        "{{teaching_style}}": str(hints.get("teaching_style") or "讲练结合"),
        "{{difficulty_level}}": "中等（匹配班级学情）",
        "{{teacher_remarks}}": _history_blob(history)[:300] or "按课堂常规备课",
    }
    filled = template
    for key, val in replacements.items():
        filled = filled.replace(key, val)
    return filled


def build_think_messages(
    content_type: str,
    history: list[dict[str, str]],
    existing_outline: dict[str, Any] | None,
    title: str | None = None,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Messages for DeepSeek thinking, driven by teacher-prep-skill template."""
    kind = "课件 PPT" if content_type == "courseware" else "试卷"
    context = resolve_skill_context(history, title)
    filled = fill_prep_template(context, history)
    context["template_filled"] = bool(filled)

    pedagogy = (
        "你是资深教研员 + 课堂设计教练。思考过程必须教学化、结构化，"
        "禁止空泛套话（如「首先分析需求」「然后输出大纲」）。"
        "请严格按下列骨架推理（教师会看见你的思考）：\n"
        "1. 锚定学情：年级学段、班级水平、先修与薄弱点、可接受难度。\n"
        "2. 设定可检测目标：写出 1～3 个课堂结束时可观察/可检测的学习目标。\n"
        "3. 设计导入钩子：生活情境 / 认知冲突 / 旧知迁移，说明为何能抓住本班。\n"
        "4. 编排节段逻辑：严格按备课节奏 "
        "导入(5′)→概念建构(12′)→例题精讲(15′)→变式练习(10′)→小结(3′)。\n"
        "5. 课标与知识图谱校准：每个节段对应哪些知识点，明确「不讲什么」。\n"
        "6. 整理大纲：产出可直接生成课堂 PPT 的结构化章节。\n"
    )
    skill_intro = (
        "你正在使用 SkillHub 技能 teacher-prep-skill（教师个性化备课助手）。"
        "必须遵循其教材知识图谱 / 课标边界 / 学情约束，不要超纲。\n"
        f"{pedagogy}"
    )
    if filled:
        system = (
            f"{skill_intro}\n"
            f"以下是已注入教材与学情的备课模板。据此完成推理后，"
            f"最终只输出适合课堂教学的结构化{kind}大纲 JSON（单个对象）：\n"
            "字段：key_points (string[]，可检测目标), "
            "outline ({section, items[], phase?}[]，phase 取 "
            "导入|概念建构|例题精讲|变式练习|小结|作业), "
            "notes (string[]，易错点与提问建议), raw_summary (string，一段教学设计摘要)。\n"
            "章节 4～6 个，每节 2～4 个要点；文案用中文课堂口语，具体可讲授。\n"
            "不要包裹多余说明，JSON 外不要再写散文。\n\n"
            f"—— 备课模板 ——\n{filled}"
        )
    else:
        system = (
            f"{skill_intro}\n"
            f"根据师生对话澄清结果完成上述推理后，输出结构化{kind}大纲 JSON。"
            "字段：key_points, outline({section,items[],phase?}), notes, raw_summary。"
        )

    lines = []
    for m in history:
        role = m.get("role") or "user"
        label = "教师助手" if role == "teacher" else "用户"
        lines.append(f"{label}: {m.get('content', '')}")
    user_blob = "\n".join(lines) if lines else "（尚无对话，请给通用课堂课件大纲）"
    if existing_outline:
        user_blob += "\n\n已有草稿大纲（可 refining）:\n" + json.dumps(
            existing_outline, ensure_ascii=False
        )
    if context.get("knowledge_points"):
        user_blob += "\n\n课标/教材知识点约束:\n" + "、".join(context["knowledge_points"])
    user_blob += (
        "\n\n请先在思考中完成「学情→目标→钩子→节段→课标」推理，"
        "再输出最终 JSON 大纲。"
    )

    return (
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user_blob},
        ],
        context,
    )


def build_ppt_messages(
    outline: dict[str, Any],
    history: list[dict[str, str]],
    title: str | None,
    style_id: str,
    model_id: str,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    context = resolve_skill_context(history, title)
    filled = fill_prep_template(context, history)
    context["template_filled"] = bool(filled)
    system = (
        "你正在使用 teacher-prep-skill 生成真实课堂课件幻灯片。"
        "严格按备课模板 PPT 结构（约 18 页）："
        "导入页(2)、概念建构(5)、例题精讲(5)、课堂练习(4)、小结(1)、作业(1)。\n"
        "文案要求：中文课堂讲授口吻，短句可投屏；例题生活化；"
        "每页只服务一个教学动作；禁止堆砌空泛口号。\n"
        "输出单个 JSON 对象，字段：\n"
        "title (string),\n"
        "ppt_outline ([{title, subtitle?, bullets[], speaker_note?, layout?, phase?}]),\n"
        "key_points (string[]), notes (string[])。\n"
        "layout 取值：cover | agenda | section | content | example | practice | "
        "summary | homework；phase 取值：导入|概念建构|例题精讲|变式练习|小结|作业。\n"
        "bullets 每页 2～5 条；不要 markdown 围栏。"
    )
    if filled:
        system += f"\n\n—— 备课模板 ——\n{filled}"
    user = (
        f"课件标题：{title or 'AI 备课课件'}\n"
        f"风格：{style_id} · 模型标记：{model_id}\n"
        f"已确认大纲：\n{json.dumps(outline, ensure_ascii=False)}\n"
        "请生成完整 ppt_outline：封面→目标→概念→例题→练习→小结→分层作业。"
    )
    return (
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        context,
    )


def _slides_from_ppt_outline(
    ppt_outline: list[Any],
    *,
    title: str,
    style_id: str,
    model_id: str,
) -> list[dict[str, Any]]:
    slides: list[dict[str, Any]] = []
    for i, raw in enumerate(ppt_outline or [], start=1):
        if isinstance(raw, str):
            slides.append(
                {
                    "slide_no": i,
                    "layout": "content",
                    "title": raw,
                    "subtitle": None,
                    "bullets": [],
                    "speaker_note": None,
                }
            )
            continue
        if not isinstance(raw, dict):
            continue
        bullets = raw.get("bullets") or raw.get("items") or raw.get("points") or []
        if isinstance(bullets, str):
            bullets = [bullets]
        slides.append(
            {
                "slide_no": i,
                "layout": str(raw.get("layout") or ("cover" if i == 1 else "content")),
                "phase": raw.get("phase"),
                "title": str(raw.get("title") or raw.get("section") or f"第 {i} 页"),
                "subtitle": raw.get("subtitle"),
                "bullets": [str(b) for b in bullets if str(b).strip()][:6],
                "speaker_note": raw.get("speaker_note") or raw.get("note"),
            }
        )
    if not slides:
        return []
    # Ensure cover title
    if slides and not slides[0].get("title"):
        slides[0]["title"] = title
    if slides and slides[0].get("layout") == "cover":
        slides[0]["subtitle"] = slides[0].get("subtitle") or f"{style_id} · {model_id}"
    return slides


def local_skill_slides(
    outline: dict[str, Any],
    style_id: str,
    model_id: str,
    title: str | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Skill-structured ~18-page deck without LLM (offline / mock fallback)."""
    style = next((s for s in mock_ai.STYLES if s["id"] == style_id), mock_ai.STYLES[0])
    ppt_title = title or "AI 备课课件"
    key_points = list(outline.get("key_points") or [])
    sections = list(outline.get("outline") or [])
    notes = list(outline.get("notes") or [])
    kps = (context or {}).get("knowledge_points") or key_points
    chapter = (context or {}).get("chapter") or {}
    chapter_title = chapter.get("title") or (sections[0]["section"] if sections else "本章")

    prior = "、".join(kps[:2]) if kps else "相关先修概念"
    hook = f"从「{prior}」出发，抛出一个生活情境冲突"
    slides: list[dict[str, Any]] = [
        {
            "slide_no": 1,
            "layout": "cover",
            "phase": "导入",
            "title": ppt_title,
            "subtitle": f"teacher-prep · {style['name']} · {chapter_title}",
            "bullets": [],
            "speaker_note": "封面：问候班级，点明本节只解决一个核心问题",
        },
        {
            "slide_no": 2,
            "layout": "agenda",
            "phase": "导入",
            "title": "情境导入",
            "subtitle": f"5′ · {chapter_title}",
            "bullets": [
                f"钩子：{hook}",
                f"先修唤醒：{prior}",
                "请学生用一句话猜：本节要解决什么？",
            ],
            "speaker_note": "导入 5′：先问后讲，收集前概念",
        },
        {
            "slide_no": 3,
            "layout": "agenda",
            "phase": "导入",
            "title": "本节可检测目标",
            "subtitle": "下课时我们怎么知道学会了",
            "bullets": key_points[:4]
            or [
                "能用自己的话解释核心概念",
                "独立完成一道基础例题并说出步骤",
                "在变式中指出不变的结构",
            ],
            "speaker_note": "目标板书，课末回扣",
        },
    ]

    # Concept construction (~5)
    concept_secs = sections[:3] or [
        {"section": "核心概念", "items": kps[:3] or ["概念界定", "关键特征", "与旧知区别"]}
    ]
    for sec in concept_secs:
        items = list(sec.get("items") or ["要点"])
        slides.append(
            {
                "slide_no": len(slides) + 1,
                "layout": "section",
                "phase": "概念建构",
                "title": sec.get("section", "概念建构"),
                "subtitle": "概念建构 · 12′",
                "bullets": items[:4],
                "speaker_note": f"板块导航：{sec.get('section', '')}，先整体后细节",
            }
        )
        for item in items[:2]:
            slides.append(
                {
                    "slide_no": len(slides) + 1,
                    "layout": "content",
                    "phase": "概念建构",
                    "title": str(item),
                    "subtitle": f"课标边界 · {sec.get('section')}",
                    "bullets": [
                        f"定义：用课堂语言说清「{item}」是什么",
                        f"联系：它和「{prior}」差在哪里",
                        "易错：学生最常把哪两点混在一起",
                    ],
                    "speaker_note": f"细讲 {item}；请薄弱学生复述关键词",
                }
            )

    # Worked examples (~5)
    scenes = ["买文具找零", "班级值日排班", "体育课计时跑"]
    for i in range(1, 4):
        slides.append(
            {
                "slide_no": len(slides) + 1,
                "layout": "example",
                "phase": "例题精讲",
                "title": f"例题精讲 {i}",
                "subtitle": f"场景：{scenes[i - 1]} · 由易到难",
                "bullets": [
                    "审题：圈出已知、所求与单位",
                    f"建模：对应知识点「{(kps[i - 1] if i - 1 < len(kps) else '本节要点')}」",
                    "规范书写：步骤完整、结论可检验",
                ],
                "speaker_note": "例题精讲：教师示范 → 学生跟说一步",
            }
        )
    slides.append(
        {
            "slide_no": len(slides) + 1,
            "layout": "example",
            "phase": "例题精讲",
            "title": "变式对照",
            "subtitle": "结构保留 · 换皮不换骨",
            "bullets": [
                "并排对比：原题 vs 变式，哪些数变了",
                "迁移点：解题骨架哪里完全一样",
                "请一名学生上台口述思路，同学纠错",
            ],
            "speaker_note": "变式过渡：强调结构而非答案",
        }
    )
    slides.append(
        {
            "slide_no": len(slides) + 1,
            "layout": "example",
            "phase": "例题精讲",
            "title": "易错点预警",
            "subtitle": "针对本班学情",
            "bullets": notes[:3]
            or [
                "符号与单位漏写是高频失分点",
                "严禁拓展到未学课标内容",
                "薄弱学生：先问「已知是什么」再问算法",
            ],
            "speaker_note": "点名追问 1～2 位关注学生",
        }
    )

    # Practice (~4)
    practice_labels = ["基础练① 模仿", "基础练② 巩固", "基础练③ 限时", "变式练 迁移"]
    for i, label in enumerate(practice_labels, start=1):
        kp = kps[i - 1] if i - 1 < len(kps) else "本节要点"
        slides.append(
            {
                "slide_no": len(slides) + 1,
                "layout": "practice",
                "phase": "变式练习",
                "title": label,
                "subtitle": "当堂 10′ · 独立完成 → 同桌互查",
                "bullets": [
                    f"本题只考：{kp}",
                    "先写思路关键词，再写完整步骤",
                    "教师巡视：收集三类错因贴到板书",
                ],
                "speaker_note": "练习段：少讲多看，错因即时板书",
            }
        )

    slides.append(
        {
            "slide_no": len(slides) + 1,
            "layout": "summary",
            "phase": "小结",
            "title": "课堂小结",
            "subtitle": "3′ · 回扣学习目标",
            "bullets": key_points[:3]
            or [
                "一张结构图：概念 → 例题骨架 → 易错点",
                "请学生用 20 秒复述「今天学会了什么」",
                "预告下节：在本节骨架上增加一层难度",
            ],
            "speaker_note": "小结：学生说，教师补",
        }
    )
    slides.append(
        {
            "slide_no": len(slides) + 1,
            "layout": "homework",
            "phase": "作业",
            "title": "分层作业",
            "subtitle": "基础 5 · 拔高 3 · 选做 1",
            "bullets": [
                notes[0] if notes else "基础：模仿例题结构完成 5 题",
                notes[1] if len(notes) > 1 else "拔高：换情境保留结构的 3 题",
                notes[2] if len(notes) > 2 else "选做：开放题，写出两种解法",
            ],
            "speaker_note": "分层布置：明确明日抽查哪一档",
        }
    )

    for i, s in enumerate(slides, start=1):
        s["slide_no"] = i

    return {
        "title": ppt_title,
        "style_id": style_id,
        "model_id": model_id,
        "palette": style["palette"],
        "slide_count": len(slides),
        "slides": slides,
        "preview_pages": slides_to_preview_pages(slides),
        "mock": False,
        "provider_note": "teacher-prep-skill local structured deck",
        "skill_slug": SKILL_ORG_SLUG,
        "skill_path": skill_install_path(),
        "skill_context": {
            "version_id": (context or {}).get("version_id"),
            "knowledge_points": (context or {}).get("knowledge_points") or [],
            "template_filled": bool((context or {}).get("template_filled")),
        },
        "pptx_source": "teacher-prep-skill",
    }


def slides_to_preview_pages(slides: list[dict[str, Any]], limit: int = 6) -> list[dict[str, Any]]:
    """Pick a representative spread: cover → goals → concept → example → practice → summary."""
    if not slides:
        slides = []
    preferred_layouts = ["cover", "agenda", "section", "example", "practice", "summary"]
    picked: list[dict[str, Any]] = []
    used: set[int] = set()
    for layout in preferred_layouts:
        for idx, slide in enumerate(slides):
            if idx in used:
                continue
            if str(slide.get("layout") or "") == layout:
                picked.append(slide)
                used.add(idx)
                break
        if len(picked) >= limit:
            break
    for idx, slide in enumerate(slides):
        if len(picked) >= limit:
            break
        if idx not in used:
            picked.append(slide)
            used.add(idx)

    pages: list[dict[str, Any]] = []
    for i, slide in enumerate(picked[:limit], start=1):
        pages.append(
            {
                "page_no": i,
                "title": slide.get("title") or f"第 {i} 页",
                "subtitle": slide.get("subtitle"),
                "bullets": list(slide.get("bullets") or [])[:5],
                "speaker_note": slide.get("speaker_note"),
                "layout": slide.get("layout") or "content",
                "phase": slide.get("phase"),
                "mock_image_hint": f"teacher_prep_{slide.get('layout') or 'content'}",
            }
        )
    while len(pages) < limit:
        n = len(pages) + 1
        pages.append(
            {
                "page_no": n,
                "title": f"预览页 {n}",
                "subtitle": "teacher-prep",
                "bullets": ["由备课技能结构补齐"],
                "speaker_note": None,
                "layout": "content",
                "phase": None,
                "mock_image_hint": "filler",
            }
        )
    return pages


def outline_from_skill_fallback(
    content_type: str,
    history: list[dict[str, str]],
    title: str | None = None,
) -> dict[str, Any]:
    """Enrich mock outline with skill knowledge points when LLM unavailable."""
    base = mock_ai._build_outline(content_type, history)  # noqa: SLF001
    context = resolve_skill_context(history, title)
    kps = context.get("knowledge_points") or []
    chapter = context.get("chapter") or {}
    if kps:
        base["key_points"] = [
            f"落实：{kps[0]}" if kps else "明确学习目标",
            "分层例题与变式",
            "当堂检测与分层作业",
        ][:3]
        items = kps[:4] or ["概念要点"]
        section_title = chapter.get("title") or "核心知识"
        base["outline"] = [
            {
                "section": "导入与目标",
                "items": ["生活情境钩子", "可检测学习目标"],
                "phase": "导入",
            },
            {
                "section": section_title,
                "items": items,
                "phase": "概念建构",
            },
            {
                "section": "例题精讲",
                "items": ["基础例 · 生活场景", "变式对照 · 结构迁移"],
                "phase": "例题精讲",
            },
            {
                "section": "练习与小结",
                "items": ["当堂分层练", "小结回扣目标", "分层作业"],
                "phase": "变式练习",
            },
        ]
        base["notes"] = [
            "严格限定课标已学范围（teacher-prep）",
            f"教材版本：{context.get('version_id') or '未匹配到具体版本'}",
            "关注班级薄弱学生：先问已知再问算法",
        ]
        base["raw_summary"] = (
            f"教学设计摘要：围绕 {context.get('version_id') or '教材'} "
            f"{'、'.join(kps[:6])}，按导入→概念→例题→练习→小结推进。"
        ).strip()
    base["_skill_context"] = {
        "version_id": context.get("version_id"),
        "knowledge_points": kps,
        "skill_path": skill_install_path(),
    }
    return base


def parse_ppt_completion(
    raw: dict[str, Any] | None,
    *,
    outline: dict[str, Any],
    style_id: str,
    model_id: str,
    title: str | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    style = next((s for s in mock_ai.STYLES if s["id"] == style_id), mock_ai.STYLES[0])
    ppt_title = (raw or {}).get("title") or title or "AI 备课课件"
    ppt_outline = (raw or {}).get("ppt_outline") or (raw or {}).get("slides") or []
    slides = _slides_from_ppt_outline(
        ppt_outline, title=str(ppt_title), style_id=style_id, model_id=model_id
    )
    if len(slides) < 6:
        return local_skill_slides(outline, style_id, model_id, str(ppt_title), context)

    return {
        "title": ppt_title,
        "style_id": style_id,
        "model_id": model_id,
        "palette": style["palette"],
        "slide_count": len(slides),
        "slides": slides,
        "preview_pages": slides_to_preview_pages(slides),
        "mock": False,
        "provider_note": "teacher-prep-skill via DeepSeek",
        "skill_slug": SKILL_ORG_SLUG,
        "skill_path": skill_install_path(),
        "skill_context": {
            "version_id": context.get("version_id"),
            "knowledge_points": context.get("knowledge_points") or [],
            "template_filled": bool(context.get("template_filled")),
        },
        "pptx_source": "teacher-prep-skill",
        "key_points": (raw or {}).get("key_points") or outline.get("key_points"),
        "notes": (raw or {}).get("notes") or outline.get("notes"),
    }
