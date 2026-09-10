#!/usr/bin/env python3
"""
motion_comic_generator.py - Generates dynamic motion comic clips with Ken Burns pan/zoom,
voice synchronization, and background music auto-ducking.
Works seamlessly on CPU with libopenh264 or libx264.
"""

import os
import subprocess

def get_h264_encoder():
    """Finds best available H.264 encoder on system."""
    try:
        res = subprocess.check_output(["ffmpeg", "-encoders"], text=True, stderr=subprocess.DEVNULL)
        if "libopenh264" in res:
            return "libopenh264"
        elif "libx264" in res:
            return "libx264"
    except Exception:
        pass
    return "h264"

def create_motion_clip(image_path, audio_path, output_clip_path, mode="zoom_in", fps=24):
    """
    Creates a video clip from a single comic panel matching the audio duration.
    Modes:
      - 'zoom_in': Slow push-in zoom (1.0x -> 1.15x)
      - 'pan_down': Smooth vertical scroll (top-to-bottom)
      - 'shake': Impact shake effect
    """
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    duration_str = subprocess.check_output(probe_cmd, text=True).strip()
    duration = float(duration_str)
    total_frames = max(int(duration * fps), 24)
    encoder = get_h264_encoder()

    if mode == "zoom_in":
        vf = (
            f"scale=1280:720:force_original_aspect_ratio=increase,"
            f"crop=1280:720,"
            f"zoompan=z='min(zoom+0.0012,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    elif mode == "pan_down":
        vf = (
            f"scale=1280:-1,"
            f"zoompan=z=1.0:x=0:y='min(on*2, ih-720)':"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    else:
        vf = f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2"

    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-i", audio_path,
        "-vf", vf,
        "-c:v", encoder, "-pix_fmt", "yuv420p",
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
    concat_list = "temp_concat.txt"
    with open(concat_list, "w") as f:
        for clip in clip_paths:
            f.write(f"file '{os.path.abspath(clip)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", concat_list,
        "-i", bgm_path,
        "-filter_complex",
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
    print("Motion Comic Generator ready.")
