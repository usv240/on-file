# On File

A Uliya Skill for UGREEN AI NAS that answers a data access or erasure request (HIPAA right of access, GDPR Articles 15 and 17) for one named person: it finds every file on the NAS that mentions them, shows the matching passage, drafts the reply letter, and copies or deletes files only after per-file approval, with a hashed audit log. Entry for the UGREEN Hackathon 2026 on AI NAS, Open Innovation track.

Everything runs on the NAS local models. No file leaves the device.

## What is here

| Folder | Content |
|---|---|
| `on-file/` | The Skill package exactly as submitted: `SKILL.md` and `references/`. Markdown only. Passes the official Uliya Skill Kit checker with zero errors, warnings and notes. |
| `testbed/` | A 122-file synthetic dental practice corpus ("Lakeside Dental") with ground truth, a scorer, and a laptop stand-in harness that replays the Skill's workflow with local models. Results so far are in `testbed/RESULTS.md`. |
| `proposal/` | The Round 1 proposal (`final.md` and the PDF built from it). |

## The test corpus

Every name, address, phone number and ID in the corpus is invented. It is deterministic: the same seed produces byte-identical files.

| Group | Files | Purpose |
|---|---|---|
| target | 40 | Files about the requester, Maria Lopez, across docx, xlsx, text PDF, image-only scanned PDF, phone photos, email exports, voicemail transcripts, document properties, a photo caption and a calendar |
| decoy | 12 | A different patient with an overlapping name, Maria Lopez-Ruiz. None may be auto-included |
| noise | 10 | "Lopez" as a company, a staff member and a street |
| unreadable | 3 | A password-protected PDF, a damaged document and a blank scan. All must be listed as unreadable |
| background | 57 | Other patients, suppliers, policies, reception photos |

Build it and score a run:

```text
cd testbed
python make_corpus.py --out corpus
python score.py hash corpus/lakeside-dental before.json
python score.py score corpus/expected.json path/to/evidence.tsv
python score.py verify corpus/lakeside-dental before.json
```

Other entrants are welcome to use the corpus to test their own Skills.

## Stand-in results (laptop, provisional)

Qwen3 4B and Qwen3-VL 2B through Ollama stand in for the NAS models; input was the name only. 40 of 40 target files surfaced, 37 auto-included at 100 percent precision, 0 of 12 decoys and 0 of 10 noise files auto-included, 3 of 3 unreadable files reported, 7 items left for the user to decide. Details and the earlier failed run are in `testbed/RESULTS.md`. These numbers will be replaced by NAS measurements in Round 2.

## Licence

MIT for everything in this repository. The Skill package itself contains no third-party components.
