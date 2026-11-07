# Disclosure: components, hackathon work, AI tools

## Third-party components inside the Skill package

None. The package is Markdown only: `SKILL.md` and the files in `references/`. It contains no scripts, binaries, libraries, credentials or personal data. All runtime capabilities are the UGREEN AI NAS expert agents listed in the capability catalog (v2.0.0) and the NAS local models they use.

## Third-party components used outside the package (testing only, not submitted)

The synthetic test corpus and the laptop stand-in harness used to measure provisional numbers are not part of the Skill. They use: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT) serving Qwen3 4B and Qwen3-VL 2B instruct (Apache 2.0) as stand-ins for the NAS local models, and the offline Windows speech voices and recognizer (System.Speech, part of Windows) to turn the test voicemails into real audio and transcribe them. Their sources are the official PyPI and GitHub distributions.

## Principal functionality developed for this Hackathon

All of it. The orchestration contract in `SKILL.md`, the disambiguation rules, the advocate and skeptic double-check, the letter templates, the audit and undo design, the synthetic corpus and the scoring method were written during the Hackathon period. No earlier Skill or submission material was reused.

## AI tools used and their principal uses

Claude Code (Anthropic) was used under the team's direction for: rules research and link checking; scanning the Skills Hub, UGREEN Community, Devpost and GitHub for overlapping ideas; drafting this `SKILL.md` and the reference files from the team's design; writing the corpus generators, the scoring and summary scripts, the audio round-trip script and the laptop stand-in harness; writing the blind test corpus, done by a separate Claude agent that was not allowed to read the Skill or the rules; independent reviews of the package against the judging criteria by fresh Claude agents, whose findings led to the shared-file, retention, same-name-household, quote-check, document-pass and middle-name rules; and drafting the Round 1 proposal answers. The idea, the choice of request types and the naming are the team's own; the team directed the work, reviewed the drafts and made the final choices. No AI tool is called at runtime other than the NAS local models through the expert agents.

## Data handling

The Skill reads only the folders the user names, writes only to the case folder the user names (and, if the user accepts, creates one restricted shared folder for requests), and performs no network calls itself. Which model each NAS expert uses is a platform setting; the setup asks the user to confirm the on-device models. Deletions go to the NAS recycle bin. Files that also hold other people's data are never handed over whole or deleted. The Skill never stores personal data outside the user's NAS.
