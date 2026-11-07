# Disclosure: components, hackathon work, AI tools

## Third-party components inside the Skill package

None. The package is Markdown only: `SKILL.md` and the files in `references/`. It contains no scripts, binaries, libraries, credentials or personal data. All runtime capabilities are the UGREEN AI NAS expert agents listed in the capability catalog (v2.0.0) and the NAS local models they use.

## Third-party components used outside the package (testing only, not submitted)

The synthetic test corpus and the laptop stand-in harness used to measure provisional numbers are not part of the Skill. They use: Python 3.12 (PSF licence), python-docx (MIT), openpyxl (MIT), reportlab (BSD), Pillow (MIT-CMU), pypdf (BSD), requests (Apache 2.0), Ollama (MIT) serving Qwen3 4B and Qwen3-VL 2B (Apache 2.0) as stand-ins for the NAS local models. Their sources are the official PyPI and GitHub distributions.

## Principal functionality developed for this Hackathon

All of it. The orchestration contract in `SKILL.md`, the disambiguation rules, the advocate and skeptic double-check, the letter templates, the audit and undo design, the synthetic corpus and the scoring method were written during the Hackathon period. No earlier Skill or submission material was reused.

## AI tools used and their principal uses

Claude Code (Anthropic) was used under the team's direction for: rules research and link checking; scanning the Skills Hub, UGREEN Community, Devpost and GitHub for overlapping ideas; drafting this `SKILL.md` and the reference files from the team's design; writing the synthetic corpus generator and the scoring script. The idea, the choice of request types, the naming, the proposal answers and every design decision are the team's own. No AI tool is called at runtime other than the NAS local models through the expert agents.

## Data handling

The Skill reads only the folders the user names, writes only to the case folder the user names, and performs no network calls. Deletions go to the NAS recycle bin. The Skill never stores personal data outside the user's NAS.
