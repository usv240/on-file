# On File

Round 1 proposal, UGREEN Hackathon 2026 on AI NAS. Track: Open Innovation.

## 1. What does your Skill do?

On File finds the files in chosen NAS folders mentioning one patient or customer, quotes the passage, drafts the legal reply, and changes files only after per-file approval.

## 2. Who is your target user, and what is their problem?

Small clinics and shops with forms, scans, photos and voicemails on a NAS. When someone requests everything held on them, US law (HIPAA) allows 30 days and EU law (GDPR) one month, no small-business exemption. In 2026 Shen Smiles, a ten-person dental practice, paid 140,000 USD after one patient's records request went unanswered.

## 3. What is your solution?

It searches file names, text, scanned pages, photo text and captions, document properties, voicemails, subtitles and camera face names. It separates same-name people and extracts the person's entries from shared files. The Skill itself sends nothing off the NAS.

## 4. What is the main user flow?

Input: request type, name, date received, folders, case folder, report-only or act mode. It shows days left and three lists (included, needs your decision, unreadable), then saves an evidence index and letter. In act mode each copy, extract or deletion waits for its own approval.

## 5. How is your idea different from existing tools or common AI solutions?

PII Crawler (497 USD, local) already finds one person's data, scans included; OneTrust and Transcend automate requests in business systems; chat assistants need uploads. On File's difference: no model can include or exclude a file without a quote checked against that file, so a same-name mother stays out. It then finishes: extracts, retained records, letter, per-file approval.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

file-agent: find, cat, stat, sha256sum, scan-dedupe, share-mkdir, mkdir, cpmv, del, echo, restore, tag-add, tag-add-file (steps 0, 1, 3, 6, 7, 8). knowledge-agent: collect-evidence, audio-transcription, save-text (2, 3, 6, 7). document-agent: qa, metadata, extract, writing, translate (3 to 7). photo-agent: search-picture, vision-ocr, vision-vlm, meta (3 to 5). media-agent: search (3). security-monitor-agent: faces (3).

## 7. What is your technical approach?

The Skill directs six NAS expert agents. Only step 7 changes the person's files, one approval each. A name counts only beside the person's identifiers; name-only files get for and against checks; unclear ones go to the user. Erasure cases keep a record, not the erased data.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: SKILL.md and eight references, checker-clean; two synthetic dental corpora with answer keys. Laptop stand-in (small models, exact-text search, name only), harder corpus written with its rules: 43 of 43 requester files found, 34 auto-included, none wrongly; 0 of 26 look-alikes; 7 of 7 shared files flagged. Nothing planned is unbuilt. Needs a NAS: search recall, scan and property reading, approvals, restore, audio; each has a fallback.

## 9. How will you test your Skill if you become a Finalist?

Core 1, access: 43 of 43 found, shared files planned as extracts, letter written. Core 2, erasure: hash all files, approve each deletion; only planned deletions gone, all else unchanged. Edge: the requester's mother, also Maria Lopez, same address; it asks once, then includes none of hers.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

Nicknames need user-supplied identifiers. Poor scans can hide a name. Archives and protected files are flagged; mailboxes and practice software are out of reach. Camera identities and shared files are changed by hand. Model choice is a NAS setting. Not legal advice. No outside service.

---

Team: Ujwal Vanjare, individual entrant.

Third-party components: none inside the Skill package (Markdown only). Testing tools outside the package: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT), Qwen3 4B and Qwen3-VL 2B (Apache 2.0). Sources: official PyPI, GitHub and Ollama distributions.

AI tools used: Claude Code (Anthropic) for rules research, collision scans, drafting SKILL.md and references from the team's design, the corpus generator, the scorer, a review against the judging criteria, and this document's layout. Idea, design decisions and final wording are the team's own.

Test corpora and scorer (optional): https://github.com/usv240/on-file
