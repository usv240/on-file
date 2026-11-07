# Install, setup, removal and testing

## Install

The Skill is a Markdown package: `SKILL.md` and the `references/` folder, nothing else. It has no scripts, no binaries and no configuration file.

- Round 1 (static): unzip the package and run the official Uliya Skill Kit checker on the folder. Expected result: static-pass with zero errors, zero warnings and zero notes.
- On the NAS: add the package through the UGOS AI assistant's Skills page, or install it from the UGREEN Skills Hub once published there. The Skill appears under the name `on-file` and is triggered by requests such as "a patient asked for everything we hold about her" or "a customer asked to be deleted".

Nothing is installed outside the Skills directory. No model, library or service is downloaded.

## Setup

There is no configuration. Every run collects its inputs from the user (see Required input in `SKILL.md`). Four NAS settings affect results and are worth checking once:

1. Recycle bin enabled on the shares that will be in scope, so that erasure can be undone within the recycle window. The Skill warns before any deletion in a folder where it is not enabled.
2. Knowledge index covering the folders that will be in scope, so content search finds recent text documents. Files not yet indexed are still caught by the file-name search and, for images, by OCR.
3. Photos indexing of the folders that hold scans and phone photos, so OCR text and recognised people are searchable.
4. A case-folder location outside the folders in scope that only the people handling requests can open, for example a restricted shared folder named Requests. Case folders hold personal data: the index quotes passages, and access cases hold copies.

No credentials, API keys or network access are needed or used. The Skill runs with the NAS account of the user who starts it and reads only what that account can read.

## Removal

Remove the Skill from the Skills page (or uninstall it from the Skills Hub). The package has no background processes, schedules or persisted state outside the user's own folders, so nothing else needs stopping.

What remains after removal, all of it created on the user's request and kept deliberately as the record of the response:

- The case folders the user named, each holding an evidence index, a letter and, for act runs, an audit log and a hand-over folder.
- File tags named dsar followed by the case date and case name on files that were acted on. They can be removed with the tag tools of the file manager.
- Deleted files in the recycle bin until the recycle window ends.

Deleting a case folder, its tags and its recycle-bin entries removes every trace of a case.

## Testing

### Quick check without a corpus (about 5 minutes)

1. Create a scratch folder with three files: a text document mentioning an invented person with an invented email address, a second document mentioning a different invented person with a similar name, and a copy of the first document under a different name.
2. Run the Skill in report-only mode with the invented name and the scratch folder in scope.
3. Expected: the first document and its copy are "included" (the copy with source "duplicate of"), the similar-name document is "needs confirmation" or "excluded", and the index and letter appear in the case folder. Nothing is copied or deleted.

### Full measurement with the Lakeside Dental corpus

A synthetic corpus of 122 files for a fictional dental practice, with ground truth and a scorer, is published for anyone to use: https://github.com/usv240/on-file (folder `testbed`). It is not part of this Skill package. It contains:

| Group | Files | What it tests |
|---|---|---|
| target | 40 | Files about the requester, Maria Lopez, in docx, xlsx, text PDF, image-only scanned PDF, phone photo of a sign-in sheet, email export, voicemail transcript, document properties, photo caption and a calendar with no identifier |
| decoy | 12 | A different patient with an overlapping name, Maria Lopez-Ruiz. None may be auto-included |
| noise | 10 | "Lopez" as a company, a staff member and a street |
| unreadable | 3 | A password-protected PDF, a damaged document and a blank scan. All three must be listed as unreadable |
| background | 57 | Other patients, suppliers, policies, reception photos |

Test cases and expected results:

- Core 1, access, report-only, name only as input: 40 of 40 target files surfaced (included or on the confirmation list); 0 of 12 decoys and 0 of 10 noise files auto-included; 3 of 3 unreadable files listed; index and letter saved.
- Core 2, erasure, act mode: hash every file first with the scorer; approve each deletion; afterwards exactly the included files are gone, every other hash is unchanged, nothing was added, and the audit log has one completed line per deleted file.
- Edge, same-name and unreadable: the 12 decoy files end as "excluded" or "needs confirmation", never "included, auto"; the 3 unreadable files appear in the closing message with a reason.

The scorer reads the evidence index as a tab-separated file with at least the columns path and decision, and prints recall, precision, decoy and noise counts, unreadable counts, and the integrity result after erasure. Laptop stand-in results for these cases are in [limits](limits.md); they will be replaced by NAS results.

### Repeat use

Run the access case twice with the same case name. Expected on the second run: every file reported as "already done", no new copy, no new approval for copies, and the audit log extended with "already done" lines. Then run a second case for a different invented person in the same folders and check that the two case folders and case tags do not mix.

### What to look at if a test fails

- Target files missing from the index: check that the knowledge index and Photos index cover the folder (Setup, items 2 and 3). File-name hits alone mean the content index did not return results for that folder; the closing message says so.
- A decoy auto-included: the file contains the exact full name together with one of the requester's strong identifiers. That is a data problem to inspect, not a Skill decision to override silently.
- An unreadable file missing: this is a defect; the index must list every candidate that could not be opened.

## Versions

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-11-07 | Round 1 package. Static checker pass; workflow measured on a laptop stand-in. |
| 0.2.0 | planned, Round 2 | NAS measurements replace the laptop numbers; approval counts and transcription times measured on the iDX6011 Pro; letter wording tuned. |

Upgrading replaces the package files only. Case folders from earlier versions are plain text and stay readable; a re-run of an old case with a newer version reads its index and audit log the same way.
