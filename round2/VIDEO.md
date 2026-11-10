# Round 2 demo video: script and shot list

Rules for the video: a public YouTube link, no more than 3 minutes (judges may stop at 3:00), English narration or complete English subtitles, recorded on the assigned NAS during the testing day, showing the core workflow, key capabilities and actual results. No third-party music or trademarks; UGREEN's own marks are fine.

Target length 2:50. Recorded on the 28-file demo corpus (`testbed/corpus-demo`, uploaded as `dist/round2-upload/demo.zip`), because one short run shows every case: a scanned form, text in a phone photo, a photo caption, a voicemail recording, a subtitle file, document properties, two shared files, the requester's mother with the same name, a spouse, a longer-name patient, look-alike names and two unreadable files.

## Setup before recording

- Browser window at 1920 x 1080, zoom set so the assistant's replies are readable at 720p. Close other tabs, turn off notifications, hide bookmarks.
- Recorder: OBS Studio (Display or Window Capture, 1080p, 30 fps) or Windows Game Bar (Win+Alt+R). Record the screen only; add the narration or subtitles afterwards.
- A fresh case name for each take, so no take resumes another.
- Do the untimed demo run first (runbook, 0:40 to 1:20). Record only after the decision point.
- Waits are cut, never sped up silently: every cut shows a small label, for example "4 minutes of searching cut". The video shows what really happened; nothing is staged or edited into the replies.

## Shot list

| Time | On screen | Narration or subtitle |
|---|---|---|
| 0:00 to 0:12 | The NAS file manager, the folder `lakeside-dental` open: Patients, Forms-Scanned, Photos, Voicemail, Admin. | A dental patient, Maria Lopez, asks for every record the practice holds about her. The law gives 30 days. Her data sits in forms, scans, phone photos and voicemails, and her mother has the same name. |
| 0:12 to 0:30 | The AI assistant. Paste the access request (runbook, Request texts). The Skill's reply: inputs, legal due date, days left, proposed case name. Confirm the case name. | On File is a Skill for the NAS assistant. I give it the request type, her name, the date it arrived and the folders. It shows the due date and proposes a case name. |
| 0:30 to 0:55 | The counters after steps 1, 2 and 3, one after another, with the "cut" label between them. Hold on the step 3 line: text in scans and photos, captions, recordings. | It searches file names, document text, text in scans and photos, photo captions, document properties and voicemail recordings, with the NAS's own experts. Nothing is uploaded. |
| 0:55 to 1:20 | The same-name question: two intake forms named Maria Lopez, born 1984 and 1958. Choose 1984. | Two intake forms carry her exact name, one born in 1984 and one in 1958, at the same address. It stops and asks which one is the requester's. |
| 1:20 to 1:55 | The step 5 counters, then the evidence index opened from the case folder. Scroll slowly past: an included row with its quote; the mother's form, "excluded, identifiers of a same-name person", with the quote; the longer-name patient, excluded; the subtitle file and the calendar, "needs your decision". Pause on one "decided by" path. | Every decision keeps its quote and the path of rules that made it. Her mother's files are excluded, with the line that proves it. A name with no identifier is never included: it comes to me, with the evidence for and against. |
| 1:55 to 2:15 | The closing message: included, excluded, your decisions, unreadable files, then the enclosure list and the letter. | Files that also hold other patients become extracts of her own entries. The letter and the list of records name no one else. |
| 2:15 to 2:40 | Act mode on the same case: the approval count announced, then two approval dialogs ("Allow once"), then a cut, then the audit log in the case folder. | In act mode, each copy is its own approval, and every action goes into an audit log with checksums. |
| 2:40 to 2:50 | The verify step: "untouched files verified: unchanged", and the hand-over count. | At the end it checks that every file it did not touch is unchanged. Search, decisions, letter: all on the NAS. |
| 2:50 to 3:00 | End card: On File, github.com/usv240/on-file. | On File. |

Narration: about 220 words, read slowly. If there is no narration, the same lines become burned-in subtitles; `video-subtitles.srt` holds them with draft timings to adjust in the editor.

## What must be visible somewhere in the video

The judging asks for actual results, so these appear on screen at least once, each for long enough to read:

- the legal due date and days left;
- a counters line from step 3 that shows a recording and text in a photo;
- the same-name question and the answer;
- one included row with its quote, one excluded row of the mother's with its quote;
- the "needs your decision" list;
- one approval dialog;
- the verify line.

## Editing

- Free editors: Clipchamp (built into Windows 11), DaVinci Resolve or Shotcut. Cut the waits, add the "cut" labels, import `video-subtitles.srt` or add the narration track.
- Export 1080p MP4. Check the length is under 3:00.
- Upload to YouTube as public, title "On File: a records request answered on a UGREEN AI NAS", English subtitles set. Open the link signed out to check it plays.
