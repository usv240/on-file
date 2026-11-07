# Devpost submission form text

Paste these into the Devpost form. Track question: Open Innovation.

## Project name

On File

## Tagline (under 120 characters)

Answer "send me everything you hold about me" or "delete me" from your NAS, with proof, in one afternoon.

## About the project

### What it does

On File is a Uliya Skill for UGREEN AI NAS. Give it one person's name, the request type (HIPAA access, GDPR access or GDPR erasure) and the folders to search. It finds every file that mentions that person, including scanned forms, phone photos, voicemails, subtitles, document properties and named faces in the camera system, and shows the matching passage for each. It tells same-name people apart, drafts the reply letter, and in act mode copies or deletes files one at a time, each behind its own approval, with a hashed audit log and a verification pass that proves nothing else was touched.

### Why it matters

Any practice or business with records on a NAS gets these requests. HIPAA gives 30 days, GDPR one month, and there is no small-business exemption. The files are scattered across intake forms, spreadsheets, scans and photos, and nobody knows every place one name sits. Sending the records to a cloud model to search them is itself a disclosure. On File runs where the data already lives.

### How it is built

Markdown only: SKILL.md and eight reference files. The parent orchestrates six UGOS expert agents (file, knowledge, document, photo, media, security monitor) through 24 catalog actions. Steps 1 to 5 only read. Step 6 writes new files to the case folder only. Step 7 is the only step that touches the person's files, one file per platform approval, and the user is told how many approvals to expect before the first one. The closing message shows the legal due date and days left. Disambiguation is a rule set: an exact name with a strong identifier auto-includes, a partial name never does, and name-only hits get an advocate query and a skeptic query, with disagreement sent to the user.

### What has been measured

A 122-file synthetic dental corpus with ground truth and a scorer, run on a laptop with Qwen3 4B and a 2B vision model standing in for the NAS models, with only the name as input: 40 of 40 target files surfaced, 37 auto-included at 100 percent precision, 0 of 12 same-name decoys and 0 of 10 noise files auto-included, 3 of 3 unreadable files reported. The corpus and scorer are public for other entrants to use.

### What is next

Round 2 on the iDX6011 Pro: re-run the corpus with the real agents, replace the laptop numbers, record the three test cases.

## Built with

uliya, ugos, markdown, python (test corpus only)

## Try it out links

https://github.com/usv240/on-file

## Which track best fits your Skill?

Open Innovation
