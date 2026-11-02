"""Build a real .pptx from slide JSON. Prefer python-pptx; improved OOXML fallback."""

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

    for slide in _slides_or_placeholder(content):
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
        if note:
            try:
                ns = s.notes_slide
                ns.notes_text_frame.text = str(note)
            except Exception:
                pass

    dest.parent.mkdir(parents=True, exist_ok=True)
    # Atomic write: save to buffer then replace, avoids truncated downloads mid-write
    buf = io.BytesIO()
    prs.save(buf)
    data = buf.getvalue()
    _assert_valid_pptx_bytes(data)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
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


def _minimal_pptx_bytes(content: dict[str, Any]) -> bytes:
    """OOXML with theme/master/layout so Keynote/PowerPoint can open (not just zip-valid)."""
    slides = _slides_or_placeholder(content)
    titles = [str(s.get("title") or f"Slide {i}") for i, s in enumerate(slides, 1)]

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

    # presentation rels: slides + slideMaster
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
        for i, slide in enumerate(slides, 1):
            title = escape(titles[i - 1])
            bullets = slide.get("bullets") or []
            body_lines = []
            for b in bullets[:8]:
                body_lines.append(
                    '<a:p><a:r><a:rPr lang="zh-CN" sz="1800"/><a:t>'
                    f"{escape(str(b))}</a:t></a:r></a:p>"
                )
            body_xml = "".join(body_lines) or '<a:p><a:endParaRPr lang="zh-CN"/></a:p>'
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
    # Prefer re-validating the on-disk file (catches partial writes)
    try:
        _assert_valid_pptx_bytes(dest.read_bytes())
    except RuntimeError:
        # Last-resort rebuild via openable OOXML so download stays usable.
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
        "mock": False if meta["builder"] == "python-pptx" else content.get("mock", True),
    }
