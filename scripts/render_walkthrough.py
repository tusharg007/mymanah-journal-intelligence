"""Package real-time browser recordings with captions below the untouched app viewport."""
from __future__ import annotations

import argparse
import json
import subprocess
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDINGS = ROOT / "artifacts" / "walkthrough-v5"


def stamp(seconds: float) -> str:
    centiseconds = round(seconds * 100)
    hours, rest = divmod(centiseconds, 360000)
    minutes, rest = divmod(rest, 6000)
    seconds, fraction = divmod(rest, 100)
    return f"{hours}:{minutes:02}:{seconds:02}.{fraction:02}"


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--overview", action="store_true")
    modes.add_argument("--desktop-only", action="store_true")
    args = parser.parse_args()
    recordings = (ROOT / "artifacts/walkthrough-policy5-overview" if args.overview
                  else ROOT / "artifacts/walkthrough-policy5-desktop" if args.desktop_only else RECORDINGS)
    reports = json.loads((recordings / "recording-report.json").read_text(encoding="utf-8"))
    assert {row["name"] for row in reports} == ({"desktop"} if args.overview or args.desktop_only else {"desktop", "mobile"}), "Requested recordings must finish"
    for row in reports:
        name = row["name"]
        source = recordings / f"{name}.webm"
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(source)
        ], text=True))
        duration = float(probe["format"]["duration"])
        assert duration >= row["end"] - 2, "Recording lost elapsed workflow time"
        width, height = row["viewport"]["width"], row["viewport"]["height"]
        band = 112 if name == "mobile" else 100
        font_size = 16 if name == "mobile" else 26
        ass = [
            "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height + band}",
            "WrapStyle: 0", "", "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            f"Style: Default,Segoe UI,{font_size},&H00FFFFFF,&H00FFFFFF,&H00122B22,&H00122B22,0,0,0,0,100,100,0,0,1,0,0,2,16,16,20,1",
            "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
        ]
        for index, chapter in enumerate(row["chapters"]):
            end = row["chapters"][index + 1]["start"] if index + 1 < len(row["chapters"]) else duration
            lines = [part for line in chapter["caption"].splitlines()
                     for part in textwrap.wrap(line, width=43 if name == "mobile" else 90)]
            caption = r"\N".join(lines)
            ass.append(f"Dialogue: 0,{stamp(chapter['start'])},{stamp(end)},Default,,0,0,0,,{caption}")
        (recordings / f"{name}.ass").write_text("\n".join(ass), encoding="utf-8")
        destination = ROOT / "docs" / ("walkthrough-short.mp4" if args.overview else f"walkthrough-{name}.mp4")
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
            "-vf", f"pad=iw:ih+{band}:0:0:color=0x122b22,ass=filename={name}.ass",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-movflags", "+faststart", "-an", str(destination)
        ], cwd=recordings, check=True)
        row["video"] = f"docs/{destination.name}"
        row["videoDurationSeconds"] = duration
        row["captionPlacement"] = "Separate band below the original app viewport; no results covered"
        print(f"{name}: {duration:.2f} seconds, complete capture with result reading time", flush=True)
        for index, evidence in enumerate(row["evidence"], start=1):
            subprocess.run([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", str(evidence["inspectVideoAt"]),
                "-i", str(destination), "-frames:v", "1", str(recordings / f"{name}-decoded-{index}.png")
            ], check=True)
        subprocess.run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-sseof", "-0.25", "-i", str(destination),
            "-frames:v", "1", str(recordings / f"{name}-decoded-final.png")
        ], check=True)
    report_name = ("walkthrough-policy5-overview.json" if args.overview
                   else "walkthrough-policy5-desktop.json" if args.desktop_only else "walkthrough-recording.json")
    (ROOT / "reports" / report_name).write_text(json.dumps(reports, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
