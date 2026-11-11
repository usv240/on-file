# Audit log, verification and undo

## Audit log

One plain-text file in the case folder, written with the file expert in append mode. One line per event:

`time | action | path | sha256 before | result state | approval state | note`

- `action` is one of copy, extract, delete, tag, restore.
- `sha256 before` is the checksum recorded in step 6, before any change. The same checksums are already saved in the evidence index.
- `result state` is the delegation state returned: completed, failed, cancelled, waiting_approval.
- `approval state` is approved, pending or declined as reported by the platform for that file.
- `note` holds the recycle-bin path of a deleted file, the failure reason, "declined by user", "already done", or "duplicate of" plus the original path.

When it is written: after every 10 files acted on, when the user stops the run, and at the end. Each write is an append and asks for one platform approval, so an 8-file erasure asks for 8 deletion approvals and 1 log approval, and a 33-file hand-over for 33 and 4. The log is never rewritten. If a run stops between two writes, the recycle-bin paths of the last few deletions are not in the log yet; a restore then finds those files by name in the share's recycle-bin folder.

At the close, the Skill reports the audit log's own sha256. The user keeps that value with the case; if the log is edited later, its checksum no longer matches. The log is a record, not a tamper-proof ledger.

## Resuming an interrupted run

A run that stopped during the search resumes from the progress saved in the evidence index at the end of step 3 or step 5. The index's first line says which, and the run continues with the next step without searching again.

A re-run with the same case name first reads the saved evidence index and audit log (step 0), so the included list, the planned actions and the checksums come from the first run. Every file is then checked before it is acted on. For erasure, a path that is already gone is logged as "already done". For access, a copy or extract that already exists in the hand-over folder is logged as "already done". A re-run therefore never acts on a file twice, even if the run stopped between two log checkpoints.

## Verification

Before acting (step 6) the Skill records sha256, size and modified time for every included file and for a sample of up to 20 files in scope that are not included, and saves them in the evidence index.

After acting (step 8) it re-reads the sample and every included file that was not changed (retained, to edit by hand, declined, pending, and every original that was only copied or extracted), and reports "untouched files verified: N of N unchanged". For erasure it confirms each deleted path is no longer present.

This turns "nothing else was changed" from a claim into a measurement.

## Undo

Deletions are performed by the file expert and go to the recycle bin where the NAS has it enabled. The delete returns the file's path in the recycle bin, and the audit log keeps it. If no path is returned, the log keeps the original path and a restore first finds the file by name in the share's recycle-bin folder. To undo, the user names a file; the Skill takes its recycle-bin path from the log and asks the file expert to restore it. The restore waits for its own approval and is logged as a restore action.

The Skill cannot read whether the recycle bin is enabled on a share, so it asks the user in step 0, records the answer in the index, and repeats it before the first deletion. If the answer is no, the user can copy the files to the case folder first or enable the recycle bin before going on.

Erasure is complete only when the recycle-bin entry is emptied or expires. NAS snapshots and backups keep their own copies until their schedule removes them; the Skill does not touch them, and the closing message and Template C say so.

## Closing a case

An erasure case should not keep the data it erased, and an access case should not keep copies once they are delivered. Once every item is decided and the actions are done, and for access once the user has recorded the delivery date and method, the Skill offers to close the case: it saves a case record with paths, descriptions, decisions, actions, approval states and checksums, but no passages or quotes, and then deletes the full evidence index and, for access, the hand-over folder. That takes two approvals, three for an access case. The case record, the decisions file and the audit log remain as the organisation's proof of how the request was handled. They show what was done, not what the files said.

## Case tag

The tag is optional, and the user is asked once. At the end of an act run the Skill looks for a tag named dsar followed by the date received, creates and names it if it does not exist (up to two approvals), and attaches it in one call (up to one approval). It goes only on files in the case folder: the index or case record, decisions, enclosure list, letter, audit log and hand-over files. The person's own files are never tagged, because tags are visible to every NAS user who can see a file, and a tag on a patient's records would tell other staff that a request was made. The tag carries the date only, never the person's name. Files that already carry it are skipped, so a re-run asks for no new tag approval. The tag line goes into the final audit-log write.
