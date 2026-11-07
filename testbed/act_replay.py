"""Replay the Skill's act mode (step 7 and step 8) on a copy of a corpus, from a finished run's index.

This is the laptop stand-in for the NAS file actions: it copies, extracts and deletes exactly what the
evidence index plans, writes the audit log at the Skill's checkpoints, runs the same case a second time
to check nothing is acted on twice, restores one deleted file from the recycle folder, and verifies every
file in scope by sha256. It does not call a model.

Usage:
    python act_replay.py --corpus corpus/lakeside-dental --run run8_main --mode erasure --work replay/main-erasure
    python act_replay.py --corpus corpus/lakeside-dental --run run8_main --mode access  --work replay/main-access
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import shutil
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("sr", HERE / "standin_run.py")
sr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sr)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): sha(p) for p in root.rglob("*") if p.is_file()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--run", required=True)
    ap.add_argument("--mode", choices=["access", "erasure"], required=True)
    ap.add_argument("--work", required=True)
    a = ap.parse_args()

    work = Path(a.work)
    if work.exists():
        shutil.rmtree(work)
    files = work / "files"          # the folders in scope
    recycle = work / "recycle"      # the share's recycle bin
    case = work / "case"            # the case folder
    shutil.copytree(a.corpus, files)
    recycle.mkdir(parents=True)
    case.mkdir(parents=True)

    rows = list(csv.DictReader(open(Path(a.run) / "evidence.tsv", encoding="utf-8", newline=""), delimiter="\t"))
    counters = json.loads((Path(a.run) / "counters.json").read_text(encoding="utf-8"))
    ids = {"name": None}
    ids.update(counters.get("identifiers_extracted") or {})
    name_guess = next((r["passage"] for r in rows if r["decision"] == "included"), "")
    ids["name"] = counters.get("requester_name") or ""
    if not ids["name"]:
        exp_path = Path(a.corpus).parent / "expected.json"
        ids["name"] = json.loads(exp_path.read_text(encoding="utf-8"))["requester"]["name"]

    # OCR lines the run saved: for an image the index's passage holds the OCR lines that name the person,
    # which is exactly what the Skill's extract of an image keeps
    ocr_text = {r["path"]: r["passage"].replace(" / ", "\n") for r in rows if "ocr" in r.get("source", "")}

    before = snapshot(files)
    included = [r for r in rows if r["decision"] == "included"]
    key = "access_action" if a.mode == "access" else "erasure_action"
    planned = {r["path"]: r[key] for r in included}

    def act_pass(label: str) -> dict:
        log, pending, stats = [], [], {"acted": 0, "already done": 0, "skipped (retain or edit by hand)": 0, "extract refused": 0, "log writes": 0}

        def write_log(force=False):
            if pending and (force or len(pending) >= 10):
                with open(case / "audit-log.txt", "a", encoding="utf-8") as f:
                    f.write("".join(pending))
                stats["log writes"] += 1
                pending.clear()

        if a.mode == "access" and not (case / "hand-over").exists():
            (case / "hand-over").mkdir()
            stats["hand-over folder created"] = 1
        for rp, action in planned.items():
            src = files / rp
            t = time.strftime("%Y-%m-%d %H:%M:%S")
            if action == "copy":
                dst = case / "hand-over" / Path(rp).name
                if dst.exists():
                    stats["already done"] += 1
                    pending.append(f"{t} | copy | {rp} | {before[rp][:12]} | completed | approved | already done\n")
                else:
                    shutil.copy2(src, dst)
                    stats["acted"] += 1
                    pending.append(f"{t} | copy | {rp} | {before[rp][:12]} | completed | approved |\n")
            elif action == "extract":
                dst = case / "hand-over" / f"extract of {Path(rp).name}.txt"
                if dst.exists():
                    stats["already done"] += 1
                    pending.append(f"{t} | extract | {rp} | {before[rp][:12]} | completed | approved | already done\n")
                else:
                    text, st = sr.extract_text(src)
                    if text is None:
                        # a photo or scanned image: the Skill's extract is the lines of the step 4 OCR text that
                        # name the person (SKILL.md step 7), so use the OCR text the run saved for this file
                        text = ocr_text.get(rp) or sr.doc_metadata(src)
                    lines = [ln for ln in (text or "").splitlines() if ln.strip() and (set(sr.mentions(ln, ids)) - {"name-partial"})]
                    if not lines:
                        stats["extract refused"] += 1
                        pending.append(f"{t} | extract | {rp} | {before[rp][:12]} | failed | approved | no line names the person; moved to edit by hand\n")
                    else:
                        dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
                        stats["acted"] += 1
                        pending.append(f"{t} | extract | {rp} | {before[rp][:12]} | completed | approved | {len(lines)} lines\n")
            elif action == "delete":
                if not src.exists():
                    stats["already done"] += 1
                    pending.append(f"{t} | delete | {rp} | {before[rp][:12]} | completed | approved | already done\n")
                else:
                    dst = recycle / rp
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    stats["acted"] += 1
                    pending.append(f"{t} | delete | {rp} | {before[rp][:12]} | completed | approved | recycle path {dst.relative_to(work).as_posix()}\n")
            else:
                stats["skipped (retain or edit by hand)"] += 1
                continue
            write_log()
        write_log(force=True)
        return stats

    first = act_pass("first")
    after_first = snapshot(files)
    second = act_pass("second")
    after_second = snapshot(files)

    deleted = sorted(k for k in before if k not in after_first)
    changed = sorted(k for k in before if k in after_first and after_first[k] != before[k])
    added = sorted(k for k in after_first if k not in before)
    planned_del = sorted(k for k, v in planned.items() if v == "delete")
    result = {
        "mode": a.mode,
        "files_in_scope": len(before),
        "planned": {v: sum(1 for x in planned.values() if x == v) for v in sorted(set(planned.values()))},
        "first_run": first,
        "second_run": second,
        "integrity_after_first_run": {
            "deleted": len(deleted), "deleted_equals_planned_deletions": deleted == planned_del,
            "changed": len(changed), "added": len(added),
        },
        "second_run_changed_nothing": after_second == after_first,
        "approvals_first_run": first["acted"] + first["extract refused"] + first["log writes"] + first.get("hand-over folder created", 0),
    }
    if a.mode == "access":
        ho = case / "hand-over"
        extracts = list(ho.glob("extract of *"))
        bad = []
        for e in extracts:
            for ln in e.read_text(encoding="utf-8").splitlines():
                if not (set(sr.mentions(ln, ids)) - {"name-partial"}):
                    bad.append((e.name, ln))
        result["hand_over"] = {"copies": len([p for p in ho.iterdir() if not p.name.startswith("extract of")]),
                               "extracts": len(extracts), "extract lines without the person": len(bad)}
    if planned_del:
        rp = planned_del[0]
        shutil.move(str(recycle / rp), str(files / rp))
        result["restore"] = {"path": rp, "hash_matches_before": sha(files / rp) == before[rp]}
    result["audit_log_lines"] = sum(1 for _ in open(case / "audit-log.txt", encoding="utf-8"))
    (work / "replay.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
