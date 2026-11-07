# On File testbed

A synthetic dental practice ("Lakeside Dental") used to measure the On File Skill. Every name, address, phone number and ID is invented. The corpus is deterministic: the same seed produces byte-identical files, so `expected.json` always matches.

## What is in it

| Group | Files | Purpose |
|---|---|---|
| target | 40 | Mention the requester, Maria Lopez (DOB 1984-03-12, LD-10432). Mix of docx, xlsx, text PDF, image-only scanned PDF, phone photo of a sign-in sheet, email exports, voicemail transcripts, two files where the name is only in document metadata, one photo where the name is only in the EXIF caption, one calendar where the name appears with no identifier |
| decoy | 12 | Mention a different patient with an overlapping name, Maria Lopez-Ruiz (DOB 1991-07-30, LD-11871). None of these may be auto-included |
| noise | 10 | Contain "Lopez" but are not a patient: Lopez Construction invoices, staff member Mario Lopez, Lopez Avenue addresses |
| unreadable | 3 | A password-protected PDF and a truncated docx that mention the requester but cannot be opened, and a blank scanned page. All three must appear in the index as unreadable, never be silently skipped |
| background | about 60 | Other patients, suppliers, policies, reception photos |

## Build

    python make_corpus.py --out corpus

Writes `corpus/lakeside-dental/` and `corpus/expected.json`.

## Measure a run

1. Before an erasure run: `python score.py hash corpus/lakeside-dental before.json`
2. Run the Skill on the NAS with the folder in scope and the case folder outside the corpus. In act mode, approve each deletion. Save the evidence index the Skill writes.
3. Convert the index to a tab-separated file with at least the columns `path` and `decision` (included, excluded, needs confirmation, unreadable). Paths relative to `lakeside-dental/`.
4. `python score.py score corpus/expected.json evidence.tsv`
5. After an erasure run: `python score.py verify corpus/lakeside-dental before.json`. Expected: exactly the included files deleted, zero changed, zero added.

## The numbers we report

- Recall (surfaced): target files the Skill showed to the user, included or needs confirmation, out of 40
- Precision of auto-included files
- Decoy auto-included: must be 0 of 12
- Noise auto-included: must be 0 of 10
- Unreadable reported: must be 3 of 3
- Integrity after erasure: deleted = included set, changed = 0, added = 0

## Notes

- Voicemail files are text transcripts standing in for audio. On the NAS, replace them with short recordings so the audio transcription step is exercised for real.
- The calendar file mentions both Maria Lopez and Maria Lopez-Ruiz with no identifiers. It tests that the Skill asks before including a name-only hit.
- The two metadata-only files test that document properties are read, not only body text.
- Use of this corpus by other entrants to test their own Skills is welcome.
