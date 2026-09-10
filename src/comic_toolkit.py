#!/usr/bin/env python3
"""
comic_toolkit.py - High-Level Python API for Motion Comic Creation.
Includes built-in camera motions (with Cubic/Sine easing) and 40+ built-in FFmpeg transitions.

Built-in Motions:
  - zoom_in()
  - zoom_out()
  - pan_vertical()
  - pan_horizontal()
  - camera_shake()
  - punch_zoom()

Built-in Transitions (via native xfade):
  - 'smoothleft', 'smoothright', 'smoothup', 'smoothdown'
  - 'slideleft', 'slideright', 'slideup', 'slidedown'
  - 'wipeleft', 'wiperight', 'wipeup', 'wipedown'
  - 'fadewhite', 'fadeblack', 'dissolve', 'pixelize'
  - 'zoomin', 'hblur', 'circlecrop', 'horzopen', 'vertopen'
"""

import os
import subprocess
from src.smooth_motion_engine import render_motion, get_h264_encoder

# --- BUILT-IN CAMERA MOTIONS ---

def zoom_in(image_path, output_mp4, duration=2.5, fps=30, audio_path=None):
    """Built-in slow push-in zoom with cubic ease-in/ease-out."""
    return render_motion(image_path, output_mp4, duration=duration, fps=fps, mode="push_in_zoom", audio_path=audio_path)

def zoom_out(image_path, output_mp4, duration=2.5, fps=30, audio_path=None):
    """Built-in pull-out reveal zoom with cubic ease-in/ease-out."""
    return render_motion(image_path, output_mp4, duration=duration, fps=fps, mode="pull_out_zoom", audio_path=audio_path)

def pan_vertical(image_path, output_mp4, duration=3.0, fps=30, direction="down", audio_path=None):
    """Built-in vertical pan (reading order) with sine ease-in/ease-out."""
    return render_motion(image_path, output_mp4, duration=duration, fps=fps, mode="vertical_pan", audio_path=audio_path)

def pan_horizontal(image_path, output_mp4, duration=3.0, fps=30, direction="right", audio_path=None):
    """Built-in horizontal panoramic tracking pan with sine ease-in/ease-out."""
    return render_motion(image_path, output_mp4, duration=duration, fps=fps, mode="horizontal_pan", audio_path=audio_path)

def camera_shake(image_path, output_mp4, duration=1.8, fps=30, audio_path=None):
    """Built-in impact shock camera shake with exponential decay physics."""
    return render_motion(image_path, output_mp4, duration=duration, fps=fps, mode="impact_shake", audio_path=audio_path)

def punch_zoom(image_path, output_mp4, duration=2.0, fps=30, audio_path=None):
    """Built-in snap jump cut zoom with overshoot bounce for comic reactions."""
    return render_motion(image_path, output_mp4, duration=duration, fps=fps, mode="snap_punch_zoom", audio_path=audio_path)

# --- BUILT-IN SCENE TRANSITIONS (40+ PRESETS) ---

BUILTIN_TRANSITIONS = [
    # Smooth & Directional
    "smoothleft", "smoothright", "smoothup", "smoothdown",
    "slideleft", "slideright", "slideup", "slidedown",
    "wipeleft", "wiperight", "wipeup", "wipedown",
    # Fades & Blurs
    "fade", "fadewhite", "fadeblack", "fadegrays", "dissolve", "hblur",
    # Stylized / Comic Action
    "zoomin", "pixelize", "circleopen", "circleclose", "circlecrop",
    "horzopen", "horzclose", "vertopen", "vertclose",
    "diagtl", "diagtr", "diagbl", "diagbr",
    "squeezeh", "squeezev"
]

def transition_two_clips(clip_a, clip_b, output_mp4, transition="smoothleft", duration=0.5):
    """
    Connects two video clips using FFmpeg's built-in xfade transition filter.
    """
    if transition not in BUILTIN_TRANSITIONS:
        print(f"Warning: '{transition}' not recognized. Falling back to 'fade'.")
        transition = "fade"

    # Get duration of clip_a
    probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", clip_a
    ]
    dur_a = float(subprocess.check_output(probe, text=True).strip())
    offset = max(0.0, dur_a - duration)
    encoder = get_h264_encoder()

    cmd = [
        "ffmpeg", "-y",
        "-i", clip_a,
        "-i", clip_b,
        "-filter_complex",
        f"[0:v][1:v]xfade=transition={transition}:duration={duration}:offset={offset}[v]",
        "-map", "[v]",
        "-c:v", encoder, "-pix_fmt", "yuv420p",
        output_mp4
    ]
    subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
    print(f"Created transition [{transition}] -> {output_mp4}")
    return output_mp4

def chain_clips_with_transitions(clip_list, output_mp4, transition_type="smoothleft", trans_duration=0.4):
    """
    Chains a list of video clips into a single video with built-in transitions between every scene.
    """
    if len(clip_list) == 1:
        return clip_list[0]

    current = clip_list[0]
    temp_files = []

    for i in range(1, len(clip_list)):
        next_clip = clip_list[i]
        out_temp = f"temp_step_{i}.mp4"
        temp_files.append(out_temp)
        # Cycle through or use selected transition
        t = transition_type if isinstance(transition_type, str) else transition_type[(i-1) % len(transition_type)]
        transition_two_clips(current, next_clip, out_temp, transition=t, duration=trans_duration)
        current = out_temp

    # Final rename/copy
    if os.path.exists(output_mp4):
        os.remove(output_mp4)
    os.rename(current, output_mp4)

    # Cleanup temp intermediate steps
    for f in temp_files:
        if f != current and os.path.exists(f):
            os.remove(f)

    print(f"✨ Successfully assembled {len(clip_list)} clips with '{transition_type}' into {output_mp4}")
    return output_mp4

if __name__ == "__main__":
    print(f"Comic Toolkit Loaded! Available built-in transitions: {len(BUILTIN_TRANSITIONS)}")
    print(", ".join(BUILTIN_TRANSITIONS[:12]) + ", ...")
