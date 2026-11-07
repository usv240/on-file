---
name: on-file
description: Use when a patient or customer asks what personal data you hold about them or asks to be deleted (HIPAA right of access, GDPR access or erasure). Finds every file in the chosen NAS folders that mentions the person, including scans, photos and recordings, shows the matching passage per file, writes the reply letter and an evidence index, and copies or deletes files only after per-file approval, with an audit log.
---

# Goal

Given one person's name and optional identifiers, produce a complete, checkable answer to a data access or erasure request using only files already on the NAS.

The user-visible result is four plain files saved in a case folder the user names:

1. An evidence index: one row per file that mentions the person, with the matching passage, which identifier matched, how it was confirmed, and the decision (included, excluded, needs confirmation, unreadable).
2. A reply letter drafted from the chosen template (HIPAA access, GDPR Art. 15 access, or GDPR Art. 17 erasure). See [request types](references/request-types.md) and [letter templates](references/letter-templates.md).
3. For access requests in act mode: a hand-over folder containing copies of the confirmed files.
4. For erasure requests in act mode: the confirmed files deleted to the recycle bin, and an audit log with the hash of every file before it was touched. See [audit and undo](references/audit-and-undo.md).

Supported scope: documents, spreadsheets, PDFs, scanned PDFs, photos with text, photos of the person recognised by Photos, audio recordings, videos with subtitles, document metadata, file names, and named face identities in the surveillance system (reported only). Out of scope and reported as such: archives, password-protected files, mailboxes, anything outside the chosen folders. See [limits](references/limits.md).

Default mode is report only. No copy or delete happens unless the user chooses act mode, and then each file waits for its own platform approval.

A complete fictional case, with the index, the closing message, the letter and an audit log excerpt, is in [worked example](references/example-output.md).

# Required input

Collect these from the user before any delegation. Stop with `waiting_user` if the first three are missing.

- Request type: one of HIPAA access, GDPR access, GDPR erasure.
- The person's full name as written in the request.
- Folders in scope: one or more folder paths the user names. Nothing outside them is read.
- Case folder: a folder path where the evidence index, letter and audit log are saved. The user names it; the Skill does not guess a path.
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

Steps 1 to 6 are read only. Step 7 is the only step that changes state, and only in act mode. Each delegation below is self-contained: it repeats the person's name, the identifiers, and the exact folder it applies to. Downstream steps use only the real result returned by the upstream delegation; nothing is assumed from a result that was not returned.

Keep running counters and show them after every step: folders scanned, files searched, candidates, confirmed, excluded, needs confirmation, unreadable, duplicates.

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

`delegate --target media-agent --instruction 'Search subtitles of videos in the folder the user named for the person's full name. Return video path and the matching subtitle lines. Return no results if there are none.'`

`delegate --target knowledge-agent --instruction 'For each audio file in the folder the user named, transcribe it and report whether the transcript contains the person's full name or any identifier the user supplied. Return path and the matching sentence. Return no results if there are none.'`

`delegate --target security-monitor-agent --instruction 'List named face identities in the surveillance system and report whether any identity name equals the person's full name. Read only. Return the identity name and the cameras it appears on, or no results.'`

Surveillance hits are not files. Record them in a separate "surveillance" section of the evidence index for manual action; the Skill never changes surveillance data.

If, after steps 1 to 3, the candidate list is empty for every folder, write an evidence index with zero rows and the counters, save it to the case folder (step 6), report "no files found in scope", and stop. Do not search other folders.

## Step 4. Confirm each candidate and read the passage

For each candidate file that is a document, spreadsheet or PDF:

`delegate --target document-agent --instruction 'Open the file at the given path. Answer: does this file mention the person's full name or any of the identifiers listed? Quote the exact passage. If the file cannot be opened or read, say unreadable and give the reason.'`

Also read the document properties:

`delegate --target document-agent --instruction 'Return the metadata of the file at the given path: author, last modified by, title, subject, keywords. Report whether any field contains the person's full name.'`

For each candidate that is a photo or scanned image not already confirmed by OCR text:

`delegate --target photo-agent --instruction 'Run OCR on the image at the given path and return all text. Then report whether the text contains the person's full name or any identifier listed, quoting the matched line.'`

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

If the second check returns none and the first returns a passage: "included, auto, skeptic clear". If the second check returns anything: "needs confirmation" with both quotes. The user decides each item on that list; nothing on it is acted on until the user says include or exclude.

- When the request arrived with a name only, no file can be auto-included yet. Read the exact-name intake, registration or consent forms first with the extraction below. If exactly one form's extracted full name equals the requester's name, adopt its identifiers and continue. If more than one such form exists with different dates of birth, stop with `waiting_user` and show them: the user picks the requester's form.
- When the first "included" file is an intake or registration form, run once:

`delegate --target document-agent --instruction 'Extract from the file at the given path the fields: full name, date of birth, email, phone, postal address, patient or customer ID. Return them as a list.'`

Add new identifiers to the set and re-run step 2 for the new identifiers only.

## Step 6. Duplicates, evidence index and letter

`delegate --target file-agent --instruction 'Scan the folders the user named for duplicate files. Return groups of byte-identical files with their paths.'`

Any file identical to an included file joins the included set with source "duplicate of" and the original path.

Then record a baseline for verification:

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run this for the included files and for a sample of up to 20 files in scope that are not included.

Write the evidence index:

`delegate --target knowledge-agent --instruction 'Save a text file named by the case name in the case folder the user named. Content: the evidence index table with columns path, source, matched identifiers, passage, confirmation, decision, decided by; then the surveillance section; then the unreadable list; then the counters.'`

Draft the letter from the template for the request type:

`delegate --target document-agent --instruction 'Write a reply letter using the template text given, filling the person's name, the request type, the date received, the number of files found, and the list of file descriptions from the evidence index. Keep the template wording; add nothing not in the index.'`

If the request language is not English:

`delegate --target document-agent --instruction 'Translate the letter text given into the requested language, keeping the structure and all file descriptions unchanged.'`

Save the letter with `knowledge-agent` the same way as the index. If the writing delegation returns `failed` or `cancelled`, save the unfilled template plus the index instead and say that the letter was not drafted.

In report-only mode, show the counters, the path of the index and the letter, the needs-confirmation list, the unreadable list and the surveillance finding, and stop.

## Step 7. Act, one file at a time (act mode only)

Only files whose decision is "included" are acted on. Files on the needs-confirmation list that the user did not confirm are not touched.

First, for access requests:

`delegate --target file-agent --instruction 'Create a folder named hand-over inside the case folder the user named.'`

Then for each included file, in order:

- Access: `delegate --target file-agent --instruction 'Copy the file at the given path into the hand-over folder inside the case folder. Do not move or overwrite.'`
- Erasure: `delegate --target file-agent --instruction 'Delete the file at the given path.'`
- After `completed`: `delegate --target file-agent --instruction 'Add the tag named dsar followed by the case date and the case name to the file at the given path, creating the tag if it does not exist.'` For erasure, tag the index row instead, since the file is gone.
- After each file, append one line to the audit log with `knowledge-agent`: time, action, path, sha256 recorded in step 6, result state, approval state. See [audit and undo](references/audit-and-undo.md).

A file that returns `waiting_approval` stays pending while the next file proceeds; it is logged as pending and revisited at the end. A file that returns `cancelled` is logged as "skipped by user" and never retried in this run. A file that returns `failed` is logged with the reason and the run continues with the next file.

## Step 8. Verify and close

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run on the not-included sample from step 6. Report "untouched files verified: N of N unchanged" or list any difference. For erasure, confirm each deleted path no longer exists by asking file-agent to stat it and expecting a not-found result.

Close with: counters; the paths of the index, letter and audit log; the needs-confirmation items the user still has to decide; the unreadable files the user must check by hand; the surveillance identity to remove manually, if any; and for erasure, the sentence "Deleted files are in the recycle bin and can be restored by path within the recycle window; tell me a path to restore it."

# Completion and failure

Report a business result only after the delegated expert returns `completed`. Treat every other state as a state, not a result:

- `completed`: use the returned content. If it is an empty result, record "no results" for that folder or file and continue; never substitute a similar folder, name or data source.
- `failed`: record the failure and reason against that folder or file in the evidence index. The run continues with the remaining items. If every folder in scope fails in steps 1 to 3, stop and report that no search could be completed.
- `cancelled`: record "cancelled by user" for that item. In step 7 the file is left as it was. Dependent steps for that item do not run.
- `waiting_user`: stop and ask for the missing input. Nothing is assumed.
- `waiting_approval`: the item is pending. Report it as pending, continue with items that do not depend on it, and list all pending items at close.

Partial results are always saved: the evidence index is written in step 6 even if later steps do not run, and the audit log is appended after every file so an interrupted act run can be inspected and resumed by re-running with the same case name; already-logged paths are not acted on again.

Never report "all files found" or "deleted". Report exact counts: found, confirmed, excluded, needs confirmation, unreadable, duplicates, acted on, pending, skipped, failed.

The output supports the controller's response to the request; it is not legal advice. The user is responsible for deciding the needs-confirmation items and for checking the unreadable files by hand.

Third-party components, the work developed for this Hackathon, and the AI tools used are listed in [disclosure](references/disclosure.md).

# Install, setup, removal and testing

The package is Markdown only and installs through the AI assistant's Skills page or the Skills Hub; nothing is downloaded or configured. Setup is three NAS settings to check once: recycle bin on the shares in scope, knowledge index and Photos index covering the folders in scope. Removal leaves only what the user asked for: case folders, case tags and recycle-bin entries. Testing uses a published 122-file synthetic corpus with ground truth and a scorer, with two core cases (access, erasure with integrity check) and one edge case (same-name decoys and unreadable files). Steps and expected results are in [install, setup, removal and testing](references/install-and-testing.md).
