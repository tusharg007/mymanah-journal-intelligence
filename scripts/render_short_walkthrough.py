"""Make a normal-speed 2-3 minute cut from complete recorded workflows."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    report = json.loads((ROOT / "reports/walkthrough-recording.json").read_text(encoding="utf8"))
    desktop = next(row for row in report if row["name"] == "desktop")
    chapters = {row["title"]: row["start"] for row in desktop["chapters"]}
    segments = [(0, chapters["J3 - An ordinary day"]),
                (chapters["Document upload"], chapters["Ask: What is the notice period during probation?"]),
                (chapters["Question outside the document"], desktop["end"])]
    duration = sum(end - start for start, end in segments)
    if duration < 120:
        segments.insert(1, (chapters["J5 - Interview anxiety"], chapters["J6 - Workload stress"]))
    elif duration > 180:
        segments[0] = (0, chapters["J2 - Positive achievement"])
    duration = sum(end - start for start, end in segments)
    assert 120 <= duration <= 180, f"Choose complete scenes to meet the requested cut length: {duration}"
    filters = [f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS[v{i}]"
               for i, (start, end) in enumerate(segments)]
    filters.append("".join(f"[v{i}]" for i in range(len(segments))) + f"concat=n={len(segments)}:v=1:a=0[out]")
    destination = ROOT / "docs/walkthrough-short.mp4"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(ROOT / desktop["video"]),
                    "-filter_complex", ";".join(filters), "-map", "[out]", "-c:v", "libx264", "-preset", "fast",
                    "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(destination)], check=True)
    (ROOT / "reports/walkthrough-short.json").write_text(json.dumps({
        "source": desktop["video"], "video": "docs/walkthrough-short.mp4", "duration_seconds": duration,
        "source_segments": [{"start": start, "end": end} for start, end in segments],
        "description": "Opens with corrected J1; complete scenes retain input entry, processing waits, results and embedded captions at original speed."
    }, indent=2), encoding="utf8")
    print(f"Short walkthrough: {duration:.2f}s", flush=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "25", "-i", str(destination), "-frames:v", "1",
                    str(ROOT / "artifacts/walkthrough-v4/short-opening.png")], check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-sseof", "-0.25", "-i", str(destination), "-frames:v", "1",
                    str(ROOT / "artifacts/walkthrough-v4/short-final.png")], check=True)


if __name__ == "__main__":
    main()
