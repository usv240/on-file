"""Laptop stand-in for the On File workflow.

This is NOT the Skill. The Skill is Markdown and runs inside Uliya on the NAS. This script
replays the same eight steps on a laptop so we can measure provisional numbers before we have
NAS access. Each NAS expert action is replaced by the nearest local equivalent:

    file-agent find / sha256sum / scan-dedupe   -> os.walk, hashlib
    knowledge-agent collect-evidence            -> full-text extraction + exact substring match
    document-agent qa / extract / metadata      -> Qwen3 4B via Ollama (NAS LLM is Qwen3 4B)
    photo-agent vision-ocr / search-picture ocr -> qwen3-vl:2b via Ollama (NAS VLM is a 2B Uliya-v)
    photo-agent meta                            -> Pillow EXIF
    knowledge-agent audio-transcription         -> reads the transcript stand-in files

Usage:
    python standin_run.py --corpus corpus/lakeside-dental --out run1 [--llm qwen3:4b] [--vlm qwen3-vl:2b]

    --choose-dob   simulated user answer when several exact-name intake forms are found
                   (the Skill stops with waiting_user and asks which form is the requester's)

Outputs in --out:
    evidence.tsv      path, decision, source, matched, passage, advocate, skeptic, decided_by,
                      shared, record_type, access_action, erasure_action
    counters.json     step counters and timings
    calls.jsonl       every model call (prompt, response, seconds) for inspection
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests
from docx import Document
from openpyxl import load_workbook
from PIL import Image
from pypdf import PdfReader

sys.stdout.reconfigure(encoding="utf-8")

OLLAMA = "http://localhost:11434"
REQUESTER = {
    "name": "Maria Lopez",
    "identifiers": {},  # filled from CLI / extract step
}
UNIQUE_KEYS = ("pid", "email")              # belong to one person: include with or without the name
PERSONAL_KEYS = ("dob", "phone", "address")  # can be shared by a household: include only with the exact name
STRONG_KEYS = UNIQUE_KEYS + PERSONAL_KEYS
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]

calls_log = None
OCR_CACHE: dict = {}


VERDICT_SCHEMA = {"type": "object", "properties": {"verdict": {"type": "string", "enum": ["FOUND", "NONE"]},
                  "quotes": {"type": "array", "items": {"type": "string"}}}, "required": ["verdict", "quotes"]}
FIELDS_SCHEMA = {"type": "object", "properties": {k: {"type": "string"} for k in ("full_name", "date_of_birth", "email", "phone", "postal_address", "patient_id")},
                 "required": ["full_name", "date_of_birth", "email", "phone", "postal_address", "patient_id"]}


def llm(model: str, prompt: str, images: list[bytes] | None = None, think: bool = False, num_predict: int = 700, fmt=None) -> tuple[str, float]:
    msg = {"role": "user", "content": prompt}
    if images:
        msg["images"] = [base64.b64encode(b).decode() for b in images]
    body = {"model": model, "messages": [msg], "stream": False, "think": think,
            "options": {"temperature": 0, "num_predict": num_predict}}
    if fmt is not None:
        body["format"] = fmt
    t = time.time()
    r = requests.post(f"{OLLAMA}/api/chat", json=body, timeout=600)
    r.raise_for_status()
    out = r.json()["message"]["content"].strip()
    dt = time.time() - t
    if calls_log:
        calls_log.write(json.dumps({"model": model, "prompt": prompt[:4000], "response": out[:4000], "seconds": round(dt, 2), "images": len(images or [])}) + "\n")
        calls_log.flush()
    return out, dt


# ---------- local stand-ins for expert actions ----------

def extract_text(p: Path) -> tuple[str | None, str]:
    """Return (text, status). status: ok | unreadable:<reason> | image"""
    ext = p.suffix.lower()
    try:
        if ext in (".txt", ".csv", ".md", ".eml", ".srt", ".vtt"):
            return p.read_text(encoding="utf-8", errors="replace"), "ok"
        if ext == ".docx":
            d = Document(str(p))
            parts = [x.text for x in d.paragraphs]
            for t in d.tables:
                for row in t.rows:
                    parts.append(" | ".join(c.text for c in row.cells))
            return "\n".join(parts), "ok"
        if ext == ".xlsx":
            wb = load_workbook(str(p), read_only=True, data_only=True)
            parts = []
            for ws in wb.worksheets:
                for row in ws.iter_rows(values_only=True):
                    parts.append(" | ".join("" if v is None else str(v) for v in row))
            return "\n".join(parts), "ok"
        if ext == ".pdf":
            rd = PdfReader(str(p))
            if rd.is_encrypted:
                return None, "unreadable:password-protected"
            txt = "\n".join((pg.extract_text() or "") for pg in rd.pages)
            if txt.strip():
                return txt, "ok"
            return None, "image"  # image-only PDF, needs OCR
        if ext in (".jpg", ".jpeg", ".png"):
            return None, "image"
        return None, "unreadable:unsupported type"
    except Exception as e:  # noqa: BLE001
        return None, f"unreadable:{type(e).__name__}"


def doc_metadata(p: Path) -> str:
    ext = p.suffix.lower()
    try:
        if ext == ".docx":
            cp = Document(str(p)).core_properties
            return " ".join(filter(None, [cp.author, cp.last_modified_by, cp.title, cp.subject, cp.keywords]))
        if ext == ".pdf":
            rd = PdfReader(str(p))
            if rd.is_encrypted:
                return ""
            m = rd.metadata or {}
            return " ".join(str(v) for v in m.values() if v)
        if ext in (".jpg", ".jpeg", ".png"):
            ex = Image.open(p).getexif()
            return str(ex.get(0x010E) or "")
    except Exception:  # noqa: BLE001
        return ""
    return ""


def page_images(p: Path) -> list[bytes]:
    if p.suffix.lower() == ".pdf":
        out = []
        for pg in PdfReader(str(p)).pages:
            for im in pg.images:
                out.append(im.data)
        return out
    img = Image.open(p).convert("RGB")
    img.thumbnail((1400, 1400))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return [buf.getvalue()]


def ocr(vlm: str, p: Path) -> tuple[str, str]:
    imgs = page_images(p)
    if not imgs:
        return "", "unreadable:no image"
    texts = []
    for b in imgs[:3]:
        out, _ = llm(vlm, "Transcribe all text in this image exactly as written, line by line. If there is no text, answer exactly: NO TEXT.", images=[b], num_predict=600)
        texts.append(out)
    t = "\n".join(texts)
    if not t.strip() or "NO TEXT" in t.upper():
        return t, "unreadable:no text found by OCR"
    return t, "ok"


def fold(s: str) -> str:
    """Lower case without accents, so María López matches Maria Lopez."""
    return "".join(c for c in unicodedata.normalize("NFKD", s or "") if not unicodedata.combining(c)).lower()


def phone_digits(s: str) -> str:
    d = re.sub(r"\D", "", s or "")
    return d[-10:] if len(d) >= 7 else ""


def dob_variants(v: str) -> list[str]:
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})$", (v or "").strip())
    if not m:
        return [fold(v)]
    y, mo, d = m.groups()
    mn, di, moi = MONTHS[int(mo) - 1], str(int(d)), str(int(mo))
    return list(dict.fromkeys([f"{y}-{mo}-{d}", f"{d}/{mo}/{y}", f"{mo}/{d}/{y}", f"{d}.{mo}.{y}", f"{y}/{mo}/{d}",
                               f"{di} {mn} {y}", f"{mn} {di}, {y}", f"{moi}/{di}/{y}", f"{di}/{moi}/{y}"]))


def name_variants(name: str) -> list[str]:
    parts = name.split()
    if len(parts) < 2:
        return [fold(name)]
    given, sur = " ".join(parts[:-1]), parts[-1]
    return [fold(f"{given} {sur}"), fold(f"{sur}, {given}")]


def same_value(k: str, a: str, b: str) -> bool:
    if k == "phone":
        return bool(phone_digits(a)) and phone_digits(a) == phone_digits(b)
    if k == "address":
        return fold(a.split(",")[0]).strip() == fold(b.split(",")[0]).strip()
    if k == "dob":
        return bool(set(dob_variants(a)) & set(dob_variants(b)))
    return fold(a).strip() == fold(b).strip()


def mentions(text: str, ids: dict) -> list[str]:
    """Matched identifier keys. Name: 'name' = exact full name in either order (Maria Lopez, Lopez, Maria),
    accents ignored, not followed by a hyphen or letter; 'name-partial' = only inside a longer name.
    Phone compared by digits; date of birth in common formats; address by street line."""
    hit = []
    low = fold(text)
    for k, v in ids.items():
        if k == "name" or not v:
            continue
        if k == "phone":
            pd = phone_digits(v)
            if pd and any(phone_digits(x) == pd for x in re.findall(r"\+?\(?\d[\d\s().-]{6,}\d", text or "")):
                hit.append(k)
        elif k == "dob":
            if any(re.search(r"(?<!\d)" + re.escape(x) + r"(?!\d)", low) for x in dob_variants(v)):
                hit.append(k)
        elif k == "address":
            street = fold(v.split(",")[0]).strip()
            if street and re.search(r"(?<![a-z0-9])" + re.escape(street).replace(r"\ ", r"\s+") + r"(?![a-z])", low):
                hit.append(k)
        elif fold(v) in low:
            hit.append(k)
    if "name" in ids:
        exact = partial = False
        for nv in name_variants(ids["name"]):
            n = re.escape(nv).replace(r"\ ", r"\s+")
            if re.search(r"(?<![a-z])" + n + r"(?![a-z-])", low):
                exact = True
            elif re.search(r"(?<![a-z])" + n, low):
                partial = True
        if exact:
            hit.append("name")
        elif partial:
            hit.append("name-partial")
    return hit


def exact_passage(text: str, ids: dict, matched) -> str:
    """The line(s) that actually contain a matched identifier, strongest first, like the passage
    collect-evidence returns. Empty string if no single line contains one."""
    order = [k for k in STRONG_KEYS if k in matched] + (["name"] if "name" in matched else [])
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    out = []
    for k in order:
        if not ids.get(k):
            continue
        for ln in lines:
            if k in mentions(ln, {k: ids[k]}) and ln not in out:
                out.append(ln)
                break
    return " / ".join(out)[:400]


def verified(ans: str, text: str) -> list[str]:
    """Quote verification: keep only quotes that occur in the file, ignoring case, spacing and punctuation.
    A model answer whose quote is not in the file counts as no answer."""
    if not ans or ans.startswith("NONE") or ans.startswith("UNCLEAR"):
        return []
    hay = re.sub(r"[^a-z0-9]", "", fold(text))
    out = []
    for q in ans.splitlines()[1:]:
        nq = re.sub(r"[^a-z0-9]", "", fold(q))
        if len(nq) >= 4 and nq in hay:
            out.append(q.strip())
    return out


CLASS_SCHEMA = {"type": "object", "properties": {
    "people": {"type": "array", "maxItems": 8, "items": {"type": "object", "properties": {
        "name": {"type": "string"},
        "role": {"type": "string", "enum": ["patient or client", "staff", "contact", "business"]}},
        "required": ["name", "role"]}},
    "record_type": {"type": "string", "enum": ["clinical", "billing", "correspondence", "other"]}},
    "required": ["people", "record_type"]}


# ---------- the workflow ----------

def main():
    global calls_log
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--llm", default="qwen3:4b")
    ap.add_argument("--vlm", default="qwen3-vl:2b")
    ap.add_argument("--name", default="Maria Lopez")
    ap.add_argument("--email", default="")
    ap.add_argument("--phone", default="")
    ap.add_argument("--pid", default="")
    ap.add_argument("--dob", default="")
    ap.add_argument("--address", default="")
    ap.add_argument("--choose-dob", default="", help="simulated user answer when several exact-name intake forms exist")
    a = ap.parse_args()

    root = Path(a.corpus)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    calls_log = open(out / "calls.jsonl", "w", encoding="utf-8")
    ids = {"name": a.name, "email": a.email, "phone": a.phone, "pid": a.pid, "dob": a.dob, "address": a.address}
    ids = {k: v for k, v in ids.items() if v}
    counters = {"identifiers_at_start": list(ids), "timing": {}}
    T0 = time.time()

    files = sorted(p for p in root.rglob("*") if p.is_file())
    rel = lambda p: str(p.relative_to(root)).replace("\\", "/")  # noqa: E731
    counters["files_in_scope"] = len(files)

    # Step 1: candidates by file name (file-agent find)
    t = time.time()
    cand: dict[str, dict] = {}
    surname = a.name.split()[-1].lower()
    for p in files:
        rp = rel(p)
        if a.name.lower() in rp.lower() or re.search(r"\b" + re.escape(surname) + r"\b", rp.lower()) or any(v.lower() in rp.lower() for k, v in ids.items() if k != "name"):
            cand[rp] = {"source": ["file name"], "matched": set()}
    counters["step1_filename_candidates"] = len(cand)

    def surname_in(rp: str) -> bool:
        return True  # every unreadable file in scope is reported, regardless of name
    counters["timing"]["step1"] = round(time.time() - t, 1)

    # Step 2 + 3: candidates by content (collect-evidence), OCR (photo-agent), transcripts (audio stand-in), metadata
    def content_pass(id_subset: dict, only_new: bool):
        n = 0
        for p in files:
            rp = rel(p)
            txt, st = extract_text(p)
            meta = doc_metadata(p)
            rec = cand.setdefault(rp, {"source": [], "matched": set()})
            rec["status"] = st
            if txt is None and st == "image":
                if "ocr_text" not in rec:
                    if rp not in OCR_CACHE:
                        OCR_CACHE[rp] = ocr(a.vlm, p)
                    rec["ocr_text"], rec["ocr_status"] = OCR_CACHE[rp]
                txt = rec["ocr_text"]
                src = "ocr"
            else:
                src = "audio transcript" if "Voicemail" in rp else ("subtitle" if p.suffix.lower() in (".srt", ".vtt") else "content")
            hits = mentions(txt or "", id_subset) if txt else []
            mhits = mentions(meta, id_subset) if meta else []
            if hits:
                rec["source"].append(src)
                rec["matched"].update(hits)
                rec["text"] = txt
                n += 1
            if mhits:
                rec["source"].append("metadata")
                rec["matched"].update(mhits)
                rec["meta"] = meta
                n += 1
            unreadable = st.startswith("unreadable") or rec.get("ocr_status", "ok").startswith("unreadable")
            if unreadable and surname_in(rp):
                rec["source"].append("unreadable in scope")
            if not hits and not mhits and not rec["source"]:
                del cand[rp]
        return n

    t = time.time()
    content_pass(ids, False)
    counters["step2_3_candidates_total"] = len(cand)
    counters["timing"]["step2_3"] = round(time.time() - t, 1)

    # Step 4/5: confirm, disambiguate (identifier classes, namesake rule, two checks with quote
    # verification), then classify included files (other patients in the file, record type)
    t = time.time()
    results = []
    extracted_once = False
    namesake: dict = {}
    ns_own: dict = {}
    shared_keys: set = set()
    questions: list = []

    def qa(text: str, question: str) -> str:
        ns = ""
        if namesake:
            ns = "\nA DIFFERENT person with the same name is known: " + "; ".join(f"{k}={v}" for k, v in namesake.items())
        prompt = (f"You are checking one file for a data access request.\nPerson: {ids['name']} (this exact full name; a different or longer surname, for example a hyphenated one, is a different person)\nKnown identifiers: "
                  + ("; ".join(f"{k}={v}" for k, v in ids.items() if k != "name") or "none yet") + ns
                  + f"\n\nFILE CONTENT:\n{text[:6000]}\n\nQUESTION: {question}\n"
                  "Return JSON: verdict FOUND or NONE, and quotes: the passage(s) copied verbatim from the file content (empty if NONE).")
        out, _ = llm(a.llm, prompt, fmt=VERDICT_SCHEMA)
        try:
            j = json.loads(out)
            v = str(j.get("verdict", "")).upper()
            qs = [str(q) for q in j.get("quotes", []) if str(q).strip()]
            if v == "FOUND" and not qs:
                v = "NONE"
            return v + ("\n" + "\n".join(qs) if qs else "")
        except Exception:  # noqa: BLE001
            return "UNCLEAR\n" + out[:300]

    def classify(text: str) -> tuple[bool, str, str]:
        """Shared-file check as a listing, not a yes/no judgement: the model lists every person named,
        with a role; the rule decides. Any other patient or client listed makes the file shared. If the
        answer cannot be read, the file is treated as shared (the safe direction)."""
        prompt = (f"FILE CONTENT:\n{text[:6000]}\n\n"
                  "people: list the people named in this file, each once, at most 8, the requester first, with their role in this file: "
                  "'patient or client' for anyone who receives care, signs in, has an appointment, an invoice, a claim or a receipt; "
                  "'staff' for clinicians and employees acting in their job; 'contact' for an emergency contact or relative named as a contact; "
                  "'business' for a company. Include every name in tables, lists and sign-in sheets.\n"
                  "record_type: clinical (intake, consent, treatment, x-ray, referral, lab order, clinical photo), billing (invoice, receipt, insurance claim, payment), "
                  "correspondence (letters, emails, reminders, voicemails), other (calendars, schedules, sign-in sheets, testimonials).")
        out, _ = llm(a.llm, prompt, fmt=CLASS_SCHEMA, num_predict=1400)
        try:
            j = json.loads(out)
            others = [str(x.get("name", "")) for x in j.get("people", [])
                      if x.get("role") == "patient or client" and "name" not in mentions(str(x.get("name", "")), {"name": ids["name"]})]
            others = [o for o in others if o.strip()]
            return bool(others), str(j.get("record_type", "other")), ", ".join(others[:2])
        except Exception:  # noqa: BLE001
            return True, "other", "listing could not be read; treated as shared"

    def is_none(ans: str) -> bool:
        return not ans.strip() or ans.startswith("NONE")

    def order(rp: str):
        low = rp.lower()
        return (0 if ("intake" in low or "registration" in low) else 1, rp)

    def extract_ids(text: str) -> dict:
        prompt = ("Extract the patient's fields from this form. Use an empty string for a field that is not present. Copy values exactly as written.\nForm:\n" + text[:4000])
        outp, _ = llm(a.llm, prompt, fmt=FIELDS_SCHEMA)
        new = {}
        try:
            j = json.loads(outp)
        except Exception:  # noqa: BLE001
            return new
        g = lambda k: str(j.get(k, "") or "").strip()  # noqa: E731
        for src_k, dst_k in (("full_name", "_name"), ("email", "email"), ("phone", "phone"), ("date_of_birth", "dob"), ("postal_address", "address")):
            if g(src_k):
                new[dst_k] = g(src_k)
        m = re.search(r"[A-Z]{1,3}-?\d{3,}", g("patient_id"))
        if m:
            new["pid"] = m.group(0)
        return new

    def stop_waiting_user(reason: str):
        counters["state"] = "waiting_user"
        counters["questions"] = questions
        counters["stopped_because"] = reason
        counters["total_seconds"] = round(time.time() - T0, 1)
        (out / "counters.json").write_text(json.dumps(counters, indent=2), encoding="utf-8")
        print(json.dumps(counters, indent=2))
        sys.exit(0)

    seeded_from = None
    if len(ids) == 1:
        # Name only, as most requests arrive. Read the exact-name intake/registration forms first.
        forms = [rp for rp in cand if ("intake" in rp.lower() or "registration" in rp.lower()) and "name" in cand[rp]["matched"]]
        found = []
        for rp in sorted(forms):
            new = extract_ids(cand[rp].get("text") or "")
            if fold(new.get("_name", "")).strip() == fold(ids["name"]).strip():
                found.append((rp, {k: v for k, v in new.items() if k != "_name"}))
        people = []  # one entry per distinct date of birth
        for rp, f in found:
            if not any(same_value("dob", f.get("dob", ""), g.get("dob", "")) for _, g in people):
                people.append((rp, f))
        pick = None
        if len(people) == 1:
            pick = people[0]
        elif len(people) > 1:
            questions.append({"question": "Several intake forms carry this exact name with different dates of birth. Which one is the requester's?",
                              "options": [f"{rp} (born {f.get('dob', '?')})" for rp, f in people]})
            if not a.choose_dob:
                stop_waiting_user("several exact-name intake forms with different dates of birth")
            chosen = [x for x in people if same_value("dob", x[1].get("dob", ""), a.choose_dob)]
            if len(chosen) != 1:
                stop_waiting_user("the answer did not match exactly one form")
            pick = chosen[0]
            questions[-1]["answer"] = pick[0]
            other_rp, other = next(x for x in people if x is not pick)
            namesake = dict(other)
            counters["namesake_from"] = other_rp
        if pick:
            seeded_from, new = pick
            ids.update(new)
            shared_keys = {k for k in PERSONAL_KEYS if namesake.get(k) and ids.get(k) and same_value(k, ids[k], namesake[k])}
            ns_own = {k: v for k, v in namesake.items() if v and k not in shared_keys}
            counters["identifiers_seeded_from"] = seeded_from
            counters["identifiers_extracted"] = new
            counters["identifiers_shared_with_namesake"] = sorted(shared_keys)
            extracted_once = True
            content_pass(new, True)

    ADV_Q = "Quote every passage showing the person named here is the same person as the one described by the identifiers."
    SKP_Q = ("Quote every passage showing the person named here is a DIFFERENT person from the one described by the identifiers, for example a different "
             "or longer surname, a different date of birth, patient ID, email or phone, a generational suffix, an employer, a role or a relationship.")

    def file_text(rp: str, rec: dict) -> str:
        text = rec.get("text") or rec.get("ocr_text") or ""
        if not text:
            txt, st2 = extract_text(root / rp)
            if txt is None and st2 == "image":
                if rp not in OCR_CACHE:
                    OCR_CACHE[rp] = ocr(a.vlm, root / rp)
                txt = OCR_CACHE[rp][0]
            text = txt or ""
        md = rec.get("meta") or doc_metadata(root / rp)
        if md:
            text = text + "\n[document properties] " + md
        return text

    def decide(rp: str) -> dict:
        rec = cand[rp]
        st = rec.get("status", "ok")
        row = {"path": rp, "source": ",".join(dict.fromkeys(rec["source"])), "matched": "", "passage": "", "advocate": "", "skeptic": "",
               "decision": "", "decided_by": "auto", "shared": "", "record_type": "", "access_action": "", "erasure_action": ""}
        if st.startswith("unreadable") or rec.get("ocr_status", "ok").startswith("unreadable") or "unreadable in scope" in rec["source"]:
            row["decision"] = "unreadable"
            row["passage"] = st if st.startswith("unreadable") else rec.get("ocr_status", "")
            row["decided_by"] = "user checks by hand"
            return row
        text = file_text(rp, rec)
        m = set(mentions(text, ids))
        row["matched"] = ",".join(sorted(m))
        ns_m = set(mentions(text, ns_own)) if ns_own else set()
        name = "name" in m
        partial = "name-partial" in m and not name
        uniq = [k for k in m if k in UNIQUE_KEYS]
        pers = [k for k in m if k in PERSONAL_KEYS and k not in shared_keys]
        shared_only = [k for k in m if k in PERSONAL_KEYS and k in shared_keys]

        def two_checks(allow_include: bool, why: str):
            adv, skp = qa(text, ADV_Q), qa(text, SKP_Q)
            # advocate quotes count only if they exist in the file AND name the person (exact name or identifier)
            av = [q for q in verified(adv, text) if set(mentions(q, ids)) - {"name-partial"}]
            sv = verified(skp, text)
            # an automatic exclusion needs hard evidence in the skeptic quote: a longer form of the name,
            # or an identifier of a known same-name person; otherwise the user decides
            hard = [q for q in sv if "name-partial" in mentions(q, {"name": ids["name"]}) or (ns_own and mentions(q, ns_own))]
            row["advocate"] = " / ".join(av)[:600] or "none"
            row["skeptic"] = " / ".join(sv)[:600] or "none"
            if av and not sv and allow_include:
                row["decision"], row["passage"], row["decided_by"] = "included", " / ".join(av)[:400], "auto, skeptic clear"
            elif hard and not av:
                row["decision"] = "excluded, skeptic found a different person"
            else:
                row["decision"], row["decided_by"] = "needs confirmation", "user"
                row["passage"] = (" / ".join(av) or exact_passage(text, ids, m))[:400]
            row["skeptic"] = (row["skeptic"] + f" [{why}]") if why else row["skeptic"]

        if ns_m and not uniq:
            row["decision"] = "excluded, identifiers of a same-name person"
            row["advocate"] = "namesake identifier: " + ",".join(sorted(ns_m))
            row["passage"] = exact_passage(text, ns_own, ns_m)
        elif ns_m and uniq:
            row["decision"], row["decided_by"] = "needs confirmation", "user"
            row["advocate"] = "requester and same-name person both present"
            row["passage"] = exact_passage(text, ids, m)
        elif name and (uniq or "dob" in pers):
            row["decision"] = "included"
            row["advocate"] = "exact name with identifier: " + ",".join(sorted(uniq + pers))
            row["passage"] = exact_passage(text, ids, m) or " / ".join(verified(qa(text, "Quote the passage that mentions the person or one of the identifiers."), text))
        elif name and pers:
            # exact name with only a phone or address: a relative with the same name and the same home
            # would match too, so the against-check runs first; any checked quote sends the file to the user
            skp = verified(qa(text, SKP_Q), text)
            row["advocate"] = "exact name with household identifier: " + ",".join(sorted(pers))
            row["passage"] = exact_passage(text, ids, m)
            if skp:
                row["skeptic"] = " / ".join(skp)[:600] + " [identifier a household can share]"
                row["decision"], row["decided_by"] = "needs confirmation", "user"
            else:
                row["decision"] = "included"
                row["decided_by"] = "auto, against-check clear"
        elif not name and not partial and uniq:
            row["decision"] = "included"
            row["advocate"] = "identifier that belongs to one person: " + ",".join(sorted(uniq))
            row["passage"] = exact_passage(text, ids, m)
        elif not name and not partial and pers:
            two_checks(False, "identifier without the name; could be a household member")
        elif name and shared_only:
            two_checks(False, "identifier shared with a same-name person")
        elif name:
            two_checks(False, "name only, no identifier")
        elif partial:
            two_checks(False, "partial name")
        else:
            ans = qa(text, "Does this file mention the person or any of the identifiers? Quote the passage if so.")
            qs = [q for q in verified(ans, text) if mentions(q, ids)]
            row["advocate"] = " / ".join(qs) or "none"
            if qs:
                row["decision"], row["decided_by"] = "needs confirmation", "user"
            else:
                row["decision"] = "excluded, no mention"
        if row["decision"] == "included":
            sh, rt, ex = classify(text)
            row["shared"] = ("yes: " + ex) if sh else "no"
            row["record_type"] = rt
            row["access_action"] = "extract" if sh else "copy"
            row["erasure_action"] = "edit by hand" if sh else (f"retain ({rt} record)" if rt in ("clinical", "billing") else "delete")
        return row

    for rp in sorted(cand, key=order):
        row = decide(rp)
        results.append(row)
        # grow identifiers from the first included intake form when the request came with some identifiers
        if row["decision"] == "included" and not extracted_once and "intake" in rp.lower():
            extracted_once = True
            new = {k: v for k, v in extract_ids(file_text(rp, cand[rp])).items() if k != "_name" and k not in ids}
            counters["identifiers_extracted"] = new
            if new:
                ids.update(new)
                counters["step2_rerun_new_hits"] = content_pass(new, True)
    done = {r["path"] for r in results}
    for rp in sorted(cand):
        if rp not in done:
            results.append(decide(rp))
    counters["questions"] = questions
    counters["timing"]["step4_5"] = round(time.time() - t, 1)

    # Step 6: duplicates
    t = time.time()
    hashes = {}
    for p in files:
        hashes.setdefault(hashlib.sha256(p.read_bytes()).hexdigest(), []).append(rel(p))
    inc = {r["path"] for r in results if r["decision"] == "included"}
    for h, group in hashes.items():
        if len(group) > 1 and any(g in inc for g in group):
            for g in group:
                if g not in inc:
                    orig = next(r for r in results if r["path"] in group and r["decision"] == "included")
                    results.append({**orig, "path": g, "source": "duplicate of " + orig["path"]})
    counters["timing"]["step6"] = round(time.time() - t, 1)

    # write evidence index
    cols = ["path", "decision", "source", "matched", "passage", "advocate", "skeptic", "decided_by", "shared", "record_type", "access_action", "erasure_action"]
    with open(out / "evidence.tsv", "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for r in sorted(results, key=lambda x: x["path"]):
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " / ") for c in cols) + "\n")
    dec_counts = {}
    for r in results:
        k = r["decision"].split(",")[0]
        dec_counts[k] = dec_counts.get(k, 0) + 1
    counters["decisions"] = dec_counts
    plan = {}
    for r in results:
        if r["decision"] == "included":
            for k in ("access_action", "erasure_action"):
                key = f"{k}: {r[k]}"
                plan[key] = plan.get(key, 0) + 1
    counters["plan"] = plan
    counters["state"] = "completed"
    counters["identifiers_at_end"] = list(ids)
    counters["total_seconds"] = round(time.time() - T0, 1)
    (out / "counters.json").write_text(json.dumps(counters, indent=2), encoding="utf-8")
    print(json.dumps(counters, indent=2))


if __name__ == "__main__":
    main()
