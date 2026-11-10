"""Build the one-minute prototype walkthrough video from the gallery images and the two video cards.

    python proposal/gallery/render.py      # first: renders the images
    python proposal/gallery/make_video.py  # writes proposal/gallery/video/on-file-walkthrough.mp4

Each still gets a slow push-in and the slides cross-fade. Silent: every slide carries its own text.
Needs ffmpeg on PATH."""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FPS = 30
W, H = 1620, 1080
FADE = 0.7
SLIDES = [  # (image, seconds on screen)
    (HERE / "video" / "v0.png", 6),
    (HERE / "on-file-gallery-1.png", 9),
    (HERE / "on-file-gallery-2.png", 11),
    (HERE / "on-file-gallery-3.png", 11),
    (HERE / "on-file-gallery-4.png", 11),
    (HERE / "on-file-gallery-5.png", 10),
    (HERE / "video" / "v6.png", 7),
]


def main() -> None:
    args = ["ffmpeg", "-y", "-loglevel", "error"]
    parts = []
    for i, (img, sec) in enumerate(SLIDES):
        args += ["-i", str(img)]
        frames = int(sec * FPS)
        # scale up first so the push-in stays sharp, then a 3 percent zoom over the slide, centred
        parts.append(
            f"[{i}:v]scale={W * 2}:{H * 2},zoompan=z='1+0.03*on/{frames}':d={frames}:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={FPS},setsar=1,format=yuv420p[s{i}]")
    chain, offset, last = [], 0.0, "s0"
    for i in range(1, len(SLIDES)):
        offset += SLIDES[i - 1][1] - FADE
        out = f"x{i}"
        chain.append(f"[{last}][s{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[{out}]")
        last = out
    out = HERE / "video" / "on-file-walkthrough.mp4"
    args += ["-filter_complex", ";".join(parts + chain), "-map", f"[{last}]",
             "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)]
    subprocess.run(args, check=True)
    total = sum(s for _, s in SLIDES) - FADE * (len(SLIDES) - 1)
    print(f"{out}  {total:.1f} s  {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
