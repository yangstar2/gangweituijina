"""Build a real .pptx from slide JSON. Prefer python-pptx; zip fallback if missing."""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from ..config import settings

PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def storage_dir() -> Path:
    path = Path(settings.database_path).resolve().parent / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def artifact_pptx_path(artifact_id: int) -> Path:
    return storage_dir() / f"artifact_{artifact_id}.pptx"


def download_url_for(artifact_id: int) -> str:
    return f"/api/artifacts/{artifact_id}/download"


def _safe_filename(title: str | None, artifact_id: int) -> str:
    base = re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", (title or "课件").strip())[:40] or "课件"
    return f"{base}_{artifact_id}.pptx"


def _try_python_pptx(content: dict[str, Any], dest: Path) -> bool:
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
    except ImportError:
        return False

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]  # blank

    slides = content.get("slides") or []
    if not slides:
        slides = [
            {
                "title": content.get("title") or "课件",
                "subtitle": "空大纲占位",
                "bullets": ["请补充大纲后重新生成"],
                "layout": "cover",
            }
        ]

    for slide in slides:
        s = prs.slides.add_slide(blank)
        title = str(slide.get("title") or "")
        subtitle = slide.get("subtitle")
        bullets = list(slide.get("bullets") or [])

        box = s.shapes.add_textbox(Inches(0.7), Inches(0.5), Inches(11.8), Inches(1.2))
        tf = box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(32)
        p.font.bold = True

        y = 1.9
        if subtitle:
            sub = s.shapes.add_textbox(Inches(0.7), Inches(1.5), Inches(11.8), Inches(0.5))
            st = sub.text_frame.paragraphs[0]
            st.text = str(subtitle)
            st.font.size = Pt(16)
            y = 2.2

        if bullets:
            body = s.shapes.add_textbox(Inches(0.9), Inches(y), Inches(11.4), Inches(4.8))
            btf = body.text_frame
            btf.word_wrap = True
            for i, bullet in enumerate(bullets):
                para = btf.paragraphs[0] if i == 0 else btf.add_paragraph()
                para.text = str(bullet)
                para.level = 0
                para.font.size = Pt(18)
                para.space_after = Pt(8)

        note = slide.get("speaker_note")
        if note and s.has_notes_slide:
            ns = s.notes_slide
            ns.notes_text_frame.text = str(note)
        elif note:
            try:
                ns = s.notes_slide
                ns.notes_text_frame.text = str(note)
            except Exception:
                pass

    dest.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(dest))
    return True


def _minimal_pptx_bytes(content: dict[str, Any]) -> bytes:
    """Hand-rolled OOXML when python-pptx is unavailable — still a valid .pptx zip."""
    slides = content.get("slides") or [
        {"title": content.get("title") or "课件", "bullets": ["占位页"]}
    ]
    titles = [str(s.get("title") or f"Slide {i}") for i, s in enumerate(slides, 1)]

    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
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
    pres_rels_parts.append("</Relationships>")

    sld_id_lst = []
    for i in range(1, len(slides) + 1):
        sld_id_lst.append(f'<p:sldId id="{255 + i}" r:id="rId{i}"/>')
    presentation = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:sldIdLst>
    {''.join(sld_id_lst)}
  </p:sldIdLst>
  <p:sldSz cx="12192000" cy="6858000"/>
  <p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", "\n".join(content_types))
        zf.writestr("_rels/.rels", rels_root)
        zf.writestr("ppt/presentation.xml", presentation)
        zf.writestr("ppt/_rels/presentation.xml.rels", "\n".join(pres_rels_parts))
        for i, slide in enumerate(slides, 1):
            title = escape(titles[i - 1])
            bullets = slide.get("bullets") or []
            body_lines = []
            for b in bullets[:8]:
                body_lines.append(
                    "<a:p><a:r><a:rPr lang=\"zh-CN\" sz=\"1800\"/><a:t>"
                    f"{escape(str(b))}</a:t></a:r></a:p>"
                )
            body_xml = "".join(body_lines) or "<a:p><a:endParaRPr lang=\"zh-CN\"/></a:p>"
            slide_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
 xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="457200" y="274320"/><a:ext cx="11277600" cy="914400"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/><a:lstStyle/>
          <a:p><a:r><a:rPr lang="zh-CN" sz="3200" b="1"/><a:t>{title}</a:t></a:r></a:p>
        </p:txBody>
      </p:sp>
      <p:sp>
        <p:nvSpPr><p:cNvPr id="3" name="Body"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="457200" y="1371600"/><a:ext cx="11277600" cy="4572000"/></a:xfrm>
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
</p:sld>"""
            zf.writestr(f"ppt/slides/slide{i}.xml", slide_xml)
            zf.writestr(
                f"ppt/slides/_rels/slide{i}.xml.rels",
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>',
            )
    return buf.getvalue()


def write_pptx(content: dict[str, Any], dest: Path) -> dict[str, Any]:
    """Write .pptx to dest. Returns file metadata for artifact.content."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    used_lib = _try_python_pptx(content, dest)
    if not used_lib:
        dest.write_bytes(_minimal_pptx_bytes(content))
    meta = {
        "file_name": dest.name,
        "file_path": str(dest),
        "file_size": dest.stat().st_size,
        "mime_type": PPTX_MIME,
        "builder": "python-pptx" if used_lib else "ooxml-fallback",
        "mock_file": not used_lib,
    }
    return meta


def persist_artifact_pptx(artifact_id: int, content: dict[str, Any], title: str | None) -> dict[str, Any]:
    """Write pptx for artifact and return download fields to merge into content."""
    path = artifact_pptx_path(artifact_id)
    meta = write_pptx(content, path)
    # Prefer a human filename in Content-Disposition; keep storage key stable.
    download_name = _safe_filename(title or content.get("title"), artifact_id)
    return {
        "download_url": download_url_for(artifact_id),
        "file_name": download_name,
        "file_size": meta["file_size"],
        "mime_type": meta["mime_type"],
        "pptx_builder": meta["builder"],
        "has_pptx_file": True,
        "mock": False if meta["builder"] == "python-pptx" else content.get("mock", True),
    }
