# On File

A Uliya Skill for UGREEN AI NAS that answers a data access or erasure request (HIPAA right of access, GDPR Articles 15 and 17) for one named person. It finds every file on the NAS that mentions them, including scans, photos, voicemails, captions and subtitles, and quotes the passage in each. It tells same-name people apart and hands over extracts instead of other patients' data. It keeps records the law requires, drafts the reply letter, and copies, extracts or deletes files only after per-file approval, with an audit log. Entry for the UGREEN Hackathon 2026 on AI NAS, Open Innovation track.

The Skill itself never sends anything off the NAS.

## What is here

| Folder | Content |
|---|---|
| `on-file/` | The Skill package exactly as submitted: `SKILL.md` and eight files in `references/`. Markdown only. Passes the official Uliya Skill Kit checker with zero errors, warnings and notes. |
| `testbed/` | Two synthetic dental-practice corpora ("Lakeside Dental") with answer keys, a scorer, and a laptop stand-in harness that replays the Skill's workflow with small open models. Results are in `testbed/RESULTS.md`. |
| `proposal/` | The Round 1 proposal (`final.md`, the PDF built from it by `build_pdf.py`, and the Devpost form text). |

## The test corpora

Every name, address, phone number and ID is invented.

| Group | Main | Hard | Purpose |
|---|---|---|---|
| target | 40 | 43 | Files about the requester, Maria Lopez, across docx, xlsx, text PDF, image-only scanned PDF, phone photos, email, voicemail transcripts, document properties, a photo caption and a calendar. 8 (hard: 9) also hold other patients' data |
| decoy | 12 | 12 | A different patient with a longer name, Maria Lopez-Ruiz |
| noise | 10 | 10 | "Lopez" as a company, a staff member and a street |
| unreadable | 3 | 3 | A password-protected PDF, a damaged document and a blank scan |
| same-name person | 0 | 3 | The requester's mother, also Maria Lopez, at the same address |
| household | 0 | 1 | The requester's spouse at the same address |
| background | 57 | 57 | Other patients, suppliers, policies, reception photos |

The hard corpus's cases came from a review of the first version, and the rules for them were written at the same time, so it is a stricter test, not a blind one. Files written by someone who has not read the rules are welcome.

Build and score:

```text
cd testbed
python make_corpus.py --out corpus
python make_corpus.py --variant hard --out corpus-hard
python score.py hash corpus/lakeside-dental before.json
python score.py score corpus/expected.json path/to/evidence.tsv
python score.py verify corpus/lakeside-dental before.json
```

Other entrants are welcome to use the corpora to test their own Skills.

## Stand-in results (laptop, provisional)

Qwen3 4B and Qwen3-VL 2B through Ollama stand in for the NAS models. Input was the name only.

| Measure | Main | Hard |
|---|---|---|
| Requester's files found | 40 of 40 | 43 of 43 |
| Included automatically, none wrong | 37 | 35 |
| Look-alike files included | 0 of 22 | 0 of 26 |
| Unreadable files listed | 3 of 3 | 3 of 3 |
| Shared files flagged for extraction | 7 of 7 | 8 of 8 |
| Items left for the user | 4 | 11 |

Details, the earlier runs and what each fix changed are in `testbed/RESULTS.md`. These numbers will be replaced by NAS measurements in Round 2.

## Licence

MIT for everything in this repository. The Skill package itself contains no third-party components.
