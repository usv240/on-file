# Blind test corpus: Kestrel Bay Physiotherapy

This corpus was written blind. The author did not read the tool's rules, its code or any other test corpus. It is meant to check, fairly, whether a data-request tool can find everything a small practice holds about one person without mistaking other people for them.

## How to build it

```
python make_blind.py --out corpus
```

This creates `corpus/KestrelBay_Physio/` (65 files) and `corpus/expected.json` (the ground truth). The generator is deterministic: two runs produce byte-identical files. At the end it checks that every path in `expected.json` exists, that nothing extra was written, and that the minimums below are met.

Every person, address, phone number, email and ID is invented. Emails use example.com or example.org and phone numbers use the 555-01xx range.

## The practice

Kestrel Bay Physiotherapy is a small clinic in the invented town of Linden Cove, Oregon. Two physiotherapists (Tom Reyes and Priya Natarajan), a front desk and billing person (Jo Whitfield) and a part-time Pilates instructor (Sarah Kwan). The NAS folder holds what such a clinic builds up over 2026: client folders, scans from the desk scanner, phone photos, insurer screenshots, invoices, a billing ledger, the appointment book, an SMS log, exported emails, staff minutes, marketing files, and a 2023 archive from the old system.

## The requester

| Field | Value |
|---|---|
| Name | Sarah Mitchell (full name Sarah Louise Mitchell; maiden name Sarah Pryce) |
| Date of birth | 1983-09-22 |
| Email | sarah.mitchell83@example.com (she sends the request from a work address) |
| Phone | (503) 555-0147 |
| Client ID | KBP-10427 |
| Address | 17 Alder Crescent, Linden Cove, OR 97990 |

She was treated from March to June 2026 for a right shoulder injury after a cycling fall. In 2023 she was treated for an ankle sprain under her maiden name. Her husband Daniel and her son Leo are also clients. The clinic has a second, unrelated client called Sarah Mitchell (Sarah Jane, born 1961, left knee replacement).

## Counts per group

| Group | Files |
|---|---|
| target | 30 |
| decoy | 13 |
| noise | 5 |
| unreadable_requester | 2 |
| unreadable | 4 |
| background | 11 |
| Total | 65 |

Of the 30 targets, 14 are shared (they also hold other clients' data) and 4 show her only in an image: 3 through OCR (a scanned form, a sign-in sheet photo, an insurer screenshot) and 1 only in a photo's EXIF caption.

## Tricky cases and why they are there

- **Two clients with exactly the same name.** The other Sarah Mitchell has her own client folder whose name starts the same way, plus an intake form, notes, a scanned surgeon's letter, a captioned photo and an email signed just "Sarah Mitchell". Only the ID, date of birth, phone or condition (knee, not shoulder) tells them apart.
- **Same name, no identifiers.** Two phone messages say only "Sarah Mitchell". One is about a right shoulder flare (the requester). The other says "65" and mentions a knee replacement (the other client). A tool has to use context, not just the name.
- **Mixed files.** The appointment book, billing ledger, SMS log and mailing list contain both Sarah Mitchells. The SMS log uses the same contact name for both; only the phone number differs. The SMS log is also saved as UTF-16, the way a Windows export tool writes it.
- **A misdirected email.** A reminder about her shoulder appointment was sent to the other Sarah Mitchell's email address. The content is about the requester but the recipient address belongs to someone else. A follow-up incident report names both women.
- **Her data inside family members' records.** Her husband's intake form lists her as emergency contact with her mobile. Her son's consent form is signed by her, and his invoice and the insurer's statement are addressed to her. These are targets that must not be handed over whole. Her husband's own invoice (same surname, same home address) and her son's notes (no mention of her) are decoys, so a match on her address alone is not enough.
- **Name changes and misspellings.** A 2023 archive file uses her maiden name, an old ID and an old address, and is linked only by date of birth and mobile number. A staff email spells her name "Sara Mitchel". Her request comes from a work email address the clinic has never seen.
- **No name at all.** A bounced email shows only her email address and invoice number. A cancellation note names her only in the filename and confirms her mobile in the body. The corrupt discharge summary has only her client ID in its filename.
- **Hidden places.** Her treatment notes name her only in the Word page header. The home exercise sheet names her only in the document properties. A clinical photo names her only in the EXIF description. An old email thread about another client still quotes her March message at the bottom.
- **Name tokens that belong to other people.** A family doctor called Dr. Sarah Mitchell writes a referral for another client. Sarah Mitchell-Hayes and Sarah-Jane Mitchell contain her full name inside a longer one. A client called Mitchell Okoro is screened by an instructor called Sarah Kwan.
- **Names that are not people at all.** A supplier called Mitchell & Hart (with an account manager named Sarah), Mitchell Park, Mitchell Lane, and a running club award named after a Sarah Mitchell who died in 1998.
- **Files that cannot be opened.** A password-protected insurance claim and a corrupt discharge summary are hers. A corrupt knee x-ray report has a filename that points to the other Sarah Mitchell, so it should be listed as unreadable but not as hers.

## Notes on the ground truth

- `how` for non-target files lists where the look-alike name appears, so it is possible to see what a tool might have matched on.
- `strong_identifier_present` is true for her husband's invoice, a decoy, because it carries her home address. This is deliberate.
- `record_type` is filled in for the two `unreadable_requester` files as well, since they are about her.
- `practice` in `expected.json` is the folder name, `KestrelBay_Physio`.
- Judgment calls: files where she appears only as a third party in a family member's record (emergency contact, guarantor, consenting parent) are counted as targets because they hold her personal data, and as shared because they also hold the family member's data.
