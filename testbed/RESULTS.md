# Stand-in results (laptop, not the NAS)

These numbers come from `standin_run.py` replaying the Skill's workflow on a laptop with Qwen3 4B (text) and Qwen3-VL 2B (OCR) through Ollama, as stand-ins for the NAS local models. They are provisional. The same corpus will be re-run on the iDX6011 Pro in Round 2 and these numbers replaced.

Corpus: `make_corpus.py` seed 20261107, 122 files. Input to the run: the name "Maria Lopez" only, no other identifiers, the way most requests arrive.

## Run 3 (2026-11-07, passage fix only)

Same decisions as run 2 on every file (37 included, 11 excluded, 7 needs confirmation, 3 unreadable; 40 of 40 surfaced, 0 decoys, 0 noise, 3 of 3 unreadable). The change: for files decided by an exact identifier match, the passage column now holds the line that actually contains the identifier, the way `collect-evidence` returns its passage, instead of asking the model to quote one. In run 2 the model sometimes quoted a neighbouring spreadsheet row about a different patient; the decision was right but the passage was wrong. Wall time fell to 203 s because 37 quote calls were no longer needed. `run3_qwen3_4b/evidence.tsv` is the index to read.

## Run 2 (2026-11-07, after prompt and rule fixes from run 1)

| Measure | Result |
|---|---|
| Files in scope | 122 |
| Target files surfaced to the user (included or on the confirmation list) | 40 of 40 |
| Target files auto-included | 37 of 40 |
| Precision of auto-included files | 37 of 37, 100 percent |
| Same-surname decoy (Maria Lopez-Ruiz) auto-included | 0 of 12 |
| Decoy excluded automatically by the skeptic check | 9 of 12 |
| Decoy sent to the confirmation list | 3 of 12 |
| Noise files (Lopez Construction, Mario Lopez, Lopez Avenue) auto-included | 0 of 10 |
| Unreadable files reported as unreadable | 3 of 3, none silently dropped |
| Confirmation list the user must decide | 7 items (3 target, 3 decoy, 1 noise) |
| Identifiers seeded automatically from the requester's intake form | email, phone, date of birth, address, patient ID |
| Model calls | 16 OCR, 94 text |
| Wall time | 350 s (OCR 105 s, confirmation and disambiguation 245 s) |

The three target files on the confirmation list are the three designed to be hard: two where the name appears only in document properties and one calendar that lists both Maria Lopez and Maria Lopez-Ruiz with no identifiers. Sending them to the user rather than guessing is the intended behaviour.

## Run 1 (same day, before fixes), kept for the record

Name only, 40 of 40 surfaced, but 0 auto-included: the 4B model wrote reasoning instead of a verdict, and with no identifiers nothing could be confirmed. One unreadable file was dropped from the index. Wall time 2053 s. Fixes: structured verdict output, identifier seeding from the exact-name intake form, unreadable files always kept, exact versus partial name matching, intake forms processed first. All four are now in `SKILL.md` and `references/disambiguation.md`.

## What a NAS run must still answer

- Recall of `collect-evidence` on indexed folders versus this harness's exact substring match.
- OCR quality of the Photos index on real phone photos versus the VLM stand-in.
- Per-file approval flow timing, recycle-bin restore, tag creation.
- Audio transcription on real recordings (this corpus uses transcript stand-ins).
