# Round 2 test-day runbook

One assigned day on a UGREEN AI NAS iDX6011 Pro, between Nov 22 and Nov 28. The NAS is reset afterwards, and the demo video must be recorded on it. Everything below is ordered so that the video and the core measurements are done before anything optional.

## Before the day

- [ ] Read the finalist email (sent Nov 21, 12:00 AM PT, to the team Representative): device, testing day, connection steps, private submission link.
- [ ] Ask on the UGREEN Community, if still unanswered: which model runs Skills on the finalist NAS, and whether the assistant reads `references/` files on its own.
- [ ] Build the upload set: `python round2/make_upload.py` writes `dist/round2-upload/{demo,main,hard,blind}.zip`, with the voicemails as recordings (.wav).
- [ ] Build the package: `dist/on-file.zip` (submitted version) and the spare `python round2/make_strict.py <path to check-skill.mjs>`, which writes `dist/on-file-strict.zip`. Both must show static-pass, 0/0/0.
- [ ] Install OBS Studio, or check that Windows Game Bar (Win+Alt+R) records the browser window at 1080p.
- [ ] Print or open on a second screen: this runbook, [VIDEO.md](VIDEO.md), and the request texts below.
- [ ] Laptop reference indexes at hand: `testbed/run_demo/evidence.tsv`, `testbed/run8_main`, `run8_hard`, `run8_blind`.

## Request texts (paste into the assistant)

Use a received date a few days before the testing day, so the due date shows days left. Below, `RECEIVED` stands for that date.

The demo, main and hard corpora all hold a folder named lakeside-dental, so each corpus ZIP is unzipped into its own folder: `/Records/demo`, `/Records/main`, `/Records/hard`, `/Records/blind`. `CORPUS` below stands for demo, main or hard.

Access, report only:

> A patient, Maria Lopez, asked for a copy of every record we hold about her. It is a HIPAA access request, received RECEIVED. Search /Records/CORPUS/lakeside-dental and all its subfolders. Save the case in /Requests. Report only for now.

Act mode, same case:

> Run the same case, dsar-RECEIVED-lopez-maria, in act mode. I confirm Maria Lopez's identity was checked against her photo ID.

Erasure (core 2), on a copy of the main corpus:

> A patient, Maria Lopez, asked us to delete her personal data. It is a GDPR erasure request, received RECEIVED. Search /Records-copy/main/lakeside-dental and all its subfolders. Save the case in /Requests. Act mode.

Blind corpus:

> A client, Sarah Mitchell, asked for a copy of every record we hold about her. It is a HIPAA access request, received RECEIVED. Search /Records/blind/KestrelBay_Physio and all its subfolders. Save the case in /Requests. Report only.

When the Skill asks which intake form is the requester's: the hard and demo corpora, born 1984-03-12; the blind corpus, born 1983-09-22.

## The day

Times are from the moment the NAS is reachable. If the day is shorter than 8 hours, follow the cut list.

| Time | Task | Done when |
|---|---|---|
| 0:00 to 0:40 | Install. Add `on-file.zip` on the Skills page. Check the five settings in `install-and-testing.md` (on-device models, recycle bin, knowledge index, Photos indexing, a restricted Requests share). Upload the four corpus ZIPs into a scratch share `/Records` and unzip each into its own folder (see Request texts). Let the knowledge index and Photos indexing finish on `/Records`. | Skill listed; index and Photos show the folders as indexed |
| 0:40 to 1:20 | **Demo run, report only, not recorded.** Paste the demo request. Note the time each step takes and every approval asked. Copy the saved index off the NAS, then run `python round2/compare_index.py <index> testbed/run_demo/evidence.tsv testbed/corpus-demo/expected.json` and `python testbed/score.py score testbed/corpus-demo/expected.json <index>`. | Both scripts ran |
| 1:20 | **Decision point.** See below. | Version chosen |
| 1:20 to 2:30 | **Record the video** on the demo corpus with the chosen version: a fresh case name, report only, then act mode on the same case. Two takes. Follow [VIDEO.md](VIDEO.md). Copy both recordings off the NAS session immediately. | Two full takes saved on the laptop |
| 2:30 to 3:45 | **Core 1 and the edge case.** Main corpus, access, report only; then the hard corpus with its same-name question. Score both and compare with `run8_main` and `run8_hard`. | Two scores saved |
| 3:45 to 4:45 | **Core 2.** Unzip `main.zip` again into `/Records-copy/main`. Its files are the laptop's upload copy, so hash that copy on the laptop: `python testbed/score.py hash dist/round2-upload/main/lakeside-dental before-main.json`. Run the erasure in act mode, approving each deletion and timing the approvals. Then the Skill's verify step, and restore one deleted file from the recycle bin. Download `/Records-copy/main/lakeside-dental` and run `score.py verify <download> before-main.json`. | Verify result, score verify output and audit log saved |
| 4:45 to 5:30 | Blind corpus, report only, scored. | Score saved |
| 5:30 to 6:15 | Repeat use: stop a run during step 4 and resume it; run the access case a second time and check that nothing is copied twice. | Both behaviours noted |
| 6:15 to 6:45 | Cameras, only if the NAS has cameras with an enrolled test face. Otherwise record "not tested". | Noted |
| 6:45 to 7:30 | **Back up everything before the reset**: every case folder, index, enclosure list, letter, audit log, decisions file, and screenshots of each approval dialog. | All files on the laptop, opened once to check |
| 7:30 | Spare time: a third video take if the first two have problems. | |

### Decision point (at about 1:20)

The demo index has to match the laptop's demo index on every file the laptop included or excluded. On the laptop: 14 of 14 of her files found, 9 included, 0 wrongly included, both of the mother's files with her own identifiers excluded, both unreadable files listed.

- **No file included on the NAS that the laptop did not include:** keep the submitted version. Differences toward "needs confirmation" are safe; note them.
- **A wrong inclusion whose "decided by" path ends in "check against clear"**: the assistant mishandled the check against. Install `on-file-strict.zip` in place of the submitted package, re-run the demo once (report only), and record the video with it. The strict version sends a name with only a home phone or address to the user, so the four recall letters in the main corpus move to the confirmation list; update `limits.md` and the worked example before the final submission (`round2/make_strict.py` lists what changes).
- **A wrong inclusion with any other path**: read the path the assistant wrote. If a question was answered against the six facts, keep the submitted version, record the video, and report the error honestly in `limits.md`; it is the measurement the judges asked for. If the Skill stopped or looped, check the delegations it reached in the assistant's log and fix only that step.

### Cut list, in order, if time runs short

1. Cameras.
2. Repeat use (keep only the second access run, which shows that nothing is copied twice).
3. Blind corpus (report the laptop result, clearly labelled as the laptop's).
4. The restore of one file in core 2.

Never cut: the demo run, the video, core 1, the hard corpus, core 2, the backup.

## After the day (Round 2 closes Nov 30, 11:45 PM PT)

- [ ] Edit the video to under 3:00 with English subtitles (`round2/VIDEO.md` has the text), upload it to YouTube as public, and check the link while signed out.
- [ ] Replace the laptop numbers in `on-file/references/limits.md` and `install-and-testing.md` with the NAS results, keeping the laptop results as a labelled comparison. Run `testbed/summarize.py` for any number that comes from a laptop run.
- [ ] Final package: run the checker on the folder and on the ZIP (0/0/0), and check that the package behaves as the video and the docs describe.
- [ ] Submit through the private link: the final package, the video link and anything else the finalist email asks for.
