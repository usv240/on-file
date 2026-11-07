"""Score an On File evidence index against expected.json, and verify file integrity.

Subcommands:
    python score.py hash  <corpus-root> <out.json>            record sha256 of every file (run before an erasure run)
    python score.py verify <corpus-root> <before.json>         compare current files to the recorded hashes
    python score.py score <expected.json> <evidence.tsv>       compute recall, precision, decoy touches, unreadable reported

The evidence index is a tab-separated file with a header line containing at least:
    path    decision
where decision is one of: included | excluded | needs confirmation | unreadable
Paths are relative to the corpus root, forward slashes. Extra columns are ignored.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_hash(root: Path, out: Path):
    rec = {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in root.rglob("*") if p.is_file()}
    out.write_text(json.dumps(rec, indent=1), encoding="utf-8")
    print(f"hashed {len(rec)} files -> {out}")


def cmd_verify(root: Path, before_path: Path):
    before = json.loads(before_path.read_text(encoding="utf-8"))
    now = {str(p.relative_to(root)).replace("\\", "/"): sha256(p) for p in root.rglob("*") if p.is_file()}
    deleted = sorted(k for k in before if k not in now)
    changed = sorted(k for k in before if k in now and now[k] != before[k])
    added = sorted(k for k in now if k not in before)
    print(f"before: {len(before)}  now: {len(now)}")
    print(f"deleted: {len(deleted)}  changed: {len(changed)}  added: {len(added)}")
    for k in deleted:
        print("  deleted ", k)
    for k in changed:
        print("  CHANGED ", k)
    for k in added:
        print("  added   ", k)
    return deleted, changed, added


def cmd_score(expected_path: Path, evidence_path: Path):
    exp = json.loads(expected_path.read_text(encoding="utf-8"))
    files = {f["path"]: f for f in exp["files"]}
    with open(evidence_path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    decision = {}
    row_by_path = {}
    for r in rows:
        p = (r.get("path") or "").strip().replace("\\", "/")
        if p.startswith("lakeside-dental/"):
            p = p[len("lakeside-dental/"):]
        decision[p] = (r.get("decision") or "").strip().lower()
        row_by_path[p] = r

    targets = [p for p, f in files.items() if f["group"] == "target"]
    decoys = [p for p, f in files.items() if f["group"] == "decoy"]
    unreadables = [p for p, f in files.items() if f["group"].startswith("unreadable")]
    noise = [p for p, f in files.items() if f["group"] == "noise"]

    included = {p for p, dcs in decision.items() if dcs == "included"}
    needs = {p for p, dcs in decision.items() if dcs.startswith("needs")}
    unread = {p for p, dcs in decision.items() if dcs == "unreadable"}
    surfaced = included | needs  # found and shown to the user in some form

    tp_incl = sum(1 for p in targets if p in included)
    tp_surf = sum(1 for p in targets if p in surfaced)
    fp_incl = sum(1 for p in included if p not in targets)
    decoy_incl = sum(1 for p in decoys if p in included)
    decoy_needs = sum(1 for p in decoys if p in needs)
    noise_incl = sum(1 for p in noise if p in included)
    unread_ok = sum(1 for p in unreadables if p in unread)
    unread_silent = [p for p in unreadables if p not in decision]
    missed = [p for p in targets if p not in surfaced]
    missed_by_how = {}
    for p in missed:
        for h in files[p]["how"]:
            missed_by_how[h] = missed_by_how.get(h, 0) + 1

    def pct(a, b):
        return f"{a}/{b} = {100.0 * a / b:.1f}%" if b else "n/a"

    print("== On File score ==")
    print(f"Recall, surfaced (included or needs confirmation): {pct(tp_surf, len(targets))}")
    print(f"Recall, auto-included:                              {pct(tp_incl, len(targets))}")
    print(f"Precision of included:                              {pct(tp_incl, len(included))}")
    print(f"Decoy (same-surname person) auto-included:          {decoy_incl} of {len(decoys)}   (target 0)")
    print(f"Decoy sent to needs-confirmation:                   {decoy_needs} of {len(decoys)}")
    print(f"Noise (company, staff, street) auto-included:       {noise_incl} of {len(noise)}   (target 0)")
    print(f"Unreadable reported as unreadable:                  {unread_ok} of {len(unreadables)}")
    print(f"Unreadable silently missing from index:             {len(unread_silent)}")
    print(f"Target files needing confirmation (not auto):       {sum(1 for p in targets if p in needs)}")
    for grp, label in (("namesake", "Same-name person (same household)"), ("household", "Household member at the same address")):
        g = [p for p, f in files.items() if f["group"] == grp]
        if g:
            print(f"{label} auto-included: {sum(1 for p in g if p in included)} of {len(g)}   (target 0); "
                  f"to confirmation: {sum(1 for p in g if p in needs)}; excluded: {sum(1 for p in g if p in decision and decision[p].startswith('excluded'))}")

    # files that also hold other patients' data, and record types (only when the index has those columns)
    inc_targets = [p for p in targets if p in included]
    if inc_targets and "shared" in (rows[0] if rows else {}):
        def flagged(p):
            return (row_by_path[p].get("shared") or "").lower().startswith("yes")
        truth_shared = [p for p in inc_targets if files[p].get("shared")]
        truth_single = [p for p in inc_targets if not files[p].get("shared")]
        leak = [p for p in truth_shared if not flagged(p)]
        over = [p for p in truth_single if flagged(p)]
        print(f"Shared files flagged (others' data in file):        {pct(len(truth_shared) - len(leak), len(truth_shared))}")
        print(f"Shared files NOT flagged (would be handed over whole): {len(leak)}   (target 0)")
        for p in leak:
            print("  not flagged ", p)
        print(f"Single-person files flagged as shared (extra work): {len(over)} of {len(truth_single)}")
        for p in over:
            print("  over-flagged", p, "|", row_by_path[p].get("shared", "")[:60])
        typed = [p for p in inc_targets if files[p].get("record_type")]
        rt_ok = sum(1 for p in typed if (row_by_path[p].get("record_type") or "") == files[p]["record_type"])
        print(f"Record type correct:                                {pct(rt_ok, len(typed))}")
        for p in typed:
            got = row_by_path[p].get("record_type") or ""
            if got != files[p]["record_type"]:
                print(f"  type {got:>14} expected {files[p]['record_type']:<14} {p}")
    if missed:
        print(f"Missed targets ({len(missed)}), by how they mention the person: {missed_by_how}")
        for p in missed:
            print("  missed ", p, files[p]["how"], files[p].get("note", ""))
    if fp_incl:
        print(f"False includes ({fp_incl}):")
        for p in sorted(included - set(targets)):
            print("  false  ", p, files.get(p, {}).get("group", "unknown"))


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd = argv[1]
    if cmd == "hash" and len(argv) == 4:
        cmd_hash(Path(argv[2]), Path(argv[3]))
    elif cmd == "verify" and len(argv) == 4:
        cmd_verify(Path(argv[2]), Path(argv[3]))
    elif cmd == "score" and len(argv) == 4:
        cmd_score(Path(argv[2]), Path(argv[3]))
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
