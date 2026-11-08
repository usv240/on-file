# Disambiguation: is this the same person?

The most common error in a person search is including someone else who shares the name. These rules decide, per file, whether a hit is the requester.

## Identifier kinds

| Kind | Identifiers | With the exact full name | Without the name |
|---|---|---|---|
| Belongs to one person | patient or customer ID, personal email | include automatically | include automatically |
| Personal, not unique | date of birth | include automatically, unless a same-name person shares it | the two checks; never automatic |
| Can be shared by a household | phone number, postal address | the against-check runs first; any checked passage sends the file to the user, otherwise include and list it apart in the closing message | the two checks; never automatic |
| Context | employer, role, a family member's name, a city | the two checks | not a hit |
| Weak | first name alone, surname alone, initials | never a hit on its own; only widens the candidate list in step 1 | not a hit |

Partial name matches (for example a hyphenated surname that starts with the requester's surname, or "Mariana" for "Maria") are candidates, not hits. They always go through the two checks and are never auto-included: the best outcome is the confirmation list.

## Forms of the same identifier

People and systems write the same thing differently, so each identifier is matched in its common forms:

- Name: "Maria Lopez", "Lopez, Maria", and without accents, so "María López" matches. A longer name ("Maria Lopez-Ruiz") is a partial match, not the name.
- A middle name or initial between the given name and surname still counts as the name, so "Sarah Louise Mitchell", "SARAH L MITCHELL" and "Mitchell, Sarah J." all match a request for Sarah Mitchell. A hyphenated given name ("Sarah-Jane") or surname ("Mitchell-Hayes") does not; it is a partial match. The blind test corpus showed why this matters: the requester's own intake form gave her middle name, and an exact-only rule never adopted her identifiers.
- Phone: compared by digits, so "(555) 014-2231", "555.014.2231" and "+1 555 014 2231" are the same number.
- Patient or customer ID: compared without separators, so "LD-10432", "LD 10432" and "Ld. 10432" match. Machine transcription of a spoken ID produces exactly such forms; in the laptop audio test it turned "LD-10432" into "Ld. 10432".
- Date of birth: "1984-03-12", "12/03/1984", "03/12/1984", "12.03.1984", "12 March 1984" and "March 12, 1984". Both day-first and month-first forms are accepted, which is safe because a date of birth only counts together with the exact name.
- Address: matched on the street line ("18 Birch Lane"), regardless of case and spacing.

Nicknames, former names and transliterations are matched only when the user supplies them.

## Quote check

Every passage a model returns must appear in the file, regardless of case, spacing and punctuation. A passage offered as evidence that the file is about the person must also contain the name or an identifier. A quote that fails the check is treated as no answer. A model cannot add a file to the index by inventing or paraphrasing a passage, and cannot remove one by quoting something that is not evidence of a different person.

The text a quote is checked against comes from a different action than the quote: the content search's passage, the full text of a plain-text file, the photo expert's OCR text, a recording's transcript, or the document properties. When the only text of a Word, PDF or spreadsheet file comes from the same expert that gave the quote, the quote is marked unverified and the file goes to the user.

## The two opposing checks

For every candidate where the rules above call for them, the parent asks the document expert twice, with opposite instructions, on the same file:

1. Advocate: quote every passage showing this is the same person as described by the identifiers.
2. Skeptic: quote every passage showing this is a different person (different date of birth, ID, email or phone, a generational suffix such as Sr. or Jr., an employer, a role, a relationship).

For documents and PDFs the document expert answers; for a photo or scanned image the photo expert answers, and its quotes are checked against the OCR text. Recordings get no model check: a recording with the name only, or only a phone number or address, goes to the user with its transcript sentence.

| Advocate | Skeptic | Decision |
|---|---|---|
| passage | none | needs confirmation, with the advocate's quote as the evidence for |
| passage | passage | needs confirmation, both quotes shown |
| none | none | needs confirmation, name only, no context |
| none | passage showing a longer form of the name or a same-name person's identifier | excluded, skeptic found a different person; the quote is kept in the index |
| none | any other passage | needs confirmation; a file is never excluded on a model's opinion alone |

The checks never include a file on their own. A file is included automatically only through an identifier of the person, so a model's opinion can neither add a file nor remove one. What the checks do is sort the rest: clear cases of a different person are excluded with the quote as proof, and everything else reaches the user with the evidence for and against. The user decides every needs-confirmation item. The Skill never acts on them without that decision.

## Starting from a name only

Most requests arrive with a name and nothing else. The Skill reads the exact-name intake, registration or consent forms first and extracts their fields.

- All such forms give the same date of birth: the Skill shows the form and the identifiers taken from it, the user confirms that this is the requester, and the run continues with them.
- No such form: every hit is name-only and goes through the two checks. Expect a long confirmation list, and say so.
- Forms with different dates of birth: two people share the name, often a parent and child at the same address. The Skill stops and asks the user which form is the requester's.

## A same-name person

After the user picks the requester's form, the other form describes a same-name person. The content search runs for her own identifiers too, and three rules follow:

1. Identifiers the two share (typically the address and a home phone) stop counting for the requester.
2. A file holding the other person's own ID, email, date of birth or phone is excluded with the quote, unless it also holds any of the requester's own identifiers, in which case it goes to the confirmation list. A reminder log listing both people, each with their own phone number, is exactly such a file.
3. A file with the exact name and only a shared identifier, for example a recall letter addressed to "Maria Lopez, 18 Birch Lane", goes to the two checks and at best to the confirmation list. It is genuinely ambiguous and only the user can decide it.

## A same-name relative with no form in scope

The same-name rules need the other person's form. If a parent with the same name and the same home has no intake form in the folders searched, nothing marks the shared phone or address, and a file with the exact name and that phone or address is included once the check against finds nothing. Such files are listed apart in the closing message so the user can look them over before act mode. In the main test corpus these were four recall letters addressed to the requester at her home.

## Growing the identifier set

When the request came with some identifiers and the first included file is an intake, registration or consent form, the extract step reads the form fields (name, date of birth, email, phone, address, ID) and adds new values to the identifier set. The content search is then re-run for the new identifiers only.

## What the index records for each decision

Path, source step, matched identifiers, the passage, advocate quote, skeptic quote, decision, decided by (auto or user), other people in the file, record type and planned action. A reviewer can re-check any decision from the index without re-running the search.
