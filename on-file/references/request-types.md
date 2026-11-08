# Request types

The Skill supports three request types. Each row states what the law asks the organisation to do, the deadline, and what the Skill produces for it. This is background for the user; it is not legal advice.

| Request type | Legal basis | Deadline | What the person is entitled to | What the Skill produces |
|---|---|---|---|---|
| HIPAA access | 45 CFR 164.524 (United States, covered entities of any size) | 30 days from receipt, one 30-day extension with written notice | A copy of their protected health information in the designated record set, in the form requested if readily producible | Evidence index, access letter, hand-over folder of copies and extracts |
| GDPR access | Regulation (EU) 2016/679 Art. 15, with Art. 12(3) for timing; UK GDPR same articles | One month from receipt, extendable by two months for complex requests | A copy of the personal data undergoing processing plus the purposes, recipients, retention period and source; the copy must not adversely affect others (Art. 15(4)) | Evidence index, access letter, hand-over folder of copies and extracts |
| GDPR erasure | Art. 17, with Art. 12(3) for timing | One month, same extension | Erasure without undue delay when a ground in Art. 17(1) applies; the organisation may refuse on Art. 17(3) grounds (legal obligation, public health, legal claims) | Evidence index, erasure letter listing what was deleted, what was retained and why, and what was edited by hand; audit log |

HIPAA has no right to erasure. A US practice that receives a deletion request answers it under its own policy or a state law; the Skill's erasure mode is for GDPR and UK GDPR requests.

## The due date the Skill shows

The Skill computes the due date from the date received: 30 days for HIPAA access, one calendar month for GDPR access and erasure. It shows the date and the days left after every step and in the closing message. If the user needs the extension, the Skill says what the rule requires (HIPAA: a written notice to the person within the first 30 days, giving the reason and the new date; GDPR: telling the person within the first month, with reasons) but does not decide whether an extension applies.

## Defaults the Skill applies, which the user can change per file

- Files that also hold other people's data are never handed over whole. For access, the Skill hands over an extract of the person's own entries. For erasure, it never deletes them; it lists the passages to remove by hand.
- Clinical and billing records are retained by default in an erasure request, because health and accounting records usually carry a legal retention period. The index shows the reason, and the user can mark any of them for deletion.
- Correspondence and other files that are only about the person are deleted in an erasure request once the user approves each one.

## What the user must still decide

- Whether a retention duty applies to a file, and for how long. The defaults above are a starting point, not a legal opinion.
- The needs-confirmation items: files that mention the name but where the checks could not tell who is meant.
- Unreadable files: the Skill lists them; the user opens them by hand.
- Named face identities and camera events in the surveillance system: reported for the user to confirm. Copies of footage, with other people obscured, and removal are done in the surveillance application.
- Data held outside the folders in scope: practice-management software, imaging systems, the mail server and paper records.

## Data that is usually forgotten

The Skill searches these because requests commonly miss them: scanned sign-in sheets and consent forms photographed with a phone, voicemail recordings, document author fields, photo captions, subtitle files, byte-identical duplicate copies, a person's rows inside shared spreadsheets, and camera recordings of the person.
