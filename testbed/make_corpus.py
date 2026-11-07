"""Build the synthetic "Lakeside Dental" corpus for testing On File.

Everything here is invented. No real person, practice, address or phone number.
Deterministic: the same seed produces the same files, so expected.json always matches.

Usage:
    python make_corpus.py [--out corpus] [--seed 20261107]

Produces:
    <out>/lakeside-dental/...   the folder tree to copy onto a NAS
    <out>/expected.json         ground truth, one entry per file
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import random
import shutil
from datetime import date, timedelta
from pathlib import Path

from docx import Document
from openpyxl import Workbook
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from pypdf import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

FONT_PATH = "C:/Windows/Fonts/arial.ttf"

REQUESTER = {
    "name": "Maria Lopez",
    "dob": "1984-03-12",
    "email": "maria.lopez84@example.com",
    "phone": "(555) 014-2231",
    "pid": "LD-10432",
    "address": "18 Birch Lane, Lakeside",
}
DECOY = {
    "name": "Maria Lopez-Ruiz",
    "dob": "1991-07-30",
    "email": "m.lopezruiz@example.com",
    "phone": "(555) 019-8807",
    "pid": "LD-11871",
    "address": "402 Harbor Street, Lakeside",
}
STAFF = ["Dr. Anita Rowe", "Dr. Samuel Okafor", "Priya Natarajan (hygienist)", "Mario Lopez (front desk)"]
OTHER_PATIENTS = [
    "Thomas Berg", "Aisha Rahman", "Jonas Lindqvist", "Grace Mwangi", "Felix Hartmann",
    "Noor Haddad", "Elena Petrova", "Kwame Mensah", "Hannah Weiss", "Diego Alvarez",
    "Sofia Rinaldi", "Omar Farouk", "Lucy Chen", "Patrick Doyle", "Ingrid Solberg",
]
SUPPLIERS = ["Northwind Dental Supply", "Lopez Construction LLC", "Brightline Lab Services", "Cedar IT Services"]

records: list[dict] = []


def add(path: Path, root: Path, group: str, how: list[str], strong: bool, note: str = "",
        shared: bool = False, rtype: str | None = None):
    records.append({
        "path": str(path.relative_to(root)).replace("\\", "/"),
        "group": group,  # target | decoy | noise | unreadable | background | namesake | household
        "mentions_requester": group in ("target", "unreadable_requester"),
        "mentions_decoy": group == "decoy",
        "how": how,  # text | ocr | metadata | filename | caption | audio_transcript | subtitle
        "strong_identifier_present": strong,
        "shared": shared,  # the file also holds personal data of other people
        "record_type": rtype,  # clinical | billing | correspondence | other (targets only)
        "note": note,
    })


# ---------- writers ----------

def write_docx(path: Path, title: str, paragraphs: list[str], author: str | None = None, last_modified_by: str | None = None):
    d = Document()
    d.add_heading(title, level=1)
    for p in paragraphs:
        d.add_paragraph(p)
    if author:
        d.core_properties.author = author
    if last_modified_by:
        d.core_properties.last_modified_by = last_modified_by
    path.parent.mkdir(parents=True, exist_ok=True)
    d.save(path)


def write_pdf_text(path: Path, title: str, lines: list[str]):
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    c.setFont("Helvetica-Bold", 14)
    c.drawString(60, h - 70, title)
    c.setFont("Helvetica", 11)
    y = h - 100
    for ln in lines:
        c.drawString(60, y, ln)
        y -= 16
        if y < 60:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = h - 70
    c.save()


def render_text_image(lines: list[str], size=(1240, 1754), noise=True, rotate=0.6) -> Image.Image:
    img = Image.new("L", size, 245)
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_PATH, 34)
    y = 90
    for ln in lines:
        dr.text((110, y), ln, fill=20, font=font)
        y += 52
    if noise:
        px = img.load()
        rnd = random.Random(len(lines))
        for _ in range(size[0] * size[1] // 400):
            x, yy = rnd.randrange(size[0]), rnd.randrange(size[1])
            px[x, yy] = max(0, px[x, yy] - rnd.randrange(80))
        img = img.rotate(rotate, fillcolor=245, resample=Image.BICUBIC)
        img = img.filter(ImageFilter.GaussianBlur(0.4))
    return img.convert("RGB")


def write_scanned_pdf(path: Path, lines: list[str]):
    """Image-only PDF: no text layer, so it must be OCRed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = render_text_image(lines)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    buf.seek(0)
    c = canvas.Canvas(str(path), pagesize=A4)
    c.drawImage(ImageReader(buf), 0, 0, width=A4[0], height=A4[1])
    c.showPage()
    c.save()


def write_jpg_text(path: Path, lines: list[str], description: str | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    img = render_text_image(lines, size=(1600, 1200), rotate=1.5)
    exif = None
    if description is not None:
        ex = img.getexif()
        ex[0x010E] = description  # ImageDescription
        exif = ex.tobytes()
    if exif:
        img.save(path, format="JPEG", quality=85, exif=exif)
    else:
        img.save(path, format="JPEG", quality=85)


def write_xlsx(path: Path, header: list[str], rows: list[list]):
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(header)
    for r in rows:
        ws.append(r)
    wb.save(path)


def write_txt(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------- content helpers ----------

def d(start: date, n: int) -> str:
    return (start + timedelta(days=n)).isoformat()


def patient_block(p: dict) -> list[str]:
    return [
        f"Patient: {p['name']}",
        f"Date of birth: {p['dob']}",
        f"Patient ID: {p['pid']}",
        f"Email: {p['email']}",
        f"Phone: {p['phone']}",
        f"Address: {p['address']}",
    ]


MOTHER = {
    "name": "Maria Lopez",  # same exact name, same household
    "dob": "1958-09-04",
    "email": "",
    "phone": "(555) 014-2200",
    "pid": "LD-09811",
    "address": "18 Birch Lane, Lakeside",
}


def build_hard_extras(root: Path, rnd: random.Random, base: date):
    """Hard cases found in review: a same-name mother at the same address, a spouse at
    the same address, accented and reordered names, reformatted phone and birth date, a subtitle file."""
    R, M = REQUESTER, MOTHER
    # namesake: Maria Lopez born 1958, same address, own intake form, treatment note, recall letter
    f = root / "Patients" / "Lopez, Maria (1958)"
    p = f / "intake-form-2024-06-02.docx"
    write_docx(p, "New Patient Intake Form", [f"Patient: {M['name']}", f"Date of birth: {M['dob']}", f"Patient ID: {M['pid']}", f"Phone: {M['phone']}", f"Address: {M['address']}", "Reason for visit: denture review."], author="Lakeside Dental Front Desk")
    add(p, root, "namesake", ["text"], False, "same exact name and address, different DOB and ID; must not be auto-included")
    p = f / "treatment-note-2024-06-02.docx"
    write_docx(p, "Treatment Note", [f"Patient: {M['name']} ({M['pid']})", "Date: 2024-06-02", f"Clinician: {STAFF[0]}", "Procedure: denture reline."], author=STAFF[0])
    add(p, root, "namesake", ["text"], False, "exact name with the namesake's own ID")
    p = root / "Admin" / "Recall-Letters" / "recall-2025-06-30-09.pdf"
    write_pdf_text(p, "Recall Letter", [M["name"], M["address"], "", "Dear Maria,", "Your denture review is due. Please call us to book.", "Lakeside Dental"])
    add(p, root, "namesake", ["text"], False, "exact name plus shared address only; genuinely ambiguous, must go to confirmation")
    # household: spouse at the same address, no exact name
    p = root / "Patients" / "Lopez, Carlos" / "intake-form-2025-01-20.docx"
    write_docx(p, "New Patient Intake Form", ["Patient: Carlos Lopez", "Date of birth: 1982-11-23", "Patient ID: LD-10433", "Phone: (555) 014-2232", f"Address: {R['address']}"], author="Lakeside Dental Front Desk")
    add(p, root, "household", ["text"], False, "spouse; shares the requester's address only")
    # accented name and day-first birth date, no other identifier
    p = root / "Email" / "2025-05-14_billing_question.txt"
    write_txt(p, "From: reception@lakeside-dental.example\nTo: billing@lakeside-dental.example\nSubject: Pregunta de factura\n\nPaciente: María López, fecha de nacimiento 12/03/1984.\nPregunta por el importe de la restauración del 21/01/2025.\n")
    add(p, root, "target", ["text"], True, "accented name and DD/MM/YYYY birth date only", rtype="billing")
    # surname-first name and dotted phone in a multi-patient lab sheet
    p = root / "Admin" / "Lab-Orders" / "lab-pickup-sheet-2025-04.txt"
    lines = ["Lab pickup sheet April 2025", "BERG, THOMAS     555.010.7781", "LOPEZ, MARIA     555.014.2231", "MWANGI, GRACE    555.013.9902"]
    write_txt(p, "\n".join(lines) + "\n")
    add(p, root, "target", ["text"], True, "surname-first name and dotted phone; other patients on the same sheet", shared=True, rtype="clinical")
    # subtitle file of a testimonial video, name only
    p = root / "Videos" / "testimonial-2025.srt"
    write_txt(p, "1\n00:00:01,000 --> 00:00:04,000\nHi, I am Maria Lopez.\n\n2\n00:00:04,500 --> 00:00:08,000\nI have been coming to Lakeside Dental since January.\n")
    add(p, root, "target", ["subtitle"], False, "subtitle file, name only; expected on the confirmation list", rtype="other")


def build(root: Path, seed: int, variant: str = "main"):
    rnd = random.Random(seed)
    base = date(2025, 1, 6)
    R, D = REQUESTER, DECOY

    # ---- Requester: 40 files ----
    # 1 intake form (docx, text + author metadata)
    p = root / "Patients" / "Lopez, Maria" / "intake-form-2025-01-14.docx"
    write_docx(p, "New Patient Intake Form", patient_block(R) + [
        "Reason for visit: routine check-up and cleaning.",
        "Medical history: no known allergies. Non-smoker.",
        "Emergency contact: Carlos Lopez (spouse), (555) 014-2232.",
    ], author="Lakeside Dental Front Desk")
    add(p, root, "target", ["text"], True, "intake form; source of identifiers", rtype="clinical")

    # 2-3 consent forms, scanned (image-only PDF)
    for i, t in enumerate(["Consent for Treatment", "Consent to Radiographs"]):
        p = root / "Forms-Scanned" / f"scan_{d(base, 8 + i)}_{i + 41:03d}.pdf"
        write_scanned_pdf(p, [t, "Lakeside Dental", ""] + patient_block(R) + ["", f"Signed: {d(base, 8 + i)}", "Signature: M. Lopez"])
        add(p, root, "target", ["ocr"], True, "scanned consent, no text layer", rtype="clinical")

    # 4 x-ray report (pdf text)
    p = root / "Patients" / "Lopez, Maria" / "radiograph-report-2025-01-20.pdf"
    write_pdf_text(p, "Radiograph Report", patient_block(R) + ["", "Findings: early interproximal caries, tooth 14.", "Recommendation: composite restoration.", f"Reviewed by {STAFF[0]}."])
    add(p, root, "target", ["text"], True, rtype="clinical")

    # 5-8 invoices xlsx (she is one row among others)
    for q in range(4):
        rows = []
        for k in range(12):
            name = rnd.choice(OTHER_PATIENTS)
            rows.append([f"INV-{2025}{q + 1:02d}{k:03d}", d(base, q * 90 + k * 3), name, rnd.choice(["Cleaning", "Filling", "Exam", "Whitening"]), rnd.randrange(80, 600)])
        rows.insert(rnd.randrange(12), [f"INV-{2025}{q + 1:02d}M", d(base, q * 90 + 15), R["name"], "Composite restoration", 240, R["pid"]])
        p = root / "Admin" / "Invoices" / f"invoices-2025-Q{q + 1}.xlsx"
        write_xlsx(p, ["Invoice", "Date", "Patient", "Procedure", "Amount", "Patient ID"], rows)
        add(p, root, "target", ["text"], True, "one row among other patients", shared=True, rtype="billing")

    # 9-14 appointment emails (txt export)
    for i in range(6):
        p = root / "Email" / f"{d(base, 5 + i * 30)}_appointment_{i + 1:02d}.txt"
        write_txt(p, f"From: reception@lakeside-dental.example\nTo: {R['email']}\nSubject: Appointment reminder\n\nDear {R['name']},\n\nThis is a reminder of your appointment on {d(base, 7 + i * 30)} at 10:30 with {STAFF[i % 2]}.\n\nLakeside Dental\n")
        add(p, root, "target", ["text"], True, "email with address", rtype="correspondence")

    # 15 sign-in sheet photo (jpg, phone photo)
    p = root / "Photos" / "IMG_20250114_0917.jpg"
    write_jpg_text(p, ["Lakeside Dental  Sign-in sheet  2025-01-14", "", "09:05  Thomas Berg", "09:10  Maria Lopez        LD-10432", "09:25  Grace Mwangi", "09:40  Felix Hartmann"])
    add(p, root, "target", ["ocr"], True, "phone photo of sign-in sheet", shared=True, rtype="other")

    # 16-17 voicemail transcripts (stand-in for audio)
    for i in range(2):
        p = root / "Voicemail" / f"vm_{d(base, 40 + i * 50)}_1{i}.txt"
        write_txt(p, f"Voicemail transcript {d(base, 40 + i * 50)} 16:4{i}\nCaller: Hi, this is Maria Lopez, patient ID {R['pid']}. I need to move my appointment, please call me back on {R['phone']}. Thanks.\n")
        add(p, root, "target", ["audio_transcript"], True, "stand-in for audio; replace with real recording on NAS", rtype="correspondence")

    # 18-19 metadata-only mentions
    for i, t in enumerate(["Referral note to orthodontist", "Treatment plan summary"]):
        p = root / "Patients" / "Lopez, Maria" / f"{t.lower().replace(' ', '-')}.docx"
        write_docx(p, t, ["See attached plan. Patient details on file.", f"Prepared by {STAFF[1]}."], author=STAFF[1], last_modified_by=R["name"])
        add(p, root, "target", ["metadata", "filename"], False, "name only in last-modified-by and parent folder", rtype="clinical")

    # 20 photo with caption in EXIF
    p = root / "Photos" / "DSC_0412.jpg"
    write_jpg_text(p, ["(clinical photo placeholder)"], description=f"Post-treatment photo, {R['name']}, {R['pid']}, {d(base, 20)}")
    add(p, root, "target", ["caption"], True, "name only in EXIF ImageDescription", rtype="clinical")

    # 21-26 treatment notes docx
    for i in range(6):
        p = root / "Patients" / "Lopez, Maria" / f"treatment-note-{d(base, 20 + i * 45)}.docx"
        write_docx(p, "Treatment Note", [f"Patient: {R['name']} ({R['pid']})", f"Date: {d(base, 20 + i * 45)}", f"Clinician: {STAFF[i % 2]}", "Procedure: " + rnd.choice(["scale and polish", "composite restoration 14", "review", "fluoride varnish"]), "Next visit: 6 months."], author=STAFF[i % 2])
        add(p, root, "target", ["text"], True, rtype="clinical")

    # 27-30 recall letters pdf
    for i in range(4):
        p = root / "Admin" / "Recall-Letters" / f"recall-{d(base, 180 + i * 7)}-{i + 1:02d}.pdf"
        write_pdf_text(p, "Recall Letter", [f"{R['name']}", R["address"], "", f"Dear {R['name'].split()[0]},", "Your six-month check-up is due. Please call us to book.", "Lakeside Dental"])
        add(p, root, "target", ["text"], True, "name plus postal address", rtype="correspondence")

    # 31-33 lab orders txt
    for i in range(3):
        p = root / "Admin" / "Lab-Orders" / f"lab-order-{1000 + i * 37}.txt"
        write_txt(p, f"Lab order {1000 + i * 37}\nTo: {SUPPLIERS[2]}\nPatient: {R['name']}\nPatient ID: {R['pid']}\nItem: {rnd.choice(['crown, tooth 14', 'night guard', 'study model'])}\nDue: {d(base, 60 + i * 30)}\n")
        add(p, root, "target", ["text"], True, rtype="clinical")

    # 34-36 receipts pdf
    for i in range(3):
        p = root / "Admin" / "Receipts" / f"receipt-{d(base, 21 + i * 60)}-{i + 7:03d}.pdf"
        write_pdf_text(p, "Payment Receipt", [f"Received from: {R['name']}", f"Patient ID: {R['pid']}", f"Amount: {[240, 95, 120][i]}.00", f"Date: {d(base, 21 + i * 60)}", "Thank you."])
        add(p, root, "target", ["text"], True, rtype="billing")

    # 37-38 insurance claims xlsx
    for i in range(2):
        rows = [[f"CLM-{i}{k:03d}", rnd.choice(OTHER_PATIENTS), d(base, k * 9), rnd.randrange(50, 400)] for k in range(8)]
        rows.insert(3, [f"CLM-{i}M", R["name"], d(base, 25 + i * 60), 240, R["dob"]])
        p = root / "Admin" / "Insurance" / f"claims-batch-{i + 1}.xlsx"
        write_xlsx(p, ["Claim", "Patient", "Service date", "Amount", "DOB"], rows)
        add(p, root, "target", ["text"], True, shared=True, rtype="billing")

    # 39 referral letter docx (text)
    p = root / "Patients" / "Lopez, Maria" / "referral-letter-2025-03-02.docx"
    write_docx(p, "Referral", [f"Re: {R['name']}, DOB {R['dob']}", "Dear colleague, I am referring this patient for orthodontic assessment.", f"Kind regards, {STAFF[0]}"], author=STAFF[0])
    add(p, root, "target", ["text"], True, rtype="clinical")

    # 40 appointment calendar csv-as-txt
    p = root / "Admin" / "calendar-2025-Q1.csv"
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["date", "time", "patient", "clinician"])
    for k in range(30):
        w.writerow([d(base, k * 3), f"{9 + k % 7}:00", rnd.choice(OTHER_PATIENTS), rnd.choice(STAFF[:2])])
    w.writerow([d(base, 7), "10:30", R["name"], STAFF[0]])
    w.writerow([d(base, 9), "14:00", D["name"], STAFF[1]])  # the decoy also appears here
    write_txt(p, buf.getvalue())
    add(p, root, "target", ["text"], False, "name only, no identifier; decoy also in this file; must go to confirmation or be confirmed via other files", shared=True, rtype="other")

    # ---- Decoy: Maria Lopez-Ruiz, 12 files ----
    folder = root / "Patients" / "Lopez-Ruiz, Maria"
    p = folder / "intake-form-2025-02-03.docx"
    write_docx(p, "New Patient Intake Form", patient_block(D) + ["Reason for visit: wisdom tooth pain.", "Emergency contact: Ana Ruiz (mother)."], author="Lakeside Dental Front Desk")
    add(p, root, "decoy", ["text"], True)
    p = root / "Forms-Scanned" / f"scan_{d(base, 28)}_063.pdf"
    write_scanned_pdf(p, ["Consent for Treatment", "Lakeside Dental", ""] + patient_block(D) + ["", f"Signed: {d(base, 28)}", "Signature: M. Lopez-Ruiz"])
    add(p, root, "decoy", ["ocr"], True)
    p = folder / "radiograph-report-2025-02-10.pdf"
    write_pdf_text(p, "Radiograph Report", patient_block(D) + ["", "Findings: impacted lower third molars.", f"Reviewed by {STAFF[1]}."])
    add(p, root, "decoy", ["text"], True)
    for i in range(2):
        rows = [[f"INV-D{i}{k:03d}", d(base, 30 + k * 4), rnd.choice(OTHER_PATIENTS), "Exam", rnd.randrange(80, 300)] for k in range(10)]
        rows.insert(5, [f"INV-D{i}M", d(base, 35 + i * 30), D["name"], "Extraction", 380, D["pid"]])
        p = root / "Admin" / "Invoices" / f"invoices-2025-extractions-{i + 1}.xlsx"
        write_xlsx(p, ["Invoice", "Date", "Patient", "Procedure", "Amount", "Patient ID"], rows)
        add(p, root, "decoy", ["text"], True)
    for i in range(3):
        p = root / "Email" / f"{d(base, 33 + i * 20)}_appointment_D{i + 1}.txt"
        write_txt(p, f"From: reception@lakeside-dental.example\nTo: {D['email']}\nSubject: Appointment reminder\n\nDear {D['name']},\n\nYour appointment is on {d(base, 35 + i * 20)} at 15:00 with {STAFF[1]}.\n\nLakeside Dental\n")
        add(p, root, "decoy", ["text"], True)
    for i in range(2):
        p = folder / f"treatment-note-{d(base, 35 + i * 40)}.docx"
        write_docx(p, "Treatment Note", [f"Patient: {D['name']} ({D['pid']})", f"Date: {d(base, 35 + i * 40)}", f"Clinician: {STAFF[1]}", "Procedure: extraction 38."], author=STAFF[1])
        add(p, root, "decoy", ["text"], True)
    p = root / "Admin" / "Receipts" / f"receipt-{d(base, 36)}-022.pdf"
    write_pdf_text(p, "Payment Receipt", [f"Received from: {D['name']}", f"Patient ID: {D['pid']}", "Amount: 380.00", f"Date: {d(base, 36)}"])
    add(p, root, "decoy", ["text"], True)
    p = root / "Photos" / "IMG_20250203_0855.jpg"
    write_jpg_text(p, ["Lakeside Dental  Sign-in sheet  2025-02-03", "", "08:50  Jonas Lindqvist", "08:55  Maria Lopez-Ruiz   LD-11871", "09:10  Noor Haddad"])
    add(p, root, "decoy", ["ocr"], True)

    # ---- Noise: 10 files that contain "Lopez" but are not a patient ----
    for i in range(2):
        p = root / "Admin" / "Suppliers" / f"lopez-construction-invoice-{i + 1}.pdf"
        write_pdf_text(p, "Invoice", [SUPPLIERS[1], "Reception refit, phase " + str(i + 1), "Amount: 4,800.00", "Contact: office@lopez-construction.example"])
        add(p, root, "noise", ["text", "filename"], False, "company name")
    p = root / "Admin" / "Staff" / "rota-2025.xlsx"
    write_xlsx(p, ["Week", "Mon", "Tue", "Wed"], [[f"W{k + 1}", STAFF[3], STAFF[2], STAFF[3]] for k in range(12)])
    add(p, root, "noise", ["text"], False, "staff member Mario Lopez")
    p = root / "Admin" / "Staff" / "contract-mario-lopez.docx"
    write_docx(p, "Employment Contract", ["Employee: Mario Lopez", "Role: front desk coordinator", "Start date: 2023-05-01"], author="Lakeside Dental")
    add(p, root, "noise", ["text", "filename"], False, "staff member Mario Lopez")
    for i in range(2):
        p = root / "Admin" / "Suppliers" / f"supplier-{['northwind', 'cedar'][i]}.txt"
        write_txt(p, f"{SUPPLIERS[[0, 3][i]]}\n{[120, 77][i]} Lopez Avenue, Lakeside\nAccount manager: {['Ben Carter', 'Rita Hale'][i]}\n")
        add(p, root, "noise", ["text"], False, "street name")
    for i in range(4):
        p = root / "Admin" / "Staff" / f"timesheet-{d(base, i * 14)}.txt"
        write_txt(p, f"Timesheet week of {d(base, i * 14)}\nMario Lopez: 38.5 h\nPriya Natarajan: 36 h\n")
        add(p, root, "noise", ["text"], False, "staff member Mario Lopez")

    # ---- Unreadable: 3 files ----
    p = root / "Patients" / "Lopez, Maria" / "insurance-letter-protected.pdf"
    write_pdf_text(p, "Insurance Letter", patient_block(R) + ["Pre-authorisation granted."])
    rd = PdfReader(str(p))
    wr = PdfWriter()
    for pg in rd.pages:
        wr.add_page(pg)
    wr.encrypt("lakeside2025")
    with open(p, "wb") as f:
        wr.write(f)
    add(p, root, "unreadable_requester", ["text"], True, "password-protected; mentions requester but cannot be read without the password")
    p = root / "Patients" / "Lopez, Maria" / "old-notes-corrupt.docx"
    write_docx(p, "Old Notes", [f"Patient: {R['name']}", "Legacy notes migrated 2019."])
    data = p.read_bytes()
    p.write_bytes(data[: len(data) // 2])
    add(p, root, "unreadable_requester", ["text"], True, "truncated docx; mentions requester but cannot be opened")
    p = root / "Forms-Scanned" / "scan_2025-01-30_blank.jpg"
    img = Image.new("RGB", (1240, 1754), (242, 242, 240))
    p.parent.mkdir(parents=True, exist_ok=True)
    img.save(p, quality=70)
    add(p, root, "unreadable", ["ocr"], False, "blank page; OCR returns nothing")

    # ---- Background: about 60 files about other patients and the practice ----
    for i, name in enumerate(OTHER_PATIENTS):
        f = root / "Patients" / f"{name.split()[1]}, {name.split()[0]}"
        p = f / f"intake-form-{d(base, i * 11)}.docx"
        write_docx(p, "New Patient Intake Form", [f"Patient: {name}", f"Date of birth: 19{70 + i}-0{1 + i % 9}-1{i % 9}", f"Patient ID: LD-1{200 + i * 13:04d}", f"Email: {name.split()[0].lower()}.{name.split()[1].lower()}@example.com"], author="Lakeside Dental Front Desk")
        add(p, root, "background", ["text"], False)
        p = f / f"treatment-note-{d(base, 15 + i * 11)}.docx"
        write_docx(p, "Treatment Note", [f"Patient: {name}", f"Date: {d(base, 15 + i * 11)}", f"Clinician: {STAFF[i % 2]}", "Procedure: exam."], author=STAFF[i % 2])
        add(p, root, "background", ["text"], False)
        if i % 3 == 0:
            p = root / "Forms-Scanned" / f"scan_{d(base, 2 + i * 11)}_{100 + i:03d}.pdf"
            write_scanned_pdf(p, ["Consent for Treatment", "Lakeside Dental", "", f"Patient: {name}", f"Signed: {d(base, 2 + i * 11)}"])
            add(p, root, "background", ["ocr"], False)
        if i % 4 == 0:
            p = root / "Admin" / "Receipts" / f"receipt-{d(base, 3 + i * 11)}-{200 + i:03d}.pdf"
            write_pdf_text(p, "Payment Receipt", [f"Received from: {name}", "Amount: 95.00"])
            add(p, root, "background", ["text"], False)
    for i, t in enumerate(["privacy-notice", "retention-schedule", "infection-control", "complaints-procedure", "sterilisation-log-2025"]):
        p = root / "Policies" / f"{t}.docx"
        write_docx(p, t.replace("-", " ").title(), [f"Policy document {i + 1}.", "Lakeside Dental keeps patient records for the period required by law.", "Reviewed annually."], author="Practice Manager")
        add(p, root, "background", ["text"], False)
    for i in range(6):
        p = root / "Email" / f"{d(base, 2 + i * 23)}_supplier_{i + 1:02d}.txt"
        write_txt(p, f"From: orders@{['northwind', 'brightline', 'cedar'][i % 3]}.example\nTo: reception@lakeside-dental.example\nSubject: Order confirmation\n\nYour order has shipped.\n")
        add(p, root, "background", ["text"], False)
    for i in range(4):
        p = root / "Photos" / f"IMG_2025030{i + 1}_1203.jpg"
        write_jpg_text(p, ["(reception area photo placeholder)"], description="Reception refit, phase 1")
        add(p, root, "background", ["caption"], False)
    for i in range(3):
        p = root / "Voicemail" / f"vm_{d(base, 3 + i * 70)}_0{i}.txt"
        write_txt(p, f"Voicemail transcript\nCaller: Hello, this is {OTHER_PATIENTS[i]}, I would like to book a cleaning. Please call me back.\n")
        add(p, root, "background", ["audio_transcript"], False)

    if variant == "hard":
        build_hard_extras(root, rnd, base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="corpus")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--variant", choices=["main", "hard"], default="main",
                    help="hard: different seed plus the hard cases found in review (same-name relative, household, name and number variants, subtitles)")
    a = ap.parse_args()
    if a.seed is None:
        a.seed = 20261107 if a.variant == "main" else 20261115
    out = Path(a.out)
    root = out / "lakeside-dental"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    random.seed(a.seed)
    build(root, a.seed, a.variant)
    counts = {}
    for r in records:
        counts[r["group"]] = counts.get(r["group"], 0) + 1
    expected = {
        "requester": REQUESTER,
        "decoy": DECOY,
        "namesake": MOTHER if a.variant == "hard" else None,
        "variant": a.variant,
        "seed": a.seed,
        "counts": counts,
        "files": sorted(records, key=lambda r: r["path"]),
    }
    (out / "expected.json").write_text(json.dumps(expected, indent=2), encoding="utf-8")
    print(json.dumps(counts, indent=2))
    print(f"{len(records)} files -> {root}")


if __name__ == "__main__":
    main()
