---
name: on-file
description: Use when a patient or customer asks what personal data you hold about them or asks to be deleted (HIPAA right of access, GDPR access or erasure). Finds the files in the chosen NAS folders that mention the person, including scans, photos and recordings, shows the matching passage per file, tells same-name people apart, writes the reply letter and an evidence index, hands over copies or extracts and deletes files only after per-file approval, with an audit log.
---

# Goal

Given one person's name and optional identifiers, produce a complete, checkable answer to a data access or erasure request using only files already on the NAS.

The user-visible result is four plain files saved in a case folder the user names:

1. An evidence index: one row per file that mentions the person, with the matching passage, which identifier matched, how it was confirmed, whether the file also holds other people's data, the record type, the checksum before any change, the decision (included, excluded, needs confirmation, unreadable) and the planned action.
2. A reply letter drafted from the chosen template (HIPAA access, GDPR Art. 15 access, or GDPR Art. 17 erasure). See [request types](references/request-types.md) and [letter templates](references/letter-templates.md).
3. For access requests in act mode: a hand-over folder with a copy of each file that is only about the person, and an extract of the person's own entries from each file that also holds other people's data.
4. For erasure requests in act mode: the files that may be erased deleted to the recycle bin, the files the law requires the practice to keep listed as retained, the shared files listed for editing by hand, and an audit log of every action. See [audit and undo](references/audit-and-undo.md).

Supported scope: documents, spreadsheets, PDFs, scanned PDFs, photos with text, photos of the person recognised by Photos, photo captions, audio recordings, subtitle files, videos in the media library, document properties, file and folder names, and named face identities in the surveillance system (reported only). Out of scope and reported as such: archives, password-protected files, mailboxes, practice-management databases, imaging systems, anything outside the chosen folders. See [limits](references/limits.md).

Default mode is report only. No copy or delete happens unless the user chooses act mode, and then each file waits for its own platform approval.

A complete fictional case, with the index, the closing message, the letter and an audit log excerpt, is in [worked example](references/example-output.md).

# Required input

Collect these from the user before any delegation. Stop with `waiting_user` if the request type, the name, the date received, the folders in scope or the case folder is missing.

- Request type: one of HIPAA access, GDPR access, GDPR erasure.
- The person's full name as written in the request.
- The date the request was received. It sets the legal due date shown at every step and goes into the letter.
- Folders in scope: one or more folder paths the user names. Nothing outside them is read.
- Case folder: a folder path where the evidence index, letter and audit log are saved. The user names it; the Skill does not guess a path. It must not be inside a folder in scope. It will hold personal data, so the Skill reminds the user to choose a folder that only the people handling the request can open.
- Case name: proposed by the Skill as dsar, the date received and the person's surname and given name, for example dsar-2026-11-03-lopez-maria, and confirmed or changed by the user. The index, decisions file, enclosure list, letter, audit log and case record start with it; hand-over copies keep their own file names. A re-run with the same case name continues the same case.
- Mode: report only (default) or act.
- Identity: before act mode on an access request, the user confirms that the requester's identity was checked, for example against the photo ID or contact details on file. The Skill does not verify identity itself, and it hands nothing to a requester whose identity the user has not confirmed.
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

Keep running counters and show them after every step, together with the legal due date and the days left: folders scanned, files searched, candidates, confirmed, excluded, needs confirmation, unreadable, duplicates.

## Step 0. Case folder and existing case

If the user has no restricted folder for requests, offer once to create one:

`delegate --target file-agent --instruction 'Create a shared folder named Requests on the volume the user chooses, hidden in network places, hidden from users without permission, with its recycle bin enabled and the recycle bin open to administrators only.'`

This asks for the platform's approval. Who may open the folder is then set by the user in the NAS settings; the Skill does not change permissions.

Ask once whether the recycle bin is enabled on the shares in scope. The Skill cannot read that setting, so the answer is recorded in the index and repeated before the first deletion.

Then look for an existing case:

`delegate --target file-agent --instruction 'In the case folder the user named, find files whose name starts with the case name given. Return their paths, or an empty list.'`

If an evidence index is found, this is a re-run. Read it, the decisions file and the audit log exactly as saved:

`delegate --target file-agent --instruction 'Return the full text content of the files at the given paths.'`

On a re-run, the included list, descriptions and checksums come from the saved index, and the user's decisions from the decisions file, unless the user asks for a fresh search; go straight to step 7 for act mode, or to step 6 to redraft the letter.

## Step 1. Candidates by file and folder name

For each folder in scope:

`delegate --target file-agent --instruction 'In the folder the user named, list files whose file name or folder path contains the person's full name in either order, the surname, or any identifier the user supplied. Search recursively. Return path, size and modified time for each match. If nothing matches, return an empty list and say so.'`

Add every returned path to the candidate list with source "file name".

## Step 2. Candidates by content

Build the search terms first: the full name as written, the name in surname-first order with a comma, and the name without accents if it has any; each supplied identifier as written; phone numbers also as digits only; a date of birth also in day-first, month-first and written-month forms.

For each folder in scope and for each search term (name forms first, then email, phone, ID, date of birth, address, nickname):

`delegate --target knowledge-agent --instruction 'Collect evidence from the folder the user named for the exact term given, searching the full content of every file. Return every file that contains it, with the matching passage and the file path. Do not widen the search to similar names. If there are no results, say no results.'`

Add every returned path with source "content" and the identifier that matched. Merge duplicates by path; keep all identifiers that matched a path.

## Step 3. Candidates in photos, scans, recordings and video

Run these once per folder in scope. Each may return an empty result; record that and continue.

`delegate --target photo-agent --instruction 'Search pictures whose OCR text contains the person's full name, and separately pictures where the recognised person name equals the person's full name, limited to the folder the user named. Return file paths and, for OCR hits, the matched text. Return no results if there are none.'`

Scans and images that Photos does not index are read directly. List them:

`delegate --target file-agent --instruction 'List the PDF and image files (pdf, jpg, jpeg, png, tif, heic) in the folder the user named, recursively. Return their paths. If there are none, return an empty list.'`

For each listed image that is not already a candidate:

`delegate --target photo-agent --instruction 'Run OCR on the image at the given path and return all text. Then report whether the text contains the person's full name or any identifier listed, quoting the matched line. If no text is found, say so.'`

For each listed PDF that is not already a candidate:

`delegate --target document-agent --instruction 'Read the PDF at the given path, including text in scanned pages. Does it contain the person's full name or any of the identifiers listed? Quote the exact line. If the file cannot be read, say unreadable and give the reason. If there is no mention, say none.'`

If the document expert returns no text at all for a PDF, the PDF is listed as unreadable with the reason "scanned pages not read", so the user checks it by hand. It is never dropped.

Subtitle files are text. List them, and confirm each in step 4 like any document:

`delegate --target file-agent --instruction 'List the subtitle files (srt, vtt, ass, ssa) in the folder the user named, recursively. Return their paths, or an empty list.'`

Videos in the media library are searched by title and description only; nothing is played:

`delegate --target media-agent --instruction 'Search the video library for media whose title or description contains the person's full name. Do not play anything. Return the video paths and titles, or say no results.'`

The library search cannot be limited to a folder, so keep only results whose path is inside a folder in scope and discard the rest without recording them.

Recordings are transcribed from a list of paths:

`delegate --target file-agent --instruction 'List the audio and video files (m4a, mp3, wav, aac, amr, ogg, mp4, mov) in the folder the user named, recursively. Return their paths and modified times. If there are none, return an empty list.'`

`delegate --target knowledge-agent --instruction 'Transcribe the recordings at the given paths. For each file, report whether the transcript contains the person's full name or any identifier listed, and return the path and the matching sentence. List any file that could not be transcribed with the reason. Return no results if nothing matches.'`

Reading scans and transcribing recordings are the slowest searches. If a folder holds more than 500 scans and images or more than 200 recordings, show the count and ask the user whether to process all of them, only those modified in a date range, or leave that kind of file out of this run; record the choice in the index.

`delegate --target security-monitor-agent --instruction 'List the known face identities in the surveillance system and report whether any identity name equals the person's full name. Read only. Return the identity name and, if available, the cameras it appears on, or no results.'`

Surveillance hits are not files. Record them in a separate "surveillance" section of the evidence index for manual action; the Skill never changes surveillance data.

If, after steps 1 to 3, the candidate list is empty for every folder, write an evidence index with zero rows and the counters, save it to the case folder (step 6), report "no files found in scope", and stop. Do not search other folders.

## Step 4. Confirm each candidate and read the passage

For each candidate file that is a document, spreadsheet, PDF or subtitle file:

`delegate --target document-agent --instruction 'Open the file at the given path. Answer: does this file mention the person's full name or any of the identifiers listed? Quote the exact passage. If the file cannot be opened or read, say unreadable and give the reason.'`

Also read the document properties:

`delegate --target document-agent --instruction 'Return the metadata of the file at the given path: author, last modified by, title, subject, keywords. Report whether any field contains the person's full name.'`

For each candidate that is a photo or scanned image not already confirmed by OCR text:

`delegate --target photo-agent --instruction 'Run OCR on the image at the given path and return all text. Then report whether the text contains the person's full name or any identifier listed, quoting the matched line.'`

For every photo candidate, also read the image's own fields, because a caption can name the person when the picture shows no text:

`delegate --target photo-agent --instruction 'Return the metadata of the image at the given path, including description, caption, title, author and keywords. Report whether any field contains the person's full name or any identifier listed.'`

If a metadata action returns no fields for a file, record "properties not read" for it in the index. The file can still be found by its name, its content or the text in the image; only a mention that exists solely in the properties would be missed, and the index says so. The image metadata action accepts several paths, so the captions of all candidate photos are read in one call.

For recordings, the passage is the transcript sentence from step 3. The Skill compares the transcript with the name and identifiers itself; no model is asked about the recording.

A photo found only because Photos recognised the person's face has no text to quote. It is not excluded for lack of a passage: it goes to the confirmation list with source "recognised face", because face recognition can be wrong and only the user can confirm it.

Quote check: every quoted passage must appear in the file's text, properties or transcript, regardless of case, spacing and punctuation. A passage offered as evidence that the file is about the person must also contain the person's name or an identifier, in any of the step 2 forms. An answer whose quote fails this check is treated as no answer. This keeps a wrong or invented answer from a model out of the index.

The text a quote is checked against comes from a different action than the quote: the passage the content search returned in step 2; the full text from the file expert for plain-text files, such as text, CSV and subtitle files; the photo expert's OCR text for images; the transcript for recordings; the metadata for document properties. For a Word, PDF or spreadsheet file whose only text comes from the document expert itself, a quote that cannot be checked this way is marked unverified, and the file goes to the user instead of being decided automatically.

Outcomes per file:

- Passage found: mark "confirmed candidate" and keep the passage and the matched identifiers.
- No mention found on close reading: mark "excluded, no mention".
- Unreadable: mark "unreadable" with the reason. Never drop it from the index.

## Step 5. Disambiguate same-name people

Apply the rules in [disambiguation](references/disambiguation.md). Process intake, registration or consent forms first, because they carry the identifiers that let every later file be decided automatically.

Identifiers come in two kinds. A patient or customer ID and a personal email belong to one person. A date of birth, a phone number and a postal address can be shared by a household.

- Exact full name with an ID, email or date of birth of the requester: "included, auto".
- Exact full name with only the requester's phone or address: a relative with the same name and home would match too, so the second check below runs first. If it returns a checked passage, for example a different birth date or a "Sr.", the file goes to the confirmation list; otherwise it is "included, auto, against-check clear".
- An ID or personal email of the requester without the name: "included, auto".
- A date of birth, phone or address of the requester without the name: the two checks below, never auto-included.
- The name only as part of a longer name, for example a hyphenated surname that begins with the requester's surname: the two checks, never auto-included.
- The exact full name with no identifier: the two checks below; never auto-included.

`delegate --target document-agent --instruction 'Open the file at the given path. Quote every passage that shows the person named is the same person as the one described by the identifiers listed. If there is none, say none.'`

`delegate --target document-agent --instruction 'Open the file at the given path. Quote every passage that shows the person named is a different person from the one described by the identifiers listed, for example a different date of birth, ID, email or phone, a generational suffix such as Sr. or Jr., an employer or a role. If there is none, say none.'`

The two delegations above are for documents, spreadsheets and PDFs, including scanned PDFs. For a photo or scanned image, the same two questions go to the photo expert, which answers questions about an image:

`delegate --target photo-agent --instruction 'Look at the image at the given path. Quote every line of text in it that shows the person named is the same person as the one described by the identifiers listed. If there is none, say none.'`

`delegate --target photo-agent --instruction 'Look at the image at the given path. Quote every line of text in it that shows the person named is a different person from the one described by the identifiers listed, for example a longer name, a different ID or date of birth. If there is none, say none.'`

Image answers are checked against the OCR text from step 4. Recordings get no model check: a recording with the name only, or with only a phone number or address, goes to the confirmation list with its transcript sentence, and the user listens and decides. All answers go through the quote check.

If the first check returns none and the second returns a passage that shows a longer form of the name or an identifier of a known same-name person: "excluded, skeptic found a different person", with the quote kept. Every other combination is "needs confirmation" with both quotes, so the user sees the evidence for and against before deciding. The checks never include a file on their own: only an identifier of the person does. A file about the person is never excluded on a model's opinion alone, because a wrong exclusion leaves the person's data out of the answer. The user decides each item on that list; nothing on it is acted on until the user says include or exclude.

Starting from a name only:

- No file can be auto-included yet. Read the exact-name intake, registration or consent forms first with the extraction below. If every such form gives the same date of birth, show the form and the identifiers taken from it, and ask the user to confirm that this is the requester before using them. Then re-run step 2 for them and continue. The re-run finds files that hold only the person's ID or email, without the name.
- If the forms give different dates of birth, two people share the name. Stop with `waiting_user`, show the forms, and ask which is the requester's. After the answer, adopt the chosen form's identifiers and re-run step 2 for them. The other form describes a same-name person: any date of birth, phone or address the two share stops counting for the requester; a file holding the other person's own ID, email, date of birth or phone is "excluded, identifiers of a same-name person" with the quote, unless it also holds the requester's ID or email, in which case it goes to the confirmation list; and a file with the exact name and only a shared identifier goes to the two checks and at best to the confirmation list.

`delegate --target document-agent --instruction 'Extract from the file at the given path the fields: full name, date of birth, email, phone, postal address, patient or customer ID. Return them as a list.'`

When the request came with some identifiers and the first included file is an intake or registration form, run the same extraction once, add new identifiers to the set and re-run step 2 for the new identifiers only.

Finally, for each included file:

`delegate --target document-agent --instruction 'List the people named in the file at the given path, each once, up to eight, with their role in the file: patient or customer, staff, contact, or business. Include names in tables, lists and sign-in sheets. Classify the file as clinical record, billing record, correspondence, or other. Give a short description of the file for a letter, such as intake form dated 14 January 2025, naming no person.'`

The description is checked before use: it must not contain any name from the list. A description that does contain one is replaced by the record type and the file's date.

The file holds other people's data if the list contains any patient or customer other than the person. If the answer cannot be read, the file is treated as holding other people's data, which is the safe direction: an extract instead of a copy, editing by hand instead of deletion. The question asks for names rather than a yes or no on purpose: in testing, a small model answered no for a sign-in sheet that lists three other patients, and named all three when asked for a list.

The answer sets the planned action, shown in the index and changed by the user if needed:

| File | Access request | Erasure request |
|---|---|---|
| About the person only | copy | delete, unless it is a clinical or billing record |
| Also holds other people's data | extract of the person's own entries | edit by hand; never deleted |
| Clinical or billing record | copy or extract as above | retained by default, with the reason; the user may override per file |

## Step 6. Duplicates, evidence index and letter

The first two delegations only read:

`delegate --target file-agent --instruction 'Scan the folders the user named for duplicate files. Return groups of byte-identical files with their paths.'`

Any file identical to an included file joins the included set with source "duplicate of" and the original path, and takes the original's planned action.

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run this for the included files and for a sample of up to 20 files in scope that are not included. These checksums go into the index, so the state before any change is saved before step 7 starts.

The remaining delegations write new files into the case folder only; each one asks for the platform's approval.

`delegate --target knowledge-agent --instruction 'Save a text file in the case folder the user named, with the case name followed by index as the file name. Content: the evidence index as tab-separated text with one header line and the columns path, description, source, matched identifiers, passage, advocate quote, skeptic quote, decision, decided by, other people in file (yes or no, never their names), record type, planned action, sha256 before; then the surveillance section; then the unreadable list; then the counters and the legal due date.'`

The evidence index is an internal working record. It quotes passages from excluded and undecided files, which can be about other people, so it is never sent to the requester.

Build the enclosure list for the requester from the included rows only: description, record type, and how it is provided (copy, extract, retained, edited by hand). It holds no paths, no passages and no other person's name.

`delegate --target knowledge-agent --instruction 'Save a text file in the case folder the user named, with the case name followed by enclosure list as the file name, containing exactly the list given.'`

Draft the letter from the template for the request type:

`delegate --target document-agent --instruction 'Draft a formal reply letter using the template text given, filling the person's name, the request type, the date received, the number of records, and the descriptions from the enclosure list given, with the retained and hand-edited items in their own lists. Keep the template wording; add nothing not in the enclosure list; never name another person. Return the text only; do not save a file.'`

If the request language is not English:

`delegate --target document-agent --instruction 'Translate the letter text given into the requested language, keeping the structure and all file descriptions unchanged. Return the text only; do not save a file.'`

Save the letter with `knowledge-agent` the same way as the index. If the drafting delegation returns `failed` or `cancelled`, save the unfilled template next to the enclosure list instead and say that the letter was not drafted.

In report-only mode, show the counters, the legal due date, the paths of the index, the enclosure list and the letter, the planned actions, the needs-confirmation list, the unreadable list and the surveillance finding, and stop. A report-only run asks for four approvals: saving the index, saving the enclosure list, drafting the letter and saving the letter, plus one if the letter is translated.

The user's decisions are saved, so they are never asked twice. When the user decides needs-confirmation items or changes a planned action, in this run or a later one, append each decision with the date to the decisions file:

`delegate --target file-agent --instruction 'Append the lines given to the file in the case folder the user named whose name is the case name followed by decisions, creating it if it does not exist. Do not overwrite existing lines.'`

One approval covers each batch of decisions. If a decision changes what is enclosed, step 6 drafts the enclosure list and letter again before act mode.

## Step 7. Act, one file at a time (act mode only)

Only files whose decision is "included" are acted on, each according to its planned action. Files on the needs-confirmation list that the user did not confirm are not touched. Retained files and files marked for editing by hand are never changed by the Skill.

Before the first action, tell the user how many approvals to expect: one per copy, extract or deletion, one per audit-log write, one for the hand-over folder, and, if the user wants the case tagged, up to three for the tag. The platform's copy action takes one file, so each copy asks once. Each of those approvals is a single confirmation of a file the user has already seen on the enclosure list, and nothing reaches the requester until the user sends it. Deletions are kept to one approval each on purpose, even though the platform offers a batch deletion, because each removes a record for good once the recycle window ends.

First, for access requests, check whether the hand-over folder already exists with the same size-and-time delegation used below, and create it only if it does not:

`delegate --target file-agent --instruction 'Create a folder named hand-over inside the case folder the user named.'`

Then for each included file, in order:

- Check first: `delegate --target file-agent --instruction 'Return the size and modified time of the file at the given path, or say not found.'` For erasure, a path that is already not found is logged as "already done" and not acted on again. For access, the same check on the copy's or extract's path inside the hand-over folder tells whether it was already handed over.
- Access, copy: `delegate --target file-agent --instruction 'Copy the file at the given path into the hand-over folder inside the case folder. Do not move or overwrite.'`
- Access, extract: `delegate --target document-agent --instruction 'From the file at the given path, extract only the rows, lines or passages about the person named, with the column headings, and nothing about anyone else.'` Before saving, check the extract against the step 5 list of people in that file: if it contains any other patient's or customer's name, or a line that is not in the file, it is not saved and the file moves to "edit by hand". A clean extract is saved with `knowledge-agent` into the hand-over folder as a text file named "extract of" followed by the file's description from the enclosure list. For a photo or scanned image that also holds other people's data, such as a sign-in sheet, no model writes the extract: it is the lines of the step 4 OCR text that contain the person's name or an identifier, and nothing else.
- Erasure, delete: `delegate --target file-agent --instruction 'Delete the file at the given path and return the path it now has in the recycle bin.'` The delete returns that path. If it does not, record the original path; a restore then finds the file by name in the share's recycle-bin folder first.

Append the new lines to the audit log in the case folder after every deletion, because a restore needs the recycle-bin path the deletion returned; for copies and extracts, after every 10 files; and always when the user stops the run and at the end:

`delegate --target file-agent --instruction 'Append the lines given to the audit log file in the case folder the user named, creating the file if it does not exist. Do not overwrite existing lines.'`

Each line holds time, action, path, sha256 before, result state, approval state and note; for a deletion the note holds the recycle-bin path, which a restore needs. See [audit and undo](references/audit-and-undo.md). Because the checksums are already in the saved index and every file is checked before it is acted on, a run that stops between checkpoints can be re-run with the same case name without acting on any file twice.

At the end, if the user wants it, tag the case so it can be found later. The tag goes only on files in the case folder, never on the person's own files: tags are visible to every NAS user who can see a file, and a tag on a patient's records would tell other staff that a request was made. The tag carries the date only, never the person's name: dsar followed by the date received.

`delegate --target file-agent --instruction 'Find the tag with the name given. If it does not exist, create it. Then add it to every file in the list given that does not already carry it.'`

The list is the files in the case folder: index, decisions, enclosure list, letter, audit log and, for access, the hand-over files. On a re-run, files that already carry the tag are skipped, so no new approval is asked for them. The tag line goes into the final audit-log write.

A file that returns `waiting_approval` stays pending while the next file proceeds; it is logged as pending and revisited at the end. A file that returns `cancelled` is logged as "declined by user" and is not retried in this run. A file that returns `failed` is logged with the reason and the run continues with the next file.

## Step 8. Verify and close

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run on the not-included sample from step 6, on every included file that was not changed (retained, to edit by hand, declined, pending, and every original that was only copied or extracted), and on the audit log itself. Report "untouched files verified: N of N unchanged" or list any difference. For erasure, confirm each deleted path no longer exists by asking file-agent for its size and modified time and expecting a not-found result.

Close with: counters; approvals asked, approved, declined and pending; the legal due date and the days left; the paths of the index, enclosure list, letter and audit log, with a reminder that the index is internal and is never sent to the requester; the audit log's checksum, so a later edit to it can be detected; the needs-confirmation items the user still has to decide; the retained files with their reasons; the shared files to edit by hand, with the passages to remove; the unreadable files the user must check by hand; the surveillance identity to remove manually, if any; and a reminder to check systems outside these folders (practice-management software, imaging systems, the mail server).

For erasure, also say: "Deleted files are in the recycle bin and can be restored by path within the recycle window. Erasure is complete when the recycle bin entry is emptied or expires; copies in snapshots and backups expire on their own schedule. Tell me a path to restore it."

An erasure case should not keep the data it erased. Once every item is decided and the deletions are done, offer to close the case: save a case record that keeps paths, descriptions, decisions, actions, approval states and checksums but no passages or quotes, then delete the full evidence index.

`delegate --target knowledge-agent --instruction 'Save a text file in the case folder the user named, with the case name followed by record as the file name, containing exactly the rows given.'`

`delegate --target file-agent --instruction 'Delete the evidence index file at the given path in the case folder.'`

Each asks for one approval. The case record and the audit log are the organisation's proof of how the request was handled. They hold what was done, not what the files said.

To restore on request:

`delegate --target file-agent --instruction 'Restore the file at the recycle-bin path given to its original location.'`

The restore waits for its own approval and is appended to the audit log as a restore action.

# Completion and failure

Report a business result only after the delegated expert returns `completed`. Treat every other state as a state, not a result:

- `completed`: use the returned content. If it is an empty result, record "no results" for that folder or file and continue; never substitute a similar folder, name or data source.
- `failed`: record the failure and reason against that folder or file in the evidence index. The run continues with the remaining items. A folder the user's account cannot read returns `failed` and is listed as not searched. If every folder in scope fails in steps 1 to 3, stop and report that no search could be completed.
- `cancelled`: record "cancelled by user" for that item. In step 7 the file is left as it was. Dependent steps for that item do not run.
- `waiting_user`: stop and ask for the missing input. Nothing is assumed.
- `waiting_approval`: the item is pending. Report it as pending, continue with items that do not depend on it, and list all pending items at close.

Partial results are always saved: the evidence index, with the checksums, is written in step 6 before any change, and the audit log is appended at every checkpoint, so an interrupted act run can be inspected and resumed by re-running with the same case name.

Never report "all files found" or "deleted". Report exact counts: found, confirmed, excluded, needs confirmation, unreadable, duplicates, copied, extracted, deleted, retained, to edit by hand, already done, pending, declined, failed.

The output supports the controller's response to the request; it is not legal advice. The user is responsible for deciding the needs-confirmation items, the retention of each file, and for checking the unreadable files by hand.

Third-party components, the work developed for this Hackathon, and the AI tools used are listed in [disclosure](references/disclosure.md).

# Install, setup, removal and testing

The package is Markdown only and installs through the AI assistant's Skills page or the Skills Hub; nothing is downloaded or configured. Setup is five NAS settings to check once: on-device models for the document, photo and knowledge experts, recycle bin on the shares in scope, knowledge index and Photos index covering the folders in scope, and a case folder that only the people handling requests can open. Removal leaves only what the user asked for: case folders, case tags and recycle-bin entries. Testing uses a published synthetic corpus with ground truth and a scorer, plus a harder corpus with a same-name relative at the same address and other cases found in review, with two core cases (access, erasure with integrity check) and edge cases (same-name people, a same-name person in the same household, shared files, unreadable files). Steps, expected results and the version history are in [install, setup, removal and testing](references/install-and-testing.md).
