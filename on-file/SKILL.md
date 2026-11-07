---
name: on-file
description: Use when a patient or customer asks what personal data you hold about them or asks to be deleted (HIPAA right of access, GDPR access or erasure). Finds every file in the chosen NAS folders that mentions the person, including scans, photos and recordings, shows the matching passage per file, writes the reply letter and an evidence index, and copies or deletes files only after per-file approval, with an audit log.
---

# Goal

Given one person's name and optional identifiers, produce a complete, checkable answer to a data access or erasure request using only files already on the NAS.

The user-visible result is four plain files saved in a case folder the user names:

1. An evidence index: one row per file that mentions the person, with the matching passage, which identifier matched, how it was confirmed, the checksum before any change, and the decision (included, excluded, needs confirmation, unreadable).
2. A reply letter drafted from the chosen template (HIPAA access, GDPR Art. 15 access, or GDPR Art. 17 erasure). See [request types](references/request-types.md) and [letter templates](references/letter-templates.md).
3. For access requests in act mode: a hand-over folder containing copies of the confirmed files.
4. For erasure requests in act mode: the confirmed files deleted to the recycle bin, and an audit log of every action. See [audit and undo](references/audit-and-undo.md).

Supported scope: documents, spreadsheets, PDFs, scanned PDFs, photos with text, photos of the person recognised by Photos, audio recordings, videos with subtitles, document metadata, file names, and named face identities in the surveillance system (reported only). Out of scope and reported as such: archives, password-protected files, mailboxes, anything outside the chosen folders. See [limits](references/limits.md).

Default mode is report only. No copy or delete happens unless the user chooses act mode, and then each file waits for its own platform approval.

A complete fictional case, with the index, the closing message, the letter and an audit log excerpt, is in [worked example](references/example-output.md).

# Required input

Collect these from the user before any delegation. Stop with `waiting_user` if the request type, the name, the date received, the folders in scope or the case folder is missing.

- Request type: one of HIPAA access, GDPR access, GDPR erasure.
- The person's full name as written in the request.
- The date the request was received. It sets the legal due date shown at every step and goes into the letter.
- Folders in scope: one or more folder paths the user names. Nothing outside them is read.
- Case folder: a folder path where the evidence index, letter and audit log are saved. The user names it; the Skill does not guess a path. It must not be inside a folder in scope. It will hold personal data, so the Skill reminds the user to choose a folder that only the people handling the request can open.
- Mode: report only (default) or act.
- Optional identifiers: email, phone, date of birth, patient or customer ID, postal address, nickname or former name. Each one improves disambiguation. See [disambiguation](references/disambiguation.md).
- Optional: the language the request was written in, if not English.

Do not collect anything a child expert owns (album IDs, tag IDs, face IDs). Child experts resolve those themselves.

# Generation-time capability evidence

- `ug-filesystem` → `file-agent`
- `ug-filemgr` → `file-agent`
- `ug-document` → `document-agent`
- `ug-knowledge` → `knowledge-agent`
- `ug-photo` → `photo-agent`
- `ug-video` → `media-agent`
- `ug-surveillance` → `security-monitor-agent`

# Workflow

Steps 1 to 5 only read. Step 6 creates new files inside the case folder and nowhere else, each through a platform-approved write. Step 7 is the only step that touches the person's files, only in act mode, one file per approval. Each delegation below is self-contained: it repeats the person's name, the identifiers, and the exact folder or file it applies to. Downstream steps use only the real result returned by the upstream delegation; nothing is assumed from a result that was not returned.

Keep running counters and show them after every step, together with the legal due date: folders scanned, files searched, candidates, confirmed, excluded, needs confirmation, unreadable, duplicates.

## Step 1. Candidates by file name

For each folder in scope:

`delegate --target file-agent --instruction 'In the folder the user named, list files whose name contains the person's full name, surname, or any identifier the user supplied. Search recursively. Return path, size and modified time for each match. If nothing matches, return an empty list and say so.'`

Add every returned path to the candidate list with source "file name".

## Step 2. Candidates by content

For each folder in scope and for each identifier (full name first, then email, phone, ID, address, nickname):

`delegate --target knowledge-agent --instruction 'Collect evidence from the folder the user named for the exact identifier given. Return every file that contains it, with the matching passage and the file path. Do not widen the search to similar names. If there are no results, say no results.'`

Add every returned path with source "content" and the identifier that matched. Merge duplicates by path; keep all identifiers that matched a path.

## Step 3. Candidates in photos, scans, video and audio

Run these once per folder in scope. Each may return an empty result; record that and continue.

`delegate --target photo-agent --instruction 'Search pictures whose OCR text contains the person's full name, and separately pictures where the recognised person name equals the person's full name, limited to the folder the user named. Return file paths and, for OCR hits, the matched text. Return no results if there are none.'`

Video subtitles are searched one video at a time, so list the videos first:

`delegate --target file-agent --instruction 'List the video files (mp4, mkv, mov, avi) in the folder the user named, recursively. Return their paths. If there are none, return an empty list.'`

For each returned video:

`delegate --target media-agent --instruction 'Search the subtitles of the video at the given path for the person's full name. Return the matching subtitle lines with their times, or say no results.'`

Audio is transcribed from a list of paths, so list the recordings first:

`delegate --target file-agent --instruction 'List the audio files (m4a, mp3, wav, aac, amr, ogg) in the folder the user named, recursively. Return their paths and modified times. If there are none, return an empty list.'`

`delegate --target knowledge-agent --instruction 'Transcribe the audio files at the given paths. For each file, report whether the transcript contains the person's full name or any identifier listed, and return the path and the matching sentence. List any file that could not be transcribed with the reason. Return no results if nothing matches.'`

Transcription is the slowest search. If a folder holds more than 200 audio or video files, show the count and ask the user whether to process all of them, only those modified in a date range, or leave that media type out of this run; record the choice in the index.

`delegate --target security-monitor-agent --instruction 'List the known face identities in the surveillance system and report whether any identity name equals the person's full name. Read only. Return the identity name and the cameras it appears on, or no results.'`

Surveillance hits are not files. Record them in a separate "surveillance" section of the evidence index for manual action; the Skill never changes surveillance data.

If, after steps 1 to 3, the candidate list is empty for every folder, write an evidence index with zero rows and the counters, save it to the case folder (step 6), report "no files found in scope", and stop. Do not search other folders.

## Step 4. Confirm each candidate and read the passage

For each candidate file that is a document, spreadsheet or PDF:

`delegate --target document-agent --instruction 'Open the file at the given path. Answer: does this file mention the person's full name or any of the identifiers listed? Quote the exact passage. If the file cannot be opened or read, say unreadable and give the reason.'`

Also read the document properties:

`delegate --target document-agent --instruction 'Return the metadata of the file at the given path: author, last modified by, title, subject, keywords. Report whether any field contains the person's full name.'`

For each candidate that is a photo or scanned image not already confirmed by OCR text:

`delegate --target photo-agent --instruction 'Run OCR on the image at the given path and return all text. Then report whether the text contains the person's full name or any identifier listed, quoting the matched line.'`

For every photo candidate, also read the image's own fields, because a caption can name the person when the picture shows no text:

`delegate --target photo-agent --instruction 'Return the metadata of the image at the given path, including description, caption, title, author and keywords. Report whether any field contains the person's full name or any identifier listed.'`

Outcomes per file:

- Passage found: mark "confirmed candidate" and keep the passage and the matched identifiers.
- No mention found on close reading: mark "excluded, no mention".
- Unreadable: mark "unreadable" with the reason. Never drop it from the index.

## Step 5. Disambiguate same-name people

Apply the rules in [disambiguation](references/disambiguation.md). Process intake, registration or consent forms first, because they carry the identifiers that let every later file be decided automatically.

- A file where the exact full name co-occurs with at least one strong identifier (email, phone, date of birth, patient or customer ID, full postal address) is "included, auto".
- A file where the name appears only as part of a longer name (for example a hyphenated surname that begins with the requester's surname) is never auto-included; it goes through the two checks and, at best, to the confirmation list.
- A file where only the name matches gets two opposing checks:

`delegate --target document-agent --instruction 'Open the file at the given path. Quote every passage that shows the person named is the same person as the one described by the identifiers listed. If there is none, say none.'`

`delegate --target document-agent --instruction 'Open the file at the given path. Quote every passage that shows the person named is a different person from the one described by the identifiers listed, for example a different date of birth, address, email, phone, employer or role. If there is none, say none.'`

If the second check returns none and the first returns a passage: "included, auto, skeptic clear". If the first returns none and the second returns a passage: "excluded, skeptic found a different person", with the quote kept. Every other combination is "needs confirmation" with both quotes. The user decides each item on that list; nothing on it is acted on until the user says include or exclude.

- When the request arrived with a name only, no file can be auto-included yet. Read the exact-name intake, registration or consent forms first with the extraction below. If exactly one form's extracted full name equals the requester's name, adopt its identifiers and continue. If more than one such form exists with different dates of birth, stop with `waiting_user` and show them: the user picks the requester's form.
- When the first "included" file is an intake or registration form, run once:

`delegate --target document-agent --instruction 'Extract from the file at the given path the fields: full name, date of birth, email, phone, postal address, patient or customer ID. Return them as a list.'`

Add new identifiers to the set and re-run step 2 for the new identifiers only.

## Step 6. Duplicates, evidence index and letter

The first two delegations only read:

`delegate --target file-agent --instruction 'Scan the folders the user named for duplicate files. Return groups of byte-identical files with their paths.'`

Any file identical to an included file joins the included set with source "duplicate of" and the original path.

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run this for the included files and for a sample of up to 20 files in scope that are not included. These checksums go into the index, so the state before any change is saved before step 7 starts.

The remaining delegations write new files into the case folder only; each one asks for the platform's approval.

`delegate --target knowledge-agent --instruction 'Save a text file named by the case name in the case folder the user named. Content: the evidence index table with columns path, source, matched identifiers, passage, confirmation, decision, decided by, sha256 before; then the surveillance section; then the unreadable list; then the counters and the legal due date.'`

Draft the letter from the template for the request type:

`delegate --target document-agent --instruction 'Draft a formal reply letter using the template text given, filling the person's name, the request type, the date received, the number of files found, and the list of file descriptions from the evidence index. Keep the template wording; add nothing not in the index.'`

If the request language is not English:

`delegate --target document-agent --instruction 'Translate the letter text given into the requested language, keeping the structure and all file descriptions unchanged.'`

Save the letter with `knowledge-agent` the same way as the index. If the drafting delegation returns `failed` or `cancelled`, save the unfilled template plus the index instead and say that the letter was not drafted.

In report-only mode, show the counters, the legal due date, the path of the index and the letter, the needs-confirmation list, the unreadable list and the surveillance finding, and stop.

## Step 7. Act, one file at a time (act mode only)

Only files whose decision is "included" are acted on. Files on the needs-confirmation list that the user did not confirm are not touched.

Before the first action, tell the user how many approvals to expect: one per file, plus one per audit log checkpoint, plus one for the hand-over folder and one for the case tag.

First, for access requests:

`delegate --target file-agent --instruction 'Create a folder named hand-over inside the case folder the user named.'`

Then for each included file, in order:

- Check first: `delegate --target file-agent --instruction 'Return the size and modified time of the file at the given path, or say not found.'` For erasure, a path that is already not found is logged as "already done" and not acted on again. For access, the same check on the copy's path inside the hand-over folder tells whether it was already copied.
- Access: `delegate --target file-agent --instruction 'Copy the file at the given path into the hand-over folder inside the case folder. Do not move or overwrite.'`
- Erasure: `delegate --target file-agent --instruction 'Delete the file at the given path.'`

After every 10 files acted on, when the user stops the run, and at the end, append the new lines to the audit log in the case folder:

`delegate --target file-agent --instruction 'Append the lines given to the audit log file in the case folder the user named, creating the file if it does not exist. Do not overwrite existing lines.'`

Each line holds time, action, path, sha256 before, result state, approval state and note. See [audit and undo](references/audit-and-undo.md). Because the checksums are already in the saved index and every file is checked before it is acted on, a run that stops between checkpoints can be re-run with the same case name without acting on any file twice.

At the end, tag the case so it can be found later:

- Access: `delegate --target file-agent --instruction 'Create a tag named dsar followed by the case date and the case name if it does not exist, then add it to every file in the list given.'` The list is the originals that were copied.
- Erasure: the same delegation, with the evidence index file and the audit log in the case folder as the list, since the deleted files are gone.

A file that returns `waiting_approval` stays pending while the next file proceeds; it is logged as pending and revisited at the end. A file that returns `cancelled` is logged as "declined by user" and is not retried in this run. A file that returns `failed` is logged with the reason and the run continues with the next file.

## Step 8. Verify and close

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run on the not-included sample from step 6. Report "untouched files verified: N of N unchanged" or list any difference. For erasure, confirm each deleted path no longer exists by asking file-agent for its size and modified time and expecting a not-found result.

Close with: counters; approvals asked, approved, declined and pending; the legal due date and the days left; the paths of the index, letter and audit log; the needs-confirmation items the user still has to decide; the unreadable files the user must check by hand; the surveillance identity to remove manually, if any; and for erasure, the sentence "Deleted files are in the recycle bin and can be restored by path within the recycle window; tell me a path to restore it."

# Completion and failure

Report a business result only after the delegated expert returns `completed`. Treat every other state as a state, not a result:

- `completed`: use the returned content. If it is an empty result, record "no results" for that folder or file and continue; never substitute a similar folder, name or data source.
- `failed`: record the failure and reason against that folder or file in the evidence index. The run continues with the remaining items. A folder the user's account cannot read returns `failed` and is listed as not searched. If every folder in scope fails in steps 1 to 3, stop and report that no search could be completed.
- `cancelled`: record "cancelled by user" for that item. In step 7 the file is left as it was. Dependent steps for that item do not run.
- `waiting_user`: stop and ask for the missing input. Nothing is assumed.
- `waiting_approval`: the item is pending. Report it as pending, continue with items that do not depend on it, and list all pending items at close.

Partial results are always saved: the evidence index, with the checksums, is written in step 6 before any change, and the audit log is appended at every checkpoint, so an interrupted act run can be inspected and resumed by re-running with the same case name.

Never report "all files found" or "deleted". Report exact counts: found, confirmed, excluded, needs confirmation, unreadable, duplicates, acted on, already done, pending, declined, failed.

The output supports the controller's response to the request; it is not legal advice. The user is responsible for deciding the needs-confirmation items and for checking the unreadable files by hand.

Third-party components, the work developed for this Hackathon, and the AI tools used are listed in [disclosure](references/disclosure.md).

# Install, setup, removal and testing

The package is Markdown only and installs through the AI assistant's Skills page or the Skills Hub; nothing is downloaded or configured. Setup is four NAS settings to check once: recycle bin on the shares in scope, knowledge index and Photos index covering the folders in scope, and a case folder that only the people handling requests can open. Removal leaves only what the user asked for: case folders, case tags and recycle-bin entries. Testing uses a published 122-file synthetic corpus with ground truth and a scorer, with two core cases (access, erasure with integrity check) and one edge case (same-name decoys and unreadable files). Steps, expected results and the version history are in [install, setup, removal and testing](references/install-and-testing.md).
