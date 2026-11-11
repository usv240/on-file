"""Build the submission ZIP from the on-file folder and check it.

    python build_package.py [path/to/uliya-skill-kit/scripts/check-skill.mjs]

Writes dist/on-file.zip holding one folder, on-file/, with SKILL.md and references/*.md, the same layout as
UGREEN's own uliya-skill-kit ZIP. Checks the submission limits (10 MB zipped and unzipped, 1 MB per file,
100 files, Markdown only, no dash characters), then unzips the result into a temporary folder and, when the
checker's path is given, runs the official checker on the unzipped copy."""
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "on-file"
OUT = ROOT / "dist" / "on-file.zip"


def main() -> int:
    files = [SRC / "SKILL.md"] + sorted((SRC / "references").glob("*.md"))
    extra = [p for p in SRC.rglob("*") if p.is_file() and p not in files]
    assert not extra, f"files that would be left out: {extra}"
    for f in files:
        text = f.read_text(encoding="utf-8")
        assert f.stat().st_size <= 1_000_000, f"{f} over 1 MB"
        assert "—" not in text and "–" not in text, f"dash character in {f}"
    OUT.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(f, "on-file/" + f.relative_to(SRC).as_posix())
    unzipped = sum(f.stat().st_size for f in files)
    assert OUT.stat().st_size <= 10_000_000 and unzipped <= 10_000_000 and len(files) <= 100
    print(f"{OUT}: {len(files)} files, {OUT.stat().st_size} bytes zipped, {unzipped} unzipped")

    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(OUT) as z:
            z.extractall(tmp)
        top = sorted(p.name for p in Path(tmp).iterdir())
        assert top == ["on-file"], top
        same = all((Path(tmp) / "on-file" / f.relative_to(SRC)).read_bytes() == f.read_bytes() for f in files)
        assert same, "unzipped copy differs from the source"
        print("unzipped copy matches on-file/")
        if len(sys.argv) > 1:
            r = subprocess.run(["node", sys.argv[1], str(Path(tmp) / "on-file")], capture_output=True, text=True, encoding="utf-8")
            j = json.loads(r.stdout)
            print(f"checker on the unzipped copy: {j['status']}, {j['summary']}")
            if j["status"] != "static-pass" or any(j["summary"].values()):
                for d in j["diagnostics"]:
                    print(" ", d["severity"], d["code"], d.get("file"), d.get("line"))
                return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
