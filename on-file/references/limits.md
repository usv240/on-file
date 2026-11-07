# Limits, stated as measured properties

These are the boundaries of what the Skill does. Where a number is given, it was measured on the synthetic test corpora; where it says pending, it will be measured on the NAS in the final round.

## Measured on the synthetic corpora (laptop stand-in models, 2026-11-07; to be re-measured on the NAS)

Input was the requester's name only, the way most requests arrive. Stand-ins: Qwen3 4B for text and Qwen3-VL 2B for reading images, through Ollama on a laptop. The main corpus has 122 files; the hard corpus has 129 and adds the requester's mother with the same name at the same address, a spouse, an accented name, a surname-first name with a differently written phone number, and a subtitle file. The hard corpus's cases and the rules that handle them were written together, so it is a stricter test, not a blind one.

| Measure | Main corpus | Hard corpus |
|---|---|---|
| Files about the requester shown to the user | 40 of 40 | 43 of 43 |
| Included automatically | 37 | 35 |
| Automatically included files that were wrong | 0 | 0 |
| Look-alike files included automatically (longer name, company, staff member, street, same-name mother, spouse) | 0 of 22 | 0 of 26 |
| Unreadable files listed with a reason | 3 of 3 | 3 of 3 |
| Files holding other patients' data flagged, so they are extracted and never deleted | 7 of 7 | 8 of 8 |
| Single-person files wrongly flagged as shared | 0 of 30 | 0 of 27 |
| Record type correct (drives the retention default) | 36 of 37 | 33 of 35 |
| Items the user had to decide | 4 | 11 |
| Time on a laptop | about 6.5 minutes | about 6.5 minutes |

The hard corpus's longer confirmation list is the intended behaviour: once a same-name mother at the same address is known, a letter addressed to "Maria Lopez, 18 Birch Lane" could be for either of them, and only a person can tell. The same corpus without an answer stopped after about 1.5 minutes and asked which of the two intake forms, born 1958 or 1984, is the requester's.

Earlier versions and what each fixed are recorded with the test corpora.

## Known gaps

- Names: the Skill matches the full name in given-first and surname-first order and without accents. Nicknames, former names, transliterations and misspellings are found only if the user supplies them as identifiers. The Skill does not guess variants.
- Scans and photos: reading text in low-quality scans misses names; recall on scans is lower than on text documents, and the index marks which hits came from scanned pages or photos so the user can weigh them.
- Recordings: transcription accuracy depends on recording quality and language; hits from recordings are marked as such.
- Not opened, listed as unreadable with the reason: files inside archives, password-protected and encrypted files, mail stores.
- Not searched at all: practice-management and billing software, imaging systems such as x-ray archives, the mail server, paper records, and folders outside the scope the user named. The closing message lists the folders searched and reminds the user to check these systems, which in many practices hold most of a patient's record.
- Files that also hold other people's data: the Skill hands over an extract of the person's own entries and never deletes the file. Removing the person's entries from such a file is done by hand; the index lists the passages.
- Retention: clinical and billing records are retained by default in an erasure request. The default is a starting point; the retention period that applies is the user's decision.
- Erasure and backups: deleted files stay in the recycle bin until it is emptied or the recycle window ends, and in NAS snapshots and backups until their schedule removes them. The Skill does not change snapshots or backups.
- Surveillance face identities are reported, not removed; the platform offers no removal action to a Skill.
- Video: the Skill reads subtitle files as text and searches the video library by title and description. The library search covers the whole library; results outside the folders in scope are discarded unread. Speech in a video without a subtitle file is transcribed only when the video is in the recordings list; a person seen but not named in a video is not found.
- Approvals: act mode asks for one approval per copy, extract or deletion, plus one per audit-log checkpoint (every 10 files), one for the hand-over folder and up to two for the case tag; the main test case comes to 44. A report-only run asks for four: saving the index, saving the enclosure list, drafting the letter and saving the letter, plus one for a translation. One approval per file is deliberate even though the platform offers a batch deletion: each copy discloses a record to someone outside the practice and each deletion removes one. The count is stated before the first approval and will be timed on the NAS in the final round.
- Scale: reading scans and transcribing recordings are the slowest searches. Above 500 scans and images or 200 recordings in a folder, the Skill asks whether to process all, a date range, or none, and records the choice in the index.
- Permissions: the Skill runs with the NAS account of the user who starts it. A folder that account cannot read is listed as not searched. The Skill never changes share or folder permissions; protecting the case folder is a setup step.
- Models: the Skill never calls an outside service, but which model each NAS expert uses is a platform setting. The setup asks the user to confirm the on-device models.
- Search index: the content search depends on the NAS knowledge index covering the folders in scope. A file not yet indexed is caught only if its name or folder contains the person's name, or, for scans and images, by the reading pass; a new text document with an unrelated name is missed until indexed. The Skill says this in the closing message when a scope folder returned no content hits but did return file-name hits.
- The audit log is a plain append-only text file with its checksum reported at close. It shows later edits; it does not prevent them.
- Round 1 is static; all runtime behaviour is validated in the final round on the assigned NAS.

## Not legal advice

The index and letter support the organisation's response. The decision to include, exclude or retain a file, and the final wording of the letter, are the user's.
