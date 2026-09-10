#!/usr/bin/env python3
"""
smooth_motion_engine.py - Professional Motion Comic Camera Engine (1080p Full HD).
Uses OpenCV + mathematical easing curves (Cubic, Sine, Smoothstep) and subpixel
interpolation for butter-smooth camera pans, zooms, and impact shakes.
Pipes directly to FFmpeg for high-quality, jitter-free 1080p video.
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

def render_motion(image_path, output_mp4, duration=2.5, fps=24, mode="push_in_zoom", audio_path=None, out_w=1920, out_h=1080):
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {image_path}")

    ih, iw = img.shape[:2]
    total_frames = max(int(duration * fps), 24)
    encoder = get_h264_encoder()

    # Base scale to ensure the image at least fills the 1080p canvas
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
            # 1.35x padding to allow smooth vertical glide
            scale = base_scale * 1.35
            cw = out_w / scale
            ch = out_h / scale
            e = ease_in_out_sine(t)
            cx = iw / 2.0
            y_start = ch / 2.0
            y_end = ih - ch / 2.0
            cy = y_start + (y_end - y_start) * e

        elif mode == "horizontal_pan":
            # 1.35x padding to allow smooth horizontal glide
            scale = base_scale * 1.35
            cw = out_w / scale
            ch = out_h / scale
            e = ease_in_out_sine(t)
            cy = ih / 2.0
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
            dx = 30.0 * decay * math.sin(t * 35.0)
            dy = 22.0 * decay * math.cos(t * 40.0)
            cw = out_w / scale
            ch = out_h / scale
            cx = (iw / 2.0) + dx
            cy = (ih / 2.0) + dy

        elif mode == "snap_punch_zoom":
            if t < 0.35:
                scale = base_scale * 1.0
                cx = iw / 2.0
                cy = ih / 2.0
            else:
                bounce = 1.35 + 0.10 * math.exp(-6.0 * (t - 0.35)) * math.cos(20.0 * (t - 0.35))
                scale = base_scale * bounce
                cx = iw * 0.50
                cy = ih * 0.45
            cw = out_w / scale
            ch = out_h / scale

        else:
            scale = base_scale * (1.0 + 0.05 * t)
            cw = out_w / scale
            ch = out_h / scale
            cx = iw / 2.0
            cy = ih / 2.0

        # Sub-pixel crop and resize using OpenCV
        x1 = cx - cw / 2.0
        y1 = cy - ch / 2.0
        
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
    return output_mp4

if __name__ == "__main__":
    print("1080p Smooth Motion Engine ready.")
