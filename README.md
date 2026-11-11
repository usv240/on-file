# On File

A Uliya Skill for UGREEN AI NAS that answers a data access or erasure request (HIPAA right of access, GDPR Articles 15 and 17) for one named person. It finds the files in the folders you choose that mention them, including scans, photos, voicemails, captions, subtitles and camera events, and quotes the passage in each. It tells same-name people apart and prepares extracts so other patients' data is never handed over. It keeps records the law requires, drafts the reply letter, and copies, extracts or deletes files only after per-file approval, with an audit log. Entry for the UGREEN Hackathon 2026 on AI NAS, Open Innovation track.

The Skill itself never sends anything off the NAS.

## What is here

| Folder | Content |
|---|---|
| `on-file/` | The Skill package exactly as submitted: `SKILL.md` and eight files in `references/`. Markdown only. Passes the official Uliya Skill Kit checker with zero errors, warnings and notes. `python build_package.py <path to check-skill.mjs>` builds `dist/on-file.zip` (one folder, `on-file/`, as in UGREEN's own kit ZIP) and runs the checker on the unzipped copy. |
| `testbed/` | Three synthetic practices with answer keys: two Lakeside Dental corpora and a blind Kestrel Bay Physiotherapy corpus written by an agent that never saw the rules. Also a scorer, a summary script, an audio round-trip script and a laptop stand-in harness that replays the Skill's workflow with small open models. Results are in `testbed/RESULTS.md`. |
| `proposal/` | The Round 1 proposal (`final.md`, the PDF built from it by `build_pdf.py`, and the Devpost form text). |
| `round2/` | The plan for a finalist's one day on a real NAS: a timed runbook with a cut list, the demo video's script and subtitles, a script that builds the four corpora with voicemails as recordings, a file-by-file comparison of the NAS index with the laptop's, and a stricter spare version of the Skill kept ready in case the NAS assistant mishandles one check. |

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
python make_demo.py      # 28 files from the hard corpus: every case in one short run
python score.py hash corpus/lakeside-dental before.json
python score.py score corpus/expected.json path/to/evidence.tsv
python score.py verify corpus/lakeside-dental before.json
```

Other entrants are welcome to use the corpora to test their own Skills.

## Stand-in results (laptop, provisional)

Qwen3 4B and Qwen3-VL 2B instruct through Ollama stand in for the NAS models; voicemails are synthesized speech. Input was the name only.

| Measure | Main dental | Hard dental | Blind physio |
|---|---|---|---|
| Requester's files found | 40 of 40 | 43 of 43 | 29 of 30 |
| Included automatically | 37 | 34 | 18 |
| Wrongly included | 0 | 0 | 0 |
| Look-alike files included | 0 of 22 | 0 of 26 | 0 of 18 |
| Included shared files flagged for extraction | 7 of 7 | 7 of 7 | 6 of 6 |
| Items left for the user | 4 | 12 | 15 |

The blind corpus's first run, before the fixes it led to, found 18 of 30 with none wrongly included; that is the unbiased number. Details, the stress test and the earlier runs are in `testbed/RESULTS.md`. These numbers will be replaced by NAS measurements in Round 2.

## Licence

MIT for everything in this repository. The Skill package itself contains no third-party components.
