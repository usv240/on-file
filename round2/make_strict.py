"""Build the strict variant of the Skill, kept ready for the Round 2 test day.

    python round2/make_strict.py [path/to/check-skill.mjs]

In the submitted Skill, a file with the exact name and only a home phone or address gets the check against and
is included when that check finds nothing. In a laptop test where a small model applied the rules itself, its
mistakes came after the checks, not in the six questions. The strict variant removes the check against: such a
file goes to the user, listed apart. The only automatic inclusions left are an ID or email (question 3) and the
exact name with the date of birth (question 4). Use it only if the NAS assistant is seen to mishandle the check.

Writes dist/strict/on-file/ and dist/on-file-strict.zip, and runs the kit checker when its path is given.
In the worked example the four recall letters would move from included to the user's list; its counts are left
as they are and a note says so, to be updated if the variant is adopted."""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "on-file"
DST = ROOT / "dist" / "strict" / "on-file"  # the folder name must equal the Skill name

EDITS = {
    "SKILL.md": [
        ('No: is (e) yes? Yes: run the check against. No: run the two checks.',
         'No: is (e) yes? Yes: "needs confirmation", listed apart in the closing message as name and home phone or address only. No: run the two checks.'),
        ('(d) no, (e) yes: check against"', '(d) no, (e) yes: needs confirmation"'),
        ('- The check against, from question 4. Did it return a checked passage, for example a different birth date or a "Sr."? '
         'Yes: "needs confirmation". No: "included, auto, against-check clear". A relative with the same name and home would match '
         'the name and the phone or address too, so the closing message lists these files apart: a same-name relative with no form '
         'in scope would pass this check.\n', ''),
        ('- The two checks, from questions 2, 4 and 5.', '- The two checks, from questions 2 and 5.'),
    ],
    "references/disambiguation.md": [
        ('the against-check runs first; any checked passage sends the file to the user, otherwise include and list it apart in the closing message',
         'the user decides; such files are listed apart in the closing message'),
        ('nothing marks the shared phone or address, and a file with the exact name and that phone or address is included once the check '
         'against finds nothing. Such files are listed apart in the closing message so the user can look them over before act mode.',
         'nothing marks the shared phone or address, so a file with the exact name and only that phone or address is never included '
         'automatically: it goes to the user, listed apart in the closing message.'),
    ],
    "references/limits.md": [
        ('a file with the exact name and only the shared phone or address is included when the check against finds nothing. '
         'The closing message lists such files apart for a look before act mode.',
         'a file with the exact name and only a phone or address is never included automatically; it goes to the user, listed apart '
         'in the closing message.'),
    ],
    "references/example-output.md": [
        ('## Input\n',
         'This example was produced before the check against was removed. In this version a file with the name and only a home '
         'phone or address goes to the user, so the four recall letters below would be on the confirmation list.\n\n## Input\n'),
    ],
}


def main() -> int:
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    for rel, edits in EDITS.items():
        p = DST / rel
        s = p.read_text(encoding="utf-8")
        for old, new in edits:
            n = s.count(old)
            if n != 1:
                print(f"{rel}: expected one match, found {n}: {old[:70]!r}")
                return 1
            s = s.replace(old, new)
        p.write_text(s, encoding="utf-8")
    gone = ("run the check against", "against-check", "The check against, from")
    left = [str(p.relative_to(DST)) for p in DST.rglob("*.md")
            if p.name != "example-output.md" and any(g in p.read_text(encoding="utf-8") for g in gone)]
    if left:
        print("still mentions the check against:", left)
    out = ROOT / "dist" / "on-file-strict.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for f in [DST / "SKILL.md"] + sorted((DST / "references").glob("*.md")):
            z.write(f, "on-file/" + f.relative_to(DST).as_posix())
    print(f"written {out}")
    if len(sys.argv) > 1:
        r = subprocess.run(["node", sys.argv[1], str(DST)], capture_output=True, text=True, encoding="utf-8")
        import json
        j = json.loads(r.stdout)
        print(f"checker: {j['status']}, {j['summary']}")
        return 0 if j["status"] == "static-pass" and not any(j["summary"].values()) else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
