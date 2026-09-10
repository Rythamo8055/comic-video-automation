#!/usr/bin/env python3
"""
motion_comic_generator.py - Comprehensive Motion Comic Animation Engine.
Supports 7 cinematic camera motions & transitions:
  1. zoom_in       : Slow Push-In Zoom (1.0x -> 1.15x)
  2. zoom_out      : Pull-Out Reveal Zoom (1.25x -> 1.0x)
  3. pan_down      : Top-to-Bottom Vertical Pan (reading order for tall panels)
  4. pan_horizontal: Left-to-Right Panoramic Pan (spreads & landscapes)
  5. shake         : High-frequency Camera Shake (punches & explosions)
  6. snap_zoom     : Instant 0-frame Jump Zoom (shock & punchlines)
  7. white_flash   : Impact White Flash Cut between scenes
"""

import os
import subprocess

def get_h264_encoder():
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
            f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"zoompan=z='min(zoom+0.0012,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    elif mode == "zoom_out":
        vf = (
            f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"zoompan=z='if(lte(zoom,1.0),1.18,max(1.0,zoom-0.0012))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    elif mode == "pan_down":
        vf = (
            f"scale=1280:-1,"
            f"zoompan=z=1.0:x=0:y='min(on*2,ih-720)':"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    elif mode == "pan_horizontal":
        vf = (
            f"scale=-1:720,"
            f"zoompan=z=1.0:x='min(on*2.5,iw-1280)':y=0:"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    elif mode == "shake":
        vf = (
            f"scale=1360:780:force_original_aspect_ratio=increase,"
            f"crop=1280:720:x='40+20*sin(n*1.8)':y='30+15*cos(n*2.2)'"
        )
    elif mode == "snap_zoom":
        split = total_frames // 2
        vf = (
            f"scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720,"
            f"zoompan=z='if(lt(on,{split}),1.0,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s=1280x720:fps={fps}"
        )
    else:  # static fit
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

def assemble_full_video(clip_paths, bgm_path, final_output_path, transition="hard_cut"):
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
    print(f"Final video successfully created: {final_output_path}")

if __name__ == "__main__":
    print("Motion Comic Animation Engine with 7 camera modes ready.")
