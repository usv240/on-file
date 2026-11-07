"""Build the Round 1 proposal PDF from final.md.

Usage: python build_pdf.py [final.md] [out.pdf]
Prints the counted words of the ten answers and the PDF size. Fails if either limit is exceeded.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (Flowable, HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer)

SRC = Path(sys.argv[1] if len(sys.argv) > 1 else "final.md")
OUT = Path(sys.argv[2] if len(sys.argv) > 2 else "On-File-Round1-Proposal.pdf")

INK = colors.HexColor("#1b1f24")
MUTED = colors.HexColor("#5c6470")
RULE = colors.HexColor("#c9ced6")
ACCENT = colors.HexColor("#0b5fa5")

body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.4, leading=12.6, textColor=INK, alignment=TA_LEFT, spaceAfter=3)
q = ParagraphStyle("q", parent=body, fontName="Helvetica-Bold", fontSize=9.6, leading=12.4, spaceBefore=5, spaceAfter=1.2, textColor=INK)
title = ParagraphStyle("title", parent=body, fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=2)
sub = ParagraphStyle("sub", parent=body, fontSize=9.2, textColor=MUTED, spaceAfter=6)
small = ParagraphStyle("small", parent=body, fontSize=8.4, leading=11.4, textColor=MUTED, spaceAfter=3)
caption = ParagraphStyle("cap", parent=small, spaceBefore=2, spaceAfter=8)


class Flow(Flowable):
    """Seven boxes joined by arrows: the user flow at a glance. Labels are kept to a few words."""

    LABELS = ["Request", "Search\nevery source", "Confirm\npassage", "Disambiguate", "Index +\nletter", "Approve\neach file", "Audit +\nverify"]

    def __init__(self, width: float):
        super().__init__()
        self.width = width
        self.height = 19.5 * mm

    def draw(self):
        c = self.canv
        n = len(self.LABELS)
        gap = 4.2 * mm
        bw = (self.width - gap * (n - 1)) / n
        bh = 12.5 * mm
        y = self.height - bh - 0.5 * mm
        for i, lab in enumerate(self.LABELS):
            x = i * (bw + gap)
            writes = i == 5
            c.setStrokeColor(ACCENT if writes else RULE)
            c.setLineWidth(1.1 if writes else 0.8)
            c.setFillColor(colors.HexColor("#eef4fb") if writes else colors.white)
            c.roundRect(x, y, bw, bh, 2 * mm, stroke=1, fill=1)
            c.setFillColor(INK)
            c.setFont("Helvetica", 7.6)
            lines = lab.split("\n")
            ty = y + bh / 2 + (len(lines) - 1) * 4.2
            for ln in lines:
                c.drawCentredString(x + bw / 2, ty - 2.6, ln)
                ty -= 8.8
            if i < n - 1:
                ax0 = x + bw + 0.6 * mm
                ax1 = x + bw + gap - 0.6 * mm
                ay = y + bh / 2
                c.setStrokeColor(MUTED)
                c.setLineWidth(0.8)
                c.line(ax0, ay, ax1, ay)
                c.line(ax1, ay, ax1 - 1.4 * mm, ay + 1.0 * mm)
                c.line(ax1, ay, ax1 - 1.4 * mm, ay - 1.0 * mm)
        # read-only bracket under the search, confirm and disambiguate boxes (steps 1 to 5)
        c.setStrokeColor(RULE)
        c.setLineWidth(0.6)
        x0 = 1 * (bw + gap)
        x1 = 3 * (bw + gap) + bw
        c.line(x0, y - 1.6 * mm, x1, y - 1.6 * mm)
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Oblique", 6.8)
        c.drawCentredString((x0 + x1) / 2, y - 4.6 * mm, "read only")
        c.drawCentredString(4 * (bw + gap) + bw / 2, y - 4.6 * mm, "case folder only")
        c.drawCentredString(5 * (bw + gap) + bw / 2, y - 4.6 * mm, "touches records")


def parse(md: str):
    head, _, tail = md.partition("\n---\n")
    m = re.match(r"# (.+)\n\n(.+?)\n", head)
    doc_title, doc_sub = m.group(1), m.group(2)
    items = []
    for sec in re.split(r"\n## ", head)[1:]:
        qline, _, ans = sec.partition("\n")
        items.append((qline.strip(), " ".join(ans.split())))
    notes = [" ".join(p.split()) for p in tail.strip().split("\n\n") if p.strip()]
    return doc_title, doc_sub, items, notes


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def main():
    md = SRC.read_text(encoding="utf-8")
    doc_title, doc_sub, items, notes = parse(md)
    words = sum(len(a.split()) for _, a in items)
    print(f"answers: {len(items)} items, {words} words")
    assert len(items) == 10, "expected ten items"
    assert words <= 500, "over the 500-word limit"
    assert "—" not in md and "–" not in md, "dash characters found"

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=13 * mm, bottomMargin=12 * mm,
                            title=doc_title + " proposal", author="Ujwal Vanjare", subject="UGREEN Hackathon 2026 on AI NAS, Round 1")
    W = A4[0] - doc.leftMargin - doc.rightMargin
    story = [Paragraph(esc(doc_title), title), Paragraph(esc(doc_sub), sub), Flow(W),
             Paragraph("Steps 1 to 5 only read. Step 6 writes new files to the case folder only. Step 7 copies or deletes one file at a time, each behind its own approval. Step 8 re-hashes untouched files.", caption),
             HRFlowable(width="100%", thickness=0.6, color=RULE, spaceAfter=4)]
    for qline, ans in items:
        story.append(KeepTogether([Paragraph(esc(qline), q), Paragraph(esc(ans), body)]))
    tail = [Spacer(1, 4), HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=2, spaceAfter=5),
            Paragraph("Not counted toward the 500 words", ParagraphStyle("nc", parent=small, fontName="Helvetica-Bold"))]
    for p in notes:
        if p.startswith("Test corp"):
            label, _, url = p.partition(": ")
            p_html = f'{esc(label)}: <a href="{url}" color="#0b5fa5">{esc(url)}</a>'
            tail.append(Paragraph(p_html, small))
        else:
            tail.append(Paragraph(esc(p), small))
    tail.append(Paragraph(f"Word count of the ten answers: {words}. Laptop numbers in item 8 are stand-in measurements and will be replaced by NAS results in Round 2.", small))
    story.append(KeepTogether(tail))
    doc.build(story)
    size = OUT.stat().st_size
    print(f"wrote {OUT} ({size} bytes)")
    assert size <= 1_000_000, "PDF over 1 MB"


if __name__ == "__main__":
    main()
