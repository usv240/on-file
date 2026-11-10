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

Supported scope: documents, spreadsheets, PDFs, scanned PDFs, photos with text, photos of the person recognised by Photos, photo captions, audio recordings, subtitle files, videos in the media library, document properties, file and folder names, and the surveillance system's named face identities and camera events recognised under the person's name (reported for the user to confirm, never changed). Out of scope and reported as such: archives, password-protected files, mailboxes, practice-management databases, imaging systems, anything outside the chosen folders. See [limits](references/limits.md).

Default mode is report only. No copy or delete happens unless the user chooses act mode, and then each file waits for its own platform approval.

A complete fictional case, with the index, the closing message, the letter and an audit log excerpt, is in [worked example](references/example-output.md).

# Required input

Collect these from the user before any delegation. Stop with `waiting_user` if the request type, the name, the date received, the folders in scope or the case folder is missing.

- Request type: one of HIPAA access, GDPR access, GDPR erasure.
- The person's full name as written in the request.
- The date the request was received. It sets the legal due date shown at every step and goes into the letter.
- Folders in scope: one or more folder paths the user names. No file outside them is read. The video library and the surveillance system cannot be limited to a folder, so they are searched only for the person's name, and library results outside the folders are dropped unread.
- Case folder: a folder path where the evidence index, letter and audit log are saved. The user names it; the Skill does not guess a path. It must not be inside a folder in scope. It will hold personal data, so the Skill reminds the user to choose a folder that only the people handling the request can open.
- Case name: proposed by the Skill as dsar, the date received and the person's surname and given name, for example dsar-2026-11-03-lopez-maria, and confirmed or changed by the user. The index, decisions file, enclosure list, letter, audit log and case record start with it; hand-over copies keep their own file names. A re-run with the same case name continues the same case.
- Mode: report only (default) or act.
- Identity: before act mode on an access request, the user confirms that the requester's identity was checked, for example against the photo ID or contact details on file. The Skill does not verify identity itself, and it hands nothing to a requester whose identity the user has not confirmed.
- Optional identifiers: email, phone, date of birth, patient or customer ID, postal address, nickname or former name. Each one improves disambiguation. See [disambiguation](references/disambiguation.md).
- Optional: the language the request was written in, if not English.
- Optional: how long the NAS cameras keep recordings, if the practice has cameras.

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

Steps 1 to 5 change no file in scope: they read every file in scope, and steps 3 and 5 end by saving the progress so far into the evidence index, so a stopped run resumes without searching again; step 6 completes the index and adds the enclosure list and letter. All of these writes go into the case folder and nowhere else, each through a platform-approved write. Step 7 is the only step that touches the person's files, only in act mode, one file per approval. Each delegation below is self-contained: it repeats the person's name, the identifiers, and the exact folder or file it applies to. Downstream steps use only the real result returned by the upstream delegation; nothing is assumed from a result that was not returned.

Keep running counters and show them after every step, together with the legal due date and the days left: folders scanned, files searched, candidates, confirmed, excluded, needs confirmation, unreadable, duplicates.

## Step 0. Case folder and existing case

If the user has no restricted folder for requests, offer once to create one:

`delegate --target file-agent --instruction 'Create a shared folder named Requests on the volume the user chooses, hidden in network places, hidden from users without permission, with its recycle bin turned off.'`

The recycle bin is off in this share so that closing an erasure case removes the erased passages for good.

This asks for the platform's approval; who may open the folder is set by the user in the NAS settings.

Ask once whether the recycle bin is enabled on the shares in scope; the Skill cannot read that setting, so the answer is recorded in the index.

Then look for an existing case:

`delegate --target file-agent --instruction 'In the case folder the user named, find files whose name starts with the case name given. Return their paths, or an empty list.'`

If an evidence index is found, this is a re-run. Read it, the decisions file and the audit log exactly as saved:

`delegate --target file-agent --instruction 'Return the full text content of the files at the given paths.'`

On a re-run, the included list, descriptions and checksums come from the saved index and the user's decisions from the decisions file, unless the user asks for a fresh search; go to step 7 for act mode or step 6 to redraft the letter.

An index whose first line reads "progress: saved after step 3" or "progress: saved after step 5" belongs to a run that stopped early. The run continues with the next step, using the candidates, passages and decisions the index holds; folders are searched again only if the user asks.

## Step 1. Candidates by file and folder name

For each folder in scope:

`delegate --target file-agent --instruction 'In the folder the user named, list files whose file name or folder path contains the person's full name in either order, the surname, or any identifier the user supplied. Search recursively. Return path, size and modified time for each match. If nothing matches, return an empty list and say so.'`

Add every returned path to the candidate list with source "file name".

## Step 2. Candidates by content

Build the search terms first: the full name as written, in surname-first order with a comma, and without accents; each identifier as written; phone numbers also as digits only; an ID also without separators; a date of birth also in day-first, month-first and written-month forms. A middle name or initial between given name and surname (Sarah Louise Mitchell, SARAH L MITCHELL) is recognised when returned text is read and by the document pass below. Given name and surname are never searched as separate terms, which would return every file with either name.

For each folder in scope and for each search term (name forms first, then email, phone, ID, date of birth, address, nickname):

`delegate --target knowledge-agent --instruction 'Collect evidence from the folder the user named for the exact term given, searching the full content of every file. Return every file that contains it, with the matching passage and the file path. Do not widen the search to similar names. If there are no results, say no results.'`

Add every returned path with source "content" and the identifier that matched. Merge duplicates by path; keep all identifiers that matched a path. Every file the search reports it could not read is added to the unreadable list with the reason given.

The content search may return only its best matches, so every document in scope is also read directly:

`delegate --target file-agent --instruction 'List the document files (docx, doc, xlsx, xls, odt, ods, rtf, txt, csv, eml, msg) in the folder the user named, recursively. Return their paths. If there are none, return an empty list.'`

For the listed documents that are not already candidates, in batches of up to 20, so each answer stays complete. A file missing from an answer's coverage is asked about again on its own:

`delegate --target document-agent --instruction 'Read each file at the given paths. For each file that mentions the person's full name in either order, also with a middle name or initial between, or any identifier listed, return the path and quote the exact line. List every file that could not be opened, with the reason. Return none if no file mentions the person.'`

A file found only this way gets source "document pass"; a content search limited to that file confirms its quote, or the file goes to the user. Archives are listed and never opened:

`delegate --target file-agent --instruction 'List the archive files in the folder the user named, recursively. Return their paths, or an empty list.'`

Each archive goes to the unreadable list with the reason "archive, not opened".

## Step 3. Candidates in photos, scans, recordings and video

Run these once per folder in scope. Each may return an empty result; record that and continue.

`delegate --target photo-agent --instruction 'Search pictures whose OCR text contains the person's full name, and separately pictures where the recognised person name equals the person's full name, limited to the folder the user named. Return file paths and, for OCR hits, the matched text. Return no results if there are none.'`

Scans and images that Photos does not index are read directly. List them:

`delegate --target file-agent --instruction 'List the PDF and image files (pdf, jpg, jpeg, png, tif, heic) in the folder the user named, recursively. Return their paths. If there are none, return an empty list.'`

For each listed image that is not already a candidate:

`delegate --target photo-agent --instruction 'Run OCR on the image at the given path and return all text. Then report whether the text contains the person's full name or any identifier listed, quoting the matched line. If no text is found, say so.'`

An image with no text found goes to the end of the unreadable list under "no text found", so a blank scanned page is never missed.

For each listed PDF that is not already a candidate:

`delegate --target document-agent --instruction 'Read the PDF at the given path, including text in scanned pages. Does it contain the person's full name or any of the identifiers listed? Quote the exact line. If the file cannot be read, say unreadable and give the reason. If there is no mention, say none.'`

A PDF that returns no text is listed as unreadable, "scanned pages not read".

Subtitle files are text. List them, and confirm each in step 4 like any document:

`delegate --target file-agent --instruction 'List the subtitle files (srt, vtt, ass, ssa) in the folder the user named, recursively. Return their paths, or an empty list.'`

Videos in the media library are searched by title and description only; nothing is played:

`delegate --target media-agent --instruction 'Search the video library for media whose title or description contains the person's full name. Do not play anything. Return the video paths and titles, or say no results.'`

Keep only results inside a folder in scope; the library search cannot be limited to a folder. A result returned without a path is listed by title as "library item, location not confirmed" and is never acted on.

Recordings are transcribed from a list of paths:

`delegate --target file-agent --instruction 'List the audio and video files (m4a, mp3, wav, aac, amr, ogg, mp4, mov) in the folder the user named, recursively. Return their paths and modified times. If there are none, return an empty list.'`

`delegate --target knowledge-agent --instruction 'Transcribe the recordings at the given paths. For each file, report whether the transcript contains the person's full name or any identifier listed, and return the path and the matching sentence. List any file that could not be transcribed with the reason. Return no results if nothing matches.'`

If a folder holds more than 2000 documents, 500 scans and images or 200 recordings, show the count and ask whether to process all, a date range, or none of that kind; record the choice in the index. Above 500 files in scope, the progress is also saved after each folder in steps 2 and 3, and step 4 reads the candidates back from the saved index instead of carrying them in the conversation.

`delegate --target security-monitor-agent --instruction 'List the known face identities in the surveillance system and report whether any identity name equals the person's full name. Read only. Return the identity name and, if available, the cameras it appears on, or no results.'`

Camera recordings of an identifiable person are personal data too. The event search covers the retention period the user gave, up to the date received, or the 90 days before the date received if none was given; the index records which:

`delegate --target security-monitor-agent --instruction 'List the camera events with people or faces recognised as the known person whose name equals the person's full name, from the start date given to the date received. Return every event, not only the first ten, with its event ID, time and camera. Read only. Return no results if there are none.'`

Recognition under a name cannot tell apart two people enrolled with the same name, so no camera event is decided automatically. When the user wants to check an event, show its snapshot:

`delegate --target security-monitor-agent --instruction 'Return the snapshot of the event with the event ID given, for the user to review. Read only.'`

Surveillance hits are not files: record the identities and events in a "surveillance" section of the index, for the user to confirm and to copy or remove in the surveillance application. The Skill never exports, changes or deletes surveillance data.

If steps 1 to 3 find no candidate in any folder, save an index with zero rows and the counters (step 6), report "no files found in scope", and stop. Never search other folders.

Otherwise save the progress before confirming, because steps 2 and 3 take longest:

`delegate --target file-agent --instruction 'Write the text given to the file in the case folder the user named whose name is the case name followed by index, replacing its content if the file exists.'`

The text has "progress: saved after step 3" on its first line, then every candidate with its source, matched identifiers and passage, the unreadable list, the surveillance section and the counters, in the step 6 columns. This asks for one approval.

## Step 4. Confirm each candidate and read the passage

For the candidate documents, spreadsheets, PDFs and subtitle files, in batches of up to 20 as in step 2, with a file missing from an answer's coverage asked about again on its own:

`delegate --target document-agent --instruction 'Open each file at the given paths. For each file, answer: does it mention the person's full name or any of the identifiers listed? Quote the exact passage and give the path. If a file cannot be opened or read, say unreadable and give the reason.'`

Also read the document properties of the same batch in one call:

`delegate --target document-agent --instruction 'Return the metadata of each file at the given paths: author, last modified by, title, subject, keywords. Report for each file whether any field contains the person's full name.'`

For each candidate that is a photo or scanned image not already confirmed by OCR text:

`delegate --target photo-agent --instruction 'Run OCR on the image at the given path and return all text. Then report whether the text contains the person's full name or any identifier listed, quoting the matched line.'`

For every photo candidate, also read the image's own fields, because a caption can name the person when the picture shows no text:

`delegate --target photo-agent --instruction 'Return the metadata of the image at the given path, including description, caption, title, author and keywords. Report whether any field contains the person's full name or any identifier listed.'`

If a metadata action returns no fields, record "properties not read" for that file. The image metadata action takes several paths, so all candidate photos are read in one call.

For recordings, the passage is the transcript sentence from step 3, compared with the name and identifiers by the Skill itself.

A photo found only by face recognition has no text to quote; it goes to the confirmation list with source "recognised face".

Quote check: every quoted passage must appear, regardless of case, spacing and punctuation, in text from a different action than the quote: the content-search passage, the file expert's text for plain-text files, the OCR text for images, the transcript, or the metadata. Evidence that a file is about the person must also contain the name or an identifier. A quote that fails is treated as no answer. A Word, PDF or spreadsheet quote with no independent text to check against is marked unverified and the file goes to the user. See [disambiguation](references/disambiguation.md).

Outcomes per file:

- Passage found: mark "confirmed candidate" and keep the passage and the matched identifiers.
- No mention found on close reading: mark "excluded, no mention" only if the content search, an independent action, also returned nothing for that file. A file whose name or folder contains the person's full name, or that the content search did return, is never excluded this way: it goes to the confirmation list. So no model's answer alone removes a file.
- Unreadable: mark "unreadable" with the reason. Never drop it from the index.

## Step 5. Disambiguate same-name people

Apply the rules in [disambiguation](references/disambiguation.md). Process intake, registration or consent forms first, because they carry the identifiers that let every later file be decided automatically.

A patient or customer ID and a personal email belong to one person; a date of birth, phone or address can be shared by a household.

For each file, first write down six answers, yes or no, from every text found for it in steps 1 to 4: the content-search passages, the document pass quote, the OCR text of a photo or scan, the transcript sentence of a recording, the document or photo properties, and the passages confirmed in step 4. A value counts when it appears in that text in any of the forms listed in step 2. An identifier the requester shares with a same-name person (see "Starting from a name only") counts for neither of them.

- (a) The exact full name.
- (b) Only a longer form of the name, such as a hyphenated surname.
- (c) The requester's own ID or email.
- (d) The requester's own date of birth.
- (e) The requester's own phone or address.
- (f) A same-name person's own ID, email, date of birth or phone.

Then answer these questions in order and stop at the first one whose answer is yes:

1. Is (f) yes? Then: is (c), (d) or (e) also yes? Yes: "needs confirmation". No: "excluded, identifiers of a same-name person", with the quote.
2. Is (b) yes? Then run the two checks.
3. Is (c) yes? Then "included, auto".
4. Is (a) yes? Then: is (d) yes? Yes: "included, auto". No: is (e) yes? Yes: run the check against. No: run the two checks.
5. Is (d) or (e) yes? Then run the two checks.
6. All six are no: the file keeps its step 4 outcome. "Needs confirmation" if the step 4 reading quoted a checked passage holding the name or an identifier, even one shared with a same-name person, its file or folder name holds the full name, or the content search returned it; otherwise "excluded, no mention".

Write the path to each decision in the index's "decided by" column: the letters that are yes, then each question's answer up to the first yes, for example "a, e: 1 no, 2 no, 3 no, 4 yes, (d) no, (e) yes: check against". A reviewer can then re-check every decision from the row.

A file sent to a check is not decided until that check has returned. A checked passage is one that passed the quote check. The checks decide by the same kind of questions, in order:

- The check against, from question 4. Did it return a checked passage, for example a different birth date or a "Sr."? Yes: "needs confirmation". No: "included, auto, against-check clear". A relative with the same name and home would match the name and the phone or address too, so the closing message lists these files apart: a same-name relative with no form in scope would pass this check.
- The two checks, from questions 2, 4 and 5. They never include a file. First, did the check for return a checked passage holding the exact name or one of the requester's identifiers? Yes: "needs confirmation", with both quotes. No: second, did the check against return a checked passage holding a longer form of the name or a same-name person's identifier? Yes: "excluded, skeptic found a different person", with the quote. No: "needs confirmation", with both quotes.

`delegate --target document-agent --instruction 'Open the file at the given path. Quote every passage that shows the person named is the same person as the one described by the identifiers listed. If there is none, say none.'`

`delegate --target document-agent --instruction 'Open the file at the given path. Quote every passage that shows the person named is a different person from the one described by the identifiers listed, for example a different date of birth, ID, email or phone, a generational suffix such as Sr. or Jr., an employer or a role. If there is none, say none.'`

The two delegations above are for documents, spreadsheets and PDFs, including scanned PDFs. For a photo or scanned image, the same two questions go to the photo expert, which answers questions about an image:

`delegate --target photo-agent --instruction 'Look at the image at the given path. Quote every line of text in it that shows the person named is the same person as the one described by the identifiers listed. If there is none, say none.'`

`delegate --target photo-agent --instruction 'Look at the image at the given path. Quote every line of text in it that shows the person named is a different person from the one described by the identifiers listed, for example a longer name, a different ID or date of birth. If there is none, say none.'`

Image answers are checked against the step 4 OCR text. Recordings get no model check: one with the name only, or only a phone or address, goes to the user with its transcript sentence.

The checks never include a file; only an identifier does. Nothing on the confirmation list is acted on until the user decides it.

Starting from a name only:

- No file can be auto-included yet. Read the intake, registration or consent forms whose name matches first with the extraction below. A form matches when its given name and surname equal the request's; a middle name or initial on the form is ignored, because requests often leave it out. If every such form gives the same date of birth, show the form and the identifiers taken from it, and ask the user to confirm that this is the requester before using them. Then re-run step 2 for them and continue. The re-run finds files that hold only the person's ID or email, without the name.
- If the forms give different dates of birth, two people share the name. Stop with `waiting_user`, show the forms, and ask which is the requester's. After the answer, adopt the chosen form's identifiers and re-run step 2 for them, and also for the other form's own identifiers, so the files that hold them are known. The other form describes a same-name person: any date of birth, phone or address the two share stops counting for the requester; a file holding the other person's own ID, email, date of birth or phone is "excluded, identifiers of a same-name person" with the quote, unless it also holds any of the requester's own identifiers, in which case it goes to the confirmation list; and a file with the exact name and only a shared identifier goes to the two checks and at best to the confirmation list.

`delegate --target document-agent --instruction 'Extract from the file at the given path the fields: full name, date of birth, email, phone, postal address, patient or customer ID. Return them as a list.'`

When the request came with some identifiers and the first included file is an intake or registration form, run the same extraction once, add new identifiers to the set and re-run step 2 for the new identifiers only.

Finally, for each included file:

`delegate --target document-agent --instruction 'List the people named in the file at the given path, each once, up to eight, with their role in the file: patient or customer, staff, contact, or business. Include names in tables, lists, sign-in sheets and the sentences of the body, not only attendance lists. Also list every client or patient ID in the file. Classify the file as clinical record, billing record, correspondence, or other. Give a short description of the file for a letter, such as intake form dated 14 January 2025, naming no person.'`

A description that contains any name from the list is replaced by the record type and the file's date.

The file holds other people's data if the list names any other patient or customer, or if it lists a client ID other than the requester's. The ID check is independent of the names: in the blind test a model listed only the four staff present at a meeting and missed a client named in the minutes, whose ID gave it away. An answer that cannot be read counts as shared, the safe direction.

The answer sets the planned action, shown in the index and changed by the user if needed:

| File | Access request | Erasure request |
|---|---|---|
| About the person only | copy | delete, unless it is a clinical or billing record |
| Also holds other people's data | extract of the person's own entries | edit by hand; never deleted |
| Clinical or billing record | copy or extract as above | retained by default, with the reason; the user may override per file |

Save the progress again with the step 3 delegation, with "progress: saved after step 5" on the first line and every decision so far.

## Step 6. Duplicates, evidence index and letter

The first two delegations only read:

`delegate --target file-agent --instruction 'Scan the folders the user named for duplicate files. Return groups of byte-identical files with their paths.'`

A file identical to an included file is included as "duplicate of" the original, with the same planned action.

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run it for the included files and a sample of up to 20 files in scope that are not included; the checksums go into the index before step 7.

The remaining delegations write into the case folder only; each one asks for the platform's approval.

`delegate --target file-agent --instruction 'Write the text given to the file in the case folder the user named whose name is the case name followed by index, replacing the progress saved earlier. Content: the evidence index as tab-separated text with one header line and the columns path, description, source, matched identifiers, passage, advocate quote, skeptic quote, decision, decided by, other people in file (yes or no, never their names), record type, planned action, sha256 before; then the surveillance section; then the unreadable list; then the counters and the legal due date.'`

The index is internal: it quotes excluded and undecided files, which can be about other people, so it is never sent to the requester. The enclosure list is built from included rows only: description, record type, and how each is provided. It holds no paths, passages or other names.

`delegate --target knowledge-agent --instruction 'Save a text file in the case folder the user named, with the case name followed by enclosure list as the file name, containing exactly the list given.'`

Draft the letter from the template for the request type:

`delegate --target document-agent --instruction 'Draft a formal reply letter using the template text given, filling the person's name, the request type, the date received, the number of records, and the descriptions from the enclosure list given, with the retained and hand-edited items in their own lists. Keep the template wording; add nothing not in the enclosure list; never name another person. Return the text only; do not save a file.'`

If the request language is not English:

`delegate --target document-agent --instruction 'Translate the letter text given into the requested language, keeping the structure and all file descriptions unchanged. Return the text only; do not save a file.'`

Save the letter with `knowledge-agent` the same way. If drafting returns `failed` or `cancelled`, save the unfilled template instead and say so.

In report-only mode, show the counters, the due date, the saved paths, the planned actions, the confirmation list, the unreadable list and the surveillance finding, and stop. That is six approvals: two progress saves, the index, the enclosure list, and drafting and saving the letter; plus one for a translation, one per batch of decisions the user saves, and, above 500 files in scope, one progress save per folder.

Decisions the user makes on confirmation items or planned actions, in any run, are appended with the date to the decisions file, so nothing is asked twice:

`delegate --target file-agent --instruction 'Append the lines given to the file in the case folder the user named whose name is the case name followed by decisions, creating it if it does not exist. Do not overwrite existing lines.'`

One approval per batch of decisions. If a decision changes what is enclosed, redraft the enclosure list and letter before act mode.

## Step 7. Act, one file at a time (act mode only)

Only included files are acted on, each by its planned action. Unconfirmed, retained and hand-edit files are never changed.

Before the first action, state the approvals to expect: one per copy, extract or deletion, one per audit-log write, one for the hand-over folder, and up to three for the optional tag. Each confirms one file already on the enclosure list. Deletions stay one approval each on purpose, although a batch deletion exists. The platform offers "Allow once" and "Always allow". UGREEN's community technical FAQ states that "Always allow" covers every file under the target's parent folder, so the Skill asks the user to choose "Allow once" for every copy, extract and deletion: one approval must never cover the person's other files, or another patient's. "Always allow" is suitable only for saves into the case folder, which then stop asking. See [limits](references/limits.md).

For access, create the hand-over folder if the size-and-time check below finds none:

`delegate --target file-agent --instruction 'Create a folder named hand-over inside the case folder the user named.'`

Then for each included file, in order:

- Check first: `delegate --target file-agent --instruction 'Return the size and modified time of the file at the given path, or say not found.'` For erasure, a path that is already not found is logged as "already done" and not acted on again. For access, the same check on the copy's or extract's path inside the hand-over folder tells whether it was already handed over.
- Access, copy: `delegate --target file-agent --instruction 'Copy the file at the given path into the hand-over folder inside the case folder. Do not move or overwrite.'`
- Access, extract: `delegate --target document-agent --instruction 'From the file at the given path, extract only the rows, lines or passages about the person named, with the column headings, and nothing about anyone else.'` Before saving, the Skill keeps only the column headings and the rows or lines that contain the person's name or one of the identifiers, and drops everything else; it does not rely on the step 5 list of people, which is capped. If a kept line also names a person from that list, or nothing is left, the extract is not saved and the file moves to "edit by hand". A clean extract is saved with `knowledge-agent` into the hand-over folder as a text file named "extract of" followed by the file's description from the enclosure list. For a photo or scanned image that also holds other people's data, such as a sign-in sheet, no model writes the extract: it is the lines of the step 4 OCR text that contain the person's name or an identifier, and nothing else.
- Erasure, delete: `delegate --target file-agent --instruction 'Delete the file at the given path and return the path it now has in the recycle bin.'` The delete returns that path. If it does not, record the original path; a restore then finds the file by name in the share's recycle-bin folder first.

Append the new lines to the audit log in the case folder after every 10 files acted on, and always when the user stops the run and at the end. A deletion's recycle-bin path is kept in the running list until the next write; if a run stops between writes, a restore still finds the file by name in the share's recycle-bin folder:

`delegate --target file-agent --instruction 'Append the lines given to the audit log file in the case folder the user named, creating the file if it does not exist. Do not overwrite existing lines.'`

Each line holds time, action, path, sha256 before, result state, approval state and note, with a deletion's recycle-bin path in the note. See [audit and undo](references/audit-and-undo.md). Every file is checked before it is acted on, so a re-run never acts twice.

If the user wants a case tag, it goes only on files in the case folder, never on the person's own files, and carries the date only: dsar followed by the date received.

`delegate --target file-agent --instruction 'Find the tag with the name given. If it does not exist, create it. Then add it to every file in the list given that does not already carry it.'`

The list is the case-folder files. Files already tagged are skipped. The tag line goes into the final audit-log write.

`waiting_approval`: logged as pending, revisited at the end. `cancelled`: logged as "declined by user", not retried. `failed`: logged with the reason; the run continues.

## Step 8. Verify and close

`delegate --target file-agent --instruction 'For each path in the list given, return the sha256 checksum, size and modified time.'`

Run it on the not-included sample, on every included file that was not changed, and on the audit log. Report "untouched files verified: N of N unchanged" or each difference. For erasure, each deleted path must return not found.

Close with: counters; the files included on the name with only a phone or address, for a look before act mode; approvals asked, approved, declined and pending; due date and days left; the saved paths, noting the index is never sent; the audit log's checksum; open confirmation items; retained files with reasons; shared files to edit by hand, with the passages; unreadable files; any surveillance identity to remove manually; and a reminder to check practice software, imaging systems and the mail server.

The Skill sends nothing to the requester. For access, the user delivers the letter and the hand-over folder by the practice's own method, for example on an encrypted USB drive, by secure email, on paper, or through a NAS sharing link with a password and an expiry date that the user creates. The user gives the date and method, and they are appended to the decisions file as part of the case record.

For erasure, also say: "Deleted files are in the recycle bin and can be restored by path. Erasure is complete when the recycle bin entry is emptied or expires; snapshots and backups expire on their own schedule."

A closed case should not keep more personal data than its record needs. Offer to close it once every item is decided and the actions are done: for erasure after the deletions, for access after the user has recorded the delivery. Closing saves a case record with paths, descriptions, decisions, actions, approval states and checksums but no passages, then deletes the full index and, for access, the hand-over folder, whose files are copies:

`delegate --target knowledge-agent --instruction 'Save a text file in the case folder the user named, with the case name followed by record as the file name, containing exactly the rows given.'`

`delegate --target file-agent --instruction 'Delete the evidence index file at the given path in the case folder.'`

`delegate --target file-agent --instruction 'Delete the folder named hand-over in the case folder the user named, with its contents.'`

The case record and audit log show what was done, not what the files said. In the Requests share from step 0 the recycle bin is off, so the deletion is final; if the case folder is elsewhere, the closing message tells the user to empty the index from that share's recycle bin.

To restore on request:

`delegate --target file-agent --instruction 'Restore the file at the recycle-bin path given to its original location.'`

The restore waits for its own approval and is logged.

# Completion and failure

Report a business result only after the delegated expert returns `completed`. Treat every other state as a state, not a result:

- `completed`: use the returned content. If it is an empty result, record "no results" for that folder or file and continue; never substitute a similar folder, name or data source.
- `failed`: record the failure and reason against that folder or file in the evidence index. The run continues with the remaining items. A folder the user's account cannot read returns `failed` and is listed as not searched. If every folder in scope fails in steps 1 to 3, stop and report that no search could be completed.
- `cancelled`: record "cancelled by user" for that item. In step 7 the file is left as it was. Dependent steps for that item do not run.
- `waiting_user`: stop and ask for the missing input. Nothing is assumed.
- `waiting_approval`: the item is pending. Report it as pending, continue with items that do not depend on it, and list all pending items at close.

Partial results are always saved: the progress after steps 3 and 5, the index with checksums before any change, and the audit log at every checkpoint. A re-run with the same case name resumes from the last of these.

Never report "all files found" or "deleted". Report exact counts: found, confirmed, excluded, needs confirmation, unreadable, duplicates, copied, extracted, deleted, retained, to edit by hand, already done, pending, declined, failed.

The output supports the controller's response to the request; it is not legal advice. The user is responsible for deciding the needs-confirmation items, the retention of each file, and for checking the unreadable files by hand.

Third-party components, the work developed for this Hackathon, and the AI tools used are listed in [disclosure](references/disclosure.md).

# Install, setup, removal and testing

Markdown only; installs from the Skills page or the Skills Hub with nothing to download or configure. Setup is five NAS settings, removal leaves only the case folders, and testing uses three published synthetic corpora, one written blind, with a scorer and an act-mode replay. Steps, expected results and versions are in [install, setup, removal and testing](references/install-and-testing.md).
