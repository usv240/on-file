"""Compare the index the Skill saved on the NAS with the laptop stand-in's index for the same corpus, file by file.

    python round2/compare_index.py <nas index file> <laptop evidence.tsv> [<expected.json>]

Run it right after the first demo run on the test day. Prints how many files got the same decision (included,
excluded, needs confirmation, unreadable), lists each difference with the "decided by" path the NAS assistant wrote,
and flags first any file the NAS included that the laptop did not: a wrong inclusion is the one failure that
needs its "decided by" path read before going on (see RUNBOOK.md, decision point). With the answer key given,
each difference also shows whose file it really is."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "testbed"))
from score import kind, read_index  # noqa: E402


NAMES = {"needs": "needs confirmation"}


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    laptop = {r["path"]: r for r in read_index(Path(argv[2]), [])}
    truth = {}
    if len(argv) > 3:
        truth = {f["path"]: f for f in json.loads(Path(argv[3]).read_text(encoding="utf-8"))["files"]}
    nas = {r["path"]: r for r in read_index(Path(argv[1]), list(laptop) + list(truth))}
    paths = sorted(set(nas) | set(laptop))
    same, diffs = 0, []
    for p in paths:
        a = NAMES.get(k := kind(nas[p].get("decision", "")), k) if p in nas else "(not in NAS index)"
        b = NAMES.get(k := kind(laptop[p].get("decision", "")), k) if p in laptop else "(not in laptop index)"
        if a == b:
            same += 1
        else:
            diffs.append((a == "included", p, a, b))
    print(f"same decision: {same} of {len(paths)}")
    wrong = [d for d in diffs if d[0]]
    print(f"included on the NAS but not on the laptop: {len(wrong)}" + ("   <- see RUNBOOK.md, decision point" if wrong else ""))
    for _, p, a, b in sorted(diffs, key=lambda d: not d[0]):
        whose = ""
        if p in truth:
            whose = f"  [answer key: {truth[p]['group']}, {'the requester' if truth[p]['mentions_requester'] else 'not the requester'}]"
        by = nas.get(p, {}).get("decided_by", "")
        print(f"  {p}\n      NAS: {a}   laptop: {b}{whose}\n      NAS decided by: {by[:160]}")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
