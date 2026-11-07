# Audit log, verification and undo

## Audit log

One plain-text file in the case folder, written with the file expert in append mode. One line per event:

`time | action | path | sha256 before | result state | approval state | note`

- `action` is one of copy, delete, tag, restore.
- `sha256 before` is the checksum recorded in step 6, before any change. The same checksums are already saved in the evidence index.
- `result state` is the delegation state returned: completed, failed, cancelled, waiting_approval.
- `approval state` is approved, pending or declined as reported by the platform for that file.
- `note` holds the failure reason, "declined by user", "already done", or "duplicate of" plus the original path.

When it is written: after every 10 files acted on, when the user stops the run, and at the end. Each write is an append and asks for one platform approval, so a 37-file erasure asks for 37 deletion approvals and 4 log approvals rather than 74. The log is never rewritten.

## Resuming an interrupted run

Every file is checked before it is acted on. For erasure, a path that is already gone is logged as "already done". For access, a copy that already exists in the hand-over folder is logged as "already done". Re-running with the same case name therefore never acts on a file twice, even if the run stopped between two log checkpoints, and the missing log lines are written as "already done" on the re-run.

## Verification

Before acting (step 6) the Skill records sha256, size and modified time for every included file and for a sample of up to 20 files in scope that are not included, and saves them in the evidence index.

After acting (step 8) it re-reads the sample and reports "untouched files verified: N of N unchanged". For erasure it confirms each deleted path is no longer present.

This turns "nothing else was changed" from a claim into a measurement.

## Undo

Deletions are performed by the file expert and go to the recycle bin where the NAS has it enabled. The closing message states this and invites the user to name a path to restore. The restore is a separate delegation to the file expert and waits for its own approval. The audit log records the restore as an action.

If the recycle bin is not enabled for a folder, the Skill says so in the closing message of the report-only run and again before the first deletion in that folder, so the user can decide to copy first.

## Case tag

At the end of an act run the Skill creates one tag named dsar followed by the case date and case name. For access requests it is added to every original that was copied. For erasure requests the deleted files are gone, so it is added to the evidence index and the audit log in the case folder. Later, the user can list everything belonging to the case by tag, which keeps the case findable for the retention period the user applies to request records.
