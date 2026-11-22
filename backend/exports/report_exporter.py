from io import BytesIO
import docx
import pymupdf


def export_markdown_bytes(title: str, report_markdown: str, summary: str = "") -> bytes:
    parts = [f"# {title}".strip()]
    if summary.strip():
        parts.extend(["## Executive Summary", summary.strip()])
    parts.append(report_markdown.strip() or "No report generated.")
    content = "\n\n".join(parts) + "\n"
    return content.encode("utf-8")


def export_docx_bytes(title: str, report_markdown: str, summary: str = "") -> bytes:
    doc = docx.Document()
    doc.add_heading(title.strip() or "Research Report", level=0)

    if summary.strip():
        doc.add_heading("Executive Summary", level=1)
        doc.add_paragraph(summary.strip())

    doc.add_heading("Detailed Report", level=1)
    for raw_line in (report_markdown or "No report generated.").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("### "):
            doc.add_heading(line[4:].strip(), level=3)
        elif line.startswith("## "):
            doc.add_heading(line[3:].strip(), level=2)
        elif line.startswith("# "):
            doc.add_heading(line[2:].strip(), level=1)
        elif line.startswith(("- ", "* ")):
            doc.add_paragraph(line[2:].strip(), style="List Bullet")
        else:
            doc.add_paragraph(line)

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def export_pdf_bytes(title: str, report_markdown: str, summary: str = "") -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    margin_x = 48
    margin_y = 54
    max_width = page.rect.width - (2 * margin_x)
    y = margin_y

    def write_block(text: str, font_size: int = 10, bold: bool = False, extra_gap: float = 6.0):
        nonlocal page, y
        font_name = "hebo" if bold else "helv"
        lines = text.splitlines() or [""]
        for raw in lines:
            clean = raw.lstrip("#").strip() if raw.startswith("#") else raw
            if not clean:
                y += font_size * 0.6
                continue
            approx_chars = max(35, int(max_width / (font_size * 0.52)))
            wrapped = [clean[i : i + approx_chars] for i in range(0, len(clean), approx_chars)] or [""]
            for wline in wrapped:
                if y + font_size + 12 > page.rect.height - margin_y:
                    page = doc.new_page()
                    y = margin_y
                page.insert_text((margin_x, y), wline, fontsize=font_size, fontname=font_name)
                y += font_size * 1.35
        y += extra_gap

    write_block(title.strip() or "Research Report", font_size=16, bold=True, extra_gap=10.0)
    if summary.strip():
        write_block("Executive Summary", font_size=12, bold=True, extra_gap=4.0)
        write_block(summary.strip(), font_size=10, bold=False, extra_gap=8.0)

    write_block("Research Report", font_size=12, bold=True, extra_gap=4.0)
    write_block(report_markdown or "No report generated.", font_size=10, bold=False, extra_gap=4.0)

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

