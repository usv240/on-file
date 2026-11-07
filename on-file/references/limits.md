# Limits, stated as measured properties

These are the boundaries of what the Skill does. Where a number is given, it was measured on the synthetic test corpus; where it says pending, it will be measured on the NAS in the final round.

## Measured on the synthetic corpus (laptop stand-in models, 2026-11-07; to be re-measured on the NAS)

Corpus of 122 files for a fictional dental practice; input was the requester's name only. Stand-ins: Qwen3 4B for text, Qwen3-VL 2B for OCR.

- Files mentioning the requester shown to the user: 40 of 40 (37 included automatically, 3 sent to the confirmation list because the name appeared without any identifier).
- Precision of automatically included files: 37 of 37.
- Same-surname decoy files (a different patient, Maria Lopez-Ruiz) included automatically: 0 of 12; 9 excluded by the skeptic check, 3 sent to the confirmation list.
- Files containing "Lopez" that are a company, a staff member or a street: 0 of 10 included automatically.
- Unreadable files reported as unreadable: 3 of 3.
- Confirmation list the user had to decide: 7 items.
- Time: about 3.5 minutes for 122 files on a laptop, of which 16 image OCRs took about 105 seconds.

## Known gaps

- Nicknames, transliterations and misspellings are found only if the user supplies them as identifiers. The Skill does not guess variants.
- OCR on low-quality scans misses names; recall on scans is lower than on text documents, and the index marks which hits came from OCR so the user can weigh them.
- Audio transcription accuracy depends on recording quality and language; audio hits are marked as such.
- Files inside archives, password-protected files, encrypted files and mail stores are not opened. They are listed as unreadable with the reason.
- Folders outside the scope the user named are never searched, even if the Skill suspects more files exist elsewhere. The closing message says which folders were searched.
- Surveillance face identities are reported, not removed; the catalog has no removal action.
- Approvals: act mode asks for one approval per file acted on, plus one per audit-log checkpoint (every 10 files), one for the hand-over folder and one for the case tag. Step 6 asks for one approval per saved file and one for the letter draft. Whether one approval can cover several calls is not documented; the count is stated to the user before the first approval and measured on the NAS in the final round.
- Audio and video: transcription is the slowest search. Above 200 media files in a folder the Skill asks whether to process all, a date range, or none, and records the choice in the index.
- Permissions: the Skill runs with the NAS account of the user who starts it. A folder that account cannot read is listed as not searched. The Skill never changes share or folder permissions; protecting the case folder is the user's setup step.
- The content search depends on the NAS knowledge index covering the folders in scope. Files not yet indexed are still caught by the file-name search and, for images, by OCR, but a very recent text document may be missed until indexed. The Skill says this in the closing message when a scope folder returned no content hits but did return file-name hits.
- Round 1 is static; all runtime behaviour is validated in the final round on the assigned NAS.

## Not legal advice

The index and letter support the organisation's response. The decision to include, exclude or retain a file, and the final wording of the letter, are the user's.
