# Install, setup, removal and testing

## Install

The Skill is a Markdown package: `SKILL.md` and the `references/` folder, nothing else. It has no scripts, no binaries and no configuration file.

- Round 1 (static): unzip the package and run the official Uliya Skill Kit checker on the folder. Expected result: static-pass with zero errors, zero warnings and zero notes.
- On the NAS: add the package through the UGOS AI assistant's Skills page, or install it from the UGREEN Skills Hub once published there. The Skill appears under the name `on-file` and is triggered by requests such as "a patient asked for everything we hold about them" or "a customer asked to be deleted".

Nothing is installed outside the Skills directory. No model, library or service is downloaded.

## Setup

There is no configuration. Every run collects its inputs from the user (see Required input in `SKILL.md`). Five NAS settings affect results and are worth checking once:

1. On-device models. In the AI settings, confirm that the document, photo and knowledge experts use the models that run on the NAS, and so does the assistant that runs this Skill, because it reads every passage the experts return. The Skill itself never names a cloud model or an outside service, but which model an expert uses is a platform setting, and the privacy promise depends on it. The letter states that records were not sent to an outside service only when this is confirmed.
2. Recycle bin enabled on the shares that will be in scope, so that erasure can be undone within the recycle window. The Skill cannot read this setting, so it asks in step 0 and repeats the answer before the first deletion.
3. Knowledge index covering the folders that will be in scope, so content search finds text documents. A file not yet indexed is only partly covered: it is caught if its name or folder contains the person's name, and scans and images are caught by the reading pass in step 3, but a new text document with an unrelated name is missed until it is indexed.
4. Photos indexing of the folders that hold phone photos, so OCR text and recognised people are searchable.
5. A case-folder location outside the folders in scope that only the people handling requests can open. If there is none, the Skill offers to create a shared folder named Requests, hidden from users without permission; the user then sets who may open it. Case folders hold personal data: the index quotes passages, and access cases hold copies and extracts.

No credentials, API keys or network access are needed or used. The Skill runs with the NAS account of the user who starts it and reads only what that account can read.

## Removal

Remove the Skill from the Skills page (or uninstall it from the Skills Hub). The package has no background processes, schedules or persisted state outside the user's own folders, so nothing else needs stopping.

What remains after removal, all of it created on the user's request and kept deliberately as the record of the response:

- The case folders the user named, each holding an evidence index, a letter and, for act runs, an audit log and a hand-over folder.
- If the user chose to tag cases, a tag named dsar followed by the date received on the files in each case folder. It carries no names, is never on the person's own files, and can be removed with the tag tools of the file manager.
- Deleted files in the recycle bin until the recycle window ends.
- The Requests shared folder, if the user let the Skill create it.

Deleting a case folder, its tags and its recycle-bin entries removes every trace of a case.

## Testing

### Quick check without a corpus (about 5 minutes)

1. Create a scratch folder with four files: a text document mentioning an invented person with an invented email address; a second document mentioning a different invented person with a similar, longer name; a copy of the first document under a different name; and a small table listing the invented person, with the same email, and two other invented people.
2. Run the Skill in report-only mode with the invented name and email and the scratch folder in scope. With a name alone and no intake form, nothing is included automatically and every file goes to the confirmation list, as the rules require.
3. Expected: the first document and its copy are "included" with planned action "copy" (the copy with source "duplicate of"); the table is "included" with planned action "extract"; the similar-name document is "needs confirmation" or "excluded"; the index and letter appear in the case folder. Nothing is copied or deleted.

### Full measurement with the Lakeside Dental corpora

Two synthetic corpora for a fictional dental practice, a third written blind for a physiotherapy practice, a scorer and an act-mode replay are published for anyone to use: https://github.com/usv240/on-file (folder `testbed`). They are not part of this Skill package. Every name, address, number and ID in them is invented.

| Group | Main | Hard | What it tests |
|---|---|---|---|
| target | 40 | 43 | Files about the requester, Maria Lopez: docx, xlsx, text PDF, image-only scanned PDF, phone photo of a sign-in sheet, email, voicemail transcript, document properties, photo caption, a calendar with no identifier. 8 of them (9 in the hard corpus) also hold other patients' data. The hard corpus adds an accented name with a day-first birth date, a surname-first name with a dotted phone number on a shared lab sheet, and a subtitle file |
| decoy | 12 | 12 | A different patient with a longer name, Maria Lopez-Ruiz. None may be auto-included |
| noise | 10 | 10 | "Lopez" as a company, a staff member and a street |
| unreadable | 3 | 3 | A password-protected PDF, a damaged document and a blank scan. All three must be listed as unreadable |
| same-name person | 0 | 3 | The requester's mother, also Maria Lopez, at the same address, with her own intake form. None may be auto-included; the run must stop and ask which form is the requester's |
| household | 0 | 1 | The requester's spouse at the same address. Must not be auto-included |
| background | 57 | 57 | Other patients, suppliers, policies, reception photos |

The main corpus is the one the rules were developed on. The hard corpus uses a different random seed and adds the cases above, which came from a review of the first version. The rules for those cases were written at the same time as the cases, so the hard corpus is a stricter test, not a blind one. A blind test needs files written by someone who has not read the rules; the corpus generator and scorer are published so that anyone can add such files. The same seed gives the same paths and text; PDF and Word files differ between builds only in embedded creation times.

### A blind corpus, a stress mode, spoken voicemails and an act-mode replay

Four further checks answer the obvious doubts about the two corpora above.

- Blind corpus. A separate agent that never saw these rules wrote a third practice, Kestrel Bay Physiotherapy, with 65 files and its own answer key: a same-name client with her own folder, a maiden name, a misspelling, the requester's data inside her husband's and son's records, a name only in a Word page header, look-alike names such as Sarah Mitchell-Hayes and Mitchell Park, and unreadable files. It lives in `testbed/blind`. Some of its cases are outside what the rules promise, for example a maiden name nobody supplied, so it measures the honest ceiling.
- Stress mode. The harness can limit the content search to 10 files per search term, as an index that returns only its best matches would, and check quotes against search snippets only instead of the full file text. This measures whether the document pass in step 2 catches what the search leaves out.
- Spoken voicemails. `testbed/audio_roundtrip.ps1` speaks each voicemail with an offline Windows voice and transcribes the recording with the offline Windows recognizer, so the voicemail files are tested as machine transcripts rather than clean text. This is synthesized speech, not a phone recording.
- Act-mode replay. `testbed/act_replay.py` carries out the planned copies, extracts and deletions on a copy of a corpus, writes the audit log at the Skill's checkpoints, runs the same case a second time, restores one deleted file, and checks every file in scope by sha256. It tests the plan and the bookkeeping, not the NAS file actions themselves.

Results for all three are in [limits](limits.md).

Test cases and expected results:

- Core 1, access, report-only, name only as input: every target file surfaced (included or on the confirmation list); 0 decoys, noise, same-name or household files auto-included; every unreadable file listed; every shared file planned as an extract, never as a whole copy; index, enclosure list and letter saved; the letter's list of records names no other person.
- Core 2, erasure, act mode: hash every file first with the scorer; approve each deletion; afterwards exactly the files planned for deletion are gone, retained and hand-edit files are unchanged, every other hash is unchanged, nothing was added, and the audit log has one completed line per deleted file with its recycle-bin path.
- Edge, same-name person and unreadable files (hard corpus): the run stops once and asks which intake form is the requester's; after the answer, the mother's files are excluded or on the confirmation list, never included; the 3 unreadable files appear in the closing message with a reason.

The scorer reads the evidence index as a tab-separated file with at least the columns path and decision, and prints recall, precision, decoy, noise, same-name and household counts, unreadable counts, shared-file detection, record-type accuracy, and the integrity result after erasure. Laptop stand-in results are in [limits](limits.md); they will be replaced by NAS results.

### Repeat use

Run the access case twice with the same case name. Expected on the second run: the Skill finds and reads the saved index, reports every file as "already done", makes no new copy or extract, asks for no new approval for copies, the hand-over folder or the tag, and extends the audit log with "already done" lines. Then run a second case for a different invented person in the same folders and check that the two case folders and case tags do not mix. Decide the needs-confirmation items in the first run; the second run must not ask about them again, because they are read from the decisions file.

### What to look at if a test fails

- Target files missing from the index: check that the knowledge index and Photos index cover the folder (Setup, items 3 and 4). File-name hits alone mean the content index did not return results for that folder; the closing message says so.
- A decoy or same-name file auto-included: the file contains the exact full name together with one of the requester's identifiers that the other person does not share. That is a data problem to inspect, not a Skill decision to override silently.
- A shared file planned as a copy: the other-people check missed it. Change the planned action to extract before act mode, and report it as a defect.
- An unreadable file missing: this is a defect; the index must list every candidate that could not be opened.

## Versions

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-11-07 | Round 1 package. Static checker pass; workflow measured on a laptop stand-in on two dental corpora and a blind physiotherapy corpus, with an act-mode replay. |
| 0.2.0 | planned, Round 2 | NAS measurements replace the laptop numbers; approval counts, scan reading and transcription times measured on the iDX6011 Pro; letter wording tuned. |

Upgrading replaces the package files only. Case folders from earlier versions are plain text and stay readable; a re-run of an old case with a newer version reads its index and audit log the same way.
