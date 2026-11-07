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

Outputs in --out:
    evidence.tsv      path, decision, source, matched, passage, advocate, skeptic, decided_by
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
STRONG_KEYS = ("email", "phone", "dob", "pid", "address")

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
        if ext in (".txt", ".csv", ".md", ".eml"):
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


def mentions(text: str, ids: dict) -> list[str]:
    """Return matched identifier keys. 'name' = exact full name as a whole word (not followed by a
    hyphen or letter, so 'Maria Lopez-Ruiz' does not count); 'name-partial' = the full name occurs
    only as part of a longer name."""
    hit = []
    low = text.lower()
    for k, v in ids.items():
        if k == "name" or not v:
            continue
        if v.lower() in low:
            hit.append(k)
    if "name" in ids:
        n = re.escape(ids["name"].lower()).replace(r"\ ", r"\s+")
        if re.search(r"(?<![a-z])" + n + r"(?![a-z-])", low):
            hit.append("name")
        elif re.search(r"(?<![a-z])" + n, low):
            hit.append("name-partial")
    return hit


def exact_passage(text: str, ids: dict, matched: set) -> str:
    """The line(s) that actually contain a matched identifier, strongest first, like the passage
    collect-evidence returns. Empty string if no line contains one (then the caller asks the model)."""
    order = [k for k in STRONG_KEYS if k in matched] + (["name"] if "name" in matched else [])
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    out = []
    for k in order:
        v = ids.get(k, "")
        if not v:
            continue
        for ln in lines:
            if v.lower() in ln.lower() and ln not in out:
                out.append(ln)
                break
    return " / ".join(out)[:400]


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
                src = "audio transcript" if "Voicemail" in rp else "content"
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

    # Step 4/5: confirm with the LLM, disambiguate, extract identifiers from the first intake form
    t = time.time()
    results = []
    extracted_once = False

    def qa(text: str, question: str) -> str:
        prompt = (f"You are checking one file for a data access request.\nPerson: {ids['name']} (this exact full name; a different or longer surname, for example a hyphenated one, is a different person)\nKnown identifiers: "
                  + ("; ".join(f"{k}={v}" for k, v in ids.items() if k != "name") or "none yet")
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

    def verdict(ans: str) -> str:
        """FOUND | NONE | UNCLEAR"""
        for line in ans.strip().splitlines():
            t = line.strip().strip("*`:. ").upper()
            if t in ("FOUND", "NONE"):
                return t
        return "UNCLEAR"

    def is_none(ans: str) -> bool:
        return verdict(ans) == "NONE" or ans.strip() == ""

    def quotes(ans: str) -> str:
        lines = [l for l in ans.strip().splitlines() if l.strip()]
        body = [l.strip() for l in lines if l.strip().strip("*`:. ").upper() not in ("FOUND", "NONE")]
        return " / ".join(body)[:600]

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
        if g("full_name"):
            new["_name"] = g("full_name")
        if g("email"):
            new["email"] = g("email")
        if g("phone"):
            new["phone"] = g("phone")
        if g("date_of_birth"):
            new["dob"] = g("date_of_birth")
        if g("postal_address"):
            new["address"] = g("postal_address")
        m = re.search(r"[A-Z]{1,3}-?\d{3,}", g("patient_id"))
        if m:
            new["pid"] = m.group(0)
        return new

    seeded_from = None
    if len(ids) == 1:
        # Name only, as most requests arrive. The Skill reads exact-name intake/registration forms first.
        forms = [rp for rp in cand if ("intake" in rp.lower() or "registration" in rp.lower()) and "name" in cand[rp]["matched"]]
        found = []
        for rp in forms:
            text = cand[rp].get("text") or ""
            new = extract_ids(text)
            if new.get("_name", "").strip().lower() == ids["name"].lower():
                found.append((rp, {k: v for k, v in new.items() if k != "_name"}))
        if len(found) == 1:
            seeded_from, new = found[0]
            ids.update(new)
            counters["identifiers_seeded_from"] = seeded_from
            counters["identifiers_extracted"] = new
            extracted_once = True
            content_pass(new, True)
        elif len(found) > 1:
            counters["identifiers_seed_conflict"] = [f[0] for f in found]  # the Skill would stop with waiting_user here

    for rp in sorted(cand, key=order):
        rec = cand[rp]
        st = rec.get("status", "ok")
        row = {"path": rp, "source": ",".join(dict.fromkeys(rec["source"])), "matched": ",".join(sorted(rec["matched"])), "passage": "", "advocate": "", "skeptic": "", "decision": "", "decided_by": "auto"}
        if st.startswith("unreadable") or rec.get("ocr_status", "ok").startswith("unreadable") or "unreadable in scope" in rec["source"]:
            row["decision"] = "unreadable"
            row["passage"] = st if st.startswith("unreadable") else rec.get("ocr_status", "")
            results.append(row)
            continue
        text = rec.get("text") or rec.get("ocr_text") or ""
        if rec.get("meta"):
            text = text + "\n[document properties] " + rec["meta"]
        matched = set(rec["matched"])
        if not matched and rec["source"] == ["file name"]:
            # file name only (surname or partial): the content must be read; never auto-include
            txt, st2 = extract_text(root / rp)
            if txt is None and st2 == "image":
                if rp not in OCR_CACHE:
                    OCR_CACHE[rp] = ocr(a.vlm, root / rp)
                txt = OCR_CACHE[rp][0]
            md = doc_metadata(root / rp)
            text = (txt or "") + ("\n[document properties] " + md if md else "")
            matched = set(mentions(text, ids))
            if not matched:
                ans = qa(text, "Does this file mention the person or any of the identifiers? Quote the passage if so.")
                row["advocate"] = ans[:300].replace("\n", " / ")
                row["decision"] = "excluded, no mention" if is_none(ans) else "needs confirmation"
                row["decided_by"] = "auto" if is_none(ans) else "user"
                results.append(row)
                continue
            row["matched"] = ",".join(sorted(matched))
        strong = [k for k in matched if k in STRONG_KEYS]
        if strong and "name" in matched:
            # the real collect-evidence action returns the matching passage itself; mirror that
            # with the line that actually contains the identifier instead of asking the model to quote
            row["passage"] = exact_passage(text, ids, matched) or quotes(qa(text, "Quote the passage that mentions the person or one of the identifiers."))
            row["decision"] = "included"
            row["advocate"] = "strong identifier co-occurs: " + ",".join(strong)
        elif strong and "name" not in matched and "name-partial" not in matched:
            row["passage"] = exact_passage(text, ids, matched) or quotes(qa(text, "Quote the passage that contains the identifier."))
            row["decision"] = "included"
            row["advocate"] = "strong identifier only: " + ",".join(strong)
        else:
            adv = qa(text, "Quote every passage showing the person named here is the same person as the one described by the identifiers.")
            skp = qa(text, "Quote every passage showing the person named here is a DIFFERENT person from the one described by the identifiers, for example a different or longer surname, date of birth, address, email, phone, employer, role or relationship.")
            row["advocate"], row["skeptic"] = adv[:600].replace("\n", " / "), skp[:600].replace("\n", " / ")
            adv_none, skp_none = is_none(adv), is_none(skp)
            partial_only = "name" not in matched
            if not adv_none and skp_none and not partial_only:
                row["decision"] = "included"
                row["passage"] = quotes(adv)
                row["decided_by"] = "auto, skeptic clear"
            elif adv_none and not skp_none:
                row["decision"] = "excluded, skeptic found a different person"
            elif adv_none and skp_none and partial_only:
                row["decision"] = "excluded, partial name only"
            else:
                row["decision"] = "needs confirmation"
                row["decided_by"] = "user"
        results.append(row)
        # grow identifiers from the first included intake form
        if row["decision"] == "included" and not extracted_once and "intake" in rp.lower():
            extracted_once = True
            new = {k: v for k, v in extract_ids(text).items() if k != "_name" and k not in ids}
            counters["identifiers_extracted"] = new
            if new:
                ids.update(new)
                added = content_pass(new, True)
                counters["step2_rerun_new_hits"] = added
                # newly found candidates are processed by the loop because we iterate a sorted snapshot; re-run loop for them
    # second pass for candidates added after the snapshot
    done = {r["path"] for r in results}
    for rp in sorted(cand):
        if rp in done:
            continue
        rec = cand[rp]
        row = {"path": rp, "source": ",".join(dict.fromkeys(rec["source"])), "matched": ",".join(sorted(rec["matched"])), "passage": "", "advocate": "", "skeptic": "", "decision": "", "decided_by": "auto"}
        text = rec.get("text") or rec.get("ocr_text") or ""
        strong = [k for k in rec["matched"] if k in STRONG_KEYS]
        if strong:
            row["passage"] = quotes(qa(text, "Quote the passage that contains the identifier."))
            row["decision"] = "included"
            row["advocate"] = "strong identifier (added after extract): " + ",".join(strong)
        else:
            row["decision"] = "needs confirmation"
            row["decided_by"] = "user"
        results.append(row)
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
                    results.append({"path": g, "source": "duplicate of " + next(x for x in group if x in inc), "matched": "", "passage": "", "advocate": "", "skeptic": "", "decision": "included", "decided_by": "auto"})
    counters["timing"]["step6"] = round(time.time() - t, 1)

    # write evidence index
    cols = ["path", "decision", "source", "matched", "passage", "advocate", "skeptic", "decided_by"]
    with open(out / "evidence.tsv", "w", encoding="utf-8") as f:
        f.write("\t".join(cols) + "\n")
        for r in sorted(results, key=lambda x: x["path"]):
            f.write("\t".join(str(r.get(c, "")).replace("\t", " ").replace("\n", " / ") for c in cols) + "\n")
    dec_counts = {}
    for r in results:
        k = r["decision"].split(",")[0]
        dec_counts[k] = dec_counts.get(k, 0) + 1
    counters["decisions"] = dec_counts
    counters["identifiers_at_end"] = list(ids)
    counters["total_seconds"] = round(time.time() - T0, 1)
    (out / "counters.json").write_text(json.dumps(counters, indent=2), encoding="utf-8")
    print(json.dumps(counters, indent=2))


if __name__ == "__main__":
    main()
