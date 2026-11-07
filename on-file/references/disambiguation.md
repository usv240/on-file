# Disambiguation: is this the same person?

The most common error in a person search is including someone else who shares the name. These rules decide, per file, whether a hit is the requester.

## Identifier strength

| Strength | Identifiers | Rule |
|---|---|---|
| Strong | email address, phone number, date of birth, patient or customer ID, full postal address | Name plus any one strong identifier in the same file: include automatically |
| Medium | employer, role, a family member's name, a city | Name plus medium identifiers only: run the two opposing checks |
| Weak | first name alone, surname alone, initials | Never a hit on its own; used only to widen the candidate list in step 1 |

Partial name matches (for example a hyphenated surname that starts with the requester's surname) are candidates, not hits. They always go through the two opposing checks and are never auto-included: the best outcome for a partial match is the confirmation list, unless a strong identifier of the requester is in the same file.

Order of work: intake, registration and consent forms first. The first confirmed form supplies the strong identifiers, so most later files are decided by identifier co-occurrence rather than by the two checks.

## The two opposing checks

For every candidate where only the name (or name plus medium identifiers) matched, the parent asks the document expert twice, with opposite instructions, on the same file:

1. Advocate: quote every passage showing this is the same person as described by the identifiers.
2. Skeptic: quote every passage showing this is a different person (different date of birth, address, email, phone, employer, role, relationship).

Decision table:

| Advocate | Skeptic | Decision |
|---|---|---|
| passage | none | included, auto, skeptic clear |
| passage | passage | needs confirmation (both quotes shown) |
| none | none | needs confirmation (name only, no context) |
| none | passage | excluded, auto, skeptic found a different person; the quote is kept in the index |

The user decides every needs-confirmation item. The Skill never acts on them without that decision.

## Starting from a name only

Most requests arrive with a name and nothing else. The Skill then reads the exact-name intake, registration or consent forms first and extracts their fields. One matching form: its identifiers are adopted and the run continues. Several matching forms with different dates of birth: the Skill stops and asks the user which form is the requester's. No matching form: every hit is name-only and goes through the two checks; expect a long confirmation list, and say so.

## Growing the identifier set

When the first included file is an intake, registration or consent form, the extract step reads the form fields (name, date of birth, email, phone, address, ID) and adds any new values to the identifier set. The content search is then re-run for the new identifiers only. This is how a request that arrived with only a name ends up matched on email and phone as well.

## What the index records for each decision

Path, source step, matched identifiers, the passage, advocate quote, skeptic quote, decision, decided by (auto or user). A reviewer can re-check any decision from the index without re-running the search.
