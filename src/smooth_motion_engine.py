#!/usr/bin/env python3
"""
smooth_motion_engine.py - Professional Motion Comic Camera Engine.
Uses OpenCV + mathematical easing curves (Cubic, Sine, Smoothstep) and subpixel
interpolation for butter-smooth camera pans, zooms, and impact shakes.
Pipes directly to FFmpeg for high-quality, jitter-free video.
"""

import os
import math
import subprocess
import cv2
import numpy as np

def ease_in_out_cubic(t):
    return 4 * t * t * t if t < 0.5 else 1.0 - math.pow(-2 * t + 2, 3) / 2.0

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1.0) / 2.0

def ease_out_quad(t):
    return 1.0 - (1.0 - t) * (1.0 - t)

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

def render_motion(image_path, output_mp4, duration=2.5, fps=30, mode="push_in_zoom", audio_path=None):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    ih, iw = img.shape[:2]
    out_w, out_h = 1280, 720
    total_frames = int(duration * fps)
    encoder = get_h264_encoder()

    # Base scale to ensure the image at least fills the 1280x720 canvas
    base_scale = max(out_w / iw, out_h / ih)
    
    # FFmpeg Pipe
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{out_w}x{out_h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-"
    ]
    if audio_path and os.path.exists(audio_path):
        ffmpeg_cmd.extend(["-i", audio_path, "-c:a", "aac", "-b:a", "192k"])

    ffmpeg_cmd.extend([
        "-c:v", encoder,
        "-pix_fmt", "yuv420p",
        "-t", str(duration),
        output_mp4
    ])

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for i in range(total_frames):
        t = i / max(total_frames - 1, 1)  # 0.0 -> 1.0

        if mode == "push_in_zoom":
            # Smooth cubic ease-in-out zoom from 1.0x to 1.30x
            e = ease_in_out_cubic(t)
            scale = base_scale * (1.0 + 0.30 * e)
            # Center zoom
            cw = out_w / scale
            ch = out_h / scale
            cx = iw / 2.0
            cy = ih / 2.0

        elif mode == "pull_out_zoom":
            # Smooth zoom out from 1.30x to 1.0x
            e = ease_in_out_cubic(t)
            scale = base_scale * (1.30 - 0.30 * e)
            cw = out_w / scale
            ch = out_h / scale
            cx = iw / 2.0
            cy = ih / 2.0

        elif mode == "vertical_pan":
            # Extra zoom of 1.35x to create vertical panning headroom
            scale = base_scale * 1.35
            cw = out_w / scale
            ch = out_h / scale
            e = ease_in_out_sine(t)
            cx = iw / 2.0
            # Pan from top (y_min) to bottom (y_max)
            y_start = ch / 2.0
            y_end = ih - ch / 2.0
            cy = y_start + (y_end - y_start) * e

        elif mode == "horizontal_pan":
            # Extra zoom of 1.35x to create horizontal panning headroom
            scale = base_scale * 1.35
            cw = out_w / scale
            ch = out_h / scale
            e = ease_in_out_sine(t)
            cy = ih / 2.0
            # Pan from left (x_min) to right (x_max)
            x_start = cw / 2.0
            x_end = iw - cw / 2.0
            cx = x_start + (x_end - x_start) * e

        elif mode == "diagonal_pan":
            scale = base_scale * 1.35
            cw = out_w / scale
            ch = out_h / scale
            e = ease_in_out_sine(t)
            cx = (cw / 2.0) + (iw - cw) * e
            cy = (ch / 2.0) + (ih - ch) * e

        elif mode == "impact_shake":
            # Exponentially decaying impact shock (punches / explosions)
            scale = base_scale * 1.08
            decay = math.exp(-4.0 * t)
            dx = 25.0 * decay * math.sin(t * 35.0)
            dy = 18.0 * decay * math.cos(t * 40.0)
            cw = out_w / scale
            ch = out_h / scale
            cx = (iw / 2.0) + dx
            cy = (ih / 2.0) + dy

        elif mode == "snap_punch_zoom":
            # Jump cut at 40% time into face with slight 2-frame bounce
            if t < 0.40:
                scale = base_scale * 1.0
                cx = iw / 2.0
                cy = ih / 2.0
            else:
                punch_t = min((t - 0.40) / 0.1, 1.0)
                # Bounce overshoot from 1.45x settling to 1.35x
                bounce = 1.35 + 0.10 * math.exp(-6.0 * (t - 0.40)) * math.cos(20.0 * (t - 0.40))
                scale = base_scale * bounce
                # Zoom into focal character
                cx = iw * 0.45
                cy = ih * 0.40
            cw = out_w / scale
            ch = out_h / scale

        else: # Default gentle float
            scale = base_scale * (1.0 + 0.05 * t)
            cw = out_w / scale
            ch = out_h / scale
            cx = iw / 2.0
            cy = ih / 2.0

        # Sub-pixel crop and resize using OpenCV
        x1 = cx - cw / 2.0
        y1 = cy - ch / 2.0
        
        # Source points and destination points for affine transform
        src_pts = np.float32([
            [x1, y1],
            [x1 + cw, y1],
            [x1, y1 + ch]
        ])
        dst_pts = np.float32([
            [0, 0],
            [out_w, 0],
            [0, out_h]
        ])
        matrix = cv2.getAffineTransform(src_pts, dst_pts)
        frame = cv2.warpAffine(img, matrix, (out_w, out_h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Rendered [{mode}] -> {output_mp4}")
    return output_mp4

if __name__ == "__main__":
    print("Testing smooth motion engine...")
