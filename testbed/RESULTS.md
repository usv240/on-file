# Stand-in results (laptop, not the NAS)

These numbers come from `standin_run.py` replaying the Skill's workflow on a laptop with Qwen3 4B (text) and Qwen3-VL 2B (reading images) through Ollama, as stand-ins for the NAS models. They are provisional. Both corpora will be re-run on the iDX6011 Pro in Round 2 and these numbers replaced.

Input to every run: the name "Maria Lopez" only, no other identifiers, the way most requests arrive.

## Run 5 (2026-11-07, current rules)

| Measure | Main corpus (122 files) | Hard corpus (129 files) |
|---|---|---|
| Target files shown to the user (included or on the confirmation list) | 40 of 40 | 43 of 43 |
| Target files included automatically | 37 | 34 |
| Precision of automatic inclusion | 37 of 37 | 34 of 34 |
| Decoy, Maria Lopez-Ruiz, included automatically | 0 of 12 (11 excluded, 1 to the user) | 0 of 12 (11 excluded, 1 to the user) |
| Noise (Lopez Construction, Mario Lopez, Lopez Avenue) included automatically | 0 of 10 | 0 of 10 |
| Same-name mother at the same address included automatically | not in corpus | 0 of 3 (2 excluded, 1 to the user) |
| Spouse at the same address included automatically | not in corpus | 0 of 1 (excluded) |
| Unreadable files listed with a reason | 3 of 3 | 3 of 3 |
| Included shared files (other patients' data) flagged | 7 of 7 | 7 of 7 |
| Single-person files wrongly flagged as shared | 0 of 30 | 0 of 27 |
| Record type correct | 36 of 37 | 32 of 34 |
| Confirmation list | 4 (3 target, 1 decoy) | 11 (9 target, 1 mother, 1 decoy) |
| Planned access actions | 30 copies, 7 extracts | 27 copies, 7 extracts |
| Planned erasure actions | 12 delete, 18 retain, 7 edit by hand | 9 delete, 18 retain, 7 edit by hand |
| Wall time | 353 s | 355 s |

Run directories: `run5_main`, `run5_hard`, and `run4_hard_noanswer`. The last is the hard corpus without an answer to the question. It stopped after 85 s in the waiting-for-user state and asked which of the two exact-name intake forms, born 1958 or 1984, is the requester's. That stage did not change between runs 4 and 5. `run5_hard` is the same corpus with the answer given as 1984 through `--choose-dob`.

On the hard corpus, 9 target files went to the user:

- Four recall letters addressed to "Maria Lopez, 18 Birch Lane". Once the mother at the same address is known, they could be for either woman.
- A lab pickup sheet with only the name and a phone number. Since run 5, a file with the exact name and only a phone or address gets the against-check first, because a same-name relative at the same home would match too. The model's against-quote here was the requester's own line, weak evidence, and the rule sends any such quote to the user, which is the safe direction.
- The calendar, two files with the name only in document properties, and a subtitle file with the name only.

Shared files: the main corpus has 8 and the hard corpus 9. The included ones were all flagged. The rest (the calendar, and in the hard corpus the lab sheet) went to the user before any action.

Run 4 differed from run 5 only in that rule. It included the lab sheet automatically, which was correct, and put one more decoy email on the confirmation list instead of excluding it. Files decided by an identifier gave the same result in every run. Files decided by the model's two checks can vary between runs, which is why the checks can send a file to the user or exclude it with a quote, but never include it.

What changed from run 3, and why. A review of the first package against the judging criteria found gaps, and each became a rule:

- Files that also hold other patients' data are handed over as extracts and never deleted. The model is asked to list the people named in a file, with roles. An earlier version asked yes or no, and Qwen3 4B answered no for a sign-in sheet that names three other patients. Asked for a list, it named all three.
- In an erasure request, clinical and billing records are retained by default, with the reason.
- An ID or personal email belongs to one person. A birth date, phone or address can be shared by a household, so it counts only with the exact name. When a same-name person is found, the Skill stops and asks, then excludes that person's identifiers.
- A file with the exact name and only a phone number or address gets the against-check before it is included, because a same-name relative at the same home would match too. The user confirms the identifiers taken from an intake form before they are used; the harness assumes that confirmation.
- Names match in surname-first order and without accents. Phone numbers match by digits. Birth dates match in common formats.
- Every quoted passage must exist in the file. Evidence for inclusion must name the person. An automatic exclusion needs a quote showing a longer name or a same-name person's identifier. A model's opinion alone never includes a file, and never excludes one without such a quote.

The hard corpus was built from that review, and the rules for its cases were written at the same time. It is a stricter test, not a blind one.

## Run 3 (2026-11-07, passage fix only)

Same decisions as run 2. For files decided by an exact identifier match, the passage column holds the line that contains the identifier, the way `collect-evidence` returns its passage. In run 2 the model sometimes quoted a neighbouring spreadsheet row about a different patient: the decision was right but the passage was wrong. 203 s.

## Run 2 (2026-11-07, after the run 1 fixes)

40 of 40 surfaced, 37 included automatically at 37 of 37 precision, 0 of 12 decoys and 0 of 10 noise files included, 3 of 3 unreadable listed, 7-item confirmation list, 350 s.

## Run 1 (same day, before fixes), kept for the record

40 of 40 surfaced, but 0 included automatically. The 4B model wrote reasoning instead of a verdict, and with no identifiers nothing could be confirmed. One unreadable file was dropped from the index. 2053 s. Fixes: structured verdict output, identifiers taken from the exact-name intake form, unreadable files always kept, exact versus partial name matching, intake forms processed first.

## What a NAS run must still answer

- Recall of `collect-evidence` on indexed folders, compared with this harness's exact text match.
- Quality of the Photos index and of document reading on real phone photos and scans, compared with the 2B stand-in.
- Per-file approval flow, the number of approvals in practice, recycle-bin restore, and tag creation.
- Transcription of real recordings. This corpus uses transcript files in their place.
