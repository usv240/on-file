# On File testbed

Two synthetic corpora for a fictional dental practice ("Lakeside Dental") used to measure the On File Skill, a scorer, and a laptop stand-in harness. Every name, address, phone number and ID is invented. The same seed gives the same paths and text; PDF and Word files differ between builds only in embedded creation times, so hash a corpus after building it.

## What is in each corpus

| Group | Main | Hard | Purpose |
|---|---|---|---|
| target | 40 | 43 | Mention the requester, Maria Lopez (DOB 1984-03-12, LD-10432): docx, xlsx, text PDF, image-only scanned PDF, phone photo of a sign-in sheet, email exports, voicemail transcripts, two files where the name is only in document properties, a photo where the name is only in the caption, and a calendar where the name appears with no identifier. 8 (hard: 9) also hold other patients' data |
| decoy | 12 | 12 | A different patient with a longer name, Maria Lopez-Ruiz (DOB 1991-07-30, LD-11871). None may be auto-included |
| noise | 10 | 10 | "Lopez" as a company, a staff member (Mario Lopez) and a street |
| unreadable | 3 | 3 | A password-protected PDF and a truncated docx that mention the requester, and a blank scanned page. All three must appear in the index as unreadable |
| same-name person | 0 | 3 | The requester's mother, also Maria Lopez (DOB 1958-09-04, LD-09811), at the same address and with her own intake form. None may be auto-included; a name-only run must stop and ask which intake form is the requester's |
| household | 0 | 1 | The requester's spouse at the same address |
| background | 57 | 57 | Other patients, suppliers, policies, reception photos |

The hard corpus also has an email with the accented name "María López" and a day-first birth date, a lab pickup sheet with "LOPEZ, MARIA" and a dotted phone number among other patients, and a subtitle file. Those cases came from a review of the first version of the Skill, and the rules that handle them were written at the same time. The hard corpus is a stricter test, not a blind one. A blind test needs files written by someone who has not read the rules; contributions are welcome.

Ground truth per file in `expected.json`: group, how the person is mentioned (text, ocr, metadata, filename, caption, audio_transcript, subtitle), whether a strong identifier is present, whether the file also holds other people's data, and the record type (clinical, billing, correspondence, other) for target files.

## The blind corpus

`blind/` holds a third corpus written by a separate agent that was not allowed to read the Skill, the rules or the other corpora: Kestrel Bay Physiotherapy, requester Sarah Mitchell, 65 files. Its README lists the cases it chose. Build it with `python blind/make_blind.py --out blind/corpus`. It tests the rules on files they were not written for.

## Build

    python make_corpus.py --out corpus
    python make_corpus.py --variant hard --out corpus-hard

## Measure a run

1. Before an erasure run: `python score.py hash corpus/lakeside-dental before.json`
2. Run the Skill on the NAS with the corpus folder in scope and the case folder outside it. In act mode, approve each action. Save the evidence index the Skill writes.
3. Convert the index to a tab-separated file with at least the columns `path` and `decision` (included, excluded, needs confirmation, unreadable). Paths relative to `lakeside-dental/`. Add the columns `shared` (yes or no) and `record_type` to score the shared-file and retention checks.
4. `python score.py score corpus/expected.json evidence.tsv`
5. After an erasure run: `python score.py verify corpus/lakeside-dental before.json`. Expected: exactly the files planned for deletion are gone, zero changed, zero added.

## The numbers we report

- Recall (surfaced): target files the Skill showed to the user, included or needs confirmation
- Precision of auto-included files
- Decoy, noise, same-name person and household files auto-included: must all be 0
- Unreadable reported: must be 3 of 3
- Shared files flagged: every target file that also holds other patients' data must be flagged, so it is handed over as an extract and never deleted
- Record type accuracy, which drives the retention default
- Integrity after erasure: deleted = planned deletions, changed = 0, added = 0

## Laptop stand-in harness

Options beyond the basics:

- `--transcripts audio_main` uses machine transcripts of synthesized speech for the voicemails. Make them with `audio_roundtrip.ps1 -Corpus corpus\lakeside-dental -Out audio_main` (Windows, offline voice and recognizer).
- `--topk 10` limits the content search to 10 files per search term, as an index that returns its best matches would.
- `--snippet-check` checks quotes from documents against the search snippets only, not the full text.


`standin_run.py` replays the Skill's steps on a laptop with small open models through Ollama (Qwen3 4B for text, Qwen3-VL 2B instruct for reading images; the reasoning variant returns empty text on dense pages) in place of the NAS experts. `summarize.py` prints the reported measures from the run folders. It is not the Skill and does not run on the NAS. `--choose-dob` simulates the user's answer when the run stops to ask which intake form is the requester's. Results are in `RESULTS.md`.

## Notes

- Voicemail files are text transcripts standing in for audio. On the NAS, replace them with short recordings so the transcription step is exercised for real.
- The calendar file mentions both Maria Lopez and Maria Lopez-Ruiz with no identifiers. It tests that the Skill asks before including a name-only hit.
- The two document-property files test that properties are read, not only body text.
- Use of these corpora by other entrants to test their own Skills is welcome.
