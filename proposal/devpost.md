# Devpost submission form text

Paste these into the Devpost form. Track question: Open Innovation.

## Project name

On File

## Tagline (under 120 characters)

Answer "send me everything you hold about me" or "delete me" from your NAS, with proof, without uploading anything.

## About the project

### What it does

On File is a Uliya Skill for UGREEN AI NAS. Give it one person's name, the date the request arrived, the request type (HIPAA access, GDPR access or GDPR erasure) and the folders to search. It finds the files in those folders that mention that person, including scanned forms, phone photos, voicemails, subtitle files, document properties, photo captions and named faces in the camera system, and quotes the passage in each.

It tells same-name people apart, including a parent and child with the same name at the same address. It notices when a file also holds other patients' data, such as a shared spreadsheet or a sign-in sheet, and prepares an extract of the person's own entries instead of handing over the whole file. In an erasure request it keeps clinical and billing records the law usually requires, and lists them in the letter with the reason. It drafts the reply letter with a list of records that names no one else, shows the legal due date and the days left, and in act mode copies, extracts or deletes files one at a time, each behind its own approval, with an audit log and a checksum check that the files it did not change are unchanged.

### Why it matters

Any clinic, dental office or shop with records on a NAS gets these requests. HIPAA gives 30 days, GDPR one month, and there is no small-business exemption. In 2026 a solo dental practice in rural Pennsylvania, ten employees, paid the US regulator 140,000 USD in a case that began with one patient's unanswered records request; the regulator had already cut the penalty by 90 percent so the practice could stay open. The files are scattered across forms, spreadsheets, scans and photos, and nobody knows every place one name sits. Uploading the records to a cloud assistant to search them is itself a disclosure. On File runs where the data already lives.

### How it is built

Markdown only: SKILL.md and eight reference files. The parent Skill directs six UGOS expert agents (file, knowledge, document, photo, media, security monitor) through 27 catalog actions. Steps 1 to 5 only read. Step 6 writes new files to the case folder only. Step 7 is the only step that touches the person's files, one approval per file, and the user is told how many approvals to expect before the first one.

The decisions are rules, not model guesses. A name counts only next to one of the person's identifiers; an ID or personal email belongs to one person, while a birth date, phone or address can be shared by a household. Files with only the name get one check for evidence it is the person and one for evidence it is not; clear cases of someone else are excluded with the quote as proof, and the rest go to the user with the evidence for and against. A model's opinion never includes a file, and never excludes one without a quote showing a different person. Every quoted passage must appear in the file, so a model cannot add a file by inventing a quote. Shared files are found by asking the model to list everyone named in the file, not by asking yes or no; in testing, a small model answered "no" for a sign-in sheet with three other patients and named all three when asked for a list.

### What has been measured

Three synthetic practices with answer keys and a scorer, run on a laptop with small open models (Qwen3 4B and a 2B vision model) standing in for the NAS models, with only the name as input and the voicemails as real synthesized audio. Two are dental practices; the third, a physiotherapy practice, was written blind by a separate agent that never saw the rules.

| Measure | Main dental | Harder dental | Blind physio |
|---|---|---|---|
| Requester's files found | 40 of 40 | 43 of 43 | 29 of 30 |
| Included automatically | 37 | 34 | 18 |
| Wrongly included | 0 | 0 | 0 |
| Look-alike files included | 0 of 22 | 0 of 26 | 0 of 18 |
| Shared files flagged for extraction | 7 of 7 | 7 of 7 | 6 of 6 |

The blind practice was first run before the fixes it led to: 18 of 30 found, none wrongly included. It exposed three rule flaws (a middle name on the intake form, a client named only in meeting minutes, a log listing both same-name women), now fixed. A stress test that caps the search at 10 results per term changed nothing: a direct pass over every document caught what the capped search dropped.

The harder corpus adds the requester's mother with the same name at the same address, a spouse, an accented name, a surname-first name with a differently written phone number, and a subtitle file. Its cases came from a review of the first version, so it is a stricter test, not a blind one. The corpora and scorer are public for other entrants to use.

### What is next

Round 2 on the iDX6011 Pro: re-run both corpora with the real agents, replace the laptop numbers, measure approvals and transcription time, and record the three test cases.

## Built with

uliya, ugos, markdown, python (test corpora only)

## Try it out links

https://github.com/usv240/on-file

## Which track best fits your Skill?

Open Innovation
