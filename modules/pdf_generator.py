import re

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _normalize_pdf_text(text):

    if not text:
        return ""

    normalized = str(text).replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _escape_pdf_text(text):

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _build_paragraph(style, text, preserve_line_breaks=False):

    escaped_text = _escape_pdf_text(text)

    if preserve_line_breaks:
        escaped_text = escaped_text.replace("\n", "<br/>")

    return Paragraph(escaped_text, style)


def create_pdf(text, path):

    doc = SimpleDocTemplate(
        path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "BlogTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        spaceAfter=14,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        "BlogHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=8,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "BlogBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        spaceAfter=10,
    )
    tag_style = ParagraphStyle(
        "BlogTags",
        parent=body_style,
        fontName="Helvetica-Bold",
        textColor="#444444",
        spaceAfter=14,
    )

    normalized_text = _normalize_pdf_text(text)
    story = []

    if not normalized_text:
        doc.build([Paragraph("No content available.", body_style)])
        return

    blocks = [block.strip() for block in normalized_text.split("\n\n") if block.strip()]

    for block in blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue

        first_line = lines[0]

        if first_line.startswith("# "):
            story.append(_build_paragraph(title_style, first_line[2:].strip()))
            remainder = "\n".join(lines[1:]).strip()
            if remainder:
                story.append(_build_paragraph(body_style, remainder, preserve_line_breaks=True))
            continue

        if first_line.startswith("## "):
            story.append(_build_paragraph(heading_style, first_line[3:].strip()))
            remainder = "\n".join(lines[1:]).strip()
            if remainder:
                story.append(_build_paragraph(body_style, remainder, preserve_line_breaks=True))
            continue

        if first_line.lower().startswith("tags:"):
            story.append(_build_paragraph(tag_style, first_line))
            remainder = "\n".join(lines[1:]).strip()
            if remainder:
                story.append(_build_paragraph(body_style, remainder, preserve_line_breaks=True))
            continue

        story.append(_build_paragraph(body_style, block, preserve_line_breaks=True))

    doc.build(story)
