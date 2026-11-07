# Request types

The Skill supports three request types. Each row states what the law asks the organisation to do, the deadline, and what the Skill produces for it. This is background for the user; it is not legal advice.

| Request type | Legal basis | Deadline | What the person is entitled to | What the Skill produces |
|---|---|---|---|---|
| HIPAA access | 45 CFR 164.524 (United States, covered entities of any size) | 30 days from receipt, one 30-day extension with written notice | A copy of their protected health information in the designated record set, in the form requested if readily producible | Evidence index, access letter, hand-over folder of copies |
| GDPR access | Regulation (EU) 2016/679 Art. 15, with Art. 12(3) for timing; UK GDPR same articles | One month from receipt, extendable by two months for complex requests | A copy of the personal data undergoing processing plus the purposes, recipients, retention period and source | Evidence index, access letter, hand-over folder of copies |
| GDPR erasure | Art. 17, with Art. 12(3) for timing | One month, same extension | Erasure without undue delay when a ground in Art. 17(1) applies; the organisation may refuse on Art. 17(3) grounds (legal obligation, legal claims) | Evidence index, erasure letter listing what was deleted and what was retained and why, audit log |

## The due date the Skill shows

The Skill computes the due date from the date received: 30 days for HIPAA access, one calendar month for GDPR access and erasure. It shows the date and the days left after every step and in the closing message. If the user needs the extension, the Skill says what the rule requires (HIPAA: a written notice to the person within the first 30 days, giving the reason and the new date; GDPR: telling the person within the first month, with reasons) but does not decide whether an extension applies.

## What the user must still decide

- Whether a retention duty applies to a file (for example, medical records retention periods, accounting records, pending legal claims). The Skill lists each included file; the user excludes files that must be kept and the letter states them as retained.
- The needs-confirmation items: files that mention the name but where the skeptic check found a sign of a different person.
- Unreadable files: the Skill lists them; the user opens them by hand.
- Named face identities in the surveillance system: reported only; removal is done in the surveillance application.

## Data that is usually forgotten

The Skill searches these because requests commonly miss them: scanned sign-in sheets and consent forms photographed with a phone, voicemail recordings, document author fields, photo captions, videos with subtitles, byte-identical duplicate copies, and face identities in the camera system.
