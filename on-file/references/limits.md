# Limits, stated as measured properties

These are the boundaries of what the Skill does. Where a number is given, it was measured on the synthetic test corpora; where it says pending, it will be measured on the NAS in the final round.

## Measured on the synthetic corpora (laptop stand-in models, run 9, 2026-11-11; to be re-measured on the NAS)

Input was the requester's name only. Stand-ins: Qwen3 4B for text and Qwen3-VL 2B instruct for reading images, through Ollama on a laptop. Voicemails are synthesized speech, transcribed offline. The stand-in runs the Skill's rules as Python code and uses the models for reading, OCR, quotes, checks and classification; whether the NAS assistant follows the same rules from this text is for the final round to show. Three corpora: Lakeside Dental (122 files), a harder Lakeside corpus (129 files) with a same-name mother at the same address and other cases written together with the rules, and Kestrel Bay Physiotherapy (65 files), written blind by a separate agent that never saw the rules.

| Measure | Main | Hard | Blind |
|---|---|---|---|
| Requester's files found (included or sent to the user) | 40 of 40 | 43 of 43 | 30 of 30 |
| Included automatically | 33 | 34 | 18 |
| Wrongly included | 0 | 0 | 0 |
| Look-alike files included (other people, companies, streets) | 0 of 22 | 0 of 26 | 0 of 18 |
| Unreadable files listed with a reason | 3 of 3 | 3 of 3 | 6 of 6 |
| Included files holding others' data, flagged so they are extracted and never deleted | 7 of 7 | 7 of 7 | 6 of 6 |
| Items the user had to decide | 7 | 12 | 16 |

Stress test: with the content search limited to 10 files per search term, the files found, the files included automatically and the wrong inclusions did not change on the main and hard corpora, because the document pass found the 9 files on each corpus that the capped search dropped. The test measures which files are found. Once a file is found, the stand-in reads its identifiers from the full text, as the Skill does from the document pass quote and step 4; only the quotes of the two checks were limited to the search snippets.

The blind corpus was first run before the fixes it led to, and that run is the unbiased one: 18 of 30 found, none included automatically, none wrongly included. It exposed three rule flaws, now fixed: a middle name on the intake form stopped identifiers being adopted; a client named only in the body of meeting minutes was missed by the people list, so another client's ID now also marks a file as shared; and a log listing both same-name women was excluded, so a file with both people's identifiers now goes to the user. In both blind runs under the current rules the text model misread the other Sarah Mitchell's email address on her intake form, so a reminder sent by mistake to her address went to the user instead of being excluded, and a newsletter list holding both women's addresses was included as an extract instead of going to the user. With the address read correctly, as in run 8, that reminder is excluded and missed (29 of 30) and the list goes to the user (17 included). Only the appointment's context shows whose that reminder is.

With a same-name person in the folders and no answer given, the run stops and asks which intake form is the requester's.

Act mode was replayed on a copy of each corpus from the planned actions (`act_replay.py`). In all eight cases (access and erasure on the three corpora and the 28-file demo corpus), only the planned files changed and every other file kept its checksum, a second run acted on nothing, restored files matched their original checksums, and every extract kept only lines that name the person, which is the Skill's extract rule applied by the replay; extracts written by the NAS document expert are checked by the same rule before they are saved. The replays used the approval counts stated above: 38 for the main access case and 9 for the main erasure case.


## Known gaps

- A same-name relative with no form in scope: a file with the exact name and only a phone or address is never included automatically; it goes to the user, listed apart in the closing message.
- Names: the Skill matches the full name in given-first and surname-first order and without accents. Nicknames, former names, transliterations and misspellings are found only if the user supplies them as identifiers. The Skill does not guess variants.
- Scans and photos: reading text in low-quality scans misses names; recall on scans is lower than on text documents, and the index marks which hits came from scanned pages or photos so the user can weigh them.
- Recordings: transcription accuracy depends on recording quality and language; hits from recordings are marked as such.
- Not opened, listed as unreadable with the reason: files inside archives, password-protected and encrypted files, mail stores. Archives are listed by the file expert; files the content search or the document pass could not open are listed with the reason the expert gave.
- Not searched at all: practice-management and billing software, imaging systems such as x-ray archives, the mail server, paper records, and folders outside the scope the user named. The closing message lists the folders searched and reminds the user to check these systems, which in many practices hold most of a patient's record.
- Files that also hold other people's data: the Skill hands over an extract of the person's own entries and never deletes the file. Removing the person's entries from such a file is done by hand; the index lists the passages.
- Retention: clinical and billing records are retained by default in an erasure request. The default is a starting point; the retention period that applies is the user's decision.
- Erasure and backups: deleted files stay in the recycle bin until it is emptied or the recycle window ends, and in NAS snapshots and backups until their schedule removes them. The Skill does not change snapshots or backups.
- Surveillance: face identities and camera events recognised under the person's name are reported for the user to confirm, and footage is copied or removed in the surveillance application; the platform offers a Skill no export or removal action. Recognition under a name cannot separate two people enrolled with the same name, so no camera event is decided automatically, and a person seen but never enrolled is not found. The camera and video searches matter for practices with reception cameras or recorded consultations, where CCTV of an identifiable person is personal data; elsewhere they return nothing quickly.
- Video: the Skill reads subtitle files as text and searches the video library by title and description. The library search covers the whole library; results outside the folders in scope are discarded unread. Speech in a video without a subtitle file is transcribed only when the video is in the recordings list; a person seen but not named in a video is not found.
- Approvals: a report-only run asks for six (two progress saves, saving the index and the enclosure list, drafting and saving the letter), plus one for a translation. An access hand-over asks for one per copy or extract, one per 10 files for the audit log and one for the hand-over folder: 38 for the main test case's 33 records. An erasure asks for one per deletion and one per 10 files for the audit log: 9 for the main test case's 8 deletions. The optional case tag adds up to three; closing a case adds two, three for an access case. Each approval confirms one file the user has already seen on the enclosure list. The platform's copy action takes one file and its batch workflow documents no copy mode, so copies cannot share an approval; deletions are kept to one approval each on purpose, even though a batch deletion exists. The count is stated before the first approval and will be timed on the NAS in the final round.
- Scale: reading documents and scans and transcribing recordings are the slowest searches. Above 2000 documents, 500 scans and images or 200 recordings in a folder, the Skill asks whether to process all, a date range, or none, and records the choice in the index. Above 500 files in scope it also saves progress after each folder, so the candidate list lives in the case folder rather than in the conversation.
- Delegations per run, counted from the steps for the main test corpus (one folder, 122 files: 89 documents, 25 PDFs, 8 images; 58 candidates, 33 included): up to 139 for a report-only run. That is 34 that do not depend on size (listings, searches per name form and identifier, saves, letter), 3 document-pass batches of 20, up to 33 OCR or PDF reads for scans and images not already found, 6 for confirming candidates in batches, 30 for the checks on 15 undecided files, and 33 for listing the people in each included file. An access hand-over then adds about 79 (a check, a copy or an extract per file, the extracts' saves, audit-log writes and the verify step). The document pass grows by one call per 20 documents, and scans and images by one call each, which is why the thresholds above apply to scans first. The laptop stand-in ran the same work in 496 seconds.
- Permissions: the Skill runs with the NAS account of the user who starts it. A folder that account cannot read is listed as not searched. The Skill never changes share or folder permissions; protecting the case folder is a setup step.
- Models: the Skill never calls an outside service, but which model each NAS expert uses is a platform setting. The setup asks the user to confirm the on-device models, for the experts and for the assistant that runs the Skill, and the letter's sentence that records were not sent to an outside service is included only after that confirmation.
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
| Transcription accepts video files (mp4, mov) as well as audio | Videos are still searched by subtitle file and by library title; a video that cannot be transcribed is listed as unreadable |
| One question to the document expert covers every file in a batch of 20 | A file missing from an answer's coverage is asked about again on its own |
| The video library search returns each result's file path | A result without a path is listed by title as "library item, location not confirmed" and never acted on |
| The face list returns identity names | If it returns only face IDs, the camera event search by name still runs; if neither returns names, the surveillance section says "not checked" and the closing message asks the user to check the surveillance application |
| The camera event search filters by a known person's name and returns every event asked for | The count is shown with the results; if events come back under other names, the filter did not apply, and the section says "not checked" instead of listing them |
| The delete action removes a folder with its contents | Each file in the hand-over folder is deleted by path, then the empty folder |
| Writing a file with replace keeps one index file | Each save's returned path is shown, and a re-run reads the newest file whose name starts with the case name followed by index |
- Round 1 is static; all runtime behaviour is validated in the final round on the assigned NAS.

## Not legal advice

The index and letter support the organisation's response. The decision to include, exclude or retain a file, and the final wording of the letter, are the user's.
