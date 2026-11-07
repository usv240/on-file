# Audit log, verification and undo

## Audit log

One plain-text file in the case folder, appended after every state change in act mode. One line per event:

`time | action | path | sha256 before | result state | approval state | note`

- `action` is one of copy, delete, tag, restore.
- `sha256 before` is the checksum recorded in step 6, before any change.
- `result state` is the delegation state returned: completed, failed, cancelled, waiting_approval.
- `approval state` is approved, pending or declined as reported by the platform for that file.
- `note` holds the failure reason, "skipped by user", or "duplicate of" plus the original path.

The log is appended, never rewritten. An interrupted run leaves a readable log; re-running with the same case name reads the log first and does not act again on paths already marked completed.

## Verification

Before acting (step 6) the Skill records sha256, size and modified time for every included file and for a sample of up to 20 files in scope that are not included.

After acting (step 8) it re-reads the sample and reports "untouched files verified: N of N unchanged". For erasure it confirms each deleted path is no longer present.

This turns "nothing else was changed" from a claim into a measurement.

## Undo

Deletions are performed by the file expert and go to the recycle bin where the NAS has it enabled. The closing message states this and invites the user to name a path to restore. The restore is a separate delegation to the file expert and waits for its own approval. The audit log records the restore as an action.

If the recycle bin is not enabled for a folder, the Skill says so in the closing message before any deletion in that folder is approved, so the user can decide to copy first.

## Case tag

Every file acted on receives a tag named dsar followed by the case date and case name. Later, the user can list all files of the case by tag, which keeps the case findable for the retention period the user applies to request records.
