#!/usr/bin/env python3
"""
video_analyzer.py - Analyzes reference recap videos:
- Scene cut frequency & duration distribution
- Words Per Minute (WPM) narration pace
- Audio volume & dynamics
"""

import sys
import re
import json
import subprocess

def analyze_video(video_path, max_duration=120):
    print(f"--- Analyzing {video_path} ---")

    # 1. Probe basic specs
    probe = subprocess.check_output([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", video_path
    ], text=True)
    data = json.loads(probe)
    duration = float(data["format"]["duration"])
    vstream = next(s for s in data["streams"] if s["codec_type"] == "video")
    astream = next((s for s in data["streams"] if s["codec_type"] == "audio"), None)

    print(f"Duration: {duration:.1f}s (~{duration/60:.2f} mins)")
    print(f"Resolution: {vstream['width']}x{vstream['height']} @ {vstream.get('r_frame_rate', 'unknown')} fps")

    # 2. Scene cut detection
    cmd = [
        "ffmpeg", "-i", video_path, "-t", str(max_duration),
        "-filter_complex", "select='gt(scene,0.2)',metadata=print:file=-",
        "-f", "null", "-"
    ]
    proc = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    cuts = []
    for line in proc.stdout.splitlines() + proc.stderr.splitlines():
        if "pts_time:" in line:
            m = re.search(r"pts_time:([0-9.]+)", line)
            if m:
                t = float(m.group(1))
                if not cuts or abs(t - cuts[-1]) > 0.3:
                    cuts.append(t)

    print(f"\n[Scene Analysis] (First {max_duration}s):")
    print(f"  Detected Cuts: {len(cuts)}")
    if len(cuts) > 1:
        diffs = [cuts[i+1] - cuts[i] for i in range(len(cuts)-1)]
        print(f"  Average Cut Duration: {sum(diffs)/len(diffs):.2f}s")
        print(f"  Min Cut: {min(diffs):.2f}s | Max Cut: {max(diffs):.2f}s")

    # 3. Audio volume dynamics
    vol = subprocess.run([
        "ffmpeg", "-i", video_path, "-af", "volumedetect", "-f", "null", "-"
    ], stderr=subprocess.PIPE, text=True)
    print("\n[Audio Dynamics]:")
    for line in vol.stderr.splitlines():
        if "mean_volume" in line or "max_volume" in line:
            print(" ", line.strip())

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "analysis/chaquetrix.mp4"
    analyze_video(path)
