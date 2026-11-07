# On File

Round 1 proposal, UGREEN Hackathon 2026 on AI NAS. Track: Open Innovation.

## 1. What does your Skill do?

On File finds every NAS file that mentions one person, shows the passage, drafts the HIPAA or GDPR reply, and copies or deletes only after per-file approval, with a hashed audit log.

## 2. Who is your target user, and what is their problem?

Small practices whose intake forms, spreadsheets, scanned consents, photos and voicemails sit on a NAS. When a patient asks for everything held about them, HIPAA allows 30 days and GDPR one month, no small-business exemption. One rural dental practice paid 140,000 USD in 2026. Nobody knows every place one name sits.

## 3. What is your solution?

It searches chosen folders by file name, content, OCR of scans and photos, document properties, transcripts, subtitles and surveillance faces; quotes the passage; separates same-name people by identifiers and a two-sided check; drafts the letter. Nothing leaves the NAS.

## 4. What is the main user flow?

Input: request type, name, date received, folders, case folder, mode (default report-only). It searches, shows three lists (included, needs your decision, unreadable) and saves the evidence index and letter. In act mode each included file is copied or deleted after its own approval. The close gives exact counts, days left and undo steps.

## 5. How is your idea different from existing tools or common AI solutions?

Enterprise discovery tools (Varonis, BigID, OneTrust) are cloud products for large firms; small-business tools search text only. Chat assistants need uploads, itself a transfer. On File runs where the data lives, never auto-includes a name without a strong identifier, and gates each change behind approval and a hash log. No Hub Skill does this.

## 6. Which UGREEN AI NAS features does your Skill use, and at which step?

file-agent: find, stat, sha256sum, scan-dedupe, mkdir, cpmv, del, echo, restore, tags (steps 1, 3, 6, 7, 8). knowledge-agent: collect-evidence, audio-transcription, save-text (2, 3, 6, 7). document-agent: qa, metadata, extract, writing, translate (4, 5, 6). photo-agent: search-picture (OCR, person), vision-ocr, meta (3, 4). media-agent: subtitle-search (3). security-monitor-agent: faces (3).

## 7. What is your technical approach?

Markdown only; one parent, six experts. Steps 1 to 5 only read; step 6 writes only to the case folder; step 7 acts per file behind gateway approval. Exact name plus a strong identifier auto-includes; a partial name never does; name-only hits get advocate and skeptic queries; disagreement goes to the user. Identifiers seed from the intake form. Unreadable files are listed, never dropped. Local LLM and VLM only.

## 8. What have you built so far? What is not built yet? What still needs testing on a NAS?

Built: SKILL.md plus eight references, checker-clean; a 122-file dental corpus with ground truth; a laptop run (Qwen3 4B, name only): 40 of 40 targets surfaced, 37 auto-included at 100 percent precision, 0 of 12 decoys auto-included, 3 of 3 unreadable reported. Not built: nothing. Needs NAS: collect-evidence recall, Photos OCR, approval flow, recycle-bin restore, real audio.

## 9. How will you test your Skill if you become a Finalist?

Corpus on the NAS. Core 1, access: 40 of 40 target files surfaced, letter written. Core 2, erasure: hash all files, approve each deletion; only included files gone, other hashes unchanged, audit log complete. Edge: 12 Maria Lopez-Ruiz and 3 unreadable files; 0 decoys auto-included, 3 of 3 reported.

## 10. What are the known limits, risks, or outside dependencies of your Skill?

Nicknames and misspellings need user-supplied identifiers. OCR misses on poor scans; hits are marked. Archives, protected files and mailboxes are listed, not opened. Surveillance identities are reported, not removed. Content search depends on the knowledge index. Not legal advice. No network or outside service.

---

Team: Ujwal Vanjare, individual entrant.

Third-party components: none inside the Skill package (Markdown only). Testing tools outside the package: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT), Qwen3 4B and Qwen3-VL 2B (Apache 2.0). Sources: official PyPI, GitHub and Ollama distributions.

AI tools used: Claude Code (Anthropic) for rules research, collision scans, drafting SKILL.md and references from the team's design, the corpus generator, the scorer and this document's layout. Idea, design decisions and final wording are the team's own.

Test corpus and scorer (optional): https://github.com/usv240/on-file
