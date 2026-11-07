# On File

Round 1 proposal, UGREEN Hackathon 2026 on AI NAS. Track: Open Innovation.

## 1. What does your Skill do?

On File finds every file in chosen NAS folders mentioning one patient or customer, quotes the passage, drafts the legal reply, and changes files only after per-file approval.

## 2. Who is your target user, and what is their problem?

Small clinics and shops whose forms, spreadsheets, scans, photos and voicemails sit on a NAS. When someone asks for everything held about them, US law (HIPAA) allows 30 days and EU law (GDPR) one month, with no small-business exemption. In 2026 a ten-person dental practice paid 140,000 USD after one patient's records request went unanswered.

## 3. What is your solution?

It searches file names, text, scanned pages, photo text and captions, document properties, voicemails, subtitles and camera face names. It tells same-name people apart, hands over extracts instead of other patients' data, keeps legally required records, and drafts the letter. Nothing leaves the NAS.

## 4. What is the main user flow?

Input: request type, name, date received, folders, case folder, mode. It shows days left and three lists (included, needs your decision, unreadable), then saves an evidence index and letter. In act mode each copy, extract or deletion waits for its own approval; the summary explains undo.

## 5. How is your idea different from existing tools or common AI solutions?

Enterprise discovery platforms suit large firms; other tools search text only or give advice. Chat assistants need uploads, itself a disclosure. On File searches scans, photos, recordings and camera faces where they live, never includes a bare name, never hands over other patients' data, and proves untouched files stayed unchanged.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

file-agent: find, stat, sha256sum, scan-dedupe, share-mkdir, mkdir, cpmv, del, echo, restore, tag-add, tag-add-file (steps 0, 1, 3, 6, 7, 8). knowledge-agent: collect-evidence, audio-transcription, save-text (2, 3, 6, 7). document-agent: qa, metadata, extract, writing, translate (0, 3 to 7). photo-agent: search-picture, vision-ocr, meta (3, 4). media-agent: search (3). security-monitor-agent: faces (3).

## 7. What is your technical approach?

One parent directs six NAS experts. Steps 1 to 5 only read; step 6 writes to the case folder; step 7 changes files, one approval each. A name counts only beside the person's ID, email, birth date, phone or address; name-only files get for and against checks; unclear ones go to the user. Quotes must exist in the file. On-device models.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: SKILL.md and eight references, passing UGREEN's checker; two synthetic dental corpora with answer keys and a scorer. Laptop run, small open models, name only, harder corpus: all 43 requester files found, 35 included automatically, none wrongly; 0 of 26 look-alike files included; 8 of 8 shared files flagged. Not built: no missing step. Needs a NAS: real search index, photo text, approvals, restore, audio.

## 9. How will you test your Skill if you become a Finalist?

Harder corpus on the NAS. Core 1, access: all 43 requester files found, shared files given as extracts, letter written. Core 2, erasure: hash all files, approve each deletion; only planned deletions gone, all else unchanged. Edge: the requester's mother, also Maria Lopez, same address; the Skill asks once, then includes none of hers.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

Nicknames need user-supplied identifiers. Poor scans can hide a name. Archives, protected files, mailboxes and practice software are flagged, not opened. Camera identities and shared files are changed by hand. Model choice is a NAS setting. Not legal advice. No outside service.

---

Team: Ujwal Vanjare, individual entrant.

Third-party components: none inside the Skill package (Markdown only). Testing tools outside the package: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT), Qwen3 4B and Qwen3-VL 2B (Apache 2.0). Sources: official PyPI, GitHub and Ollama distributions.

AI tools used: Claude Code (Anthropic) for rules research, collision scans, drafting SKILL.md and references from the team's design, the corpus generator, the scorer, a review against the judging criteria, and this document's layout. Idea, design decisions and final wording are the team's own.

Test corpora and scorer (optional): https://github.com/usv240/on-file
