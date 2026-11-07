# Limits, stated as measured properties

These are the boundaries of what the Skill does. Where a number is given, it was measured on the synthetic test corpora; where it says pending, it will be measured on the NAS in the final round.

## Measured on the synthetic corpora (laptop stand-in models, 2026-11-07; to be re-measured on the NAS)

Input was the requester's name only. Stand-ins: Qwen3 4B for text and Qwen3-VL 2B instruct for reading images, through Ollama on a laptop. Voicemails are real synthesized audio transcribed offline. Three corpora: Lakeside Dental (122 files), a harder Lakeside corpus (129 files) with a same-name mother at the same address and other cases written together with the rules, and Kestrel Bay Physiotherapy (65 files), written blind by a separate agent that never saw the rules.

| Measure | Main | Hard | Blind |
|---|---|---|---|
| Requester's files found (included or sent to the user) | 40 of 40 | 43 of 43 | 29 of 30 |
| Included automatically | 37 | 34 | 18 |
| Wrongly included | 0 | 0 | 0 |
| Look-alike files included (other people, companies, streets) | 0 of 22 | 0 of 26 | 0 of 18 |
| Unreadable files listed with a reason | 3 of 3 | 3 of 3 | 6 of 6 |
| Included files holding others' data, flagged so they are extracted and never deleted | 7 of 7 | 7 of 7 | 6 of 6 |
| Items the user had to decide | 4 | 12 | 15 |

Stress test: with the content search limited to 10 files per search term and quotes checked against search snippets only, the main and hard results did not change. The document pass found the 9 and 8 files that the capped search dropped.

The blind corpus was first run before the fixes it led to, and that run is the unbiased one: 18 of 30 found, none included automatically, none wrongly included. It exposed three rule flaws, now fixed: a middle name on the intake form stopped identifiers being adopted; a client named only in the body of meeting minutes was missed by the people list, so another client's ID now also marks a file as shared; and a log listing both same-name women was excluded, so a file with both people's identifiers now goes to the user. The one blind file still missed is a reminder sent by mistake to the other woman's email address; only the appointment's context shows whose it is.

With a same-name person in the folders and no answer given, the run stops and asks which intake form is the requester's.


## Known gaps

- Names: the Skill matches the full name in given-first and surname-first order and without accents. Nicknames, former names, transliterations and misspellings are found only if the user supplies them as identifiers. The Skill does not guess variants.
- Scans and photos: reading text in low-quality scans misses names; recall on scans is lower than on text documents, and the index marks which hits came from scanned pages or photos so the user can weigh them.
- Recordings: transcription accuracy depends on recording quality and language; hits from recordings are marked as such.
- Not opened, listed as unreadable with the reason: files inside archives, password-protected and encrypted files, mail stores. Archives are listed by the file expert; files the content search or the document pass could not open are listed with the reason the expert gave.
- Not searched at all: practice-management and billing software, imaging systems such as x-ray archives, the mail server, paper records, and folders outside the scope the user named. The closing message lists the folders searched and reminds the user to check these systems, which in many practices hold most of a patient's record.
- Files that also hold other people's data: the Skill hands over an extract of the person's own entries and never deletes the file. Removing the person's entries from such a file is done by hand; the index lists the passages.
- Retention: clinical and billing records are retained by default in an erasure request. The default is a starting point; the retention period that applies is the user's decision.
- Erasure and backups: deleted files stay in the recycle bin until it is emptied or the recycle window ends, and in NAS snapshots and backups until their schedule removes them. The Skill does not change snapshots or backups.
- Surveillance face identities are reported, not removed; the platform offers no removal action to a Skill.
- Video: the Skill reads subtitle files as text and searches the video library by title and description. The library search covers the whole library; results outside the folders in scope are discarded unread. Speech in a video without a subtitle file is transcribed only when the video is in the recordings list; a person seen but not named in a video is not found.
- Approvals: a report-only run asks for four (saving the index and the enclosure list, drafting and saving the letter), plus one for a translation. An access hand-over asks for one per copy or extract, one per 10 files for the audit log and one for the hand-over folder: 42 for the main test case's 37 records. An erasure asks for one per deletion and one per 10 files for the audit log: 14 for the main test case's 12 deletions. The optional case tag adds up to three; closing an erasure case adds two. Each approval confirms one file the user has already seen on the enclosure list. The platform's copy action takes one file and its batch workflow documents no copy mode, so copies cannot share an approval; deletions are kept to one approval each on purpose, even though a batch deletion exists. The count is stated before the first approval and will be timed on the NAS in the final round.
- Scale: reading scans and transcribing recordings are the slowest searches. Above 500 scans and images or 200 recordings in a folder, the Skill asks whether to process all, a date range, or none, and records the choice in the index.
- Permissions: the Skill runs with the NAS account of the user who starts it. A folder that account cannot read is listed as not searched. The Skill never changes share or folder permissions; protecting the case folder is a setup step.
- Models: the Skill never calls an outside service, but which model each NAS expert uses is a platform setting. The setup asks the user to confirm the on-device models, and the letter's sentence that records were not sent to an outside service is included only after that confirmation.
- Identity: the Skill does not verify who the requester is. Before an access hand-over, the user confirms the identity check was done.
- Search index: the content search depends on the NAS knowledge index covering the folders in scope. A file the index misses is still read by the document pass, but its quote cannot be confirmed by the index, so it goes to the user instead of being decided automatically.
- The audit log is a plain append-only text file with its checksum reported at close. It shows later edits; it does not prevent them.

## Not yet confirmed on a NAS, with the fallback for each

The catalog lists these actions, but what they return has not been seen on a device. Each has a fallback, so an unexpected answer never drops a file silently.

| Assumption | If it does not hold |
|---|---|
| The content search returns every file that contains the exact term, not only the top matches | Every document is also read directly by the document expert in step 2, and every PDF and image in step 3. A file found only by that pass goes to the user unless a content search on that one file confirms its quote. The laptop stress test limits the search to 10 results per term to measure this |
| The document expert reads text in scanned PDF pages | A PDF with no text returned is listed as unreadable, "scanned pages not read", for the user to check |
| The document metadata action returns author and last-modified-by | The index records "properties not read" for the file |
| The photo metadata action returns the image description | The index records "properties not read"; the photo is still searched by its text and by recognised faces |
| The delete returns the file's recycle-bin path | The original path is logged, and a restore looks for the file by name in the share's recycle-bin folder |
| Saving a text file keeps the case name in the file name | The saved path returned by each save is shown at close and recorded in the audit log, and a re-run is pointed at it |
| The photo expert answers a question about an image with a quote | Answers are checked against the OCR text; an answer that cannot be checked sends the photo to the user |
- Round 1 is static; all runtime behaviour is validated in the final round on the assigned NAS.

## Not legal advice

The index and letter support the organisation's response. The decision to include, exclude or retain a file, and the final wording of the letter, are the user's.
