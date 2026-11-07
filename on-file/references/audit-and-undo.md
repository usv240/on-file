# Audit log, verification and undo

## Audit log

One plain-text file in the case folder, written with the file expert in append mode. One line per event:

`time | action | path | sha256 before | result state | approval state | note`

- `action` is one of copy, extract, delete, tag, restore.
- `sha256 before` is the checksum recorded in step 6, before any change. The same checksums are already saved in the evidence index.
- `result state` is the delegation state returned: completed, failed, cancelled, waiting_approval.
- `approval state` is approved, pending or declined as reported by the platform for that file.
- `note` holds the recycle-bin path of a deleted file, the failure reason, "declined by user", "already done", or "duplicate of" plus the original path.

When it is written: after every 10 files acted on, when the user stops the run, and at the end. Each write is an append and asks for one platform approval, so a 12-file erasure asks for 12 deletion approvals and 2 log approvals rather than 24. The log is never rewritten.

At the close, the Skill reports the audit log's own sha256. The user keeps that value with the case; if the log is edited later, its checksum no longer matches. The log is a record, not a tamper-proof ledger.

## Resuming an interrupted run

A re-run with the same case name first reads the saved evidence index and audit log (step 0), so the included list, the planned actions and the checksums come from the first run. Every file is then checked before it is acted on. For erasure, a path that is already gone is logged as "already done". For access, a copy or extract that already exists in the hand-over folder is logged as "already done". A re-run therefore never acts on a file twice, even if the run stopped between two log checkpoints.

## Verification

Before acting (step 6) the Skill records sha256, size and modified time for every included file and for a sample of up to 20 files in scope that are not included, and saves them in the evidence index.

After acting (step 8) it re-reads the sample and every included file that was not changed (retained, to edit by hand, declined, pending, and every original that was only copied or extracted), and reports "untouched files verified: N of N unchanged". For erasure it confirms each deleted path is no longer present.

This turns "nothing else was changed" from a claim into a measurement.

## Undo

Deletions are performed by the file expert and go to the recycle bin where the NAS has it enabled. The delete returns the file's path in the recycle bin, and the audit log keeps it. To undo, the user names a file; the Skill takes its recycle-bin path from the log and asks the file expert to restore it. The restore waits for its own approval and is logged as a restore action.

The Skill cannot read whether the recycle bin is enabled on a share, so it asks the user in step 0, records the answer in the index, and repeats it before the first deletion. If the answer is no, the user can copy the files to the case folder first or enable the recycle bin before going on.

Erasure is complete only when the recycle-bin entry is emptied or expires. NAS snapshots and backups keep their own copies until their schedule removes them; the Skill does not touch them, and the closing message and Template C say so.

## Case tag

At the end of an act run the Skill looks for a tag named dsar followed by the date received, creates it if it does not exist (one approval), and attaches it to the files in one call (up to one approval). The tag carries the date only, never the person's name, because tags are visible to every NAS user who can see a file. For access requests it is attached to every original that was copied or extracted. For erasure requests the deleted files are gone, so it is attached to the case files in the case folder. Files that already carry the tag are skipped, so a re-run asks for no new tag approval. Later, the user can list everything belonging to the case by tag, and the index says which person each date belongs to.
