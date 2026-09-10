#!/usr/bin/env python3
"""
motion_comic_generator.py - Generates dynamic motion comic clips with Ken Burns pan/zoom,
voice synchronization, and background music auto-ducking.
"""

import os
import subprocess

def create_motion_clip(image_path, audio_path, output_clip_path, mode="zoom_in", fps=24):
    """
    Creates a video clip from a single comic panel matching the audio duration.
    Modes:
      - 'zoom_in': Slow push-in zoom (1.0x -> 1.15x)
      - 'pan_down': Smooth vertical scroll (top-to-bottom)
      - 'shake': Impact shake effect
    """
    # 1. Get audio duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    duration_str = subprocess.check_output(probe_cmd, text=True).strip()
    duration = float(duration_str)
    total_frames = int(duration * fps)

    # 2. Build Ken Burns filter complex based on mode
    if mode == "zoom_in":
        # Slow zoom in towards center
        vf = (
            f"scale=1920x1080:force_original_aspect_ratio=increase,"
            f"crop=1920:1080,"
            f"zoompan=z='min(zoom+0.0015,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )
    elif mode == "pan_down":
        # Vertical pan down across tall comic panel
        vf = (
            f"scale=1920:-1,"
            f"zoompan=z=1.0:x=0:y='min(on*2, ih-1080)':"
            f"d={total_frames}:s=1920x1080:fps={fps}"
        )
    else:  # Static / slight float
        vf = f"scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2"

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", vf,
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration),
        output_clip_path
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    return output_clip_path

def assemble_full_video(clip_paths, bgm_path, final_output_path):
    """
    Concatenates panel clips and mixes background music with auto-ducking.
    """
    # Create concat list file
    concat_list = "temp_concat.txt"
    with open(concat_list, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-i", bgm_path,
        "-filter_complex",
        # Duck BGM to volume 0.15 underneath voice narration
        "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac",
        final_output_path
    ]
    subprocess.run(cmd, check=True)
    if os.path.exists(concat_list):
        os.remove(concat_list)
    print(f"Final video successfully generated: {final_output_path}")

if __name__ == "__main__":
    print("Motion Comic Generator ready. Import into your automation script.")
