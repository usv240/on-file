"""Build the four test corpora as the NAS should hold them, ready to upload on the test day.

    python round2/make_upload.py

Writes dist/round2-upload/<corpus>/ and dist/round2-upload/<corpus>.zip for demo, main, hard and blind.
On the laptop the voicemails are transcript stand-ins (Voicemail/*.txt); on the NAS they must be recordings,
so each Voicemail/*.txt is replaced by its synthesized .wav from testbed/audio_<corpus>/. Every other file is
copied unchanged, so the answer keys in testbed/ still apply. All people and identifiers are invented."""
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TB = ROOT / "testbed"
OUT = ROOT / "dist" / "round2-upload"
CORPORA = {
    "demo": (TB / "corpus-demo" / "lakeside-dental", TB / "audio_demo"),
    "main": (TB / "corpus" / "lakeside-dental", TB / "audio_main"),
    "hard": (TB / "corpus-hard" / "lakeside-dental", TB / "audio_hard"),
    "blind": (TB / "blind" / "corpus" / "KestrelBay_Physio", None),
}


def main() -> int:
    if OUT.exists():
        shutil.rmtree(OUT)
    problems = 0
    for name, (src, audio) in CORPORA.items():
        dst = OUT / name / src.name
        n_files = n_wav = 0
        for f in sorted(src.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(src)
            if audio and rel.parts[0] == "Voicemail" and f.suffix == ".txt":
                wav = audio / (f.stem + ".wav")
                if not wav.exists():
                    print(f"  MISSING recording for {name}/{rel}: run testbed/audio_roundtrip.ps1 first")
                    problems += 1
                    continue
                target = dst / rel.with_suffix(".wav")
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(wav, target)
                n_wav += 1
            else:
                target = dst / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, target)
            n_files += 1
        with zipfile.ZipFile(OUT / f"{name}.zip", "w", zipfile.ZIP_DEFLATED) as z:
            for f in sorted((OUT / name).rglob("*")):
                if f.is_file():
                    z.write(f, f.relative_to(OUT / name).as_posix())
        print(f"{name:6} {n_files:4} files ({n_wav} recordings)  -> {OUT / (name + '.zip')}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
