# Worked example: what the user receives

This is a complete, fictional case so the shape of every output is clear before the Skill is run. The practice, the patients and every identifier are invented; the corpus that produced it is described in [install, setup, removal and testing](install-and-testing.md). Numbers come from the laptop stand-in run recorded in [limits](limits.md).

## Input

- Request type: HIPAA access
- Person: Maria Lopez
- Date received: 2026-11-03
- Folders in scope: the practice's records share, with the subfolders Patients, Admin, Forms-Scanned, Photos, Email and Voicemail
- Case folder: a folder named dsar-2026-11-07-lopez-maria inside a restricted Requests share, outside the folders in scope
- Mode: report only
- Identifiers: none supplied; the request arrived as a name only

## Counters shown after each step

```text
Due 2026-12-03 (HIPAA access, 30 days from 2026-11-03): 26 days left
Step 1 file names        folders 6   files 122   candidates 20
Step 2 content           candidates 58 (merged by path)
Step 3 photos/scans/audio/video/surveillance   OCR hits 6   audio hits 2   subtitle hits 0   surveillance identities 0
Step 4 confirm           confirmed 44   excluded (no mention) 2   unreadable 3
Step 5 disambiguate      identifiers seeded from intake form: email, phone, date of birth, address, patient ID
                         included 37   excluded (skeptic) 9   needs confirmation 7
Step 6 index and letter  duplicates 0   baseline hashes recorded 57 (37 included + 20 sample)
```

## Evidence index (excerpt, 12 of 59 rows)

Columns: path, source, matched identifiers, passage, confirmation, decision, decided by. The saved index also has a sha256-before column for every included file and the untouched sample; it is left out here for width.

| Path | Source | Matched | Passage | Confirmation | Decision | Decided by |
|---|---|---|---|---|---|---|
| Patients/Lopez, Maria/intake-form-2025-01-14.docx | file name, content | name, DOB, email, phone, address, patient ID | Patient: Maria Lopez. Date of birth: 1984-03-12. Patient ID: LD-10432 | exact name with five strong identifiers | included | auto |
| Admin/Insurance/claims-batch-1.xlsx | content | name, DOB | CLM-0M, Maria Lopez, 2025-01-31, 240, 1984-03-12 | exact name with date of birth | included | auto |
| Forms-Scanned/scan_2025-01-14_041.pdf | OCR | name, DOB, patient ID | Patient: Maria Lopez. Date of birth: 1984-03-12. Patient ID: LD-10432 | OCR text, strong identifiers present | included | auto |
| Photos/IMG_20250114_0917.jpg | OCR | name, patient ID | 09:10 Maria Lopez LD-10432 | OCR of a sign-in sheet photo | included | auto |
| Photos/DSC_0412.jpg | metadata | name, patient ID | image description: Post-treatment photo, Maria Lopez, LD-10432 | document properties only | included | auto |
| Voicemail/vm_2025-02-15_10 | audio transcript | name, phone, patient ID | Hi, this is Maria Lopez, patient ID LD-10432, please call me back on (555) 014-2231 | transcript, strong identifiers present | included | auto |
| Admin/calendar-2025-Q1.csv | content | name | 2025-01-13, 10:30, Maria Lopez, Dr. Anita Rowe | advocate: exact name present. skeptic: the same file also lists Maria Lopez-Ruiz on 2025-01-15 | needs confirmation | user |
| Patients/Lopez, Maria/treatment-plan-summary.docx | file name, metadata | name | document properties: author Dr. Samuel Okafor, subject Maria Lopez | name only in properties, no identifier | needs confirmation | user |
| Admin/Invoices/invoices-2025-extractions-1.xlsx | content | partial name | INV-D0M, 2025-02-10, Maria Lopez-Ruiz, Extraction, 380, LD-11871 | partial name only; never auto-included | needs confirmation | user |
| Email/2025-02-28_appointment_D2.txt | content | partial name | Dear Maria Lopez-Ruiz, | skeptic: different surname and patient ID | excluded, skeptic found a different person | auto |
| Admin/Suppliers/lopez-construction-invoice-1.pdf | file name | none | no mention of the person on close reading | surname only, in a company name | excluded, no mention | auto |
| Patients/Lopez, Maria/insurance-letter-protected.pdf | file name | none | unreadable: password protected | cannot be opened | unreadable | auto |

Surveillance section: no face identity named Maria Lopez in the surveillance system.

Unreadable list: insurance-letter-protected.pdf (password protected), old-notes-corrupt.docx (file cannot be opened), scan_2025-01-30_blank.jpg (no text found by OCR).

Counters: files searched 122, candidates 58, confirmed 44, included 37, excluded 11, needs confirmation 7, unreadable 3, duplicates 0.

## Closing message (report-only mode)

```text
Search complete for Maria Lopez (HIPAA access), 6 folders, 122 files.
Due 2026-12-03, 26 days left.
Included 37, excluded 11, needs your confirmation 7, unreadable 3, duplicates 0.
Identifiers used: name, plus email, phone, date of birth, address and patient ID
taken from the intake form dated 2025-01-14.

Saved in the case folder:
  evidence index   dsar-2026-11-07-lopez-maria-index.txt
  reply letter     dsar-2026-11-07-lopez-maria-letter.txt (Template A, HIPAA access)

Please decide these 7 items (include or exclude):
  1. Admin/calendar-2025-Q1.csv (name only; file also lists Maria Lopez-Ruiz)
  2. Patients/Lopez, Maria/treatment-plan-summary.docx (name only in document properties)
  3. Patients/Lopez, Maria/referral-note-to-orthodontist.docx (name only in document properties)
  4. Admin/Invoices/invoices-2025-extractions-1.xlsx (Maria Lopez-Ruiz, partial match)
  5. Admin/Invoices/invoices-2025-extractions-2.xlsx (Maria Lopez-Ruiz, partial match)
  6. Photos/IMG_20250203_0855.jpg (OCR: Maria Lopez-Ruiz, partial match)
  7. Admin/Suppliers/lopez-construction-invoice-2.pdf (company name only)

Please check these 3 files by hand; I could not read them:
  Patients/Lopez, Maria/insurance-letter-protected.pdf (password protected)
  Patients/Lopez, Maria/old-notes-corrupt.docx (cannot be opened)
  Forms-Scanned/scan_2025-01-30_blank.jpg (no text found by OCR)

No surveillance identity matched. Nothing was copied or deleted (report-only mode).
Approvals asked in this run: 2 (saving the index and the letter).
To hand over copies, run again in act mode with the same case name. Expect
37 copy approvals, 4 audit-log approvals, 1 for the hand-over folder and
1 for the case tag.
```

## Letter (Template A, filled from the index)

```text
Date: 2026-11-07

To: Maria Lopez

Re: Your request for access to your health information, received 2026-11-03

We have completed a search of our records for information about you. The search
covered our document, scanned-form, photo and recording folders and was carried out
on our own system; your records were not sent to any outside service.

We located 37 records. They are listed in the attached index and copies are enclosed.

We also located 3 files we could not open automatically and have reviewed them by
hand: [outcome to be entered by the practice].

If you have questions about this response, contact [practice contact].

[Signature block]
```

The two bracketed fields stay bracketed because the index has nothing for them; the user fills them. The letter never names the other patient found in the same files.

## Audit log (excerpt from an act-mode erasure run on the same case)

```text
2026-11-07 14:02:11 | delete | Patients/Lopez, Maria/intake-form-2025-01-14.docx | 9f3a2c... | completed        | approved |
2026-11-07 14:02:40 | delete | Admin/Insurance/claims-batch-1.xlsx                | 41d0e7... | cancelled        | declined | declined by user
2026-11-07 14:03:05 | delete | Photos/DSC_0412.jpg                                | c7b19a... | waiting_approval | pending  | revisited at close
2026-11-07 14:09:52 | tag    | dsar-2026-11-07-lopez-maria-index.txt              |           | completed        | approved | case tag dsar-2026-11-07-lopez-maria
```

The sha256 column holds the full 64-character checksum recorded before any change; it is shortened here only for width. These lines reached the file at the first checkpoint, after 10 files. Step 8 then reports, for example, "untouched files verified: 20 of 20 unchanged" and "deleted paths confirmed absent: 35 of 35; 1 pending; 1 declined".
