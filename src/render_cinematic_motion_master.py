#!/usr/bin/env python3
"""
render_cinematic_motion_master.py
High-Impact Motion Comic Engine:
  - 60 FPS buttery smooth playback
  - 100% Zero Jitter (Sub-pixel float64 affine transforms on 1080p canvas)
  - In-engine White Flash & Slide Left transitions
  - On-screen Outro Callout Banner: "WAIT FOR THE NEXT VIDEO! PART 2 COMING NEXT"
  - Centered uncropped panels on dark slate canvas
"""

import os
import sys
import math
import json
import subprocess
import cv2
import numpy as np

def ease_in_out_cubic(t):
    return 4.0 * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 3) / 2.0

def ease_in_out_sine(t):
    return -(math.cos(math.pi * t) - 1.0) / 2.0

def get_h264_encoder():
    try:
        res = subprocess.check_output(["ffmpeg", "-encoders"], text=True, stderr=subprocess.DEVNULL)
        # 1. macOS Apple Silicon / Intel Hardware Encoder
        if sys.platform == "darwin" and "h264_videotoolbox" in res:
            return "h264_videotoolbox"
        # 2. Windows NVIDIA / Intel Hardware Encoders
        if sys.platform == "win32":
            if "h264_nvenc" in res:
                return "h264_nvenc"
            if "h264_qsv" in res:
                return "h264_qsv"
        # 3. Cross-platform software encoders
        if "libx264" in res:
            return "libx264"
        if "libopenh264" in res:
            return "libopenh264"
    except Exception:
        pass
    return "h264"

def get_audio_duration(audio_path):
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    return float(subprocess.check_output(probe_cmd, text=True).strip())

def render_panel_to_canvas(img, out_w, out_h, scale_factor=1.0, offset_x=0.0, offset_y=0.0):
    ih, iw = img.shape[:2]
    
    pad_w = 80
    pad_h = 50
    safe_w = out_w - 2 * pad_w
    safe_h = out_h - 2 * pad_h
    base_fit = min(safe_w / iw, safe_h / ih)
    
    total_scale = base_fit * scale_factor
    
    target_cx = (out_w / 2.0) + offset_x
    target_cy = (out_h / 2.0) + offset_y
    src_cx = iw / 2.0
    src_cy = ih / 2.0
    
    M = cv2.getRotationMatrix2D((src_cx, src_cy), 0.0, total_scale)
    M[0, 2] += (target_cx - src_cx)
    M[1, 2] += (target_cy - src_cy)
    
    canvas = cv2.warpAffine(
        img, M, (out_w, out_h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(15, 20, 28)
    )
    
    # Outer border
    pw = iw * total_scale
    ph = ih * total_scale
    bx1 = int(round(target_cx - pw / 2.0))
    by1 = int(round(target_cy - ph / 2.0))
    bx2 = int(round(target_cx + pw / 2.0))
    by2 = int(round(target_cy + ph / 2.0))
    if 0 <= bx1 < out_w and 0 <= by1 < out_h:
        cv2.rectangle(canvas, (max(0, bx1 - 2), max(0, by1 - 2)), (min(out_w - 1, bx2 + 2), min(out_h - 1, by2 + 2)), (60, 75, 95), 2)
        
    return canvas

def draw_callout_banner(frame, text):
    """Draws a bold, high-CTR comic callout banner at the bottom of the frame."""
    h, w = frame.shape[:2]
    bw, bh = 1500, 110
    bx1 = (w - bw) // 2
    by1 = h - bh - 50
    bx2 = bx1 + bw
    by2 = by1 + bh
    
    # Drop shadow
    cv2.rectangle(frame, (bx1 + 6, by1 + 6), (bx2 + 6, by2 + 6), (0, 0, 0), -1)
    # Bright comic yellow box
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 222, 255), -1)
    # Heavy black border
    cv2.rectangle(frame, (bx1, by1), (bx2, by2), (0, 0, 0), 5)
    
    # Text with outline
    font = cv2.FONT_HERSHEY_DUPLEX
    scale = 1.35
    thick = 3
    (tw, th), _ = cv2.getTextSize(text, font, scale, thick)
    tx = (w - tw) // 2
    ty = by1 + (bh + th) // 2 - 5
    
    # Outline
    cv2.putText(frame, text, (tx, ty), font, scale, (0, 0, 0), thick + 4, cv2.LINE_AA)
    # Text
    cv2.putText(frame, text, (tx, ty), font, scale, (15, 15, 15), thick, cv2.LINE_AA)
    return frame

def render_cinematic_recap(script_json_path, audio_dir, output_mp4, bgm_path=None, fps=60):
    with open(script_json_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)
        
    out_w, out_h = 1920, 1080
    encoder = get_h264_encoder()
    
    scene_data = []
    total_duration = 0.0
    
    print(f"[*] Loading scenes, panels, and voice durations for {fps} FPS render...")
    for sc in scenes:
        sid = sc["scene_id"]
        wav_path = os.path.join(audio_dir, f"{sid}_narrator.wav")
        dur = get_audio_duration(wav_path)
        img_path = sc["panel_image"]
        img = cv2.imread(img_path)
        if img is None:
            # Fallback 1: check same directory as script_json_path
            sdir = os.path.dirname(os.path.abspath(script_json_path))
            alt_path = os.path.join(sdir, os.path.basename(img_path))
            img = cv2.imread(alt_path)
            if img is None:
                # Fallback 2: check nested comic folder
                for root, _, files in os.walk(sdir):
                    if os.path.basename(img_path) in files:
                        alt_path = os.path.join(root, os.path.basename(img_path))
                        img = cv2.imread(alt_path)
                        break
        if img is None:
            raise FileNotFoundError(f"Missing image: {sc['panel_image']}")
            
        scene_data.append({
            "id": sid,
            "img": img,
            "audio": wav_path,
            "duration": dur,
            "motion": sc.get("camera_motion", "push_in_zoom"),
            "transition": sc.get("transition", "white_flash"),
            "overlay_text": sc.get("overlay_text", ""),
            "frames": int(round(dur * fps)),
            "start_time": total_duration
        })
        total_duration += dur
        print(f"  -> {sid}: dur={dur:.2f}s, frames={int(round(dur*fps))}, motion={sc.get('camera_motion')}, trans={sc.get('transition')}")
        
    master_audio = "temp_master_voice_60fps.wav"
    audio_concat_list = "temp_audio_list_60fps.txt"
    with open(audio_concat_list, "w") as f:
        for s in scene_data:
            f.write(f"file '{os.path.abspath(s['audio'])}'\n")
            
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_concat_list,
        "-c:a", "pcm_s16le", master_audio
    ], check=True, stderr=subprocess.DEVNULL)
    
    print(f"[*] Streaming 1080p60 (60 FPS) zero-jitter frames directly to FFmpeg...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{out_w}x{out_h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-i", master_audio
    ]
    
    if bgm_path and os.path.exists(bgm_path):
        ffmpeg_cmd.extend([
            "-stream_loop", "-1", "-i", bgm_path,
            "-filter_complex",
            "[2:a]volume=0.14[bgm];[1:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v",
            "-map", "[aout]"
        ])
    else:
        ffmpeg_cmd.extend(["-map", "0:v", "-map", "1:a"])
        
    ffmpeg_cmd.extend([
        "-c:v", encoder,
        "-b:v", "16M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_duration:.4f}",
        output_mp4
    ])
    
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    
    TRANS_FRAMES = int(round(0.35 * fps))  # ~0.35s transition
    
    for s_idx, sc in enumerate(scene_data):
        num_frames = sc["frames"]
        img = sc["img"]
        motion = sc["motion"]
        next_sc = scene_data[s_idx + 1] if s_idx + 1 < len(scene_data) else None
        trans_type = sc["transition"]
        overlay_text = sc["overlay_text"]
        
        print(f"  -> Rendering {sc['id']} at {fps} FPS ({num_frames} frames)...")
        
        for f in range(num_frames):
            t = f / max(num_frames - 1, 1)
            
            if motion == "push_in_zoom":
                e = ease_in_out_cubic(t)
                scale = 1.0 + 0.25 * e
                ox, oy = 0.0, 0.0
                
            elif motion == "pull_out_zoom":
                e = ease_in_out_cubic(t)
                scale = 1.25 - 0.25 * e
                ox, oy = 0.0, 0.0
                
            elif motion == "vertical_pan":
                scale = 1.15
                e = ease_in_out_sine(t)
                ox = 0.0
                oy = 40.0 * (1.0 - 2.0 * e)
                
            elif motion == "horizontal_pan":
                scale = 1.15
                e = ease_in_out_sine(t)
                ox = 50.0 * (1.0 - 2.0 * e)
                oy = 0.0
                
            elif motion == "impact_shake":
                scale = 1.08
                decay = math.exp(-4.0 * t)
                ox = 32.0 * decay * math.sin(t * 35.0)
                oy = 22.0 * decay * math.cos(t * 40.0)
                
            elif motion == "snap_punch_zoom":
                scale = 1.0 if t < 0.20 else 1.30
                ox, oy = 0.0, 0.0
                
            else:
                scale = 1.0 + 0.15 * t
                ox, oy = 0.0, 0.0
                
            frame = render_panel_to_canvas(img, out_w, out_h, scale_factor=scale, offset_x=ox, offset_y=oy)
            
            if overlay_text:
                frame = draw_callout_banner(frame, overlay_text)
                
            frames_left = num_frames - f
            if frames_left <= TRANS_FRAMES and next_sc is not None:
                tf = 1.0 - (frames_left / TRANS_FRAMES)
                
                if trans_type == "white_flash":
                    flash_intensity = math.sin(tf * math.pi) * 0.95
                    white_overlay = np.full_like(frame, 255)
                    frame = cv2.addWeighted(frame, 1.0 - flash_intensity, white_overlay, flash_intensity, 0)
                    
                elif trans_type == "slide_left":
                    e_slide = ease_in_out_sine(tf)
                    next_frame = render_panel_to_canvas(next_sc["img"], out_w, out_h, scale_factor=1.0)
                    shift_px = int(round(e_slide * out_w))
                    combined = np.full_like(frame, (15, 20, 28))
                    
                    if shift_px < out_w:
                        combined[:, :out_w - shift_px] = frame[:, shift_px:]
                    if shift_px > 0:
                        combined[:, out_w - shift_px:] = next_frame[:, :shift_px]
                    frame = combined
                    
            proc.stdin.write(frame.tobytes())
            
    proc.stdin.close()
    proc.wait()
    
    if os.path.exists(master_audio):
        os.remove(master_audio)
    if os.path.exists(audio_concat_list):
        os.remove(audio_concat_list)
        
    print(f"\n[+] SUCCESS! 1080p 60 FPS Video Created: {output_mp4}")
    return output_mp4

if __name__ == "__main__":
    script_path = "output/narrator_recap_production/narrator_script.json"
    audio_dir = "output/narrator_recap_production/voiceovers"
    out_video = "output/spiderman_recap_part1_60fps.mp4"
    bgm = "assets/bgm_action.wav"
    
    render_cinematic_recap(script_path, audio_dir, out_video, bgm_path=bgm, fps=60)
