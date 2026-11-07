"""Print the reported measures for one or more runs as a Markdown table, computed from the run files.

Usage:
    python summarize.py <expected.json>=<run dir> [<expected.json>=<run dir> ...]

Every number in RESULTS.md and in the Skill's limits reference is produced by this script, so the
documents cannot drift from the data.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

LOOKALIKE = ("decoy", "noise", "namesake", "household")


def measure(expected: Path, run: Path) -> dict:
    exp = {f["path"]: f for f in json.loads(expected.read_text(encoding="utf-8"))["files"]}
    rows = {r["path"]: r for r in csv.DictReader(open(run / "evidence.tsv", encoding="utf-8", newline=""), delimiter="\t")}
    counters = json.loads((run / "counters.json").read_text(encoding="utf-8"))
    dec = {p: (r.get("decision") or "").lower() for p, r in rows.items()}
    targets = [p for p, f in exp.items() if f["group"] == "target"]
    look = [p for p, f in exp.items() if f["group"] in LOOKALIKE]
    unread = [p for p, f in exp.items() if f["group"].startswith("unreadable")]
    included = {p for p, d in dec.items() if d == "included"}
    needs = {p for p, d in dec.items() if d.startswith("needs")}
    inc_t = [p for p in targets if p in included]
    shared_inc = [p for p in inc_t if exp[p].get("shared")]
    flagged = [p for p in shared_inc if (rows[p].get("shared") or "").lower().startswith("yes")]
    single_inc = [p for p in inc_t if not exp[p].get("shared")]
    over = [p for p in single_inc if (rows[p].get("shared") or "").lower().startswith("yes")]
    return {
        "files": len(exp),
        "found": f"{sum(1 for p in targets if p in included or p in needs)} of {len(targets)}",
        "auto": len(inc_t),
        "wrong": len(included - set(targets)),
        "lookalike_included": f"{sum(1 for p in look if p in included)} of {len(look)}",
        "unreadable_listed": f"{sum(1 for p in unread if dec.get(p) == 'unreadable')} of {len(unread)}",
        "shared_flagged": f"{len(flagged)} of {len(shared_inc)}",
        "shared_total": sum(1 for p in targets if exp[p].get("shared")),
        "over_flagged": f"{len(over)} of {len(single_inc)}",
        "to_user": len(needs),
        "doc_pass_added": counters.get("document_pass_added", 0),
        "seconds": round(counters.get("total_seconds", 0)),
        "missed": [p for p in targets if p not in included and p not in needs],
    }


def main(argv):
    pairs = [a.split("=", 1) for a in argv[1:]]
    if not pairs:
        print(__doc__)
        return 2
    res = [(run, measure(Path(e), Path(run))) for e, run in pairs]
    labels = [
        ("files", "Files in scope"),
        ("found", "Requester's files found (included or sent to the user)"),
        ("auto", "Included automatically"),
        ("wrong", "Wrongly included"),
        ("lookalike_included", "Look-alike files included (other people, companies, streets)"),
        ("unreadable_listed", "Unreadable files listed with a reason"),
        ("shared_flagged", "Included files holding others' data, flagged"),
        ("over_flagged", "Single-person files wrongly flagged as shared"),
        ("to_user", "Items left for the user to decide"),
        ("doc_pass_added", "Files added by the document pass"),
        ("seconds", "Wall time, seconds"),
    ]
    print("| Measure | " + " | ".join(r for r, _ in res) + " |")
    print("|---|" + "---|" * len(res))
    for k, lab in labels:
        print(f"| {lab} | " + " | ".join(str(m[k]) for _, m in res) + " |")
    for run, m in res:
        if m["missed"]:
            print(f"\nMissed in {run}: " + "; ".join(m["missed"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
