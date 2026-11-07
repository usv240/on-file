# On File

Round 1 proposal, UGREEN Hackathon 2026 on AI NAS. Track: Open Innovation.

## 1. What does your Skill do?

On File finds files in chosen NAS folders mentioning one patient or customer, quotes the passage, drafts the legal reply, and changes files only after per-file approval.

## 2. Who is your target user, and what is their problem?

Small practices with forms, scans, photos and voicemails on a NAS. When someone requests everything held on them, US law (HIPAA) allows 30 days and EU law (GDPR) one month, no small-business exemption. In 2026 a solo dental practice paid 140,000 USD after an unanswered records request; regulators found no access procedure.

## 3. What is your solution?

It searches file names, text, scanned pages, photo text and captions, document properties, voicemails, subtitles and camera face names. It separates same-name people and extracts the person's entries from shared files. The Skill itself sends nothing off the NAS.

## 4. What is the main user flow?

Input: request type, name, date received, folders, case folder, report-only or act mode. It shows days left and three lists (included, needs your decision, unreadable), then saves an index and letter. In act mode each copy, extract or deletion waits for its own approval.

## 5. How is your idea different from existing tools or common AI solutions?

PII Crawler (497 USD, local) finds one person's data, scans included; OneTrust and Transcend serve large firms; chat assistants need uploads. On File adds: it keeps a same-name mother out using checked identifiers, searches voicemails, photo faces and cameras on the NAS, extracts from shared files, keeps required records, drafts the letter, and asks per file.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

file-agent: find, cat, stat, sha256sum, scan-dedupe, share-mkdir, mkdir, cpmv, del, echo, restore, tag-get-by-name, tag-add, tag-set, tag-add-file (setup, search, act, verify). knowledge-agent: collect-evidence, audio-transcription, save-text (search, saving). document-agent: qa, metadata, extract, writing, translate (search, confirm, letter). photo-agent: search-picture, vision-ocr, vision-vlm, meta (search, confirm). media-agent: search; security-monitor-agent: faces (search).

## 7. What is your technical approach?

It directs six NAS expert agents. Searching only reads; only the act stage changes the person's files, one approval each. A name counts only beside the person's identifiers; name-only files get for and against checks; unclear ones go to the user. Erasure cases keep a record, not the erased data.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: SKILL.md and eight references, checker-clean; three test corpora with answer keys, one written blind by an agent kept from the rules. Laptop stand-in (rules as code, small models, synthesized voicemails, name only): 40 of 40 and 43 of 43 requester files surfaced, 37 and 34 auto-included, none wrongly. Blind: 18 of 30 at first, 29 after fixes, none wrong. Act replay changed only planned files. Not built: no step. Needs a NAS: search recall, OCR, approvals.

## 9. How will you test your Skill if you become a Finalist?

All three corpora. Core 1: every requester file found, shared files planned as extracts, letter written. Core 2, erasure: approve each deletion; only planned deletions gone, all else unchanged. Edge: the requester's mother, also Maria Lopez, same address; it asks once, then includes none of hers.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

Nicknames need supplied identifiers. Poor scans can hide a name. Archives and protected files are flagged; mailboxes and practice software are out of reach. Camera identities and shared files are edited by hand. Models are a NAS setting. Not legal advice. No outside service.

---

Team: Ujwal Vanjare, individual entrant.

Third-party components: none inside the Skill package (Markdown only). Testing tools outside the package: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT), Qwen3 4B and Qwen3-VL 2B instruct (Apache 2.0), Windows offline speech (System.Speech). Sources: official PyPI, GitHub and Ollama distributions.

AI tools used: Claude Code (Anthropic) for rules research, collision scans, drafting SKILL.md, the references and these answers, the corpus generators, the scorer, the laptop harness and reviews against the judging criteria; a separate Claude agent, kept from the rules, wrote the blind test corpus. The idea, request types and naming are the team's own; the team directed the work, reviewed the drafts and made the final choices.

Test corpora and scorer (optional): https://github.com/usv240/on-file
