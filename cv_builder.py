#!/usr/bin/env python3
"""
ATS-Friendly CV Builder
Parses a structured Markdown file and outputs HTML, PDF, and DOCX.
Usage: python cv_builder.py [input_file] [-o OUTPUT_DIR] [-n NAME] [--no-html] [--no-pdf] [--no-docx]
"""

import re
import sys
import argparse
from html import escape
from pathlib import Path

# ── Dependency check ──────────────────────────────────────────────────────────
try:
    import yaml  # noqa: F401
except ImportError:
    print("Missing dependency: pyyaml. Run: pip install -r requirements.txt")
    sys.exit(1)

try:
    from weasyprint import HTML as WeasyprintHTML
    WEASYPRINT_OK = True
except ImportError:
    WEASYPRINT_OK = False

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    DOCX_OK = True
except ImportError:
    DOCX_OK = False


# ── Parser ────────────────────────────────────────────────────────────────────

def parse_cv(md_path: Path) -> dict:
    text = md_path.read_text(encoding="utf-8")
    lines = [
        l for l in text.splitlines()
        if not (l.strip().startswith("#") and not l.strip().startswith("##"))
    ]
    text = "\n".join(lines)

    raw_blocks = re.split(r"(?m)^---$", text)
    cv = {"meta": {}, "sections": []}
    current_header = None
    current_body_lines = []

    def flush():
        if current_header is None:
            return
        block = (current_header + "\n" + "\n".join(current_body_lines)).strip()
        if re.match(r"^## META", block):
            cv["meta"] = _parse_meta(re.sub(r"^## META\s*", "", block).strip())
        elif re.match(r"^## ", block):
            section = _parse_section(block)
            if section:
                cv["sections"].append(section)

    for raw in raw_blocks:
        raw = raw.strip()
        if not raw:
            continue
        first_line = raw.splitlines()[0].strip()
        if first_line.startswith("## "):
            flush()
            current_header = first_line
            current_body_lines = raw.splitlines()[1:]
        elif current_header is not None:
            current_body_lines.extend(raw.splitlines())

    flush()
    return cv


def _parse_meta(text: str) -> dict:
    meta = {}
    contact_items = []  # ordered list of ("type", value) — preserves input order
    current_list = None  # "links" or "extras"
    list_buffer = []

    def flush_list():
        nonlocal current_list, list_buffer
        if current_list == "links":
            for item in list_buffer:
                contact_items.append(("link", item))
            meta["links"] = list_buffer[:]
        elif current_list == "extras":
            for item in list_buffer:
                contact_items.append(("text", item))
        current_list = None
        list_buffer = []

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        # Collect list items (- prefixed) for current list block
        if line.strip().startswith("- ") and current_list is not None:
            raw = line.strip()[2:]
            if current_list == "links":
                list_buffer.append(_parse_inline_links(raw))
            else:
                list_buffer.append(raw)
            continue
        # A non-list line ends any active list block
        if current_list is not None:
            flush_list()
        if line.startswith("links:"):
            current_list = "links"
            continue
        if line.startswith("extras:"):
            current_list = "extras"
            continue
        if ":" in line:
            key, _, val = line.partition(":")
            k, v = key.strip(), val.strip()
            meta[k] = v
            if k == "email" and v:
                contact_items.append(("email", v))
            elif k == "phone" and v:
                contact_items.append(("phone", v))
            # name, profession, etc. are stored in meta but not in the contact bar

    if current_list is not None:
        flush_list()

    meta["contact_items"] = contact_items
    return meta


def _parse_section(block: str) -> dict | None:
    lines = block.splitlines()
    title = re.sub(r"^## ", "", lines[0]).strip()

    enabled = True
    for line in lines[1:]:
        m = re.match(r"^enabled:\s*(true|false)", line.strip(), re.I)
        if m:
            enabled = m.group(1).lower() == "true"
            break
    if not enabled:
        return None

    body_lines = []
    skip_enabled = True
    for line in lines[1:]:
        if skip_enabled and re.match(r"^enabled:", line.strip(), re.I):
            skip_enabled = False
            continue
        body_lines.append(line)
    body = "\n".join(body_lines).strip()

    section = {"title": title, "type": "generic", "content": None, "entries": []}
    if re.search(r"^### ", body, re.MULTILINE):
        section["type"] = "entries"
        section["entries"] = _parse_entries(body)
    else:
        section["type"] = "text"
        section["content"] = _normalise_skills(body)
    return section


def _normalise_skills(text: str) -> str:
    """Normalise comma/pipe/bullet separated lists to • separated.
    Only applies when the text looks like a flat tag list (no sentence punctuation).
    """
    stripped = text.strip()
    # Skip multi-paragraph blocks
    if "\n\n" in stripped:
        return stripped
    flat = " ".join(stripped.splitlines())
    # Skip if it reads like a sentence (contains a full stop or question/exclamation mark)
    if re.search(r"[.?!]", flat):
        return stripped
    items = re.split(r"\s*[,|•]\s*", flat)
    items = [i.strip() for i in items if i.strip()]
    if len(items) > 1:
        return " • ".join(items)
    return stripped


def _parse_entries(body: str) -> list:
    entries = []
    for chunk in re.split(r"(?=^### )", body, flags=re.MULTILINE):
        chunk = chunk.strip()
        if not chunk:
            continue
        entry_lines = chunk.splitlines()
        entry = {
            "name": re.sub(r"^### ", "", entry_lines[0]).strip(),
            "fields": {},
            "bullets": [],
        }
        in_bullets = False
        for line in entry_lines[1:]:
            line_s = line.strip()
            if line_s.startswith("bullets:"):
                in_bullets = True
                continue
            if in_bullets:
                if line_s.startswith("- "):
                    entry["bullets"].append(_parse_inline_links(line_s[2:]))
                continue
            if ":" in line_s and not line_s.startswith("-"):
                key, _, val = line_s.partition(":")
                entry["fields"][key.strip()] = val.strip()
        entries.append(entry)
    return entries


def _parse_inline_links(text: str):
    parts = []
    last = 0
    for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        if m.start() > last:
            parts.append(text[last:m.start()])
        parts.append((m.group(1), m.group(2)))
        last = m.end()
    if last < len(text):
        parts.append(text[last:])
    return parts if (len(parts) > 1 or (parts and isinstance(parts[0], tuple))) else text


# ── HTML Builder ──────────────────────────────────────────────────────────────

def _slug(title: str) -> str:
    """Convert a section title to a URL-safe anchor id."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def _segments_to_html(segments) -> str:
    if isinstance(segments, str):
        return escape(segments)
    parts = []
    for seg in segments:
        if isinstance(seg, tuple):
            label, url = seg
            parts.append(f'<a href="{escape(url)}">{escape(label)}</a>')
        else:
            parts.append(escape(seg))
    return "".join(parts)


def build_html(cv: dict) -> str:
    meta = cv["meta"]
    name = escape(meta.get("name", ""))
    profession = escape(meta.get("profession", ""))

    contact_parts = []
    for kind, val in meta.get("contact_items", []):
        if kind == "email":
            contact_parts.append(f'<a href="mailto:{escape(val)}">{escape(val)}</a>')
        elif kind == "phone":
            contact_parts.append(escape(val))
        elif kind == "text":
            contact_parts.append(escape(val))
        elif kind == "link":
            contact_parts.append(_segments_to_html(val))
    contact_html = " &nbsp;•&nbsp; ".join(contact_parts)

    profession_html = f'<div class="profession">{profession}</div>' if profession else ""
    sections_html = "".join(_section_to_html(s) for s in cv["sections"])
    doc_title = f"{name} — {profession}" if profession else name

    toc_items = "".join(
        f'<li><a href="#{_slug(s["title"])}">{escape(s["title"])}</a></li>'
        for s in cv["sections"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{doc_title} - CV</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9pt;
    color: #000;
    background: #fff;
  }}
  #toc {{
    position: fixed;
    top: 0; left: 0;
    width: 140px;
    height: 100vh;
    background: #f5f5f5;
    border-right: 1px solid #ddd;
    padding: 16px 10px;
    overflow-y: auto;
    font-size: 8pt;
  }}
  #toc h2 {{
    font-size: 8pt;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #666;
    margin-bottom: 8px;
  }}
  #toc ul {{ list-style: none; }}
  #toc ul li {{ margin-bottom: 6px; }}
  #toc ul li a {{ color: #000080; text-decoration: none; font-weight: bold; }}
  #toc ul li a:hover {{ text-decoration: underline; }}
  #cv {{
    margin-left: 155px;
    padding: 0.45in 0.55in;
    max-width: 8.5in;
  }}
  .cv-header {{ text-align: center; margin-bottom: 7px; }}
  h1 {{ font-size: 20pt; font-weight: bold; letter-spacing: 0.5px; margin-bottom: 1px; }}
  .profession {{ font-size: 10pt; color: #333; margin-bottom: 3px; }}
  .contact {{ font-size: 8.5pt; color: #222; }}
  .contact a {{ color: #000080; text-decoration: none; }}
  .section-title {{
    font-size: 10pt; font-weight: bold; text-transform: uppercase;
    letter-spacing: 0.8px; border-bottom: 1.2px solid #000;
    padding-bottom: 1px; margin-top: 7px; margin-bottom: 3px;
  }}
  .section-text {{ font-size: 9pt; line-height: 1.35; }}
  .entry {{ margin-bottom: 4px; }}
  .entry-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
  .entry-name {{ font-weight: bold; font-size: 9pt; }}
  .entry-date {{ font-size: 8.5pt; color: #444; white-space: nowrap; }}
  .entry-sub {{ font-size: 8.5pt; font-style: italic; color: #333; margin-bottom: 1px; }}
  ul {{ margin-left: 13px; margin-top: 1px; }}
  ul li {{ font-size: 9pt; line-height: 1.3; margin-bottom: 1px; }}
  ul li a {{ color: #000080; text-decoration: none; }}
  @media print {{
    #toc {{ display: none; }}
    #cv {{ margin-left: 0; padding: 0.4in 0.5in; }}
    a {{ color: #000080; }}
    @page {{ size: letter; margin: 0; }}
    .section-title {{
      bookmark-level: 1;
      bookmark-label: content();
    }}
  }}
</style>
</head>
<body>
<nav id="toc">
  <h2>Contents</h2>
  <ul>{toc_items}</ul>
</nav>
<div id="cv">
<div class="cv-header">
  <h1>{name}</h1>
  {profession_html}
  <div class="contact">{contact_html}</div>
</div>
{sections_html}
</div>
</body>
</html>"""


def _section_to_html(section: dict) -> str:
    title = escape(section["title"])
    slug = _slug(section["title"])
    parts = [f'<div class="section-title" id="{slug}">{title}</div>\n']
    if section["type"] == "text":
        parts.append(f'<div class="section-text">{escape(section["content"])}</div>\n')
    elif section["type"] == "entries":
        parts.extend(_entry_to_html(e) for e in section["entries"])
    return "".join(parts)


def _entry_to_html(entry: dict) -> str:
    f = entry["fields"]
    name = escape(entry["name"])
    role = escape(f.get("role", f.get("degree", "")))
    field = escape(f.get("field", ""))
    org = escape(f.get("org", ""))
    date = escape(f.get("date", ""))

    parts = ['<div class="entry">']
    parts.append(f'<div class="entry-header"><span class="entry-name">{name}</span>')
    if date:
        parts.append(f'<span class="entry-date">{date}</span>')
    parts.append('</div>')

    sub_parts = [v for v in [role, field, org] if v]
    if sub_parts:
        parts.append(f'<div class="entry-sub">{" &nbsp;•&nbsp; ".join(sub_parts)}</div>')

    if entry["bullets"]:
        items = "".join(f"<li>{_segments_to_html(b)}</li>" for b in entry["bullets"])
        parts.append(f"<ul>{items}</ul>")

    parts.append("</div>\n")
    return "".join(parts)


# ── DOCX Builder ──────────────────────────────────────────────────────────────

def _add_run_with_links(para, segments, bold=False, italic=False, size_pt=9):
    if isinstance(segments, str):
        run = para.add_run(segments)
        run.bold = bold
        run.italic = italic
        run.font.size = Pt(size_pt)
        return
    for seg in segments:
        if isinstance(seg, tuple):
            label, url = seg
            run = para.add_run(label)
            run.bold = bold
            run.italic = italic
            run.font.size = Pt(size_pt)
            run.font.color.rgb = RGBColor(0, 0, 128)
            r_id = para.part.relate_to(
                url,
                "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
                is_external=True,
            )
            rPr = run._r.get_or_add_rPr()
            rStyle = OxmlElement("w:rStyle")
            rStyle.set(qn("w:val"), "Hyperlink")
            rPr.insert(0, rStyle)
            hyperlink = OxmlElement("w:hyperlink")
            hyperlink.set(qn("r:id"), r_id)
            hyperlink.append(run._r)
            para._p.append(hyperlink)
        else:
            run = para.add_run(seg)
            run.bold = bold
            run.italic = italic
            run.font.size = Pt(size_pt)


def _set_para_spacing(para, before=0, after=0, line=None):
    pPr = para._p.get_or_add_pPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:before"), str(before))
    spacing.set(qn("w:after"), str(after))
    if line is not None:
        spacing.set(qn("w:line"), str(line))
        spacing.set(qn("w:lineRule"), "exact")
    pPr.append(spacing)


def _set_para_align(para, alignment):
    para.alignment = alignment


def _docx_add_toc(doc):
    """Insert a TOC field that Word renders automatically on open."""
    toc_para = doc.add_paragraph()
    _set_para_spacing(toc_para, before=0, after=40)
    run = toc_para.add_run()
    fldChar_begin = OxmlElement("w:fldChar")
    fldChar_begin.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText")
    instrText.set(qn("xml:space"), "preserve")
    instrText.text = ' TOC \\o "1-1" \\h \\z \\u '
    fldChar_sep = OxmlElement("w:fldChar")
    fldChar_sep.set(qn("w:fldCharType"), "separate")
    fldChar_end = OxmlElement("w:fldChar")
    fldChar_end.set(qn("w:fldCharType"), "end")
    run._r.append(fldChar_begin)
    run._r.append(instrText)
    run._r.append(fldChar_sep)
    run._r.append(fldChar_end)
    placeholder = toc_para.add_run("[Table of Contents — open in Word and press Ctrl+A then F9 to update]")
    placeholder.font.size = Pt(8)
    placeholder.font.color.rgb = RGBColor(120, 120, 120)
    placeholder.font.italic = True
    # Page break after TOC
    pb = doc.add_paragraph()
    pb.add_run().add_break(__import__("docx.enum.text", fromlist=["WD_BREAK"]).WD_BREAK.PAGE)


def build_docx(cv: dict, out_path: Path):
    doc = Document()

    # Tight margins for 1-page
    for sec in doc.sections:
        sec.top_margin = Inches(0.45)
        sec.bottom_margin = Inches(0.45)
        sec.left_margin = Inches(0.55)
        sec.right_margin = Inches(0.55)

    meta = cv["meta"]
    name = meta.get("name", "")
    profession = meta.get("profession", "")

    # Document title in properties
    doc.core_properties.title = f"{name} — {profession}" if profession else name
    doc.core_properties.author = name

    # TOC field (Word populates this on open)
    _docx_add_toc(doc)

    # Name — centred
    name_para = doc.add_paragraph()
    _set_para_spacing(name_para, before=0, after=20)
    _set_para_align(name_para, WD_ALIGN_PARAGRAPH.CENTER)
    run = name_para.add_run(name)
    run.bold = True
    run.font.size = Pt(20)

    # Profession — centred
    if profession:
        prof_para = doc.add_paragraph()
        _set_para_spacing(prof_para, before=0, after=15)
        _set_para_align(prof_para, WD_ALIGN_PARAGRAPH.CENTER)
        r = prof_para.add_run(profession)
        r.font.size = Pt(10)
        r.font.color.rgb = RGBColor(51, 51, 51)

    # Contact line — centred
    contact_para = doc.add_paragraph()
    _set_para_spacing(contact_para, before=0, after=50)
    _set_para_align(contact_para, WD_ALIGN_PARAGRAPH.CENTER)

    contact_items = meta.get("contact_items", [])

    for i, (kind, val) in enumerate(contact_items):
        if i > 0:
            sep = contact_para.add_run("  •  ")
            sep.font.size = Pt(8.5)
        if kind == "email":
            r = contact_para.add_run(val)
            r.font.size = Pt(8.5)
            r.font.color.rgb = RGBColor(0, 0, 128)
        elif kind == "phone":
            r = contact_para.add_run(val)
            r.font.size = Pt(8.5)
        elif kind == "text":
            r = contact_para.add_run(val)
            r.font.size = Pt(8.5)
        elif kind == "link":
            _add_run_with_links(contact_para, val, size_pt=8.5)

    for section in cv["sections"]:
        _docx_section(doc, section)

    doc.save(out_path)


def _docx_section(doc, section: dict):
    # Use Heading 1 style so the TOC field picks up section titles
    title_para = doc.add_paragraph(style="Heading 1")
    _set_para_spacing(title_para, before=60, after=15)
    title_para.clear()
    run = title_para.add_run(section["title"].upper())
    run.bold = True
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0, 0, 0)
    # Underline border
    pPr = title_para._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "000000")
    pBdr.append(bottom)
    pPr.append(pBdr)

    if section["type"] == "text":
        p = doc.add_paragraph()
        _set_para_spacing(p, before=0, after=0)
        p.add_run(section["content"]).font.size = Pt(9)
    elif section["type"] == "entries":
        for entry in section["entries"]:
            _docx_entry(doc, entry)


def _docx_entry(doc, entry: dict):
    f = entry["fields"]
    name = entry["name"]
    role = f.get("role", f.get("degree", ""))
    field = f.get("field", "")
    org = f.get("org", "")
    date = f.get("date", "")

    # Name + date on same line via right-aligned tab
    p = doc.add_paragraph()
    _set_para_spacing(p, before=30, after=0)
    p.paragraph_format.tab_stops.add_tab_stop(Inches(6.4), WD_ALIGN_PARAGRAPH.RIGHT)
    r = p.add_run(name)
    r.bold = True
    r.font.size = Pt(9)
    if date:
        tab = p.add_run("\t" + date)
        tab.font.size = Pt(8.5)
        tab.font.color.rgb = RGBColor(68, 68, 68)

    sub_parts = [v for v in [role, field, org] if v]
    if sub_parts:
        p2 = doc.add_paragraph()
        _set_para_spacing(p2, before=0, after=0)
        r2 = p2.add_run("  •  ".join(sub_parts))
        r2.italic = True
        r2.font.size = Pt(8.5)
        r2.font.color.rgb = RGBColor(51, 51, 51)

    for bullet in entry["bullets"]:
        bp = doc.add_paragraph(style="List Bullet")
        _set_para_spacing(bp, before=0, after=0)
        bp.paragraph_format.left_indent = Inches(0.15)
        _add_run_with_links(bp, bullet, size_pt=9)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ATS CV Builder")
    parser.add_argument("input", nargs="?", default="input/cv_template.md")
    parser.add_argument(
        "-o", "--output-dir",
        default="output",
        help="Directory to save generated files (default: output)",
    )
    parser.add_argument(
        "-n", "--name",
        default=None,
        help="Custom base name for output files without extension (default: input file name)",
    )
    parser.add_argument("--no-html", action="store_true", help="Skip HTML output")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF output")
    parser.add_argument("--no-docx", action="store_true", help="Skip DOCX output")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Parsing: {input_path}")
    cv = parse_cv(input_path)
    stem = Path(args.name).stem if args.name else input_path.stem

    html_content = None
    if not args.no_html or not args.no_pdf:
        html_content = build_html(cv)

    if not args.no_html:
        html_path = output_dir / f"{stem}.html"
        html_path.write_text(html_content, encoding="utf-8")
        print(f"  ✓ HTML  → {html_path}")

    if not args.no_pdf:
        if WEASYPRINT_OK:
            pdf_path = output_dir / f"{stem}.pdf"
            WeasyprintHTML(string=html_content, base_url=str(output_dir)).write_pdf(str(pdf_path))
            print(f"  ✓ PDF   → {pdf_path}")
        else:
            print("  ✗ PDF skipped (weasyprint not installed)")

    if not args.no_docx:
        if DOCX_OK:
            docx_path = output_dir / f"{stem}.docx"
            build_docx(cv, docx_path)
            print(f"  ✓ DOCX  → {docx_path}")
        else:
            print("  ✗ DOCX skipped (python-docx not installed)")

    print("Done.")


if __name__ == "__main__":
    main()
