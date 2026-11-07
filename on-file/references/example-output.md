# Worked example: what the user receives

This is a complete, fictional case so the shape of every output is clear before the Skill is run. The practice, the patients and every identifier are invented. The decisions and passages below are the ones the laptop stand-in produced on the main test corpus described in [install, setup, removal and testing](install-and-testing.md); the counts add up across every step. Voicemails appear as recordings, as they would on a NAS; the test corpus uses transcript files in their place.

## Input

- Request type: HIPAA access
- Person: Maria Lopez
- Date received: 2026-11-03
- Folders in scope: the practice's records folder, searched with all its subfolders
- Case folder: a folder named dsar-2026-11-07-lopez-maria inside a restricted Requests share, outside the records folder
- Mode: report only
- Identifiers: none supplied; the request arrived as a name only

## Counters shown after each step

```text
Due 2026-12-03 (HIPAA access, 30 days from 2026-11-03): 26 days left
Step 1 file and folder names   files 122   candidates 20
Step 2 content                 candidates 58 (merged by path)
Step 3 scans, photos, sound    text in scans and photos 5   captions and properties 3
                               recordings 2   subtitle files 0   video titles 0   camera faces 0
Step 4 confirm                 unreadable 3   excluded, no mention 3
Step 5 disambiguate            identifiers taken from the intake form dated 2025-01-14:
                               email, phone, date of birth, address, patient ID
                               included 37   excluded, a different person 11   needs your decision 4
                               of the 37: copy 30, extract 7 (other patients in the file)
Step 6 index and letter        duplicates 0   checksums recorded 57 (37 included + 20 sample)
Total: 37 + 11 + 4 + 3 + 3 = 58 candidates
```

## Evidence index (excerpt, 13 of 58 rows)

Columns: path, source, matched identifiers, passage, decision, decided by, other people in file, record type, planned action. The saved index also has the advocate and skeptic quotes and a sha256-before column; they are left out here for width.

| Path | Source | Matched | Passage | Decision | By | Others in file | Type | Planned action |
|---|---|---|---|---|---|---|---|---|
| Patients/Lopez, Maria/intake-form-2025-01-14.docx | folder name, content | name, DOB, email, phone, address, ID | Patient: Maria Lopez. Date of birth: 1984-03-12. Patient ID: LD-10432 | included | auto | no | clinical | copy |
| Admin/Insurance/claims-batch-1.xlsx | content | name, DOB | CLM-0M, Maria Lopez, 2025-01-31, 240, 1984-03-12 | included | auto | yes | billing | extract |
| Forms-Scanned/scan_2025-01-14_041.pdf | text in scan | name, DOB, email, phone, address, ID | Patient: Maria Lopez. Patient ID: LD-10432 | included | auto | no | clinical | copy |
| Photos/IMG_20250114_0917.jpg | text in photo | name, ID | 09:10 Maria Lopez LD-10432 | included | auto | yes | clinical | extract |
| Photos/DSC_0412.jpg | caption | name, ID | Post-treatment photo, Maria Lopez, LD-10432, 2025-01-26 | included | auto | no | clinical | copy |
| Voicemail/vm_2025-02-15_10.m4a | recording | name, phone, ID | Hi, this is Maria Lopez, patient ID LD-10432 ... call me back on (555) 014-2231 | included | auto | no | correspondence | copy |
| Admin/Recall-Letters/recall-2025-07-05-01.pdf | content | name, address | Maria Lopez, 18 Birch Lane, Lakeside | included | auto | no | correspondence | copy |
| Admin/calendar-2025-Q1.csv | content | name | 2025-01-13, 10:30, Maria Lopez, Dr. Anita Rowe | needs your decision: the same file lists Maria Lopez-Ruiz on 2025-01-15 | user | | | |
| Patients/Lopez, Maria/treatment-plan-summary.docx | folder name, properties | name | last modified by: Maria Lopez | needs your decision: name only in the document properties | user | | | |
| Admin/Invoices/invoices-2025-extractions-1.xlsx | content | longer name | Maria Lopez-Ruiz, Extraction, LD-11871 | needs your decision: a longer name is never included automatically | user | | | |
| Email/2025-02-28_appointment_D2.txt | content | longer name | Dear Maria Lopez-Ruiz, | excluded, a different person | auto | | | |
| Admin/Suppliers/lopez-construction-invoice-1.pdf | file name | none | no mention of the person | excluded, no mention | auto | | | |
| Patients/Lopez, Maria/insurance-letter-protected.pdf | folder name | none | unreadable: password protected | unreadable | you check by hand | | | |

Surveillance section: no face identity named Maria Lopez in the camera system.

Unreadable list: insurance-letter-protected.pdf (password protected), old-notes-corrupt.docx (cannot be opened), scan_2025-01-30_blank.jpg (no text found).

If this were a GDPR erasure request for the same person, the planned actions for the 37 included files would be: delete 12 (letters, emails, voicemails), retain 18 (15 clinical and 3 billing records, with the retention reason), edit by hand 7 (files that also hold other patients' data).

## Closing message (report-only mode)

```text
Search complete for Maria Lopez (HIPAA access): 1 folder with its subfolders, 122 files.
Due 2026-12-03, 26 days left.
Included 37, excluded 14, needs your decision 4, unreadable 3, duplicates 0.
Identifiers used: the name, plus email, phone, date of birth, address and patient ID
from the intake form dated 2025-01-14.
Planned hand-over: 30 copies and 7 extracts. The 7 files also hold other patients'
data, so only Maria Lopez's own entries would be handed over from them.

Saved in the case folder:
  evidence index   dsar-2026-11-07-lopez-maria-index.txt
  reply letter     dsar-2026-11-07-lopez-maria-letter.txt (Template A, HIPAA access)

Please decide these 4 items (include or exclude):
  1. Admin/calendar-2025-Q1.csv (name only; the file also lists Maria Lopez-Ruiz)
  2. Patients/Lopez, Maria/treatment-plan-summary.docx (name only in document properties)
  3. Patients/Lopez, Maria/referral-note-to-orthodontist.docx (name only in document properties)
  4. Admin/Invoices/invoices-2025-extractions-1.xlsx (a longer name, Maria Lopez-Ruiz;
     the check against found no quote that proves a different person)

Please check these 3 files by hand; I could not read them:
  Patients/Lopez, Maria/insurance-letter-protected.pdf (password protected)
  Patients/Lopez, Maria/old-notes-corrupt.docx (cannot be opened)
  Forms-Scanned/scan_2025-01-30_blank.jpg (no text found)

No camera face identity matched. Nothing was copied or deleted (report-only mode).
Also check systems outside these folders: practice software, x-ray archive, mail server.
Approvals asked in this run: 3 (saving the index, drafting the letter, saving the letter).
To hand over, run again in act mode with the same case name. Expect 30 copy
approvals, 7 extract approvals, 4 audit-log approvals, 1 for the hand-over folder
and 2 for the case tag.
```

## Letter (Template A, filled from the index)

```text
Date: 2026-11-07

To: Maria Lopez

Re: Your request for access to your health information, received 2026-11-03

We have completed a search of our records for information about you. The search
covered our document, scanned-form, photo and recording folders and was carried out
on our own system; your records were not sent to any outside service.

We located 37 records. They are listed in the attached index. 30 are enclosed as
copies. 7 records also contain information about other patients; for those we enclose
an extract with only the entries about you.

We also located 3 files we could not open automatically and have reviewed them by
hand: [outcome to be entered by the practice].

If you have questions about this response, contact [practice contact].

[Signature block]
```

The two bracketed fields stay bracketed because the index has nothing for them; the user fills them. The letter never names the other patients found in the same files.

## Audit log (excerpt from the act-mode run of the same case)

```text
2026-11-07 14:02:11 | copy    | Patients/Lopez, Maria/intake-form-2025-01-14.docx | 9f3a2c... | completed        | approved |
2026-11-07 14:02:26 | extract | Admin/Insurance/claims-batch-1.xlsx                | 41d0e7... | completed        | approved | saved as extract of claims-batch-1.xlsx
2026-11-07 14:02:40 | copy    | Photos/DSC_0412.jpg                                | c7b19a... | cancelled        | declined | declined by user
2026-11-07 14:03:05 | copy    | Voicemail/vm_2025-02-15_10.m4a                     | 5e88d0... | waiting_approval | pending  | revisited at close
```

The sha256 column holds the full 64-character checksum recorded before any change; it is shortened here only for width. These lines reached the file at the first checkpoint, after 10 files. Step 8 then reports, for example, "untouched files verified: 20 of 20 unchanged", "handed over: 29 copies and 7 extracts; 1 declined", and the audit log's own checksum.
