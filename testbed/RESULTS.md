# Stand-in results (laptop, not the NAS)

These numbers come from `standin_run.py` replaying the Skill's workflow on a laptop with Qwen3 4B (text) and Qwen3-VL 2B instruct (reading images) through Ollama, as stand-ins for the NAS models. They are provisional. All three corpora will be re-run on the iDX6011 Pro in Round 2 and these numbers replaced. Every number below is produced by `summarize.py` from the run folders named in the table.

Input to every run: the requester's name only, no other identifiers, the way most requests arrive. Voicemails in the two Lakeside corpora are synthesized speech: `audio_roundtrip.ps1` speaks each one with an offline Windows voice and transcribes the recording with the offline Windows recognizer.

## Current results (runs 7 and 8, 2026-11-07)

| Measure | Main | Hard | Blind | Main, stress | Hard, stress |
|---|---|---|---|---|---|
| Files in scope | 122 | 129 | 65 | 122 | 129 |
| Requester's files found (included or sent to the user) | 40 of 40 | 43 of 43 | 29 of 30 | 40 of 40 | 43 of 43 |
| Included automatically | 37 | 34 | 18 | 37 | 34 |
| Wrongly included | 0 | 0 | 0 | 0 | 0 |
| Look-alike files included (other people, companies, streets) | 0 of 22 | 0 of 26 | 0 of 18 | 0 of 22 | 0 of 26 |
| Unreadable files listed with a reason | 3 of 3 | 3 of 3 | 6 of 6 | 3 of 3 | 3 of 3 |
| Included files holding others' data, flagged | 7 of 7 | 7 of 7 | 6 of 6 | 7 of 7 | 7 of 7 |
| Single-person files wrongly flagged as shared | 0 of 30 | 0 of 27 | 0 of 12 | 0 of 30 | 0 of 27 |
| Items left for the user to decide | 4 | 12 | 15 | 4 | 11 |
| Files added by the document pass | 0 | 0 | 0 | 9 | 8 |
| Wall time, seconds | 504 | 556 | 322 | 539 | 574 |
| Run folder | `run8_main` | `run8_hard` | `run8_blind` | `run7_main_stress` | `run7_hard_stress` |

- Main and hard: the two Lakeside Dental corpora. The hard corpus adds a same-name mother at the same address, a spouse, an accented name, a surname-first name with a differently written phone number, and a subtitle file. Its cases were written together with the rules that handle them, so it is a stricter test, not a blind one.
- Blind: Kestrel Bay Physiotherapy, written by a separate agent that was not allowed to read the Skill, the rules or the other corpora. See `blind/README.md`.
- Stress: the content search limited to 10 files per search term, as an index that returns only its best matches would, and quotes from documents checked against the search snippets only. The cap dropped 32 name hits and 8 ID hits on the main corpus and 37 and 8 on the hard corpus. The document pass found every file the capped search left out, so the results match the full runs. The stress runs use run 7 code; run 8 changed only the shared-file check and the same-name rule, which the stress test does not measure.
- Same-name question: with no answer given, both the hard and the blind corpus stop in the waiting-for-user state and ask which intake form is the requester's (`run4_hard_noanswer`, born 1958 or 1984; `run7_blind_noanswer`, born 1961 or 1983, after 68 seconds). The runs above give that answer through `--choose-dob`.

## Act mode, replayed

`act_replay.py` carries out the planned copies, extracts and deletions from each run's index on a copy of the corpus, writes the audit log at the Skill's checkpoints, runs the same case a second time, restores one deleted file and checks every file in scope by sha256. It tests the plan and the bookkeeping, not the NAS file actions.

| Case | Acted on | Deleted equals planned | Other files changed or added | Second run acted on | Restore matches | Approvals |
|---|---|---|---|---|---|---|
| Main, access | 30 copies, 7 extracts | none planned | 0 | 0 | none deleted | 42 |
| Main, erasure | 12 deleted; 18 retained and 7 for editing by hand left untouched | yes | 0 | 0 | yes | 14 |
| Hard, access | 27 copies, 7 extracts | none planned | 0 | 0 | none deleted | 39 |
| Hard, erasure | 9 deleted | yes | 0 | 0 | yes | 10 |
| Blind, access | 12 copies, 6 extracts | none planned | 0 | 0 | none deleted | 21 |
| Blind, erasure | 3 deleted | yes | 0 | 0 | yes | 4 |

No extract held a line that does not name the person. The approval counts are the ones the Skill states before act mode: one per action, one per 10 actions for the audit log, and one for the hand-over folder.

## How the laptop stand-in differs from the NAS

The harness runs the Skill's rules as Python code: name and identifier matching, the quote check, the decision table and the planned actions. The models do what the NAS experts would do: read documents, OCR images, quote passages, run the two checks, extract identifiers and list the people in a file. On the NAS the assistant follows the same rules from SKILL.md, and whether it does so as reliably is for the final round to show. The content search is an exact text match here; the stress runs show what happens when it returns only its best matches.

## The blind corpus, before and after

The first run on the blind corpus is kept exactly as it came out (`run6_blind_noanswer`).

| Measure | First blind run | After fixes |
|---|---|---|
| Requester's files found | 18 of 30 | 29 of 30 |
| Included automatically | 0 | 18 |
| Wrongly included | 0 | 0 |
| Look-alike files included | 0 of 18 | 0 of 18 |
| Included shared files flagged | none included | 6 of 6 |

The first run was safe, since nothing was wrongly included, but it was of little use. It exposed one flaw in the Skill's rules and several in the laptop stand-in:

- Rule flaw: the request said "Sarah Mitchell" and her intake form said "Sarah Louise Mitchell". The rule required the form's name to equal the request exactly, so her identifiers were never adopted and the other Sarah Mitchell's form ("Sarah Jane Mitchell") was never seen. A middle name or initial now counts as the name, and forms are compared on given name and surname.
- Rule flaw, found after the first fix: staff meeting minutes named another client only in a sentence, and the model listed only the four staff present. The file would have been handed over whole. An ID of the same form as the requester's, other than hers, now marks a file as shared, independently of the names.
- Rule flaw: a reminder log listing both women, each with her own phone number, was excluded as the other woman's. A file with the other person's identifiers now goes to the user if it also holds one of the requester's own.
- Stand-in flaws: the reasoning variant of the 2B vision model spent its whole budget thinking and returned empty text for most of the blind corpus's images, so it was replaced by the instruct variant of the same size. The harness also missed Word page headers, UTF-16 text files, underscores in file names, a caption-only photo, and a damaged image crashed it.

Once these were fixed, the blind corpus is no longer blind for this version of the rules. The "after" column shows what the fixes bought, not an unbiased score; the first column is the unbiased one. The main and hard corpora were re-run on the final code and did not lose anything.

One target is still missed: a reminder about the requester's appointment that was sent by mistake to the other Sarah Mitchell's email address. It carries the other woman's email and no identifier of the requester, so the rules exclude it as hers, with the quote in the index. Only the appointment's context (shoulder, not knee) shows whose it is. It is listed as a known limit rather than answered with a rule tuned to this one file.

The other 11 blind items sent to the user include the requester's maiden-name notes (found through her date of birth and phone), a misspelt "Sara Mitchel" message (found through her phone), her husband's invoice at the same address, a family doctor who is also called Sarah Mitchell, and a memorial award named after a different Sarah Mitchell. Each is decided by the user with the evidence for and against shown.

## Earlier runs

- Run 5 (Lakeside only, before the document pass and spoken voicemails): the same main and hard results as run 8.
- Run 4: added the shared-file, retention, household and quote-check rules and the hard corpus, after a first review against the judging criteria.
- Run 3: the passage column holds the line that contains the identifier, as `collect-evidence` returns it; before that the model sometimes quoted a neighbouring row.
- Run 2: 40 of 40 found, 37 included automatically, none wrong, 350 s.
- Run 1: 40 of 40 found but 0 included automatically, because the 4B model wrote reasoning instead of a verdict and nothing could be confirmed from a name alone; one unreadable file was dropped. Fixed with structured output, identifiers taken from the intake form, unreadable files always kept, and exact versus partial names.

## What a NAS run must still answer

- Recall of `collect-evidence` on indexed folders, and whether it returns every exact match or only the best ones; the stress runs show the document pass covers the second case.
- The NAS OCR and Photos index on real phone photos and scans, compared with the 2B stand-in.
- Per-file approval flow, the number of approvals in practice, recycle-bin restore, and tag creation.
- Transcription of real phone recordings; the laptop test used synthesized speech.
