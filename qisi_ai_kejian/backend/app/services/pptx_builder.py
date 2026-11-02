"""Build a real .pptx from slide JSON with a coherent classroom visual system.

Prefer python-pptx (shapes, theme colors, layout variants); post-process OOXML
for slide transitions / entrance-friendly timing. Improved OOXML fallback when
python-pptx is unavailable.
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from ..config import settings

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

# Coherent 「启思课堂」 visual system (not flat white bullets)
THEME = {
    "ink": "1B3A57",
    "ink_soft": "4A6078",
    "paper": "F7F4EC",
    "paper_deep": "EDE6D8",
    "accent": "C45C26",
    "accent_soft": "E8A87C",
    "sage": "2F6B4F",
    "teal": "4C8CB4",
    "white": "FFFFFF",
    "cover_deep": "152A3D",
}


def storage_dir() -> Path:
    path = Path(settings.database_path).resolve().parent / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_pptx_path(artifact_id: int) -> Path:
    return storage_dir() / f"artifact_{artifact_id}.pptx"


def download_url_for(artifact_id: int) -> str:
    return f"/api/artifacts/{artifact_id}/download"


def ascii_download_name(artifact_id: int) -> str:
    """ASCII-only name for Content-Disposition filename= (WeChat-safe)."""
    return f"artifact_{artifact_id}.pptx"


def _safe_filename(title: str | None, artifact_id: int) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", (title or "课件").strip())[:40] or "课件"
    return f"{base}_{artifact_id}.pptx"


def _slides_or_placeholder(content: dict[str, Any]) -> list[dict[str, Any]]:
    slides = content.get("slides") or []
    if slides:
        return list(slides)
    return [
        {
            "title": content.get("title") or "课件",
            "subtitle": "空大纲占位",
            "bullets": ["请补充大纲后重新生成"],
            "layout": "cover",
        }
    ]


def _palette_colors(content: dict[str, Any]) -> dict[str, str]:
    """Map style palette → theme roles; keep brand defaults when missing."""
    colors = dict(THEME)
    palette = content.get("palette") or []
    if isinstance(palette, list) and len(palette) >= 1:
        p0 = str(palette[0]).lstrip("#").upper()
        if len(p0) == 6:
            colors["paper"] = p0
    if isinstance(palette, list) and len(palette) >= 2:
        p1 = str(palette[1]).lstrip("#").upper()
        if len(p1) == 6:
            colors["ink"] = p1
            colors["cover_deep"] = p1
    if isinstance(palette, list) and len(palette) >= 3:
        p2 = str(palette[2]).lstrip("#").upper()
        if len(p2) == 6:
            colors["accent"] = p2
            colors["teal"] = p2
    return colors


def _rgb(hex_color: str):
    from pptx.dml.color import RGBColor

    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _set_run_font(run, *, size_pt: int, bold: bool = False, color: str = "1B3A57", name: str = "PingFang SC"):
    from pptx.util import Pt

    run.font.size = Pt(size_pt)
    run.font.bold = bold
    run.font.color.rgb = _rgb(color)
    run.font.name = name
    # Prefer public font API only — private rPr hooks differ across python-pptx builds
    # and are not required for Keynote/PowerPoint openability.


def _add_rect(slide, left, top, width, height, fill_hex: str, line_hex: str | None = None):
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches

    shape = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(fill_hex)
    if line_hex:
        shape.line.color.rgb = _rgb(line_hex)
    else:
        shape.line.fill.background()
    return shape


def _add_oval(slide, left, top, width, height, fill_hex: str):
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches

    shape = slide.shapes.add_shape(
        MSO_SHAPE.OVAL,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(fill_hex)
    shape.line.fill.background()
    return shape


def _add_round_rect(slide, left, top, width, height, fill_hex: str):
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches

    shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(left),
        Inches(top),
        Inches(width),
        Inches(height),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = _rgb(fill_hex)
    shape.line.fill.background()
    return shape


def _textbox(slide, left, top, width, height, text: str, *, size: int, bold: bool = False, color: str = "1B3A57", align=None):
    from pptx.enum.text import PP_ALIGN
    from pptx.util import Inches, Pt

    box = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    if align == "center":
        p.alignment = PP_ALIGN.CENTER
    elif align == "right":
        p.alignment = PP_ALIGN.RIGHT
    run = p.add_run()
    run.text = text
    _set_run_font(run, size_pt=size, bold=bold, color=color)
    return box


def _bullets_box(slide, left, top, width, height, bullets: list[str], *, size: int = 18, color: str = "1B3A57", accent: str = "C45C26"):
    from pptx.util import Inches, Pt

    body = slide.shapes.add_textbox(Inches(left), Inches(top), Inches(width), Inches(height))
    tf = body.text_frame
    tf.word_wrap = True
    for i, bullet in enumerate(bullets[:7]):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.level = 0
        para.space_after = Pt(10)
        # Accent glyph as visual bullet
        run_mark = para.add_run()
        run_mark.text = "▸ "
        _set_run_font(run_mark, size_pt=size, bold=True, color=accent)
        run = para.add_run()
        run.text = str(bullet)
        _set_run_font(run, size_pt=size, bold=False, color=color)
    return body


def _layout_of(slide: dict[str, Any], index: int) -> str:
    layout = str(slide.get("layout") or "").strip().lower()
    if layout:
        return layout
    if index == 0:
        return "cover"
    return "content"


def _paint_cover(s, slide: dict[str, Any], colors: dict[str, str], total: int, index: int):
    from pptx.util import Inches

    # Full-bleed deep ink plane
    _add_rect(s, 0, 0, 13.333, 7.5, colors["cover_deep"])
    # Soft decorative circles (atmosphere, not clutter)
    _add_oval(s, 10.2, -1.2, 4.2, 4.2, colors["ink"])
    _add_oval(s, -1.4, 5.0, 3.6, 3.6, colors["ink"])
    _add_rect(s, 0, 0, 0.22, 7.5, colors["accent"])
    # Accent band near bottom
    _add_rect(s, 0, 6.55, 13.333, 0.95, colors["ink"])

    title = str(slide.get("title") or "课堂课件")
    subtitle = str(slide.get("subtitle") or "teacher-prep · 启思备课")
    _textbox(s, 0.9, 2.0, 11.2, 1.6, title, size=40, bold=True, color=colors["white"])
    _textbox(s, 0.9, 3.7, 10.5, 0.6, subtitle, size=18, bold=False, color=colors["accent_soft"])
    _textbox(
        s,
        0.9,
        6.75,
        8.0,
        0.45,
        f"共 {total} 页 · 第 {index + 1} 页",
        size=12,
        color="A8B8C8",
    )
    kicker = str(slide.get("phase") or "导入")
    badge = _add_round_rect(s, 0.9, 1.35, 1.6, 0.42, colors["accent"])
    _textbox(s, 0.9, 1.38, 1.6, 0.4, kicker, size=12, bold=True, color=colors["white"], align="center")
    _ = badge


def _paint_section(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    _add_rect(s, 0, 0, 13.333, 7.5, colors["paper"])
    _add_rect(s, 0, 0, 4.2, 7.5, colors["ink"])
    _add_rect(s, 4.2, 0, 0.12, 7.5, colors["accent"])
    _add_oval(s, 0.6, 5.8, 2.4, 2.4, colors["cover_deep"])

    phase = str(slide.get("phase") or slide.get("subtitle") or "概念建构")
    _textbox(s, 0.55, 2.3, 3.3, 0.5, phase, size=14, bold=True, color=colors["accent_soft"])
    _textbox(s, 0.55, 2.9, 3.3, 2.2, str(slide.get("title") or "章节"), size=28, bold=True, color=colors["white"])

    bullets = list(slide.get("bullets") or [])
    if bullets:
        _bullets_box(s, 4.9, 2.0, 7.6, 4.5, bullets, size=20, color=colors["ink"], accent=colors["accent"])
    else:
        _textbox(s, 4.9, 2.8, 7.5, 1.0, str(slide.get("subtitle") or ""), size=18, color=colors["ink_soft"])
    _textbox(s, 4.9, 6.9, 7.5, 0.35, f"{index + 1} / {total}", size=11, color=colors["ink_soft"])


def _paint_agenda(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    _add_rect(s, 0, 0, 13.333, 7.5, colors["paper"])
    _add_rect(s, 0, 0, 13.333, 1.35, colors["ink"])
    _add_rect(s, 0, 1.35, 13.333, 0.1, colors["accent"])
    _textbox(s, 0.7, 0.35, 10, 0.7, str(slide.get("title") or "学习目标"), size=28, bold=True, color=colors["white"])
    if slide.get("subtitle"):
        _textbox(s, 0.7, 0.95, 10, 0.35, str(slide["subtitle"]), size=13, color=colors["accent_soft"])

    bullets = list(slide.get("bullets") or [])
    # Goal cards as rounded blocks
    y = 1.9
    for i, b in enumerate(bullets[:5]):
        _add_round_rect(s, 0.7, y, 11.9, 0.85, colors["white"] if i % 2 == 0 else colors["paper_deep"])
        _add_rect(s, 0.7, y, 0.14, 0.85, colors["accent"] if i % 2 == 0 else colors["teal"])
        _textbox(s, 1.15, y + 0.22, 11.0, 0.5, str(b), size=18, color=colors["ink"])
        y += 1.0
    _textbox(s, 0.7, 6.95, 6, 0.3, f"{index + 1} / {total}", size=11, color=colors["ink_soft"])


def _paint_content(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int, *, accent: str | None = None):
    accent = accent or colors["accent"]
    _add_rect(s, 0, 0, 13.333, 7.5, colors["paper"])
    # Top bar + left rail
    _add_rect(s, 0, 0, 13.333, 0.18, accent)
    _add_rect(s, 0, 0, 0.18, 7.5, colors["ink"])
    # Soft corner wash
    _add_oval(s, 11.6, -0.8, 2.8, 2.8, colors["paper_deep"])

    title = str(slide.get("title") or "")
    _textbox(s, 0.7, 0.45, 11.5, 0.85, title, size=30, bold=True, color=colors["ink"])
    y = 1.45
    if slide.get("subtitle"):
        _textbox(s, 0.7, 1.25, 11.5, 0.4, str(slide["subtitle"]), size=14, color=colors["ink_soft"])
        y = 1.75

    # Icon disc for hierarchy
    _add_oval(s, 0.7, y, 0.55, 0.55, accent)
    _textbox(s, 0.7, y + 0.08, 0.55, 0.4, "◆", size=12, bold=True, color=colors["white"], align="center")

    bullets = list(slide.get("bullets") or [])
    if bullets:
        _bullets_box(s, 1.5, y, 10.8, 4.6, bullets, size=18, color=colors["ink"], accent=accent)
    _textbox(s, 0.7, 6.95, 6, 0.3, f"{index + 1} / {total}", size=11, color=colors["ink_soft"])


def _paint_example(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    _add_rect(s, 0, 0, 13.333, 7.5, colors["paper"])
    _add_rect(s, 0, 0, 0.55, 7.5, colors["accent"])
    badge = _add_round_rect(s, 0.9, 0.45, 1.15, 0.48, colors["accent"])
    _ = badge
    _textbox(s, 0.9, 0.5, 1.15, 0.4, "例题", size=14, bold=True, color=colors["white"], align="center")
    _textbox(s, 2.3, 0.45, 10, 0.7, str(slide.get("title") or "例题精讲"), size=28, bold=True, color=colors["ink"])
    if slide.get("subtitle"):
        _textbox(s, 0.9, 1.2, 11.5, 0.4, str(slide["subtitle"]), size=14, color=colors["ink_soft"])
    bullets = list(slide.get("bullets") or [])
    # Step cards
    y = 1.85
    labels = ["审", "建", "解", "验", "拓"]
    for i, b in enumerate(bullets[:5]):
        _add_round_rect(s, 0.9, y, 11.5, 0.85, colors["white"])
        _add_oval(s, 1.15, y + 0.18, 0.5, 0.5, colors["accent"] if i == 0 else colors["teal"])
        _textbox(
            s,
            1.15,
            y + 0.26,
            0.5,
            0.4,
            labels[i] if i < len(labels) else str(i + 1),
            size=12,
            bold=True,
            color=colors["white"],
            align="center",
        )
        _textbox(s, 1.9, y + 0.22, 10.0, 0.5, str(b), size=17, color=colors["ink"])
        y += 0.95
    _textbox(s, 0.9, 6.95, 6, 0.3, f"{index + 1} / {total}", size=11, color=colors["ink_soft"])


def _paint_practice(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    _paint_content(s, slide, colors, index, total, accent=colors["sage"])
    # Corner ribbon
    _add_rect(s, 11.6, 0, 1.733, 0.55, colors["sage"])
    _textbox(s, 11.6, 0.1, 1.733, 0.4, "练习", size=12, bold=True, color=colors["white"], align="center")


def _paint_summary(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    _add_rect(s, 0, 0, 13.333, 7.5, colors["paper"])
    _add_rect(s, 0, 5.9, 13.333, 1.6, colors["ink"])
    _add_rect(s, 0, 0, 13.333, 0.18, colors["sage"])
    _textbox(s, 0.8, 0.55, 11.5, 0.7, str(slide.get("title") or "课堂小结"), size=30, bold=True, color=colors["ink"])
    bullets = list(slide.get("bullets") or [])
    _bullets_box(s, 0.9, 1.6, 11.5, 3.8, bullets, size=20, color=colors["ink"], accent=colors["sage"])
    _textbox(
        s,
        0.8,
        6.25,
        11.5,
        0.8,
        str(slide.get("subtitle") or "回顾结构 · 重申易错 · 预告下节"),
        size=14,
        color=colors["accent_soft"],
    )
    _textbox(s, 11.2, 6.95, 1.5, 0.3, f"{index + 1}/{total}", size=11, color="A8B8C8", align="right")


def _paint_homework(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    _add_rect(s, 0, 0, 13.333, 7.5, colors["paper"])
    _add_rect(s, 0, 0, 13.333, 1.5, colors["teal"])
    _textbox(s, 0.8, 0.4, 11, 0.7, str(slide.get("title") or "分层作业"), size=30, bold=True, color=colors["white"])
    if slide.get("subtitle"):
        _textbox(s, 0.8, 1.05, 11, 0.35, str(slide["subtitle"]), size=13, color=colors["paper"])
    bullets = list(slide.get("bullets") or [])
    tiers = [("基础", colors["sage"]), ("拔高", colors["accent"]), ("选做", colors["ink"])]
    cols = min(3, max(1, len(bullets) or 1))
    for i in range(cols):
        left = 0.7 + i * 4.15
        label, fill = tiers[i % 3]
        _add_round_rect(s, left, 2.0, 3.9, 4.2, colors["white"])
        _add_rect(s, left, 2.0, 3.9, 0.55, fill)
        _textbox(s, left, 2.1, 3.9, 0.4, label, size=14, bold=True, color=colors["white"], align="center")
        text = str(bullets[i]) if i < len(bullets) else "按学情布置"
        _textbox(s, left + 0.25, 2.85, 3.4, 3.0, text, size=16, color=colors["ink"])
    _textbox(s, 0.7, 6.95, 6, 0.3, f"{index + 1} / {total}", size=11, color=colors["ink_soft"])


def _paint_speaker_footer(s, slide: dict[str, Any], colors: dict[str, str], layout: str):
    """Render speaker notes on-slide.

    python-pptx notesSlide parts are often rejected by Keynote; keep notes in the
    JSON for in-app preview, and mirror a short footer on the canvas instead.
    """
    note = slide.get("speaker_note")
    if not note:
        return
    text = f"讲者：{note}"
    if len(text) > 48:
        text = text[:46] + "…"
    color = colors["accent_soft"] if layout == "cover" else colors["ink_soft"]
    _textbox(s, 0.7, 6.55, 10.5, 0.35, text, size=11, color=color)


def _paint_slide(s, slide: dict[str, Any], colors: dict[str, str], index: int, total: int):
    layout = _layout_of(slide, index)
    if layout == "cover":
        _paint_cover(s, slide, colors, total, index)
    elif layout == "section":
        _paint_section(s, slide, colors, index, total)
    elif layout == "agenda":
        _paint_agenda(s, slide, colors, index, total)
    elif layout == "example":
        _paint_example(s, slide, colors, index, total)
    elif layout == "practice":
        _paint_practice(s, slide, colors, index, total)
    elif layout == "summary":
        _paint_summary(s, slide, colors, index, total)
    elif layout == "homework":
        _paint_homework(s, slide, colors, index, total)
    else:
        _paint_content(s, slide, colors, index, total)

    # Footer note instead of notesSlide (Keynote-safe). Skip layouts with busy bottom bands.
    if layout not in ("cover", "summary", "homework"):
        _paint_speaker_footer(s, slide, colors, layout)


def _inject_animations(pptx_path: Path) -> None:
    """Post-process OOXML: add fade slide transitions (Keynote/PowerPoint friendly)."""
    data = pptx_path.read_bytes()
    buf_in = io.BytesIO(data)
    buf_out = io.BytesIO()
    transition = '<p:transition spd="med"><p:fade/></p:transition>'
    with zipfile.ZipFile(buf_in, "r") as zin, zipfile.ZipFile(
        buf_out, "w", compression=zipfile.ZIP_DEFLATED
    ) as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)
            if re.match(r"ppt/slides/slide\d+\.xml$", item.filename):
                text = raw.decode("utf-8")
                if "<p:transition" not in text:
                    text = text.replace("</p:sld>", transition + "</p:sld>")
                    raw = text.encode("utf-8")
            zout.writestr(item, raw)
    out = buf_out.getvalue()
    _assert_valid_pptx_bytes(out)
    tmp = pptx_path.with_suffix(pptx_path.suffix + ".animtmp")
    tmp.write_bytes(out)
    tmp.replace(pptx_path)


def _try_python_pptx(content: dict[str, Any], dest: Path) -> bool:
    try:
        from pptx import Presentation
        from pptx.util import Inches
    except ImportError:
        return False

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]  # blank
    colors = _palette_colors(content)
    slides = _slides_or_placeholder(content)
    total = len(slides)

    for index, slide in enumerate(slides):
        s = prs.slides.add_slide(blank)
        _paint_slide(s, slide, colors, index, total)

    dest.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    prs.save(buf)
    data = buf.getvalue()
    _assert_valid_pptx_bytes(data)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    try:
        _inject_animations(dest)
    except Exception:
        # Animations are best-effort; keep valid deck if post-process fails
        pass
    return True


def _theme_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Qisi">
  <a:themeElements>
    <a:clrScheme name="Qisi">
      <a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>
      <a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="1B3A57"/></a:dk2>
      <a:lt2><a:srgbClr val="F7F4EC"/></a:lt2>
      <a:accent1><a:srgbClr val="C45C26"/></a:accent1>
      <a:accent2><a:srgbClr val="4C8CB4"/></a:accent2>
      <a:accent3><a:srgbClr val="2F6B4F"/></a:accent3>
      <a:accent4><a:srgbClr val="B08D57"/></a:accent4>
      <a:accent5><a:srgbClr val="6B7C8C"/></a:accent5>
      <a:accent6><a:srgbClr val="8C5A4A"/></a:accent6>
      <a:hlink><a:srgbClr val="4C8CB4"/></a:hlink>
      <a:folHlink><a:srgbClr val="8C5A4A"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Qisi">
      <a:majorFont><a:latin typeface="Arial"/><a:ea typeface="PingFang SC"/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Arial"/><a:ea typeface="PingFang SC"/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="Qisi">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
</a:theme>"""


def _slide_master_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="2" name="Title Placeholder"/><p:cNvSpPr><a:spLocks noGrp="1"/></p:cNvSpPr>
          <p:nvPr><p:ph type="title"/></p:nvPr></p:nvSpPr>
        <p:spPr/>
        <p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:endParaRPr/></a:p></p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2"
   accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst>
    <p:sldLayoutId id="2147483649" r:id="rId1"/>
  </p:sldLayoutIdLst>
</p:sldMaster>"""


def _slide_layout_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def _fallback_slide_xml(slide: dict[str, Any], index: int, total: int, colors: dict[str, str]) -> str:
    layout = _layout_of(slide, index)
    title = escape(str(slide.get("title") or f"第 {index + 1} 页"))
    subtitle = escape(str(slide.get("subtitle") or ""))
    bullets = slide.get("bullets") or []
    body_lines = []
    for b in bullets[:7]:
        body_lines.append(
            '<a:p><a:r><a:rPr lang="zh-CN" sz="1800" b="1">'
            f'<a:solidFill><a:srgbClr val="{colors["accent"]}"/></a:solidFill></a:rPr>'
            f'<a:t>▸ </a:t></a:r><a:r><a:rPr lang="zh-CN" sz="1800">'
            f'<a:solidFill><a:srgbClr val="{colors["ink"]}"/></a:solidFill></a:rPr>'
            f"<a:t>{escape(str(b))}</a:t></a:r></a:p>"
        )
    body_xml = "".join(body_lines) or '<a:p><a:endParaRPr lang="zh-CN"/></a:p>'

    if layout == "cover":
        bg = colors["cover_deep"]
        title_color = colors["white"]
        bar = (
            f'<p:sp><p:nvSpPr><p:cNvPr id="4" name="Accent"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="200000" cy="6858000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{colors["accent"]}"/></a:solidFill></p:spPr>'
            f"<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
        )
    else:
        bg = colors["paper"]
        title_color = colors["ink"]
        bar = (
            f'<p:sp><p:nvSpPr><p:cNvPr id="4" name="Top"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="12192000" cy="160000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{colors["accent"]}"/></a:solidFill></p:spPr>'
            f"<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>"
        )

    sub_xml = ""
    if subtitle:
        sub_xml = (
            f'<p:sp><p:nvSpPr><p:cNvPr id="5" name="Sub"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="457200" y="1200000"/><a:ext cx="11277600" cy="400000"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r>'
            f'<a:rPr lang="zh-CN" sz="1400"/><a:t>{subtitle}</a:t></a:r></a:p></p:txBody></p:sp>'
        )

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr><a:solidFill><a:srgbClr val="{bg}"/></a:solidFill><a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
      {bar}
      <p:sp>
        <p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="457200" y="400000"/><a:ext cx="11277600" cy="900000"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/><a:lstStyle/>
          <a:p><a:r><a:rPr lang="zh-CN" sz="3200" b="1">
            <a:solidFill><a:srgbClr val="{title_color}"/></a:solidFill>
          </a:rPr><a:t>{title}</a:t></a:r></a:p>
        </p:txBody>
      </p:sp>
      {sub_xml}
      <p:sp>
        <p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="457200" y="1700000"/><a:ext cx="11277600" cy="4500000"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/><a:lstStyle/>
          {body_xml}
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
  <p:transition spd="med"><p:fade/></p:transition>
</p:sld>"""


def _minimal_pptx_bytes(content: dict[str, Any]) -> bytes:
    """OOXML with theme/master/layout + colored backgrounds so Keynote/PowerPoint open."""
    slides = _slides_or_placeholder(content)
    colors = _palette_colors(content)

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, len(slides) + 1):
        content_types.append(
            f'<Override PartName="/ppt/slides/slide{i}.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
        )
    content_types.append("</Types>")

    rels_root = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

    pres_rels_parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    ]
    for i in range(1, len(slides) + 1):
        pres_rels_parts.append(
            f'<Relationship Id="rId{i}" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" '
            f'Target="slides/slide{i}.xml"/>'
        )
    master_rid = len(slides) + 1
    pres_rels_parts.append(
        f'<Relationship Id="rId{master_rid}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" '
        'Target="slideMasters/slideMaster1.xml"/>'
    )
    pres_rels_parts.append("</Relationships>")

    sld_id_lst = []
    for i in range(1, len(slides) + 1):
        sld_id_lst.append(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>')
    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId{master_rid}"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    {''.join(sld_id_lst)}
  </p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""

    master_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""

    layout_rels = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""

    core = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>Qisi PPT</dc:title>
  <dc:creator>qisi_ai_kejian</dc:creator>
</cp:coreProperties>"""

    app = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>qisi_ai_kejian</Application>
  <Slides>{len(slides)}</Slides>
</Properties>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "\n".join(content_types))
        zf.writestr("_rels/.rels", rels_root)
        zf.writestr("docProps/core.xml", core)
        zf.writestr("docProps/app.xml", app)
        zf.writestr("ppt/presentation.xml", presentation)
        zf.writestr("ppt/_rels/presentation.xml.rels", "\n".join(pres_rels_parts))
        zf.writestr("ppt/theme/theme1.xml", _theme_xml())
        zf.writestr("ppt/slideMasters/slideMaster1.xml", _slide_master_xml())
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", master_rels)
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", _slide_layout_xml())
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", layout_rels)
        for i, slide in enumerate(slides):
            zf.writestr(f"ppt/slides/slide{i + 1}.xml", _fallback_slide_xml(slide, i, len(slides), colors))
            zf.writestr(
                f"ppt/slides/_rels/slide{i + 1}.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" '
                'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" '
                'Target="../slideLayouts/slideLayout1.xml"/>'
                "</Relationships>",
            )
    return buf.getvalue()


def _assert_valid_pptx_bytes(data: bytes) -> None:
    if len(data) < 100 or data[:2] != b"PK":
        raise RuntimeError("pptx output missing ZIP/OOXML signature")
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        bad = zf.testzip()
        if bad is not None:
            raise RuntimeError(f"pptx zip integrity failed: {bad}")
        names = set(zf.namelist())
        required = {"[Content_Types].xml", "ppt/presentation.xml", "_rels/.rels"}
        missing = required - names
        if missing:
            raise RuntimeError(f"pptx missing parts: {sorted(missing)}")


def write_pptx(content: dict[str, Any], dest: Path) -> dict[str, Any]:
    """Write .pptx to dest. Returns file metadata for artifact.content."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    used_lib = _try_python_pptx(content, dest)
    if not used_lib:
        data = _minimal_pptx_bytes(content)
        _assert_valid_pptx_bytes(data)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(dest)
    try:
        _assert_valid_pptx_bytes(dest.read_bytes())
    except RuntimeError:
        data = _minimal_pptx_bytes(content)
        _assert_valid_pptx_bytes(data)
        tmp = dest.with_suffix(dest.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(dest)
        used_lib = False
        _assert_valid_pptx_bytes(dest.read_bytes())
    meta = {
        "file_name": dest.name,
        "file_path": str(dest),
        "file_size": dest.stat().st_size,
        "mime_type": PPTX_MIME,
        "builder": "python-pptx" if used_lib else "ooxml-fallback",
        "mock_file": not used_lib,
        "pptx_valid": True,
        "visual_theme": "qisi-classroom",
        "has_transitions": True,
    }
    return meta


def persist_artifact_pptx(artifact_id: int, content: dict[str, Any], title: str | None) -> dict[str, Any]:
    """Write pptx for artifact and return download fields to merge into content."""
    path = artifact_pptx_path(artifact_id)
    meta = write_pptx(content, path)
    download_name = _safe_filename(title or content.get("title"), artifact_id)
    return {
        "download_url": download_url_for(artifact_id),
        "file_name": download_name,
        "ascii_file_name": ascii_download_name(artifact_id),
        "file_size": meta["file_size"],
        "mime_type": meta["mime_type"],
        "pptx_builder": meta["builder"],
        "has_pptx_file": True,
        "pptx_valid": bool(meta.get("pptx_valid", True)),
        "visual_theme": meta.get("visual_theme"),
        "has_transitions": bool(meta.get("has_transitions")),
        "mock": False if meta["builder"] == "python-pptx" else content.get("mock", True),
    }
