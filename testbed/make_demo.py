"""Build the demo corpus: 28 files copied from the hard corpus, chosen so that one short run shows every
case the Skill handles (scanned form, photo text, photo caption, voicemail, subtitle file, document
properties, shared files, same-name mother, longer name, spouse, unreadable files, look-alike names).

    python make_demo.py            # writes corpus-demo/ and audio_demo/ next to this script

The answer key keeps the hard corpus's entries for the chosen files, so score.py works unchanged.
All people, practices and identifiers are invented."""
import json
import shutil
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "corpus-hard"
DST = HERE / "corpus-demo"

FILES = [
    # the requester, Maria Lopez born 1984
    "Forms-Scanned/scan_2025-01-14_041.pdf",          # scanned consent form, no text layer: identifiers come from here
    "Patients/Lopez, Maria/intake-form-2025-01-14.docx",
    "Patients/Lopez, Maria/treatment-note-2025-01-26.docx",
    "Admin/Insurance/claims-batch-1.xlsx",             # shared with other patients: extract
    "Photos/IMG_20250114_0917.jpg",                    # phone photo of a sign-in sheet: text in the photo, shared
    "Photos/DSC_0412.jpg",                             # name only in the photo caption
    "Voicemail/vm_2025-02-15_10.txt",                  # recording (the NAS copy is the .wav)
    "Email/2025-05-14_billing_question.txt",           # accented name and day-first birth date
    "Admin/Lab-Orders/lab-pickup-sheet-2025-04.txt",   # surname-first name and dotted phone, shared
    "Admin/Recall-Letters/recall-2025-07-05-01.pdf",   # name and home address only
    "Email/2025-01-11_appointment_01.txt",
    "Patients/Lopez, Maria/treatment-plan-summary.docx",  # name only in the document properties
    "Videos/testimonial-2025.srt",                     # subtitle file, name only
    "Admin/calendar-2025-Q1.csv",                      # name only, and the longer-name patient in the same file
    "Patients/Lopez, Maria/insurance-letter-protected.pdf",  # unreadable: password protected
    "Forms-Scanned/scan_2025-01-30_blank.jpg",         # unreadable: no text found
    # her mother, also Maria Lopez, born 1958, same address
    "Patients/Lopez, Maria (1958)/intake-form-2024-06-02.docx",
    "Patients/Lopez, Maria (1958)/treatment-note-2024-06-02.docx",
    "Admin/Recall-Letters/recall-2025-06-30-09.pdf",   # name and the shared address only: genuinely ambiguous
    # her husband at the same address
    "Patients/Lopez, Carlos/intake-form-2025-01-20.docx",
    # a different patient with a longer name
    "Patients/Lopez-Ruiz, Maria/intake-form-2025-02-03.docx",
    "Email/2025-02-08_appointment_D1.txt",
    # look-alike names that are not her
    "Admin/Staff/contract-mario-lopez.docx",
    "Admin/Suppliers/lopez-construction-invoice-1.pdf",
    # other patients and practice files
    "Patients/Berg, Thomas/intake-form-2025-01-06.docx",
    "Patients/Mwangi, Grace/intake-form-2025-02-08.docx",
    "Policies/privacy-notice.docx",
    "Voicemail/vm_2025-01-09_00.txt",
]
GROUP_KEY = {"unreadable": "unreadable", "background": "background", "noise": "noise", "decoy": "decoy",
             "namesake": "namesake", "household": "household"}


def main() -> None:
    exp = json.loads((SRC / "expected.json").read_text(encoding="utf-8"))
    by_path = {f["path"]: f for f in exp["files"]}
    missing = [p for p in FILES if p not in by_path]
    assert not missing, missing
    if DST.exists():
        shutil.rmtree(DST)
    for p in FILES:
        src = SRC / "lakeside-dental" / p
        dst = DST / "lakeside-dental" / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    files = [by_path[p] for p in FILES]
    counts = Counter()
    for f in files:
        g = f["group"]
        if g == "unreadable" and f["mentions_requester"]:
            counts["unreadable_requester"] += 1
        else:
            counts[GROUP_KEY.get(g, g)] += 1
    out = dict(exp)
    out["variant"] = "demo (28 files chosen from the hard corpus)"
    out["files"] = files
    out["counts"] = {k: counts.get(k, 0) for k in exp["counts"]}
    (DST / "expected.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")

    audio_src, audio_dst = HERE / "audio_hard", HERE / "audio_demo"
    audio_dst.mkdir(exist_ok=True)
    for p in FILES:
        if p.startswith("Voicemail/"):
            stem = Path(p).stem
            for f in audio_src.glob(stem + ".*"):
                shutil.copy2(f, audio_dst / f.name)
    print(f"{len(FILES)} files, counts {out['counts']}")


if __name__ == "__main__":
    main()
