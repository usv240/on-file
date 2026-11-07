#!/usr/bin/env python3
"""Deterministic generator for the blind test corpus.

Practice: Kestrel Bay Physiotherapy (a small physiotherapy clinic).
Requester: Sarah Mitchell (client KBP-10427).

Run from this folder:
    python make_blind.py --out corpus

Creates corpus/KestrelBay_Physio/ with the practice files and
corpus/expected.json with the ground truth, then checks that every
expected path exists and that nothing extra was written.

Every person, address, phone number, email and ID below is invented.
Emails use example.com / example.org; phone numbers use 555-01xx.
"""

import argparse
import csv
import hashlib
import io
import json
import os
import random
import re
import shutil
import sys
import zipfile
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from email import policy
from email.message import EmailMessage
from email.utils import format_datetime

import openpyxl
from docx import Document
from docx.shared import Pt
from openpyxl.styles import Font
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib import pdfencrypt
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas as rl_canvas

FONT_PATH = "C:/Windows/Fonts/arial.ttf"

PRACTICE_DIR = "KestrelBay_Physio"
PRACTICE_NAME = "Kestrel Bay Physiotherapy"
PRACTICE_ADDR = "112 Wharf Street, Suite 2, Linden Cove, OR 97991"
PRACTICE_CONTACT = "Tel (503) 555-0100  |  kbp.frontdesk@example.com"

FRONT_DESK = "Kestrel Bay Physiotherapy <kbp.frontdesk@example.com>"
JO = "Jo Whitfield <kbp.frontdesk@example.com>"
TOM = "Tom Reyes <kbp.tom.reyes@example.com>"
PRIYA = "Priya Natarajan <kbp.priya.n@example.com>"

REQUESTER = {
    "name": "Sarah Mitchell",
    "dob": "1983-09-22",
    "email": "sarah.mitchell83@example.com",
    "phone": "(503) 555-0147",
    "pid": "KBP-10427",
    "address": "17 Alder Crescent, Linden Cove, OR 97990",
}

ALLOWED_EXT = {".docx", ".xlsx", ".txt", ".csv", ".eml", ".pdf", ".jpg", ".png"}
GROUPS = ["target", "decoy", "noise", "unreadable_requester", "unreadable", "background"]


# ---------------------------------------------------------------------------
# Corpus registry
# ---------------------------------------------------------------------------

def aware(dt):
    """Attach Pacific time (PDT between the 2026 DST dates, else PST)."""
    pdt = datetime(2026, 3, 8, 2) <= dt < datetime(2026, 11, 1, 2)
    return dt.replace(tzinfo=timezone(timedelta(hours=-7 if pdt else -8)))


class Corpus:
    def __init__(self, root):
        self.root = root
        self.entries = []

    def fp(self, rel):
        full = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        return full

    def add(self, rel, group, how, strong, shared, record_type, note, when):
        assert group in GROUPS, group
        full = os.path.join(self.root, *rel.split("/"))
        if not os.path.isfile(full):
            raise RuntimeError("generator did not write " + rel)
        ts = aware(when).timestamp()
        os.utime(full, (ts, ts))
        self.entries.append({
            "path": rel,
            "group": group,
            "how": list(how),
            "strong_identifier_present": bool(strong),
            "shared": bool(shared),
            "record_type": record_type,
            "note": note,
        })


# ---------------------------------------------------------------------------
# Format helpers
# ---------------------------------------------------------------------------

ZIP_DT = (2026, 1, 1, 0, 0, 0)


def normalize_ooxml(path, created, modified):
    """Rewrite an Office zip with fixed entry timestamps and fixed core dates,
    so the output is byte-for-byte reproducible."""
    with open(path, "rb") as fh:
        src = zipfile.ZipFile(io.BytesIO(fh.read()))
    c_iso = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    m_iso = modified.strftime("%Y-%m-%dT%H:%M:%SZ")
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for info in src.infolist():
            data = src.read(info.filename)
            if info.filename == "docProps/core.xml":
                text = data.decode("utf-8")
                text = re.sub(r"(<dcterms:created[^>]*>)[^<]*(</dcterms:created>)",
                              lambda m: m.group(1) + c_iso + m.group(2), text)
                text = re.sub(r"(<dcterms:modified[^>]*>)[^<]*(</dcterms:modified>)",
                              lambda m: m.group(1) + m_iso + m.group(2), text)
                data = text.encode("utf-8")
            zi = zipfile.ZipInfo(info.filename, date_time=ZIP_DT)
            zi.compress_type = zipfile.ZIP_DEFLATED
            zi.external_attr = 0o644 << 16
            dst.writestr(zi, data)
    with open(path, "wb") as fh:
        fh.write(out.getvalue())


def write_docx(path, blocks, props, header=None):
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    if header:
        doc.sections[0].header.paragraphs[0].text = header
    for blk in blocks:
        kind = blk[0]
        if kind == "h1":
            doc.add_heading(blk[1], level=1)
        elif kind == "h2":
            doc.add_heading(blk[1], level=2)
        elif kind == "p":
            doc.add_paragraph(blk[1])
        elif kind == "b":
            doc.add_paragraph().add_run(blk[1]).bold = True
        elif kind == "small":
            doc.add_paragraph().add_run(blk[1]).font.size = Pt(9)
        elif kind == "bullet":
            doc.add_paragraph(blk[1], style="List Bullet")
        elif kind == "table":
            rows = blk[1]
            table = doc.add_table(rows=len(rows), cols=len(rows[0]))
            table.style = "Table Grid"
            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    table.cell(i, j).text = str(val)
            if len(blk) > 2 and blk[2] == "header":
                for cell in table.rows[0].cells:
                    for par in cell.paragraphs:
                        for run in par.runs:
                            run.bold = True
            doc.add_paragraph("")
        else:
            raise ValueError(kind)
    cp = doc.core_properties
    cp.author = props.get("author", "")
    cp.last_modified_by = props.get("last_modified_by", props.get("author", ""))
    cp.title = props.get("title", "")
    cp.subject = props.get("subject", "")
    cp.keywords = props.get("keywords", "")
    cp.comments = props.get("comments", "")
    cp.category = props.get("category", "")
    cp.revision = props.get("revision", 1)
    created = props["created"]
    modified = props.get("modified", created)
    cp.created = created
    cp.modified = modified
    cp.last_printed = created
    doc.save(path)
    normalize_ooxml(path, created, modified)


def write_xlsx(path, sheets, props):
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for name, rows in sheets:
        ws = wb.create_sheet(title=name)
        for r in rows:
            ws.append(list(r))
        for cell in ws[1]:
            cell.font = Font(bold=True)
        for col in ws.columns:
            width = 0
            for c in col:
                if isinstance(c.value, date):
                    c.number_format = "yyyy-mm-dd"
                    width = max(width, 10)
                elif c.value is not None:
                    width = max(width, len(str(c.value)))
            ws.column_dimensions[col[0].column_letter].width = min(max(10, width + 2), 70)
    p = wb.properties
    p.creator = props.get("author", "")
    p.lastModifiedBy = props.get("last_modified_by", props.get("author", ""))
    p.title = props.get("title")
    p.subject = props.get("subject")
    p.keywords = props.get("keywords")
    p.description = props.get("comments")
    created = props["created"]
    modified = props.get("modified", created)
    p.created = created
    p.modified = modified
    wb.save(path)
    normalize_ooxml(path, created, modified)


def wrap_pts(text, font, size, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if pdfmetrics.stringWidth(trial, font, size) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class PdfDoc:
    """Small text-PDF writer (real text layer, Helvetica)."""

    def __init__(self, path, title="", author="", subject="", creator="ClinicDesk 4.2 PDF export",
                 head=None, encrypt=None):
        kw = {"pagesize": letter, "invariant": 1}
        if encrypt:
            kw["encrypt"] = pdfencrypt.StandardEncryption(
                encrypt, ownerPassword=encrypt + "#owner", canPrint=1, canModify=0,
                canCopy=0, canAnnotate=0, strength=128)
        self.c = rl_canvas.Canvas(path, **kw)
        self.c.setTitle(title)
        self.c.setAuthor(author)
        self.c.setSubject(subject)
        self.c.setCreator(creator)
        self.head = [PRACTICE_NAME, PRACTICE_ADDR, PRACTICE_CONTACT] if head is None else head
        self._start()

    def _start(self):
        self.y = 752
        if self.head:
            self.c.setFont("Helvetica-Bold", 15)
            self.c.drawString(72, self.y, self.head[0])
            self.y -= 15
            self.c.setFont("Helvetica", 9)
            for line in self.head[1:]:
                self.c.drawString(72, self.y, line)
                self.y -= 11
            self.c.setLineWidth(0.8)
            self.c.line(72, self.y, 540, self.y)
            self.y -= 24

    def _need(self, h):
        if self.y - h < 64:
            self.c.showPage()
            self._start()

    def h1(self, text):
        self._need(26)
        self.c.setFont("Helvetica-Bold", 14)
        self.c.drawString(72, self.y, text)
        self.y -= 24

    def h2(self, text):
        self._need(24)
        self.y -= 4
        self.c.setFont("Helvetica-Bold", 11)
        self.c.drawString(72, self.y, text)
        self.y -= 16

    def p(self, text, font="Helvetica", size=10, lead=13.5):
        for para in text.split("\n"):
            for line in wrap_pts(para, font, size, 468) or [""]:
                self._need(lead)
                self.c.setFont(font, size)
                self.c.drawString(72, self.y, line)
                self.y -= lead
        self.y -= 5

    def row(self, cells, xs, font="Helvetica", size=9.5, lead=13.5):
        self._need(lead)
        self.c.setFont(font, size)
        for text, x in zip(cells, xs):
            self.c.drawString(x, self.y, str(text))
        self.y -= lead

    def rule(self):
        self._need(10)
        self.c.line(72, self.y + 5, 540, self.y + 5)
        self.y -= 8

    def space(self, h):
        self.y -= h

    def save(self):
        self.c.showPage()
        self.c.save()


def write_eml(path, frm, to, subject, when, body, cc=None, extra=None):
    msg = EmailMessage(policy=policy.SMTP)
    msg["From"] = frm
    msg["To"] = to if isinstance(to, str) else ", ".join(to)
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg["Date"] = format_datetime(aware(when))
    digest = hashlib.sha1((path.replace("\\", "/").split(PRACTICE_DIR)[-1] + subject).encode()).hexdigest()[:20]
    msg["Message-ID"] = "<%s@mail.example.com>" % digest
    for k, v in (extra or []):
        msg[k] = v
    msg.set_content(body)
    with open(path, "wb") as fh:
        fh.write(msg.as_bytes())


def write_text(path, text, encoding="utf-8"):
    text = text.replace("\r\n", "\n").replace("\n", "\r\n")
    if encoding == "utf-16-bom":
        data = b"\xff\xfe" + text.encode("utf-16-le")
    elif encoding == "utf-8-bom":
        data = b"\xef\xbb\xbf" + text.encode("utf-8")
    else:
        data = text.encode(encoding)
    with open(path, "wb") as fh:
        fh.write(data)


def write_csv(path, rows, bom=False):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\r\n")
    for r in rows:
        w.writerow(r)
    data = buf.getvalue().encode("utf-8")
    with open(path, "wb") as fh:
        fh.write((b"\xef\xbb\xbf" if bom else b"") + data)


def write_corrupt(path, kind, size, seed):
    """A file whose header looks right but whose body is unrecoverable noise."""
    prefixes = {
        "zip": b"PK\x03\x04\x14\x00\x06\x00\x08\x00\x00\x00!\x00",
        "pdf": b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n",
        "jpg": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00H\x00H\x00\x00",
    }
    rnd = random.Random(seed)
    with open(path, "wb") as fh:
        fh.write(prefixes[kind] + rnd.randbytes(size))


# ---------------------------------------------------------------------------
# Image helpers (all text drawn into pixels, no text layer)
# ---------------------------------------------------------------------------

_FONTS = {}


def F(size):
    if size not in _FONTS:
        _FONTS[size] = ImageFont.truetype(FONT_PATH, size)
    return _FONTS[size]


def wrap_px(text, font, width):
    out = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split():
            trial = (cur + " " + w).strip()
            if font.getlength(trial) <= width:
                cur = trial
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def squiggle(draw, x, y, w, rnd, fill, width=3):
    pts = []
    for i in range(0, w, 7):
        pts.append((x + i, y + rnd.randint(-14, 14)))
    draw.line(pts, fill=fill, width=width, joint="curve")


def scan_page(items, seed, angle=0.5):
    """Render a paper form or letter as a grey 150 dpi 'scan'."""
    W, H = 1275, 1650
    img = Image.new("L", (W, H), 252)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    x0, y = 110, 110
    for it in items:
        k = it[0]
        if k == "title":
            d.text((x0, y), it[1], font=F(44), fill=15)
            y += 72
        elif k == "sub":
            d.text((x0, y), it[1], font=F(27), fill=55)
            y += 48
        elif k == "rule":
            d.line((x0, y, W - x0, y), fill=60, width=3)
            y += 28
        elif k == "text":
            for line in wrap_px(it[1], F(29), W - 2 * x0):
                d.text((x0, y), line, font=F(29), fill=25)
                y += 42
            y += 14
        elif k == "field":
            label, value = it[1], it[2]
            d.text((x0, y), label, font=F(28), fill=45)
            lx = x0 + int(d.textlength(label, font=F(28))) + 18
            d.line((lx, y + 38, W - x0, y + 38), fill=130, width=2)
            d.text((lx + 12, y - 4), value, font=F(34), fill=10)
            y += 64
        elif k == "check":
            label, ticked = it[1], it[2]
            d.rectangle((x0, y + 4, x0 + 30, y + 34), outline=40, width=3)
            if ticked:
                d.line((x0 + 4, y + 8, x0 + 26, y + 30), fill=10, width=4)
                d.line((x0 + 26, y + 8, x0 + 4, y + 30), fill=10, width=4)
            d.text((x0 + 48, y + 2), label, font=F(28), fill=35)
            y += 50
        elif k == "sig":
            d.text((x0, y), it[1], font=F(28), fill=45)
            squiggle(d, x0 + 170, y + 20, 330, rnd, 20)
            if len(it) > 2:
                d.text((x0 + 620, y), it[2], font=F(28), fill=45)
                d.text((x0 + 720, y - 4), it[3], font=F(34), fill=10)
            y += 80
        elif k == "space":
            y += it[1]
    px = img.load()
    for _ in range(2600):
        px[rnd.randrange(W), rnd.randrange(H)] = rnd.randrange(70, 190)
    img = img.rotate(angle, resample=Image.BICUBIC, fillcolor=246)
    return img.filter(ImageFilter.GaussianBlur(0.6))


def write_scan_pdf(path, pages, title):
    """Image-only PDF, like a document scanner produces (no text layer)."""
    c = rl_canvas.Canvas(path, pagesize=letter, invariant=1)
    c.setTitle(title)
    c.setAuthor("")
    c.setSubject("")
    c.setCreator("Brother ADS-1700W")
    for img in pages:
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=80)
        buf.seek(0)
        c.drawImage(ImageReader(buf), 0, 0, width=612, height=792)
        c.showPage()
    c.save()


def photo_noise(img, rnd, n=9000, amp=16, blur=1.0):
    W, H = img.size
    px = img.load()
    for _ in range(n):
        x, y = rnd.randrange(W), rnd.randrange(H)
        r, g, b = px[x, y]
        k = rnd.randint(-amp, amp)
        px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)))
    return img.filter(ImageFilter.GaussianBlur(blur))


def save_jpeg(img, path, when, description=None, artist=None, model="iPad (9th generation)"):
    ex = Image.Exif()
    ex[0x010F] = "Apple"
    ex[0x0110] = model
    ex[0x0132] = when.strftime("%Y:%m:%d %H:%M:%S")
    if description:
        ex[0x010E] = description
    if artist:
        ex[0x013B] = artist
    img.save(path, "JPEG", quality=85, exif=ex.tobytes())


def clinical_photo(kind, seed):
    """A posture-grid range-of-motion photo. No text anywhere in the pixels."""
    rnd = random.Random(seed)
    W, H = 1024, 1365
    img = Image.new("RGB", (W, H), (214, 222, 230))
    d = ImageDraw.Draw(img)
    for x in range(0, W, 48):
        d.line((x, 0, x, H), fill=(182, 193, 205), width=2)
    for y in range(0, H, 48):
        d.line((0, y, W, y), fill=(182, 193, 205), width=2)
    d.rectangle((0, 1180, W, H), fill=(150, 140, 128))
    skin, white = (224, 186, 160), (244, 244, 244)
    if kind == "shoulder":
        cx = 512
        d.ellipse((cx - 70, 170, cx + 70, 320), fill=skin)
        d.rectangle((cx - 30, 310, cx + 30, 350), fill=skin)
        d.polygon([(cx - 140, 345), (cx + 140, 345), (cx + 120, 720), (cx - 120, 720)], fill=(70, 110, 150))
        d.rectangle((cx - 120, 720, cx + 120, 840), fill=(50, 50, 60))
        d.rectangle((cx - 110, 840, cx - 30, 1180), fill=skin)
        d.rectangle((cx + 30, 840, cx + 110, 1180), fill=skin)
        d.line((cx + 140, 370, cx + 175, 700), fill=skin, width=56)
        d.line((cx - 140, 370, cx - 190, 60), fill=skin, width=56)
        d.line((cx - 140, 370, cx - 140, 700), fill=white, width=8)
        d.line((cx - 140, 370, cx - 185, 90), fill=white, width=8)
        d.ellipse((cx - 170, 340, cx - 110, 400), outline=white, width=6)
    else:
        d.rectangle((150, 760, 900, 820), fill=(90, 120, 110))
        d.rectangle((180, 820, 220, 1180), fill=(60, 60, 60))
        d.rectangle((830, 820, 870, 1180), fill=(60, 60, 60))
        d.ellipse((260, 260, 400, 410), fill=skin)
        d.polygon([(250, 420), (410, 420), (420, 760), (240, 760)], fill=(150, 80, 90))
        d.rectangle((300, 680, 640, 760), fill=(50, 50, 60))
        d.line((640, 720, 1000, 700), fill=skin, width=70)
        d.line((640, 720, 400, 720), fill=white, width=8)
        d.line((640, 720, 960, 702), fill=white, width=8)
        d.ellipse((610, 690, 670, 750), outline=white, width=6)
    return photo_noise(img, rnd)


def signin_sheet_photo(seed):
    """Phone photo of a paper sign-in sheet lying on a desk."""
    rnd = random.Random(seed)
    PW, PH = 1100, 1420
    paper = Image.new("RGB", (PW, PH), (247, 245, 238))
    d = ImageDraw.Draw(paper)
    ink, pen = (35, 35, 35), (25, 45, 130)
    d.text((70, 60), "Kestrel Bay Physiotherapy", font=F(34), fill=ink)
    d.text((70, 112), "Shoulder Strength Group - sign-in sheet", font=F(40), fill=ink)
    d.text((70, 178), "Tuesday 14 April 2026   10:00 - 11:00   Lead: Tom Reyes, PT", font=F(27), fill=ink)
    cols = [70, 560, 760, 1030]
    top, rowh = 250, 92
    for i in range(12):
        d.line((cols[0], top + i * rowh, cols[-1], top + i * rowh), fill=(90, 90, 90), width=2)
    for x in cols:
        d.line((x, top, x, top + 11 * rowh), fill=(90, 90, 90), width=2)
    for text, x in zip(["Name (please print)", "Time in", "Signature"], cols):
        d.text((x + 14, top + 28), text, font=F(30), fill=ink)
    people = [("Grace Obi", "9:52"), ("Peter Vance", "9:58"), ("Sarah Mitchell", "10:01"), ("Ana Ruiz", "10:05")]
    for i, (name, t) in enumerate(people):
        ry = top + (i + 1) * rowh
        d.text((cols[0] + 16 + rnd.randint(-4, 6), ry + 22 + rnd.randint(-4, 4)), name, font=F(40), fill=pen)
        d.text((cols[1] + 24, ry + 24), t, font=F(38), fill=pen)
        squiggle(d, cols[2] + 20, ry + 46, 220, rnd, pen, width=4)
    sheet = paper.convert("RGBA").rotate(-2.5, resample=Image.BICUBIC, expand=True)
    bg = Image.new("RGB", (1500, 1720), (122, 86, 54))
    bd = ImageDraw.Draw(bg)
    for y in range(0, 1720, 9):
        shade = rnd.randint(-14, 14)
        bd.line((0, y, 1500, y + rnd.randint(-6, 6)), fill=(122 + shade, 86 + shade, 54 + shade), width=4)
    bg.paste(sheet, (180, 120), sheet)
    return photo_noise(bg, rnd, n=12000, amp=12, blur=0.9)


def portal_screenshot():
    """Screenshot of an insurer's provider portal in a browser window."""
    W, H = 1440, 900
    img = Image.new("RGB", (W, H), (245, 247, 250))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 44), fill=(222, 225, 230))
    d.rounded_rectangle((180, 8, 1180, 36), radius=12, fill=(255, 255, 255))
    d.text((200, 12), "https://provider.cascadia-health.example.com/prior-auth/PA-2026-55821", font=F(17), fill=(60, 60, 60))
    d.rectangle((0, 44, W, 108), fill=(18, 52, 96))
    d.text((32, 62), "Cascadia Health Plan  |  Provider Portal", font=F(26), fill=(255, 255, 255))
    d.text((1120, 66), "Signed in: jwhitfield", font=F(18), fill=(200, 215, 235))
    d.rectangle((0, 108, 250, H - 40), fill=(232, 236, 242))
    for i, item in enumerate(["Dashboard", "Eligibility", "Prior authorizations", "Claims", "Remittance", "Messages"]):
        d.text((28, 140 + i * 46), item, font=F(20), fill=(30, 50, 80) if i == 2 else (80, 90, 105))
    d.rectangle((290, 140, 1400, 820), fill=(255, 255, 255), outline=(205, 210, 218), width=2)
    d.text((320, 165), "Prior Authorization", font=F(30), fill=(20, 30, 45))
    d.rounded_rectangle((640, 166, 790, 200), radius=8, fill=(214, 240, 222))
    d.text((660, 171), "APPROVED", font=F(20), fill=(20, 110, 50))
    fields = [
        ("Authorization no.", "PA-2026-55821"),
        ("Member name", "SARAH L MITCHELL"),
        ("Member ID", "CHP-20931-01"),
        ("Date of birth", "09/22/1983"),
        ("Plan", "Cascadia Silver PPO"),
        ("Requesting provider", "Kestrel Bay Physiotherapy"),
        ("Service", "Physical therapy evaluation and treatment"),
        ("Diagnosis", "M75.81  Other shoulder lesions, right shoulder"),
        ("Visits approved", "12"),
        ("Valid", "03/05/2026 to 06/30/2026"),
        ("Decision date", "03/05/2026 10:14"),
    ]
    for i, (label, value) in enumerate(fields):
        y = 235 + i * 50
        d.text((330, y), label, font=F(21), fill=(110, 118, 130))
        d.text((640, y), value, font=F(22), fill=(25, 30, 40))
        d.line((320, y + 38, 1370, y + 38), fill=(236, 238, 242), width=1)
    d.rectangle((0, H - 40, W, H), fill=(30, 32, 38))
    d.text((W - 190, H - 31), "10:15 AM  3/5/2026", font=F(17), fill=(230, 230, 230))
    return img


def reception_photo(seed):
    rnd = random.Random(seed)
    W, H = 1600, 1200
    img = Image.new("RGB", (W, H), (226, 220, 208))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 860, W, H), fill=(160, 132, 100))
    d.rectangle((420, 560, 1180, 900), fill=(240, 240, 236))
    d.rectangle((420, 540, 1180, 570), fill=(120, 90, 60))
    d.rectangle((700, 420, 900, 545), fill=(40, 40, 46))
    for x in (140, 1300):
        d.rectangle((x, 700, x + 160, 760), fill=(70, 110, 150))
        d.rectangle((x, 760, x + 20, 900), fill=(60, 60, 60))
        d.rectangle((x + 140, 760, x + 160, 900), fill=(60, 60, 60))
    d.ellipse((1380, 380, 1560, 620), fill=(70, 130, 80))
    d.rectangle((1440, 600, 1500, 860), fill=(150, 100, 70))
    d.rectangle((560, 120, 1040, 360), fill=(250, 250, 250), outline=(180, 180, 180), width=4)
    d.polygon([(640, 320), (800, 160), (960, 320)], fill=(90, 150, 190))
    return photo_noise(img, rnd, n=15000, amp=14, blur=1.4)


def letterhead_docx():
    return [("b", PRACTICE_NAME), ("small", PRACTICE_ADDR + "  |  " + PRACTICE_CONTACT)]


# ---------------------------------------------------------------------------
# TARGET files: about the requester, Sarah Louise Mitchell, KBP-10427
# ---------------------------------------------------------------------------

def build_targets(C):
    # 1. Her own intake form, inside her client folder.
    rel = "Clients/Mitchell_Sarah_KBP-10427/intake_form.docx"
    when = datetime(2026, 3, 3, 9, 20)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Client intake form"),
        ("table", [
            ["Client ID", "KBP-10427"],
            ["Full name", "Sarah Louise Mitchell"],
            ["Previous name(s)", "Sarah Pryce (seen here in 2023 under this name)"],
            ["Date of birth", "09/22/1983"],
            ["Address", "17 Alder Crescent, Linden Cove, OR 97990"],
            ["Mobile", "(503) 555-0147"],
            ["Email", "sarah.mitchell83@example.com"],
            ["Occupation", "Graphic designer, Harlow Design Studio"],
            ["Family doctor", "Dr. Alan Pierce, Linden Cove Medical Group"],
            ["Emergency contact", "Emma Pryce (sister), (503) 555-0172"],
            ["Insurance", "Cascadia Health Plan, member ID CHP-20931-01, policy holder: self"],
            ["How did you hear about us?", "Returning client"],
        ]),
        ("h2", "Reason for visit"),
        ("p", "Right shoulder pain since a fall from my bicycle on 02/14/2026. Hard to lift my arm above "
              "shoulder height and to sleep on my right side."),
        ("h2", "Medical history"),
        ("p", "Mild asthma, uses a salbutamol inhaler as needed. Left ankle sprain 2023 (treated at Kestrel Bay). "
              "No surgeries. No known drug allergies."),
        ("h2", "Consent"),
        ("p", "I consent to assessment and treatment, and to Kestrel Bay Physiotherapy keeping my records as "
              "described in the privacy notice."),
        ("p", "Signed: Sarah Mitchell          Date: 03/03/2026"),
    ], {"author": "Jo Whitfield", "title": "Client intake form", "created": when})
    C.add(rel, "target", ["text", "filename"], True, False, "clinical",
          "Her own intake form with DOB, address, phone, email, client ID and her previous name Sarah Pryce.", when)

    # 2. Initial assessment (text PDF exported from the clinic system).
    rel = "Clients/Mitchell_Sarah_KBP-10427/initial_assessment_2026-03-03.pdf"
    when = datetime(2026, 3, 3, 11, 42)
    pdf = PdfDoc(C.fp(rel), title="Initial assessment", author="Tom Reyes")
    pdf.h1("Initial Assessment - Musculoskeletal")
    pdf.p("Client: Mitchell, Sarah L.      Client ID: KBP-10427      DOB: 22 Sep 1983", font="Helvetica-Bold")
    pdf.p("Date of assessment: 03/03/2026      Clinician: Tom Reyes, PT, DPT\n"
          "Referral: self-referral (direct access).  Family doctor: Dr. Alan Pierce")
    pdf.h2("Subjective")
    pdf.p("42-year-old graphic designer, right-hand dominant. Fell from her bicycle on 02/14/2026 onto an "
          "outstretched right arm. Seen at urgent care the same day; x-ray showed no fracture or dislocation. "
          "Pain over the lateral right shoulder, 6/10 at worst and 2/10 at rest. Aggravated by overhead "
          "reaching, putting on a coat and lying on the right side. Wakes two to three times a night. "
          "Goals: return to her cycling commute and to full days at the computer without pain.")
    pdf.p("Past history: left ankle sprain 2023, fully recovered. Mild asthma. No red flags reported "
          "(no weight loss, no night sweats, no neurological symptoms).")
    pdf.h2("Objective")
    pdf.p("Posture: mildly protracted right scapula. AROM right shoulder: flexion 120 deg, abduction 95 deg "
          "with a painful arc from 70 to 110 deg, external rotation 45 deg, internal rotation to L3. Left "
          "shoulder full range.")
    pdf.p("Strength: right external rotation 4-/5, abduction 4/5, internal rotation 5/5. Special tests: "
          "Hawkins-Kennedy positive, empty can positive for pain, drop arm negative, external rotation lag "
          "sign negative. Cervical screen clear.")
    pdf.h2("Assessment")
    pdf.p("Post-traumatic right supraspinatus tendinopathy with secondary scapular dyskinesis. No clinical "
          "signs of a full-thickness rotator cuff tear.")
    pdf.h2("Plan")
    pdf.p("Twice weekly for six weeks, then review. Manual therapy, isometric loading progressing to isotonic "
          "rotator cuff and scapular strengthening. Home exercise programme issued. Invite to the Tuesday "
          "shoulder strength group from week six. Re-assess at four weeks; refer back to the family doctor "
          "for ultrasound if there is no improvement.")
    pdf.space(10)
    pdf.p("Electronically signed: Tom Reyes, PT, DPT   03/03/2026 11:42", font="Helvetica-Oblique")
    pdf.save()
    C.add(rel, "target", ["text", "filename"], True, False, "clinical",
          "Her initial physiotherapy assessment with name in reversed order, DOB and client ID.", when)

    # 3. Treatment notes: identity only in the Word page header.
    rel = "Clients/Mitchell_Sarah_KBP-10427/treatment_notes.docx"
    when = datetime(2026, 6, 19, 11, 5)
    sessions = [
        ["Date", "Clinician", "Note"],
        ["03/03/2026", "TR", "Initial assessment, see separate report. HEP phase 1: pendulums, isometric ER and abduction."],
        ["03/06/2026", "TR", "Pain 5/10. Soft tissue to upper trapezius and posterior cuff. Isometrics 5 x 30 s. Tolerated well."],
        ["03/10/2026", "TR", "Flexion 130 deg. Added scapular setting and wall slides."],
        ["03/13/2026", "TR", "Sleeping better, wakes once a night. Started banded ER (yellow)."],
        ["03/17/2026", "TR", "Painful arc now 80 to 100 deg. Progressed to red band."],
        ["03/24/2026", "TR", "Phase 2 HEP issued (week 3 sheet). Abduction 140 deg."],
        ["03/31/2026", "TR", "Back on the bike for short rides. ER strength 4/5."],
        ["04/07/2026", "TR", "Four-week review: flexion 165, abduction 160, ER 70. Hawkins mildly positive. Plan: join shoulder group 14 April."],
        ["04/14/2026", "TR", "First shoulder strength group session, then review. Note: the email reminder for today went to the wrong address, see incident PI-2026-003."],
        ["04/21/2026", "TR", "Wants to return to swimming. Breaststroke only for two weeks."],
        ["04/30/2026", "TR", "Rebooked from 04/28 (client cancelled, child unwell). Progressed to green band."],
        ["05/08/2026", "TR", "Good week. Full flexion. Added prone Y and T raises."],
        ["05/22/2026", "TR", "Flare after gardening at the weekend (phoned 05/21). Back to isometrics, ice. Pain 4/10."],
        ["05/29/2026", "TR", "Settled. Resumed green band. Full pain-free range."],
        ["06/19/2026", "TR", "Discharged. Strength 5/5, return to all activities. Discharge summary to Dr. Pierce."],
    ]
    write_docx(C.fp(rel), [
        ("h1", "Treatment notes - right shoulder"),
        ("table", sessions, "header"),
    ], {"author": "Tom Reyes", "title": "Treatment notes", "created": datetime(2026, 3, 3, 12, 0),
        "modified": when, "revision": 15},
        header="CLIENT: Sarah Mitchell   |   ID: KBP-10427   |   DOB: 09/22/1983   |   Clinician: T. Reyes")
    C.add(rel, "target", ["text", "filename"], True, False, "clinical",
          "Session notes; her name, DOB and ID appear only in the Word page header, not the body.", when)

    # 4. Progress letter to her family doctor.
    rel = "Clients/Mitchell_Sarah_KBP-10427/letter_to_GP_2026-04-20.docx"
    when = datetime(2026, 4, 20, 15, 30)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("p", "April 20, 2026"),
        ("p", "Dr. Alan Pierce\nLinden Cove Medical Group\n55 Birch Avenue\nLinden Cove, OR 97990"),
        ("p", "Dear Dr. Pierce,"),
        ("b", "Re: Ms Sarah Mitchell, DOB 09/22/1983, 17 Alder Crescent, Linden Cove"),
        ("p", "Thank you for your earlier note about Ms Mitchell. She has attended eleven sessions since 3 March for "
              "a post-traumatic right supraspinatus tendinopathy following a fall from her bicycle."),
        ("p", "At her four-week review her shoulder flexion had improved from 120 to 165 degrees and abduction from "
              "95 to 160 degrees. External rotation strength is now 4/5. Night pain has largely resolved. She has "
              "joined our shoulder strength group and is cycling short distances again."),
        ("p", "I do not think an ultrasound is needed at this stage. I expect to discharge her by late June."),
        ("p", "Yours sincerely,"),
        ("p", "Tom Reyes, PT, DPT\nKestrel Bay Physiotherapy"),
    ], {"author": "Tom Reyes", "title": "Progress letter", "created": when})
    C.add(rel, "target", ["text", "filename"], True, False, "correspondence",
          "Progress letter about her to her family doctor, with DOB and address.", when)

    # 5. Home exercise programme: her name only in document properties.
    rel = "Exercise_Programmes/HEP_shoulder_week3.docx"
    when = datetime(2026, 3, 24, 10, 40)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Home Exercise Programme - Week 3"),
        ("p", "Shoulder rehabilitation, phase 2. Do these exercises once a day unless told otherwise. Stop and call "
              "us if pain goes above 5/10 or lasts more than an hour after exercise."),
        ("table", [
            ["Exercise", "Sets x reps", "Notes"],
            ["Banded external rotation (red)", "3 x 12", "Elbow tucked in against a rolled towel"],
            ["Banded internal rotation (red)", "3 x 12", "Slow return"],
            ["Scapular retraction with band", "3 x 15", "Squeeze for 2 seconds"],
            ["Wall slides", "2 x 10", "Stop at a pain-free height"],
            ["Side-lying external rotation, 1 lb", "2 x 12", "Lie on the unaffected side"],
            ["Sleeper stretch", "3 x 30 s", "Gentle, no sharp pain"],
        ], "header"),
        ("p", "Clinician: Tom Reyes, PT. Next review in two weeks."),
    ], {"author": "Tom Reyes", "title": "HEP - Sarah Mitchell - week 3",
        "subject": "KBP-10427 right shoulder phase 2", "keywords": "Mitchell; shoulder; HEP",
        "comments": "Printed and handed to client 03/24/2026", "created": when})
    C.add(rel, "target", ["metadata"], True, False, "clinical",
          "Generic-looking exercise sheet; her name and client ID are only in the document properties.", when)

    # 6. Scanned paper health questionnaire (image-only PDF, generic scanner filename).
    rel = "Scans/scan_20260303_0915.pdf"
    when = datetime(2026, 3, 3, 9, 15)
    p1 = scan_page([
        ("title", "KESTREL BAY PHYSIOTHERAPY"),
        ("sub", "New client health questionnaire  -  please print clearly"),
        ("rule",),
        ("field", "Full name:", "SARAH L. MITCHELL"),
        ("field", "Date of birth:", "09/22/1983"),
        ("field", "Phone:", "503 555 0147"),
        ("field", "Address:", "17 ALDER CRES, LINDEN COVE OR 97990"),
        ("field", "Email:", "sarah.mitchell83@example.com"),
        ("field", "Family doctor:", "DR PIERCE"),
        ("space", 10),
        ("field", "Main problem:", "R SHOULDER - FELL OFF BIKE 14 FEB"),
        ("field", "Pain now (0-10):", "6"),
        ("field", "Worst pain (0-10):", "8 AT NIGHT"),
        ("space", 10),
        ("sub", "Do you have, or have you had:"),
        ("check", "Heart problems", False),
        ("check", "High blood pressure", False),
        ("check", "Asthma or breathing problems", True),
        ("check", "Diabetes", False),
        ("check", "Surgery in the last 12 months", False),
        ("check", "Pregnant or possibly pregnant", False),
        ("space", 24),
        ("sig", "Signature:", "Date:", "3/3/26"),
    ], seed=101, angle=0.6)
    p2 = scan_page([
        ("title", "HEALTH QUESTIONNAIRE  (page 2)"),
        ("sub", "Red flag screening - completed with clinician"),
        ("rule",),
        ("check", "Unexplained weight loss", False),
        ("check", "Night pain not eased by changing position", False),
        ("check", "Numbness or pins and needles in the arm", False),
        ("check", "Recent fever or feeling generally unwell", False),
        ("check", "History of cancer", False),
        ("space", 30),
        ("field", "Clinician:", "T. REYES"),
        ("field", "Client initials:", "S.M."),
    ], seed=102, angle=-0.4)
    write_scan_pdf(C.fp(rel), [p1, p2], "scan_20260303_0915")
    C.add(rel, "target", ["ocr"], True, False, "clinical",
          "Scanned paper questionnaire; her name, DOB, phone and address exist only as pixels.", when)

    # 7. Range-of-motion photo; identity only in the EXIF caption.
    rel = "Photos/IMG_4471.jpg"
    when = datetime(2026, 3, 3, 10, 5)
    save_jpeg(clinical_photo("shoulder", 201), C.fp(rel), when,
              description="Sarah Mitchell KBP-10427 - R shoulder flexion, front view - 03/03/2026",
              artist="Tom Reyes")
    C.add(rel, "target", ["caption"], True, False, "clinical",
          "Clinical photo with no visible text; her name and ID are only in the EXIF image description.", when)

    # 8. Screenshot of the insurer portal pre-authorisation.
    rel = "Screenshots/Screenshot 2026-03-05 101522.png"
    when = datetime(2026, 3, 5, 10, 15, 22)
    portal_screenshot().save(C.fp(rel), "PNG")
    C.add(rel, "target", ["ocr"], True, False, "billing",
          "Screenshot of her insurance pre-authorisation; name (upper case) and DOB only in pixels.", when)

    # 9. Photo of the paper sign-in sheet of the shoulder group.
    rel = "Photos/IMG_20260414_1012.jpg"
    when = datetime(2026, 4, 14, 10, 12)
    save_jpeg(signin_sheet_photo(301), C.fp(rel), when, model="iPhone 13")
    C.add(rel, "target", ["ocr"], False, True, "other",
          "Phone photo of a class sign-in sheet listing her and three other clients; shoulder class context marks her.", when)

    # 10. Her own invoice.
    rel = "Billing/invoice_INV-2026-0318.pdf"
    when = datetime(2026, 3, 18, 16, 0)
    pdf = PdfDoc(C.fp(rel), title="Invoice INV-2026-0318", author="Kestrel Bay Physiotherapy")
    pdf.h1("INVOICE  INV-2026-0318")
    pdf.p("Invoice date: 03/18/2026        Payment due: 04/17/2026")
    pdf.p("Bill to:\nSarah Mitchell\n17 Alder Crescent\nLinden Cove, OR 97990", font="Helvetica-Bold")
    pdf.p("Client ID: KBP-10427        Insurance: Cascadia Health Plan, member CHP-20931-01")
    xs = [72, 150, 205, 470]
    pdf.row(["Date", "Code", "Description", "Amount"], xs, font="Helvetica-Bold")
    pdf.rule()
    for r in [
        ["03/03/2026", "97161", "PT evaluation, low complexity", "165.00"],
        ["03/03/2026", "97140", "Manual therapy, 15 min", "55.00"],
        ["03/06/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
        ["03/06/2026", "97140", "Manual therapy, 15 min", "55.00"],
        ["03/10/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
        ["03/13/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
        ["03/17/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
    ]:
        pdf.row(r, xs)
    pdf.rule()
    pdf.row(["", "", "Total charges", "715.00"], xs, font="Helvetica-Bold")
    pdf.row(["", "", "Insurance paid", "-572.00"], xs)
    pdf.row(["", "", "Balance due from client", "143.00"], xs, font="Helvetica-Bold")
    pdf.space(12)
    pdf.p("Thank you. Pay online, by card at reception, or by check payable to Kestrel Bay Physiotherapy.")
    pdf.save()
    C.add(rel, "target", ["text"], True, False, "billing",
          "Her invoice with address and client ID; the filename has no name.", when)

    # 11. Practice-wide billing ledger (both Sarah Mitchells appear).
    rel = "Billing/billing_ledger_2026.csv"
    when = datetime(2026, 9, 30, 17, 30)
    write_csv(C.fp(rel), [
        ["date", "invoice", "client_id", "client_name", "payer", "description", "billed", "insurer_paid", "client_paid", "balance"],
        ["2026-01-30", "INV-2026-0104", "KBP-10302", "Liu, Hannah", "Self-pay", "Neck x3", "330.00", "0.00", "330.00", "0.00"],
        ["2026-02-27", "INV-2026-0211", "KBP-10388", "Mitchell, Sarah J.", "Evergreen Medicare Advantage", "Knee prehab x3", "385.00", "308.00", "77.00", "0.00"],
        ["2026-02-27", "INV-2026-0212", "KBP-10290", "Santos, Miguel", "Cascadia Health Plan", "ACL rehab x4", "440.00", "352.00", "88.00", "0.00"],
        ["2026-03-18", "INV-2026-0318", "KBP-10427", "Mitchell, Sarah L.", "Cascadia Health Plan", "Shoulder 03/03-03/17", "715.00", "572.00", "0.00", "143.00"],
        ["2026-03-31", "INV-2026-0341", "KBP-10388", "Mitchell, Sarah J.", "Evergreen Medicare Advantage", "Knee prehab x4", "440.00", "352.00", "88.00", "0.00"],
        ["2026-04-02", "INV-2026-0402", "KBP-10355", "Patel, Raj", "Northline Insurance", "Hamstring x4", "440.00", "352.00", "88.00", "0.00"],
        ["2026-04-30", "INV-2026-0433", "KBP-10427", "Mitchell, Sarah L.", "Cascadia Health Plan", "Shoulder 03/20-04/30", "880.00", "704.00", "176.00", "0.00"],
        ["2026-04-30", "INV-2026-0434", "KBP-10311", "Obi, Grace", "Self-pay", "Shoulder group x4", "160.00", "0.00", "160.00", "0.00"],
        ["2026-04-30", "INV-2026-0435", "KBP-10344", "Vance, Peter", "Evergreen Medicare Advantage", "Shoulder group x4 + review", "270.00", "216.00", "54.00", "0.00"],
        ["2026-04-30", "INV-2026-0436", "KBP-10398", "Ruiz, Ana", "Cascadia Health Plan", "Shoulder group x4", "160.00", "128.00", "32.00", "0.00"],
        ["2026-05-29", "INV-2026-0467", "KBP-10431", "Mitchell, Daniel", "Self-pay", "Low back x3", "330.00", "0.00", "330.00", "0.00"],
        ["2026-05-29", "INV-2026-0470", "KBP-10427", "Mitchell, Sarah L.", "Cascadia Health Plan", "Shoulder May x3", "385.00", "294.40", "90.60", "0.00"],
        ["2026-05-29", "INV-2026-0471", "KBP-10388", "Mitchell, Sarah J.", "Evergreen Medicare Advantage", "Knee prehab x3", "330.00", "264.00", "66.00", "0.00"],
        ["2026-06-12", "INV-2026-0544", "KBP-10432", "Mitchell, Leo", "Cascadia Health Plan (guarantor S. Mitchell)", "Knee x3", "385.00", "308.00", "77.00", "0.00"],
        ["2026-06-19", "INV-2026-0560", "KBP-10427", "Mitchell, Sarah L.", "Cascadia Health Plan", "Discharge session", "110.00", "88.00", "22.00", "0.00"],
        ["2026-06-30", "INV-2026-0581", "KBP-10355", "Patel, Raj", "Northline Insurance", "Hamstring May x4 - DENIED", "440.00", "0.00", "0.00", "440.00"],
        ["2026-07-31", "INV-2026-0620", "KBP-10388", "Mitchell, Sarah J.", "Evergreen Medicare Advantage", "Post-op knee x6", "660.00", "528.00", "132.00", "0.00"],
        ["2026-08-31", "INV-2026-0702", "KBP-10460", "Mitchell-Hayes, Sarah", "Self-pay", "Heel x2", "275.00", "0.00", "275.00", "0.00"],
        ["2026-08-31", "INV-2026-0703", "KBP-10475", "Okoro, Mitchell", "Self-pay", "Clinical Pilates x4", "180.00", "0.00", "180.00", "0.00"],
        ["2026-09-30", "INV-2026-0788", "KBP-10419", "Fern, Lucia", "Cascadia Health Plan", "Hip x4", "440.00", "352.00", "88.00", "0.00"],
    ], bom=True)
    C.add(rel, "target", ["text"], True, True, "billing",
          "Ledger of all clients; her rows sit next to the other Sarah Mitchell and her husband and son.", when)

    # 12. Appointment book for Q2 (three sheets).
    rel = "Admin/appointments_2026_Q2.xlsx"
    when = datetime(2026, 6, 30, 17, 45)
    head = ["Date", "Time", "Clinician", "Client", "Client ID", "Appointment type", "Status"]
    T, P = "Tom Reyes", "Priya Natarajan"
    april = [head,
             [date(2026, 4, 7), "09:00", P, "Sarah Mitchell", "KBP-10388", "Knee prehab", "Attended"],
             [date(2026, 4, 7), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder 4-week review", "Attended"],
             [date(2026, 4, 7), "11:00", T, "Raj Patel", "KBP-10355", "Hamstring follow-up", "Attended"],
             [date(2026, 4, 9), "14:00", T, "Hannah Liu", "KBP-10302", "Neck follow-up", "Attended"],
             [date(2026, 4, 14), "10:00", T, "Grace Obi", "KBP-10311", "Shoulder strength group", "Attended"],
             [date(2026, 4, 14), "10:00", T, "Peter Vance", "KBP-10344", "Shoulder strength group", "Attended"],
             [date(2026, 4, 14), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder strength group + review", "Attended"],
             [date(2026, 4, 14), "10:00", T, "Ana Ruiz", "KBP-10398", "Shoulder strength group", "Attended"],
             [date(2026, 4, 16), "09:00", P, "Sarah Mitchell", "KBP-10388", "Knee prehab", "Attended"],
             [date(2026, 4, 21), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up", "Attended"],
             [date(2026, 4, 23), "15:00", P, "Miguel Santos", "KBP-10290", "ACL rehab", "Attended"],
             [date(2026, 4, 28), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up", "Cancelled - rebooked 04/30"],
             [date(2026, 4, 30), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up", "Attended"],
             [date(2026, 4, 30), "16:00", P, "Owen Brandt", "KBP-10412", "Tennis elbow", "Attended"]]
    may = [head,
           [date(2026, 5, 5), "11:00", T, "Grace Obi", "KBP-10311", "Shoulder strength group", "Attended"],
           [date(2026, 5, 6), "09:00", P, "Daniel Mitchell", "KBP-10431", "New - low back pain", "Attended"],
           [date(2026, 5, 8), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up", "Attended"],
           [date(2026, 5, 11), "16:00", T, "Leo Mitchell", "KBP-10432", "New - knee pain (under 18)", "Attended"],
           [date(2026, 5, 12), "11:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder strength group", "Attended"],
           [date(2026, 5, 12), "11:00", T, "Ana Ruiz", "KBP-10398", "Shoulder strength group", "Attended"],
           [date(2026, 5, 13), "09:00", P, "Daniel Mitchell", "KBP-10431", "Low back follow-up", "Attended"],
           [date(2026, 5, 14), "09:00", P, "Sarah Mitchell", "KBP-10388", "Knee prehab", "Attended"],
           [date(2026, 5, 20), "09:00", P, "Daniel Mitchell", "KBP-10431", "Low back follow-up", "Attended"],
           [date(2026, 5, 21), "09:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up", "Moved to 05/22"],
           [date(2026, 5, 22), "14:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up (flare)", "Attended"],
           [date(2026, 5, 26), "16:00", T, "Leo Mitchell", "KBP-10432", "Knee follow-up", "Attended"],
           [date(2026, 5, 28), "15:00", P, "Lucia Fern", "KBP-10419", "Hip", "Attended"],
           [date(2026, 5, 29), "10:00", T, "Sarah Mitchell", "KBP-10427", "Shoulder follow-up", "Attended"]]
    june = [head,
            [date(2026, 6, 2), "09:00", P, "Sarah Mitchell", "KBP-10388", "Final pre-op session", "Attended"],
            [date(2026, 6, 4), "11:00", T, "Raj Patel", "KBP-10355", "Hamstring follow-up", "Attended"],
            [date(2026, 6, 9), "16:00", T, "Leo Mitchell", "KBP-10432", "Knee follow-up", "Attended"],
            [date(2026, 6, 16), "15:00", P, "Lucia Fern", "KBP-10419", "Hip", "Attended"],
            [date(2026, 6, 19), "10:00", T, "Sarah Mitchell", "KBP-10427", "Discharge", "Attended"],
            [date(2026, 6, 30), "09:00", P, "Sarah Mitchell", "KBP-10388", "Post-op knee review (day 8)", "Attended"],
            [date(2026, 6, 30), "16:00", P, "Owen Brandt", "KBP-10412", "Tennis elbow", "DNA"]]
    write_xlsx(C.fp(rel), [("April", april), ("May", may), ("June", june)],
               {"author": "Jo Whitfield", "title": "Appointments Q2 2026", "created": datetime(2026, 4, 1, 8, 30),
                "modified": when})
    C.add(rel, "target", ["text"], True, True, "other",
          "Appointment book across three sheets; two clients named Sarah Mitchell told apart only by client ID.", when)

    # 13. SMS reminder log export (UTF-16 with BOM, as the Windows SMS tool exports it).
    rel = "Admin/sms_reminder_log_2026-04.txt"
    when = datetime(2026, 4, 30, 18, 0)
    lines = ["SMS GATEWAY EXPORT  account: KestrelBayPhysio  period: 2026-04-01 to 2026-04-30",
             "timestamp           | direction | number          | contact         | message | status"]
    log = [
        ("2026-04-06 17:00:02", "OUT", "+1 503-555-0188", "Sarah Mitchell", "Hi Sarah, reminder: Tue 7 Apr 09:00 with Priya at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-06 17:00:04", "OUT", "+1 503-555-0147", "Sarah Mitchell", "Hi Sarah, reminder: Tue 7 Apr 10:00 with Tom at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-06 17:00:06", "OUT", "+1 503-555-0115", "Raj Patel", "Hi Raj, reminder: Tue 7 Apr 11:00 with Tom at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-06 18:12:40", "IN", "+1 503-555-0147", "Sarah Mitchell", "C", "RECEIVED"),
        ("2026-04-06 19:03:11", "IN", "+1 503-555-0188", "Sarah Mitchell", "C see you then", "RECEIVED"),
        ("2026-04-08 17:00:03", "OUT", "+1 503-555-0114", "Hannah Liu", "Hi Hannah, reminder: Thu 9 Apr 14:00 with Tom at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-13 17:00:02", "OUT", "+1 503-555-0111", "Grace Obi", "Hi Grace, reminder: Shoulder group Tue 14 Apr 10:00. Reply C to confirm.", "DELIVERED"),
        ("2026-04-13 17:00:03", "OUT", "+1 503-555-0112", "Peter Vance", "Hi Peter, reminder: Shoulder group Tue 14 Apr 10:00. Reply C to confirm.", "DELIVERED"),
        ("2026-04-13 17:00:05", "OUT", "+1 503-555-0147", "Sarah Mitchell", "Hi Sarah, reminder: Shoulder group Tue 14 Apr 10:00, then review with Tom. Reply C to confirm.", "DELIVERED"),
        ("2026-04-13 17:00:06", "OUT", "+1 503-555-0113", "Ana Ruiz", "Hi Ana, reminder: Shoulder group Tue 14 Apr 10:00. Reply C to confirm.", "DELIVERED"),
        ("2026-04-13 17:20:51", "IN", "+1 503-555-0112", "Peter Vance", "C thanks", "RECEIVED"),
        ("2026-04-15 17:00:02", "OUT", "+1 503-555-0188", "Sarah Mitchell", "Hi Sarah, reminder: Thu 16 Apr 09:00 with Priya at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-20 17:00:03", "OUT", "+1 503-555-0147", "Sarah Mitchell", "Hi Sarah, reminder: Tue 21 Apr 10:00 with Tom at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-22 17:00:02", "OUT", "+1 503-555-0118", "Miguel Santos", "Hi Miguel, reminder: Thu 23 Apr 15:00 with Priya at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-27 17:00:04", "OUT", "+1 503-555-0147", "Sarah Mitchell", "Hi Sarah, reminder: Tue 28 Apr 10:00 with Tom at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-28 08:01:15", "OUT", "+1 503-555-0147", "Sarah Mitchell", "Your Tue 28 Apr appointment is cancelled. New time: Thu 30 Apr 10:00 with Tom.", "DELIVERED"),
        ("2026-04-29 17:00:03", "OUT", "+1 503-555-0147", "Sarah Mitchell", "Hi Sarah, reminder: Thu 30 Apr 10:00 with Tom at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-29 17:00:05", "OUT", "+1 503-555-0116", "Owen Brandt", "Hi Owen, reminder: Thu 30 Apr 16:00 with Priya at Kestrel Bay Physio. Reply C to confirm.", "DELIVERED"),
        ("2026-04-29 17:31:09", "IN", "+1 503-555-0147", "Sarah Mitchell", "C", "RECEIVED"),
    ]
    for row in log:
        lines.append(" | ".join(row))
    write_text(C.fp(rel), "\n".join(lines) + "\n", encoding="utf-16-bom")
    C.add(rel, "target", ["text"], True, True, "correspondence",
          "UTF-16 SMS log; both Sarah Mitchells appear under the same contact name, only the number differs.", when)

    # 14. The misdirected reminder: content about her, sent to the other Sarah Mitchell.
    rel = "Email/2026-04-13_appointment_reminder.eml"
    when = datetime(2026, 4, 13, 16, 2, 11)
    write_eml(C.fp(rel), FRONT_DESK, "Sarah Mitchell <sjmitchell61@example.org>",
              "Appointment reminder - Tuesday 14 April", when,
              "Dear Sarah Mitchell,\n\n"
              "This is a reminder of your appointment at Kestrel Bay Physiotherapy:\n\n"
              "  Tuesday 14 April 2026 at 10:00\n"
              "  Shoulder strength group, followed by your right shoulder review with Tom Reyes\n\n"
              "Please bring your resistance band and wear a loose top.\n"
              "If you need to change this appointment, call us on (503) 555-0100.\n\n"
              "Kind regards,\nKestrel Bay Physiotherapy\n")
    C.add(rel, "target", ["text"], False, True, "correspondence",
          "Reminder about her shoulder appointment sent by mistake to the other Sarah Mitchell's email address.", when)

    # 15. Privacy incident report about that misdirected email.
    rel = "Admin/incident_report_2026-04-14_misdirected_email.docx"
    when = datetime(2026, 4, 14, 12, 30)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Privacy incident report"),
        ("table", [
            ["Incident no.", "PI-2026-003"],
            ["Date of incident", "04/13/2026 16:02"],
            ["Date reported", "04/14/2026"],
            ["Reported by", "Jo Whitfield, front desk"],
            ["Type", "Misdirected email (appointment reminder)"],
        ]),
        ("h2", "What happened"),
        ("p", "An appointment reminder for Sarah L. Mitchell (client ID KBP-10427, DOB 09/22/1983) was emailed to "
              "Sarah J. Mitchell (client ID KBP-10388) at sjmitchell61@example.org. The booking system filled in "
              "the email address from the first client record with a matching name. The reminder showed the "
              "appointment time, the clinician and that it was a right shoulder review. No other clinical details "
              "were included."),
        ("h2", "How it was found"),
        ("p", "Sarah J. Mitchell phoned on 14 April at 08:30 to say she had received a reminder for a shoulder "
              "appointment that was not hers."),
        ("h2", "Actions"),
        ("bullet", "Sarah J. Mitchell asked to delete the email; she confirmed by phone on 14 April that she had."),
        ("bullet", "Sarah L. Mitchell told by phone at 09:10 on 14 April and in person at her 10:00 appointment."),
        ("bullet", "Email auto-fill switched off. Staff must confirm date of birth before contacting any client who shares a name with another client."),
        ("bullet", "Both records flagged: NAME ALERT - two clients called Sarah Mitchell."),
        ("h2", "Risk assessment"),
        ("p", "Low. One recipient, who has deleted the message. Not reportable. Reviewed by Tom Reyes (privacy officer) on 04/14/2026."),
    ], {"author": "Jo Whitfield", "last_modified_by": "Tom Reyes", "title": "Privacy incident PI-2026-003",
        "created": datetime(2026, 4, 14, 9, 40), "modified": when, "revision": 3})
    C.add(rel, "target", ["text"], True, True, "other",
          "Incident report naming both Sarah Mitchells with IDs, DOB and the other client's email.", when)

    # 16. Group email with every class member visible in To (no BCC).
    rel = "Email/2026-05-02_shoulder_group_time_change.eml"
    when = datetime(2026, 5, 2, 9, 31)
    write_eml(C.fp(rel), TOM, [
        "Grace Obi <grace.obi@example.org>",
        "Peter Vance <peter.vance@example.com>",
        "Sarah Mitchell <sarah.mitchell83@example.com>",
        "Ana Ruiz <ana.ruiz92@example.org>",
    ], "Shoulder group - new start time from 5 May", when,
        "Hi all,\n\n"
        "From Tuesday 5 May the shoulder strength group will start at 11:00 instead of 10:00, because the "
        "studio is needed for a hydrotherapy assessment in the earlier slot. Everything else stays the same.\n\n"
        "Great work so far, everyone.\n\nTom\n\n"
        "Tom Reyes, PT, DPT\nKestrel Bay Physiotherapy\n")
    C.add(rel, "target", ["text"], True, True, "correspondence",
          "Class email that exposes four clients' addresses in the To line, hers included.", when)

    # 17. Her first enquiry email.
    rel = "Email/2026-03-01_new_client_enquiry.eml"
    when = datetime(2026, 3, 1, 20, 15)
    write_eml(C.fp(rel), "Sarah Mitchell <sarah.mitchell83@example.com>", FRONT_DESK,
              "Appointment for a shoulder injury", when,
              "Hi there,\n\n"
              "I came off my bike two weeks ago (14 Feb) and my right shoulder is still really sore. I can't lift "
              "my arm above my head and I'm not sleeping well. Urgent care x-rayed it and said nothing is broken.\n\n"
              "I saw Priya in 2023 for my ankle, back then under my maiden name, Sarah Pryce. Could I book an "
              "assessment with whoever is best for shoulders? I'm free most mornings next week.\n\n"
              "Thanks,\nSarah Mitchell\nMobile: 503-555-0147\n")
    C.add(rel, "target", ["text"], True, False, "correspondence",
          "Her first enquiry from her personal email; mentions her maiden name.", when)

    # 18. Internal email with her name misspelt.
    rel = "Email/2026-05-19_reschedule_request.eml"
    when = datetime(2026, 5, 19, 10, 14)
    write_eml(C.fp(rel), JO, TOM, "Sara Mitchel - move Thurs 21st", when,
              "Hi Tom,\n\n"
              "Sara Mitchel rang, she can't make Thursday 21st at 9:00 and would like Friday 22nd in the afternoon. "
              "I've pencilled her in for 2pm Friday, ok?\n\n"
              "Her mobile is 503.555.0147 if you want to call her about the band exercises.\n\nJo\n")
    C.add(rel, "target", ["text"], True, False, "correspondence",
          "Staff email with her name misspelt as Sara Mitchel; her mobile number confirms who it is.", when)

    # 19. Phone message with no identifiers at all.
    rel = "Admin/phone_messages/msg_2026-05-21_0840.txt"
    when = datetime(2026, 5, 21, 9, 20)
    write_text(C.fp(rel),
               "PHONE MESSAGE\n"
               "Date/time: 21 May 2026, 08:40        Taken by: Jo\n"
               "For: Tom\n\n"
               "Caller: Sarah Mitchell\n"
               "Message: Right shoulder flared up after gardening at the weekend. Sore at night again. Asks if she\n"
               "should keep doing the green band exercises or stop.\n\n"
               "Tom's advice (called back 09:15): drop back to isometrics for a few days, ice 15 minutes after\n"
               "exercise, keep Friday's appointment.\n\n"
               "Done - JW\n")
    C.add(rel, "target", ["text"], False, False, "clinical",
          "Name only, no identifiers; the right-shoulder context ties it to her rather than the knee client.", when)

    # 20. Cancellation note: name only in the filename.
    rel = "Admin/phone_messages/Mitchell_S_cancellation_2026-04-28.txt"
    when = datetime(2026, 4, 28, 8, 0)
    write_text(C.fp(rel),
               "Tue 28 Apr 2026 07:55 (JW)\n"
               "Client rang to cancel today's 10:00 with Tom - her little boy is off sick.\n"
               "Rebooked: Thursday 30 Apr at 10:00.\n"
               "Mobile on file confirmed: (503) 555-0147.\n"
               "No late-cancellation fee (more than 2 hours' notice).\n")
    C.add(rel, "target", ["filename", "text"], True, False, "other",
          "Body never names the client; the filename says Mitchell_S and the phone number is hers.", when)

    # 21. Bounce notice: only her email address and invoice number.
    rel = "Email/2026-06-10_undeliverable.eml"
    when = datetime(2026, 6, 10, 9, 3, 47)
    write_eml(C.fp(rel), "Mail Delivery System <mailer-daemon@example.com>", "kbp.frontdesk@example.com",
              "Undeliverable: Your statement from Kestrel Bay Physiotherapy (INV-2026-0318)", when,
              "This is the mail system at host mx2.example.com.\n\n"
              "Your message could not be delivered to one or more recipients.\n\n"
              "<sarah.mitchell83@example.com>: host mail.example.com said: 552 5.2.2 Mailbox full\n\n"
              "----- Original message headers -----\n"
              "From: kbp.frontdesk@example.com\n"
              "To: sarah.mitchell83@example.com\n"
              "Subject: Your statement from Kestrel Bay Physiotherapy (INV-2026-0318)\n"
              "Date: Wed, 10 Jun 2026 09:02:55 -0700\n")
    C.add(rel, "target", ["text"], True, False, "correspondence",
          "Bounce message with no name at all; only her email address and her invoice number link it to her.", when)

    # 22. 2023 record under her maiden name, in the archive.
    rel = "Archive_2023/Pryce_Sarah_2023_notes.txt"
    when = datetime(2023, 6, 13, 12, 0)
    write_text(C.fp(rel),
               "KESTREL BAY PHYSIOTHERAPY - CLIENT NOTES (exported from previous system)\n"
               "Client: Sarah Pryce              Old ID: KBP-08812\n"
               "DOB: 09/22/1983                  Phone: 503-555-0147\n"
               "Email: sarah.pryce@example.com\n"
               "Address: Apt 4B, 210 Station Road, Linden Cove, OR 97991\n"
               "Clinician: Priya Natarajan, PT\n\n"
               "2023-05-09  Initial: left ankle inversion sprain playing netball on 05/06. Grade II ATFL.\n"
               "            Swelling marked. Plan: protected weight bearing, ROM, compression.\n"
               "2023-05-16  Swelling reduced. Started balance work on a foam pad.\n"
               "2023-05-30  Hopping pain-free. Return-to-netball progression given.\n"
               "2023-06-13  Discharged. Full return to sport.\n")
    C.add(rel, "target", ["text", "filename"], True, False, "clinical",
          "Her 2023 notes under her maiden name Sarah Pryce, old ID and old address; same DOB and mobile.", when)

    # 23. Husband's intake lists her as emergency contact.
    rel = "Clients/Mitchell_Daniel_KBP-10431/intake_form.docx"
    when = datetime(2026, 5, 6, 8, 50)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Client intake form"),
        ("table", [
            ["Client ID", "KBP-10431"],
            ["Full name", "Daniel James Mitchell"],
            ["Previous name(s)", "-"],
            ["Date of birth", "02/11/1980"],
            ["Address", "17 Alder Crescent, Linden Cove, OR 97990"],
            ["Mobile", "(503) 555-0163"],
            ["Email", "daniel.mitchell.80@example.com"],
            ["Occupation", "High school teacher"],
            ["Family doctor", "Dr. Alan Pierce, Linden Cove Medical Group"],
            ["Emergency contact", "Sarah Mitchell (wife), (503) 555-0147"],
            ["Insurance", "Self-pay"],
            ["How did you hear about us?", "My wife and son are clients"],
        ]),
        ("h2", "Reason for visit"),
        ("p", "Low back pain since moving furniture on 04/25/2026. Pain into the left buttock, no pins and needles."),
        ("h2", "Medical history"),
        ("p", "Nil significant. Occasional ibuprofen."),
        ("p", "Signed: D. Mitchell          Date: 05/06/2026"),
    ], {"author": "Jo Whitfield", "title": "Client intake form", "created": when})
    C.add(rel, "target", ["text"], True, True, "other",
          "Her husband's intake; she appears as emergency contact with her mobile, so her data sits in his record.", when)

    # 24. Son's consent form, signed by her as parent.
    rel = "Clients/Mitchell_Leo_KBP-10432/consent_minor_2026-05-11.pdf"
    when = datetime(2026, 5, 11, 15, 55)
    pdf = PdfDoc(C.fp(rel), title="Consent to treatment - under 18", author="Kestrel Bay Physiotherapy")
    pdf.h1("Consent to treatment - client under 18")
    pdf.p("Client: Leo Mitchell      Date of birth: 01/09/2014      Client ID: KBP-10432", font="Helvetica-Bold")
    pdf.h2("Parent or guardian")
    pdf.p("Name: Sarah Mitchell\nRelationship to client: Mother\nPhone: (503) 555-0147\n"
          "Email: sarah.mitchell83@example.com\nAddress: 17 Alder Crescent, Linden Cove, OR 97990")
    pdf.h2("Consent")
    pdf.p("I am the parent or legal guardian of the client named above. I consent to physiotherapy assessment and "
          "treatment, including exercise and manual therapy, by Kestrel Bay Physiotherapy staff. I understand a "
          "parent or guardian must be present for sessions while the client is under 16.")
    pdf.p("Reason for referral: right knee pain with soccer (suspected Osgood-Schlatter).")
    pdf.space(16)
    pdf.p("Signature: Sarah Mitchell (signed on tablet)        Date: 05/11/2026", font="Helvetica-Oblique")
    pdf.save()
    C.add(rel, "target", ["text"], True, True, "other",
          "Consent for her son, signed by her with her own contact details; also holds the child's data.", when)

    # 25. Son's invoice, addressed to her as guarantor.
    rel = "Billing/invoice_INV-2026-0544.pdf"
    when = datetime(2026, 6, 12, 16, 10)
    pdf = PdfDoc(C.fp(rel), title="Invoice INV-2026-0544", author="Kestrel Bay Physiotherapy")
    pdf.h1("INVOICE  INV-2026-0544")
    pdf.p("Invoice date: 06/12/2026        Payment due: 07/12/2026")
    pdf.p("Bill to (guarantor):\nSarah Mitchell\n17 Alder Crescent\nLinden Cove, OR 97990", font="Helvetica-Bold")
    pdf.p("Patient: Leo Mitchell   DOB 01/09/2014   Client ID: KBP-10432\n"
          "Insurance: Cascadia Health Plan, member CHP-20931-02 (dependant of CHP-20931-01)")
    xs = [72, 150, 205, 470]
    pdf.row(["Date", "Code", "Description", "Amount"], xs, font="Helvetica-Bold")
    pdf.rule()
    for r in [
        ["05/11/2026", "97161", "PT evaluation, low complexity (right knee)", "165.00"],
        ["05/26/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
        ["06/09/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
    ]:
        pdf.row(r, xs)
    pdf.rule()
    pdf.row(["", "", "Total charges", "385.00"], xs, font="Helvetica-Bold")
    pdf.row(["", "", "Insurance paid", "-308.00"], xs)
    pdf.row(["", "", "Balance due from guarantor", "77.00"], xs, font="Helvetica-Bold")
    pdf.save()
    C.add(rel, "target", ["text"], True, True, "billing",
          "Invoice for her son's treatment, addressed to her as the paying guarantor.", when)

    # 26. Insurer explanation of benefits covering her and her son.
    rel = "Billing/EOB_Cascadia_2026-05-29.pdf"
    when = datetime(2026, 6, 3, 9, 0)
    pdf = PdfDoc(C.fp(rel), title="Explanation of Benefits", author="Cascadia Health Plan",
                 creator="Cascadia Health Plan statements",
                 head=["Cascadia Health Plan", "PO Box 4410, Salem Junction, OR 97399", "Member services (800) 555-0199"])
    pdf.h1("Explanation of Benefits - THIS IS NOT A BILL")
    pdf.p("Statement date: 05/29/2026        Plan: Cascadia Silver PPO")
    pdf.p("Subscriber: SARAH L MITCHELL\n17 ALDER CRESCENT\nLINDEN COVE OR 97990\nMember ID: CHP-20931",
          font="Helvetica-Bold")
    xs = [72, 190, 265, 335, 395, 450, 500]
    pdf.row(["Patient", "Account", "Service date", "Code", "Billed", "Plan paid", "You owe"], xs, font="Helvetica-Bold", size=8.5)
    pdf.rule()
    for r in [
        ["SARAH L MITCHELL (01)", "KBP-10427", "05/08/2026", "97110", "110.00", "73.60", "18.40"],
        ["SARAH L MITCHELL (01)", "KBP-10427", "05/22/2026", "97110 97140", "165.00", "110.40", "27.60"],
        ["LEO MITCHELL (02)", "KBP-10432", "05/11/2026", "97161", "165.00", "112.00", "28.00"],
    ]:
        pdf.row(r, xs, size=8.5)
    pdf.rule()
    pdf.p("Provider for all lines: Kestrel Bay Physiotherapy. Amounts you owe are paid to the provider.")
    pdf.p("Deductible met this year: $1,500.00 of $1,500.00 (family).")
    pdf.save()
    C.add(rel, "target", ["text"], True, True, "billing",
          "Insurer statement to her as subscriber, listing her claims and her son's on one page.", when)

    # 27. Staff meeting minutes that discuss her and another client.
    rel = "Admin/staff_meeting_minutes_2026-06-03.docx"
    when = datetime(2026, 6, 3, 13, 15)
    write_docx(C.fp(rel), [
        ("h1", "Staff meeting minutes - 3 June 2026"),
        ("p", "Present: Tom Reyes, Priya Natarajan, Jo Whitfield, Sarah Kwan"),
        ("h2", "1. Privacy incident PI-2026-003 follow-up"),
        ("p", "Sarah Mitchell (KBP-10427) has asked for written confirmation that the misdirected reminder was "
              "deleted by the other recipient. Tom to send a letter this week. The date-of-birth check before "
              "contacting clients with shared names is working; Jo reports two near-misses caught in May."),
        ("h2", "2. Insurance denial"),
        ("p", "Raj Patel (KBP-10355): Northline Insurance denied his May hamstring claims as not medically "
              "necessary. Tom to write an appeal using the visit notes."),
        ("h2", "3. Hydrotherapy waitlist"),
        ("p", "Three clients waiting. The pool partner has two slots from July."),
        ("h2", "4. Summer hours"),
        ("p", "Closed Saturdays in August. Jo to update the website and voicemail."),
        ("h2", "5. Clinical Pilates"),
        ("p", "Sarah Kwan will start a Thursday evening beginners class from 18 June."),
    ], {"author": "Jo Whitfield", "title": "Staff meeting minutes", "created": when})
    C.add(rel, "target", ["text"], True, True, "other",
          "Minutes discussing her by name and ID next to another client's insurance dispute.", when)

    # 28. Email about another client that quotes her older message.
    rel = "Email/2026-06-04_RE_receipt_for_HSA_claim.eml"
    when = datetime(2026, 6, 4, 13, 22)
    write_eml(C.fp(rel), TOM, JO, "RE: Receipt for HSA claim", when,
              "Jo - different topic, sorry for replying on this old thread.\n\n"
              "Raj Patel's insurer has denied his May claims (hamstring, KBP-10355). Can you pull his visit notes "
              "and the referral so I can write the appeal before Friday?\n\nThanks,\nTom\n\n"
              "-----Original Message-----\n"
              "From: Sarah Mitchell <sarah.mitchell83@example.com>\n"
              "Sent: Thursday, March 26, 2026 7:41 PM\n"
              "To: kbp.frontdesk@example.com\n"
              "Subject: Receipt for HSA claim\n\n"
              "Hi, could you send me an itemised receipt for my March sessions? I need it for my HSA.\n"
              "Thanks, Sarah\n")
    C.add(rel, "target", ["text"], True, True, "correspondence",
          "Staff email about another client that still quotes her March message at the bottom.", when)

    # 29. Newsletter mailing list (first and last name in separate columns).
    rel = "Marketing/newsletter_subscribers.csv"
    when = datetime(2026, 9, 1, 11, 0)
    write_csv(C.fp(rel), [
        ["email", "first_name", "last_name", "subscribed_on", "source", "consent"],
        ["grace.obi@example.org", "Grace", "Obi", "2025-11-02", "front desk", "yes"],
        ["sjmitchell61@example.org", "Sarah", "Mitchell", "2026-02-10", "intake form", "yes"],
        ["marta.alvarez@example.com", "Marta", "Alvarez", "2026-02-21", "website", "yes"],
        ["sarah.mitchell83@example.com", "Sarah", "Mitchell", "2026-03-03", "intake form", "yes"],
        ["peter.vance@example.com", "Peter", "Vance", "2026-03-09", "intake form", "yes"],
        ["hannah.liu@example.com", "Hannah", "Liu", "2026-01-12", "intake form", "yes"],
        ["daniel.mitchell.80@example.com", "Daniel", "Mitchell", "2026-05-06", "intake form", "yes"],
        ["lucia.fern@example.org", "Lucia", "Fern", "2026-05-28", "intake form", "yes"],
        ["owen.brandt@example.com", "Owen", "Brandt", "2026-04-30", "website", "no"],
        ["k.osei@example.org", "Kwame", "Osei", "2026-08-15", "5K stand", "yes"],
    ])
    C.add(rel, "target", ["text"], True, True, "other",
          "Mailing list with first and last names in separate columns; both Sarah Mitchells are listed.", when)

    # 30. Her access request, sent from her work address.
    rel = "Email/2026-10-02_request_for_my_records.eml"
    when = datetime(2026, 10, 2, 12, 47)
    write_eml(C.fp(rel), "Sarah Mitchell <s.mitchell.harlow@example.org>", FRONT_DESK,
              "Request for a copy of my records", when,
              "Dear Kestrel Bay Physiotherapy,\n\n"
              "I am writing to ask for a copy of all personal information you hold about me, including clinical "
              "notes, letters, emails, invoices, insurance paperwork and any photographs taken during my treatment.\n\n"
              "To help you find my records:\n"
              "  Name: Sarah Louise Mitchell\n"
              "  Date of birth: 22 September 1983\n"
              "  Client number: KBP-10427\n"
              "  Address: 17 Alder Crescent, Linden Cove, OR 97990\n"
              "  Mobile: (503) 555-0147\n\n"
              "I was also a client in 2023 under my maiden name, Sarah Pryce. I am writing from my work email; "
              "please send the records to my personal email address on file.\n\n"
              "I understand you have another client with the same name, so please make sure only my records are "
              "included.\n\nKind regards,\nSarah Mitchell\n")
    C.add(rel, "target", ["text"], True, False, "correspondence",
          "The access request itself, from a work email address the practice has never seen before.", when)


# ---------------------------------------------------------------------------
# UNREADABLE files that are about the requester
# ---------------------------------------------------------------------------

def build_unreadable_requester(C):
    rel = "Billing/claims/Mitchell_Sarah_KBP-10427_claim_2026-06.pdf"
    when = datetime(2026, 6, 22, 10, 30)
    pdf = PdfDoc(C.fp(rel), title="Claim submission", author="Kestrel Bay Physiotherapy", encrypt="Kbp!2026claims")
    pdf.h1("Provider claim submission - Cascadia Health Plan")
    pdf.p("Patient: Sarah L Mitchell   DOB 09/22/1983   Member CHP-20931-01   Account KBP-10427")
    pdf.p("Services 05/29/2026 to 06/19/2026: 97110 x4, 97140 x1. Diagnosis M75.81. Total billed $330.00.")
    pdf.save()
    C.add(rel, "unreadable_requester", ["filename"], True, False, "billing",
          "Password-protected insurance claim; only the filename shows it is hers.", when)

    rel = "Discharges/discharge_summary_KBP-10427.docx"
    when = datetime(2026, 6, 19, 12, 10)
    write_corrupt(C.fp(rel), "zip", 18000, seed=901)
    C.add(rel, "unreadable_requester", ["filename"], True, False, "clinical",
          "Corrupt Word file; only her client ID in the filename links it to her, not her name.", when)


# ---------------------------------------------------------------------------
# DECOYS: other people who could be mistaken for the requester
# ---------------------------------------------------------------------------

def build_decoys(C):
    # The other client called Sarah Mitchell (Sarah Jane, born 1961, left knee).
    rel = "Clients/Mitchell_Sarah_KBP-10388/intake_form.docx"
    when = datetime(2026, 2, 10, 9, 5)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Client intake form"),
        ("table", [
            ["Client ID", "KBP-10388"],
            ["Full name", "Sarah Jane Mitchell"],
            ["Previous name(s)", "-"],
            ["Date of birth", "05/30/1961"],
            ["Address", "9 Quarry Road, Linden Cove, OR 97990"],
            ["Mobile", "(503) 555-0188"],
            ["Email", "sjmitchell61@example.org"],
            ["Occupation", "Retired librarian"],
            ["Family doctor", "Dr. Ines Calloway, Harbourview Clinic"],
            ["Emergency contact", "Robert Mitchell (husband), (503) 555-0189"],
            ["Insurance", "Evergreen Medicare Advantage, member EMA-551-0388"],
            ["How did you hear about us?", "Surgeon's recommendation"],
        ]),
        ("h2", "Reason for visit"),
        ("p", "Left knee osteoarthritis. Total knee replacement planned for June. Surgeon recommends prehab."),
        ("h2", "Medical history"),
        ("p", "High blood pressure (controlled). Right knee arthroscopy 2015."),
        ("p", "Signed: Sarah J. Mitchell          Date: 02/10/2026"),
    ], {"author": "Jo Whitfield", "title": "Client intake form", "created": when})
    C.add(rel, "decoy", ["text", "filename"], False, False, None,
          "Same first and last name, different client: born 1961, different ID, address, phone and email.", when)

    rel = "Clients/Mitchell_Sarah_KBP-10388/treatment_notes.txt"
    when = datetime(2026, 9, 15, 10, 0)
    write_text(C.fp(rel),
               "MITCHELL, SARAH J.     ID KBP-10388     DOB 05/30/1961\n"
               "Clinician: Priya Natarajan, PT\n"
               "Condition: left knee osteoarthritis; prehab before total knee replacement, then post-op rehab\n\n"
               "2026-02-10  Initial assessment. Flexion 105, extension -5, quads lag. Prehab 2x/week until surgery.\n"
               "2026-02-24  ROM photos taken. Step-ups introduced.\n"
               "2026-03-10  Pain 3/10 on stairs. Added sit-to-stand from low chair.\n"
               "2026-04-07  Flexion 110. Walking 30 minutes without a stick.\n"
               "2026-04-14  Rang front desk: received a reminder email for someone else's shoulder appointment.\n"
               "            Passed to Tom (privacy incident PI-2026-003).\n"
               "2026-06-02  Final pre-op session. Crutch training done.\n"
               "2026-06-30  Post-op review day 8. Flexion 75, extension -8. Wound clean.\n"
               "2026-07-08  Phone call: knee more swollen and warm. Advised to contact surgeon today.\n"
               "2026-07-28  Hydrotherapy started.\n"
               "2026-09-15  Flexion 115, extension 0. Discharged to gym programme.\n")
    C.add(rel, "decoy", ["text", "filename"], False, False, None,
          "Treatment notes of the other Sarah Mitchell; mentions the misdirected email without naming the requester.", when)

    rel = "Scans/scan_20260611_1402.pdf"
    when = datetime(2026, 6, 11, 14, 2)
    page = scan_page([
        ("title", "LINDEN COVE ORTHOPAEDICS"),
        ("sub", "410 Hospital Drive, Linden Cove, OR 97991    Tel (503) 555-0130"),
        ("rule",),
        ("text", "June 9, 2026"),
        ("text", "Priya Natarajan, PT\nKestrel Bay Physiotherapy"),
        ("text", "Re: Mrs Sarah J. Mitchell    DOB 05/30/1961    Our ref: LCO-44871"),
        ("text", "Dear Ms Natarajan,"),
        ("text", "Thank you for your prehabilitation work with Mrs Mitchell. Her left total knee replacement is "
                 "confirmed for Monday 22 June 2026. Please continue quadriceps strengthening and range of motion "
                 "work until surgery. After discharge she will need outpatient physiotherapy two to three times a "
                 "week for eight weeks, with a focus on knee flexion beyond 110 degrees and gait retraining. "
                 "Hydrotherapy may begin once the wound has healed, usually at about three weeks."),
        ("text", "Yours sincerely,"),
        ("space", 50),
        ("text", "Dr. Felix Harmon, MD\nOrthopaedic Surgeon"),
    ], seed=401, angle=-0.7)
    write_scan_pdf(C.fp(rel), [page], "scan_20260611_1402")
    C.add(rel, "decoy", ["ocr"], False, False, None,
          "Scanned surgeon's letter about the other Sarah Mitchell (b. 1961); name only in pixels.", when)

    rel = "Photos/IMG_4502.jpg"
    when = datetime(2026, 2, 24, 9, 40)
    save_jpeg(clinical_photo("knee", 402), C.fp(rel), when,
              description="Sarah J. Mitchell KBP-10388 - L knee extension, side view - 02/24/2026",
              artist="Priya Natarajan")
    C.add(rel, "decoy", ["caption"], False, False, None,
          "Clinical photo whose EXIF caption names the other Sarah Mitchell and her ID.", when)

    rel = "Email/2026-02-17_knee_exercise_question.eml"
    when = datetime(2026, 2, 17, 19, 40)
    write_eml(C.fp(rel), "Sarah Mitchell <sjmitchell61@example.org>", FRONT_DESK,
              "Question about my knee exercises before surgery", when,
              "Hello Priya,\n\n"
              "My surgeon, Dr Harmon, has booked my left knee replacement for 22 June. Should I keep doing the "
              "step-ups you gave me, or stop them on days when the knee is swollen?\n\n"
              "Also, could I move Thursday's appointment to 2pm?\n\n"
              "Many thanks,\nSarah Mitchell\n9 Quarry Road\n(503) 555-0188\n")
    C.add(rel, "decoy", ["text"], False, False, None,
          "Email signed exactly 'Sarah Mitchell' but from the other client (knee, different address and phone).", when)

    rel = "Admin/hydrotherapy_waitlist_2026.xlsx"
    when = datetime(2026, 6, 30, 16, 0)
    write_xlsx(C.fp(rel), [("Waitlist", [
        ["Added", "Client", "Client ID", "Age", "Reason", "Priority", "Notes"],
        [date(2026, 5, 18), "Vance, Peter", "KBP-10344", 67, "Frozen shoulder, land exercise plateaued", "Medium", "Prefers mornings"],
        [date(2026, 5, 28), "Fern, Lucia", "KBP-10419", 54, "Hip OA", "Low", ""],
        [date(2026, 6, 30), "Mitchell, S. J.", "KBP-10388", 65, "Left TKR 06/22, start when wound healed", "High", "Surgeon letter on file"],
        [date(2026, 6, 30), "Santos, Miguel", "KBP-10290", 37, "ACL reconstruction, running prep", "Low", "Evenings only"],
    ])], {"author": "Priya Natarajan", "title": "Hydrotherapy waitlist", "created": datetime(2026, 5, 18, 12, 0),
          "modified": when})
    C.add(rel, "decoy", ["text"], False, False, None,
          "Waitlist with 'Mitchell, S. J.' (the other Sarah Mitchell, KBP-10388); the requester is not on it.", when)

    rel = "Admin/phone_messages/msg_2026-07-08_1130.txt"
    when = datetime(2026, 7, 8, 11, 50)
    write_text(C.fp(rel),
               "PHONE MESSAGE\n"
               "Date/time: 8 July 2026, 11:30        Taken by: Jo\n"
               "For: Priya\n\n"
               "Caller: Sarah Mitchell, 65\n"
               "Message: Two weeks since her knee replacement. Left knee more swollen and warm since yesterday,\n"
               "some redness around the scar. No fever that she knows of.\n\n"
               "Action: Priya called back 11:45 and advised her to contact the surgeon's office today.\n"
               "Hydrotherapy start postponed.\n\n"
               "Done - JW\n")
    C.add(rel, "decoy", ["text"], False, False, None,
          "Same name and no IDs; only the age (65) and the knee surgery show it is the other Sarah Mitchell.", when)

    rel = "Referrals/referral_Hannah_Liu_2026-01-22.docx"
    when = datetime(2026, 1, 22, 14, 20)
    write_docx(C.fp(rel), [
        ("b", "Northgate Family Practice"),
        ("small", "300 Northgate Avenue, Linden Cove, OR 97991  |  Tel (503) 555-0150  |  Fax (503) 555-0151"),
        ("p", "January 22, 2026"),
        ("p", "To: Kestrel Bay Physiotherapy"),
        ("b", "Re: Hannah Liu, DOB 04/12/1995"),
        ("p", "Dear colleague,"),
        ("p", "Thank you for seeing this 30-year-old software tester with a three-month history of neck pain and "
              "right-sided headaches that are worse after long days at the computer. Neurological examination is "
              "normal. I would be grateful for assessment and treatment, including advice on her workstation."),
        ("p", "Kind regards,"),
        ("p", "Dr. Sarah Mitchell, MD\nFamily Physician, Northgate Family Practice"),
    ], {"author": "Dr Sarah Mitchell", "title": "Referral - H Liu", "created": when})
    C.add(rel, "decoy", ["text", "metadata"], False, False, None,
          "Referral about another client written by a family doctor who is also called Sarah Mitchell.", when)

    rel = "Email/2026-09-12_new_enquiry.eml"
    when = datetime(2026, 9, 12, 8, 5)
    write_eml(C.fp(rel), "Sarah-Jane Mitchell <sjane.mitchell@example.com>", FRONT_DESK,
              "Pelvic girdle pain - do you treat pregnancy-related pain?", when,
              "Hello,\n\n"
              "I'm 24 weeks pregnant and have had pelvic girdle pain for about a month, mostly when turning over in "
              "bed and on stairs. Do you have someone who specialises in pregnancy-related pain? I'm usually free "
              "after 4pm.\n\nThank you,\nSarah-Jane Mitchell\n(503) 555-0191\n")
    C.add(rel, "decoy", ["text"], False, False, None,
          "New enquiry from Sarah-Jane Mitchell, a different person with a hyphenated first name.", when)

    rel = "Clients/Mitchell-Hayes_Sarah_KBP-10460/assessment_2026-08-05.docx"
    when = datetime(2026, 8, 5, 16, 40)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Initial assessment"),
        ("table", [
            ["Client", "Sarah Mitchell-Hayes"],
            ["Client ID", "KBP-10460"],
            ["Date of birth", "11/03/1990"],
            ["Address", "44 Cedar Loop, Linden Cove, OR 97990"],
            ["Phone", "(503) 555-0129"],
            ["Email", "s.mitchellhayes@example.org"],
            ["Clinician", "Priya Natarajan, PT"],
            ["Date", "08/05/2026"],
        ]),
        ("h2", "Subjective"),
        ("p", "Right heel pain for three months, worst with the first steps in the morning. Started marathon "
              "training in April."),
        ("h2", "Objective"),
        ("p", "Tender over the medial calcaneal tubercle. Windlass test positive. Calf length reduced on the right."),
        ("h2", "Assessment and plan"),
        ("p", "Right plantar fasciopathy. Calf and plantar fascia loading, footwear advice, taping. Review in two weeks."),
    ], {"author": "Priya Natarajan", "title": "Initial assessment", "created": when})
    C.add(rel, "decoy", ["text", "filename"], False, False, None,
          "Sarah Mitchell-Hayes: a double-barrelled surname that contains the requester's full name.", when)

    rel = "Clients/Mitchell_Daniel_KBP-10431/invoice_INV-2026-0467.pdf"
    when = datetime(2026, 5, 29, 16, 20)
    pdf = PdfDoc(C.fp(rel), title="Invoice INV-2026-0467", author="Kestrel Bay Physiotherapy")
    pdf.h1("INVOICE  INV-2026-0467")
    pdf.p("Invoice date: 05/29/2026        Payment due: 06/28/2026")
    pdf.p("Bill to:\nDaniel Mitchell\n17 Alder Crescent\nLinden Cove, OR 97990", font="Helvetica-Bold")
    pdf.p("Client ID: KBP-10431        Payer: self-pay")
    xs = [72, 150, 205, 470]
    pdf.row(["Date", "Code", "Description", "Amount"], xs, font="Helvetica-Bold")
    pdf.rule()
    for r in [
        ["05/06/2026", "97161", "PT evaluation, low complexity (low back)", "165.00"],
        ["05/13/2026", "97110", "Therapeutic exercise, 1 unit", "55.00"],
        ["05/13/2026", "97140", "Manual therapy, 15 min", "55.00"],
        ["05/20/2026", "97110", "Therapeutic exercise, 1 unit", "55.00"],
    ]:
        pdf.row(r, xs)
    pdf.rule()
    pdf.row(["", "", "Total charges", "330.00"], xs, font="Helvetica-Bold")
    pdf.row(["", "", "Paid by card 05/29/2026", "-330.00"], xs)
    pdf.row(["", "", "Balance", "0.00"], xs, font="Helvetica-Bold")
    pdf.save()
    C.add(rel, "decoy", ["text", "filename"], True, False, None,
          "Her husband's invoice: same surname and the same home address as the requester, but not about her.", when)

    rel = "Clients/Mitchell_Leo_KBP-10432/treatment_notes.txt"
    when = datetime(2026, 6, 9, 17, 0)
    write_text(C.fp(rel),
               "MITCHELL, LEO     ID KBP-10432     DOB 01/09/2014\n"
               "Clinician: Tom Reyes, PT\n"
               "Condition: right knee pain with soccer, Osgood-Schlatter\n\n"
               "2026-05-11  Initial assessment. Tender tibial tubercle. Pain 5/10 after matches.\n"
               "            Plan: load management, quad and hamstring flexibility, return-to-sport plan.\n"
               "2026-05-26  Attended with dad today. Pain 3/10. Playing half matches.\n"
               "2026-06-09  Attended with dad. Pain 2/10. Full matches with ice afterwards. Review in 4 weeks.\n")
    C.add(rel, "decoy", ["text", "filename"], False, False, None,
          "Her son's notes; same surname, and no mention of her (he attended with his father).", when)

    rel = "Clients/Okoro_Mitchell_KBP-10475/pilates_screening_2026-07-14.pdf"
    when = datetime(2026, 7, 14, 19, 30)
    pdf = PdfDoc(C.fp(rel), title="Clinical Pilates screening", author="Sarah Kwan")
    pdf.h1("Clinical Pilates screening")
    pdf.p("Client: Mitchell Okoro      Client ID: KBP-10475      DOB: 07/15/1977", font="Helvetica-Bold")
    pdf.p("Date: 07/14/2026      Instructor: Sarah Kwan, Clinical Pilates instructor\n"
          "Referred by: Priya Natarajan, PT, after lumbar disc rehabilitation")
    pdf.h2("Screening")
    pdf.p("Pain-free in standing and walking. Mild guarding into lumbar flexion. Good deep abdominal activation in "
          "crook lying. Single leg bridge holds 20 seconds each side.")
    pdf.h2("Plan")
    pdf.p("Beginners mat class, Thursdays 18:00, for eight weeks. Avoid loaded flexion for four weeks.")
    pdf.space(8)
    pdf.p("Signed: Sarah Kwan", font="Helvetica-Oblique")
    pdf.save()
    C.add(rel, "decoy", ["text", "filename", "metadata"], False, False, None,
          "Client whose first name is Mitchell, signed by a staff member whose first name is Sarah.", when)


# ---------------------------------------------------------------------------
# NOISE: part of the requester's name, but not about any client
# ---------------------------------------------------------------------------

def build_noise(C):
    rel = "Billing/suppliers/Mitchell_Hart_Medical_INV-7781.pdf"
    when = datetime(2026, 2, 12, 11, 0)
    pdf = PdfDoc(C.fp(rel), title="Invoice 7781", author="Mitchell & Hart Medical Supplies",
                 creator="Mitchell & Hart billing",
                 head=["Mitchell & Hart Medical Supplies Ltd.", "400 Foundry Road, Riverton, OR 97377",
                       "Orders (503) 555-0176  |  orders.mitchellhart@example.com"])
    pdf.h1("INVOICE 7781")
    pdf.p("Date: 02/12/2026      Account: KBP-0042      Terms: 30 days")
    pdf.p("Bill to: Kestrel Bay Physiotherapy, 112 Wharf Street, Suite 2, Linden Cove, OR 97991")
    xs = [72, 120, 400, 470]
    pdf.row(["Qty", "Item", "Unit", "Total"], xs, font="Helvetica-Bold")
    pdf.rule()
    for r in [["10", "Resistance band roll, red, 25 yd", "38.00", "380.00"],
              ["10", "Resistance band roll, green, 25 yd", "38.00", "380.00"],
              ["4", "Kinesiology tape, 6 pack", "42.50", "170.00"],
              ["2", "Ultrasound gel, 5 L", "19.75", "39.50"]]:
        pdf.row(r, xs)
    pdf.rule()
    pdf.row(["", "", "Total", "969.50"], xs, font="Helvetica-Bold")
    pdf.space(10)
    pdf.p("Your account manager: Sarah Okafor, (503) 555-0177. Thank you for your order.")
    pdf.save()
    C.add(rel, "noise", ["text", "filename", "metadata"], False, False, None,
          "Supplier invoice from 'Mitchell & Hart' whose account manager is a Sarah; no client data.", when)

    rel = "Staff/rota_2026_Q2.xlsx"
    when = datetime(2026, 3, 27, 15, 0)
    weeks = []
    start = date(2026, 4, 6)
    for i in range(13):
        wk = start + timedelta(days=7 * i)
        weeks.append([wk, "TR, PN, JW", "TR, PN, JW, SK (Pilates 18:00-20:00)", "TR, JW", "PN, JW, SK (Pilates 18:00-20:00)",
                      "TR, PN, JW", "PN (09:00-13:00)" if i % 2 else "TR (09:00-13:00)"])
    write_xlsx(C.fp(rel), [
        ("Staff", [["Initials", "Name", "Role", "Hours"],
                   ["TR", "Tom Reyes", "Physiotherapist, owner", "Full time"],
                   ["PN", "Priya Natarajan", "Physiotherapist", "Full time"],
                   ["JW", "Jo Whitfield", "Front desk and billing", "Full time"],
                   ["SK", "Sarah Kwan", "Clinical Pilates instructor", "Tue and Thu evenings"]]),
        ("Q2 rota", [["Week commencing", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]] + weeks),
    ], {"author": "Tom Reyes", "title": "Staff rota Q2 2026", "created": when})
    C.add(rel, "noise", ["text"], False, False, None,
          "Staff rota; the only Sarah is the Pilates instructor Sarah Kwan.", when)

    rel = "Marketing/Mitchell_Park_5K_flyer.docx"
    when = datetime(2026, 8, 20, 10, 0)
    write_docx(C.fp(rel), [
        ("h1", "See you at the Mitchell Park 5K!"),
        ("p", "Sunday 20 September 2026, Mitchell Park, Linden Cove"),
        ("p", "Kestrel Bay Physiotherapy is the official physio partner of this year's Mitchell Park 5K fun run."),
        ("bullet", "Free group warm-up at 8:30 by the Mitchell Park boathouse"),
        ("bullet", "Injury screening tent near the finish line"),
        ("bullet", "Post-race stretching and recovery tips"),
        ("p", "Bring the family. Under-12s run free."),
        ("p", PRACTICE_NAME + "  |  " + PRACTICE_CONTACT),
    ], {"author": "Jo Whitfield", "title": "Mitchell Park 5K flyer", "created": when})
    C.add(rel, "noise", ["text", "filename", "metadata"], False, False, None,
          "Event flyer for a park named Mitchell Park.", when)

    rel = "Email/2026-08-03_parking_notice_Mitchell_Lane.eml"
    when = datetime(2026, 8, 3, 10, 0)
    write_eml(C.fp(rel), "Linden Cove City Parking <parking.lindencove@example.org>", "kbp.frontdesk@example.com",
              "Notice: resurfacing of the Mitchell Lane rear car park, 10-14 August", when,
              "Dear business owner,\n\n"
              "The public car park behind Wharf Street, entered from Mitchell Lane, will be closed for resurfacing "
              "from Monday 10 August to Friday 14 August. Please let your customers know they can use the Harbour "
              "Road car park during this time.\n\n"
              "Linden Cove City Parking Services\n")
    C.add(rel, "noise", ["text"], False, False, None,
          "Council notice about a street called Mitchell Lane.", when)

    rel = "Marketing/Sarah_Mitchell_Memorial_Award_nomination.docx"
    when = datetime(2026, 9, 25, 14, 0)
    write_docx(C.fp(rel), [
        ("h1", "Linden Cove Running Club"),
        ("h2", "Sarah Mitchell Memorial Volunteer Award 2026 - nomination form"),
        ("p", "The award is named after the club's founder, Sarah Mitchell (1931-1998), and honours a local "
              "volunteer who has helped people in Linden Cove stay active."),
        ("table", [
            ["Nominee", "Jo Whitfield"],
            ["Organisation", "Kestrel Bay Physiotherapy"],
            ["Nominated by", "Tom Reyes"],
            ["Reason", "Jo has run the injury tent at the Mitchell Park 5K for three years and organises our free "
                       "warm-up sessions."],
        ]),
        ("p", "Return to the club secretary by 15 October 2026."),
    ], {"author": "Tom Reyes", "title": "Award nomination", "created": when})
    C.add(rel, "noise", ["text", "filename"], False, False, None,
          "Exact full-name match, but it is a community award named after a woman who died in 1998.", when)


# ---------------------------------------------------------------------------
# BACKGROUND: ordinary practice files with no link to the requester
# ---------------------------------------------------------------------------

def build_background(C):
    rel = "Clients/Liu_Hannah_KBP-10302/treatment_notes.docx"
    when = datetime(2026, 4, 9, 15, 0)
    write_docx(C.fp(rel), [
        ("h1", "Treatment notes - neck"),
        ("p", "Client: Hannah Liu    ID: KBP-10302    DOB: 04/12/1995    Clinician: Tom Reyes"),
        ("p", "Referred by her family physician (Northgate Family Practice)."),
        ("table", [
            ["Date", "Note"],
            ["01/27/2026", "Initial: neck pain 3 months, right-sided headaches. Cervical rotation R 50 deg. Postural advice, deep neck flexor training."],
            ["02/10/2026", "Headaches down from daily to twice a week. Workstation set-up reviewed with photos."],
            ["03/03/2026", "Rotation R 70 deg. Added thoracic mobility."],
            ["04/09/2026", "Headache-free for two weeks. Discharged with home programme."],
        ], "header"),
    ], {"author": "Tom Reyes", "title": "Treatment notes", "created": datetime(2026, 1, 27, 11, 0), "modified": when})
    C.add(rel, "background", [], False, False, None, "Another client's notes with no name overlap.", when)

    rel = "Clients/Patel_Raj_KBP-10355/invoice_INV-2026-0402.pdf"
    when = datetime(2026, 4, 2, 16, 0)
    pdf = PdfDoc(C.fp(rel), title="Invoice INV-2026-0402", author="Kestrel Bay Physiotherapy")
    pdf.h1("INVOICE  INV-2026-0402")
    pdf.p("Invoice date: 04/02/2026        Payment due: 05/02/2026")
    pdf.p("Bill to:\nRaj Patel\n88 Orchard Way\nLinden Cove, OR 97991", font="Helvetica-Bold")
    pdf.p("Client ID: KBP-10355        Insurance: Northline Insurance, policy NLI-7730041")
    xs = [72, 150, 205, 470]
    pdf.row(["Date", "Code", "Description", "Amount"], xs, font="Helvetica-Bold")
    pdf.rule()
    for r in [["03/12/2026", "97161", "PT evaluation, low complexity (hamstring)", "165.00"],
              ["03/19/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
              ["03/26/2026", "97110", "Therapeutic exercise, 2 units", "110.00"],
              ["03/31/2026", "97110", "Therapeutic exercise, 1 unit", "55.00"]]:
        pdf.row(r, xs)
    pdf.rule()
    pdf.row(["", "", "Total charges", "440.00"], xs, font="Helvetica-Bold")
    pdf.save()
    C.add(rel, "background", [], False, False, None, "Another client's invoice.", when)

    rel = "Clients/Santos_Miguel_KBP-10290/intake_form.docx"
    when = datetime(2026, 1, 15, 8, 45)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Client intake form"),
        ("table", [
            ["Client ID", "KBP-10290"],
            ["Full name", "Miguel Angel Santos"],
            ["Date of birth", "08/08/1988"],
            ["Address", "5 Heron Way, Linden Cove, OR 97991"],
            ["Mobile", "(503) 555-0118"],
            ["Email", "miguel.santos@example.com"],
            ["Emergency contact", "Rosa Santos (mother), (503) 555-0120"],
            ["Insurance", "Cascadia Health Plan, member CHP-11872-01"],
        ]),
        ("h2", "Reason for visit"),
        ("p", "Rehabilitation after left ACL reconstruction on 12/18/2025."),
        ("p", "Signed: Miguel Santos          Date: 01/15/2026"),
    ], {"author": "Jo Whitfield", "title": "Client intake form", "created": when})
    C.add(rel, "background", [], False, False, None, "Another client's intake form.", when)

    rel = "Admin/privacy_notice.docx"
    when = datetime(2026, 1, 20, 10, 0)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Privacy notice"),
        ("p", "This notice explains how Kestrel Bay Physiotherapy collects, uses and protects your personal and "
              "health information."),
        ("h2", "What we collect"),
        ("p", "Contact details, date of birth, insurance details, your health history, assessment and treatment "
              "notes, photographs taken for clinical purposes, appointment and payment records, and messages you "
              "send us."),
        ("h2", "Why we use it"),
        ("p", "To provide and coordinate your care, to bill you or your insurer, to send appointment reminders, and "
              "to meet our legal and professional obligations."),
        ("h2", "Who we share it with"),
        ("p", "Your family doctor and other treating clinicians, your insurer when you ask us to bill them, and "
              "service providers who host our systems. We never sell your information."),
        ("h2", "How long we keep it"),
        ("p", "Adult records are kept for seven years after your last visit. Records of children are kept until "
              "they turn 25."),
        ("h2", "Your rights"),
        ("p", "You can ask for a copy of your information, ask us to correct it, or ask us to delete information we "
              "no longer need. Contact our privacy officer at kbp.privacy@example.com or (503) 555-0100."),
    ], {"author": "Tom Reyes", "title": "Privacy notice", "created": when})
    C.add(rel, "background", [], False, False, None, "Practice privacy notice.", when)

    rel = "Admin/infection_control_checklist.txt"
    when = datetime(2026, 1, 5, 8, 0)
    write_text(C.fp(rel),
               "KESTREL BAY PHYSIOTHERAPY - DAILY INFECTION CONTROL CHECKLIST\n\n"
               "[ ] Wipe all plinths and pillows with disinfectant between clients\n"
               "[ ] Replace paper roll on each plinth\n"
               "[ ] Clean shared exercise equipment (bands, weights, balls) after the group class\n"
               "[ ] Check hand sanitiser at reception and in each room\n"
               "[ ] Empty clinical waste bins; log collection day (Thursday)\n"
               "[ ] Wash towels at 60 C\n"
               "[ ] Record fridge temperature for ice packs (2 to 8 C)\n")
    C.add(rel, "background", [], False, False, None, "Generic daily checklist.", when)

    rel = "Admin/price_list_2026.pdf"
    when = datetime(2026, 1, 2, 9, 0)
    pdf = PdfDoc(C.fp(rel), title="Price list 2026", author="Kestrel Bay Physiotherapy")
    pdf.h1("Price list from 1 January 2026")
    xs = [72, 400]
    for r in [["Initial assessment (60 min)", "$165"], ["Follow-up session (30 min)", "$110"],
              ["Follow-up session (45 min)", "$140"], ["Shoulder strength group (per class)", "$40"],
              ["Clinical Pilates (per class)", "$45"], ["Hydrotherapy session (pool partner)", "$95"],
              ["Late cancellation (under 2 hours)", "$50"]]:
        pdf.row(r, xs, size=11, lead=18)
    pdf.space(10)
    pdf.p("We bill most insurers directly. Payment is due on the day for self-pay clients.")
    pdf.save()
    C.add(rel, "background", [], False, False, None, "Practice price list.", when)

    rel = "Templates/intake_form_TEMPLATE.docx"
    when = datetime(2025, 11, 3, 9, 0)
    write_docx(C.fp(rel), letterhead_docx() + [
        ("h1", "Client intake form"),
        ("table", [[label, ""] for label in [
            "Client ID", "Full name", "Previous name(s)", "Date of birth", "Address", "Mobile", "Email",
            "Occupation", "Family doctor", "Emergency contact", "Insurance", "How did you hear about us?"]]),
        ("h2", "Reason for visit"),
        ("p", ""),
        ("h2", "Medical history"),
        ("p", ""),
        ("p", "Signed: ____________________          Date: __________"),
    ], {"author": "Jo Whitfield", "title": "Client intake form", "created": when})
    C.add(rel, "background", [], False, False, None, "Blank intake template with field labels only.", when)

    rel = "Admin/equipment_maintenance_log.xlsx"
    when = datetime(2026, 9, 1, 12, 0)
    write_xlsx(C.fp(rel), [("Log", [
        ["Date", "Equipment", "Serial", "Task", "Done by", "Next due"],
        [date(2026, 1, 9), "Therapeutic ultrasound unit", "US-22-0913", "Annual calibration", "Coastline Biomedical", date(2027, 1, 9)],
        [date(2026, 1, 9), "TENS unit 1", "TN-4471", "Electrical safety test", "Coastline Biomedical", date(2027, 1, 9)],
        [date(2026, 1, 9), "TENS unit 2", "TN-4472", "Electrical safety test", "Coastline Biomedical", date(2027, 1, 9)],
        [date(2026, 3, 2), "Hi-lo plinth, room 2", "PL-0388", "Replaced actuator", "Tom Reyes", date(2026, 9, 2)],
        [date(2026, 6, 15), "Treadmill", "TM-7710", "Belt tension and lubrication", "Coastline Biomedical", date(2026, 12, 15)],
        [date(2026, 9, 1), "Hi-lo plinth, room 2", "PL-0388", "Six-month check, OK", "Priya Natarajan", date(2027, 3, 1)],
    ])], {"author": "Tom Reyes", "title": "Equipment maintenance log", "created": datetime(2026, 1, 9, 12, 0),
          "modified": when})
    C.add(rel, "background", [], False, False, None, "Equipment log with no client data.", when)

    rel = "Admin/cleaning_schedule.csv"
    when = datetime(2026, 1, 5, 8, 30)
    rows = [["day", "area", "task", "initials"]]
    for day, ini in [("Mon", "JW"), ("Tue", "TR"), ("Wed", "PN"), ("Thu", "JW"), ("Fri", "TR"), ("Sat", "PN")]:
        rows.append([day, "Reception", "Wipe counter, chairs, card machine", ini])
        rows.append([day, "Treatment rooms", "Plinths, door handles, bins", ini])
        rows.append([day, "Gym", "Equipment wipe-down, mats", ini])
    write_csv(C.fp(rel), rows)
    C.add(rel, "background", [], False, False, None, "Cleaning rota using staff initials only.", when)

    rel = "Admin/staff_meeting_minutes_2026-01-14.docx"
    when = datetime(2026, 1, 14, 13, 0)
    write_docx(C.fp(rel), [
        ("h1", "Staff meeting minutes - 14 January 2026"),
        ("p", "Present: Tom Reyes, Priya Natarajan, Jo Whitfield"),
        ("h2", "1. New booking system"),
        ("p", "Go-live 2 February. Jo to import client records from the old system; archive exports kept on the NAS."),
        ("h2", "2. Prices"),
        ("p", "New price list from 1 January agreed. Group class price unchanged."),
        ("h2", "3. Privacy notice"),
        ("p", "Updated notice approved; print copies for reception."),
        ("h2", "4. Hydrotherapy"),
        ("p", "Partnership with the Harbour Road pool confirmed for post-surgical clients."),
    ], {"author": "Jo Whitfield", "title": "Staff meeting minutes", "created": when})
    C.add(rel, "background", [], False, False, None, "Earlier staff minutes with no client names.", when)

    rel = "Photos/clinic_reception.jpg"
    when = datetime(2026, 2, 2, 8, 15)
    save_jpeg(reception_photo(501), C.fp(rel), when, model="iPhone 13")
    C.add(rel, "background", [], False, False, None, "Photo of the empty reception area for the website.", when)


# ---------------------------------------------------------------------------
# UNREADABLE files that are not about the requester
# ---------------------------------------------------------------------------

def build_unreadable(C):
    rel = "Admin/equipment_inventory_2024.xlsx"
    when = datetime(2024, 12, 18, 10, 0)
    write_corrupt(C.fp(rel), "zip", 14000, seed=911)
    C.add(rel, "unreadable", [], False, False, None, "Corrupt spreadsheet from an old backup.", when)

    rel = "Staff/payroll_2026_Q2.pdf"
    when = datetime(2026, 7, 2, 9, 0)
    pdf = PdfDoc(C.fp(rel), title="Payroll Q2 2026", author="Linden Cove Payroll Services", encrypt="Payroll#Q2-26",
                 head=["Linden Cove Payroll Services", "Confidential", ""])
    pdf.h1("Payroll summary Q2 2026 - Kestrel Bay Physiotherapy")
    for r in ["Tom Reyes - owner draw", "Priya Natarajan - salary", "Jo Whitfield - salary", "Sarah Kwan - hourly"]:
        pdf.p(r)
    pdf.save()
    C.add(rel, "unreadable", [], False, False, None, "Password-protected payroll file (staff data).", when)

    rel = "Photos/IMG_3990.jpg"
    when = datetime(2026, 1, 30, 12, 0)
    write_corrupt(C.fp(rel), "jpg", 52000, seed=912)
    C.add(rel, "unreadable", [], False, False, None, "Photo that was corrupted during a phone sync.", when)

    rel = "Scans/SJ_Mitchell_L_knee_xray_report.pdf"
    when = datetime(2026, 2, 12, 15, 30)
    write_corrupt(C.fp(rel), "pdf", 30000, seed=913)
    C.add(rel, "unreadable", ["filename"], False, False, None,
          "Corrupt scan; filename points to the other Sarah Mitchell (Sarah J., left knee), not the requester.", when)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def verify(out, expected):
    root = os.path.join(out, PRACTICE_DIR)
    on_disk = set()
    for dp, _dn, fn in os.walk(root):
        for f in fn:
            on_disk.add(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/"))
    listed = [e["path"] for e in expected["files"]]
    missing = [p for p in listed if p not in on_disk]
    extra = sorted(on_disk - set(listed))
    dups = len(listed) - len(set(listed))
    bad_ext = [p for p in listed if os.path.splitext(p)[1].lower() not in ALLOWED_EXT]
    counts = Counter(e["group"] for e in expected["files"])
    targets = [e for e in expected["files"] if e["group"] == "target"]
    shared_targets = sum(1 for e in targets if e["shared"])
    image_only = sum(1 for e in targets if set(e["how"]) <= {"ocr", "caption"})
    print("files on disk: %d   files in expected.json: %d" % (len(on_disk), len(listed)))
    for g in GROUPS:
        print("  %-22s %d" % (g, counts.get(g, 0)))
    print("shared targets: %d   image-only targets: %d" % (shared_targets, image_only))
    problems = []
    if missing:
        problems.append("missing: %s" % missing)
    if extra:
        problems.append("not in expected.json: %s" % extra)
    if dups:
        problems.append("duplicate paths: %d" % dups)
    if bad_ext:
        problems.append("bad extensions: %s" % bad_ext)
    if not 40 <= len(listed) <= 70:
        problems.append("file count out of range: %d" % len(listed))
    if any(counts.get(g, 0) == 0 for g in GROUPS):
        problems.append("a group has no files")
    if shared_targets < 3 or image_only < 2:
        problems.append("minimum shared or image-only targets not met")
    for p in problems:
        print("PROBLEM:", p)
    print("OK" if not problems else "FAILED")
    return not problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default="corpus", help="output folder (default: corpus)")
    args = ap.parse_args()
    out = args.out
    root = os.path.join(out, PRACTICE_DIR)
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root, exist_ok=True)

    C = Corpus(root)
    build_targets(C)
    build_unreadable_requester(C)
    build_decoys(C)
    build_noise(C)
    build_background(C)
    build_unreadable(C)

    expected = {
        "requester": REQUESTER,
        "practice": PRACTICE_DIR,
        "files": sorted(C.entries, key=lambda e: e["path"]),
    }
    with open(os.path.join(out, "expected.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(expected, fh, indent=2)
        fh.write("\n")
    ok = verify(out, expected)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
