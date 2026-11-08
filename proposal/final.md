# On File

Round 1 proposal, UGREEN Hackathon 2026 on AI NAS. Track: Open Innovation.

## 1. What does your Skill do?

On File finds files in chosen NAS folders that mention one person, quotes each passage, drafts the legal reply, and changes files only after per-file approval.

## 2. Who is your target user, and what is their problem?

Small practices keeping patient records on a NAS. When someone requests all their data, US law (HIPAA) allows 30 days and EU law (GDPR) one month, no small-business exemption. In 2026 a solo dental practice paid 140,000 USD after an unanswered records request; regulators found no access procedure.

## 3. What is your solution?

Practice software holds the chart; the rest sits on the NAS. On File searches file names, text, scans, photos, properties, voicemails, subtitles and camera events. It separates same-name people, extracts from shared files and sends nothing; the practice delivers copies.

## 4. What is the main user flow?

Input: request type, name, date received, folders, case folder, report-only or act mode. It shows days left and three lists (included, needs your decision, unreadable), then saves an index and letter. In act mode each copy, extract or deletion needs its own approval.

## 5. How is your idea different from existing tools or common AI solutions?

Purview and OneTrust serve Microsoft 365 and large firms; PII Crawler (497 USD, local) finds one person's files, scans included; chat assistants need uploads. On File decides each file: only the person's identifiers include it, quotes must exist in the file, no model alone adds or removes one, so a same-name mother stays out. It extracts from shared files, keeps required records, drafts the letter, deletes per approval.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

file-agent: find, cat, stat, sha256sum, scan-dedupe, share-mkdir, mkdir, cpmv, del, echo, restore, tag-get-by-name, tag-add, tag-set, tag-add-file (setup, search, act, verify). knowledge-agent: collect-evidence, audio-transcription, save-text (search, saving). document-agent: qa, metadata, extract, writing, translate (search, confirm, letter). photo-agent: search-picture, vision-ocr, vision-vlm, meta (search, confirm). media-agent: search; security-monitor-agent: faces, event-timeline, event-evidence (search).

## 7. What is your technical approach?

It directs six NAS expert agents. Searching changes no file and saves progress, so stopped runs resume. Only the act stage changes files, one approval each; reruns never act twice. Closed cases keep a record, no passages or copies.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: SKILL.md, eight references (checker-clean), three answer-keyed test corpora, one written blind by another agent. Laptop stand-in (rules as code, small models, synthesized voicemails, name only): 40 of 40 and 43 of 43 requester files surfaced, 37 and 34 auto-included, none wrongly. Blind: first run 18 of 30 surfaced, none auto-included; after fixes 29 surfaced, 18 auto-included, none wrongly. Act replay changed only planned files. Not built: nothing. Needs a NAS: its assistant applying the rules, recall, OCR, cameras, approvals.

## 9. How will you test your Skill if you become a Finalist?

Three corpora. Core 1: every requester file found, shared files planned as extracts, letter written. Core 2, erasure: approve each deletion; only planned deletions gone, all else unchanged; a rerun acts on nothing. Edge: a same-name mother at the same address; it asks once, includes none of hers.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

Nicknames need supplied identifiers. Poor scans can hide a name. Archives and protected files are flagged; mailboxes and practice software are out of reach. Footage and shared files are edited by hand. Models are a NAS setting. Not legal advice. No outside service.

---

Team: Ujwal Vanjare, individual entrant.

Third-party components: none inside the Skill package (Markdown only). Testing tools outside the package: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT), Qwen3 4B and Qwen3-VL 2B instruct (Apache 2.0), Windows offline speech (System.Speech). Sources: official PyPI, GitHub and Ollama distributions.

AI tools used: Claude Code (Anthropic) for rules research, collision scans, drafting SKILL.md, the references and these answers, the corpus generators, the scorer, the laptop harness and reviews against the judging criteria; a separate Claude agent, kept from the rules, wrote the blind test corpus. The idea, request types and naming are the team's own; the team directed the work, reviewed the drafts and made the final choices.

Test corpora and scorer (optional): https://github.com/usv240/on-file
