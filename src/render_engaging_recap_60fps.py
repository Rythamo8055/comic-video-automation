#!/usr/bin/env python3
"""
render_engaging_recap_60fps.py
Renders a high-engagement 1080p60 recap video with:
  1. Energetic, broadcast-processed voiceover (temperature=0.70, +3.5dB vocal presence, 1.12x pacing)
  2. Rich Procedural Action BGM (125 BPM kick, snare, 16th hats, driving bassline, synth arpeggio)
  3. Balanced Audio Mixing (amix normalize=0, crisp voice + clearly audible driving music)
  4. 60 FPS sub-pixel Lanczos camera motion with zero jitter
  5. In-engine White Flash & Slide transitions between every scene
  6. Outro Callout: 'WAIT FOR THE NEXT VIDEO! PART 2 COMING NEXT'
"""

import os
import sys
import math
import json
import subprocess
import cv2
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.render_cinematic_motion_master import render_panel_to_canvas, draw_callout_banner, get_h264_encoder, get_audio_duration, ease_in_out_cubic, ease_in_out_sine

def synthesize_punchy_voiceovers(script_json_path, audio_out_dir, voice_id="george"):
    os.makedirs(audio_out_dir, exist_ok=True)
    with open(script_json_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print(f"[*] Synthesizing {len(scenes)} punchy narrator scenes with voice '{voice_id}'...")
    audio_paths = []

    for sc in scenes:
        sid = sc["scene_id"]
        text = sc["line"]
        raw_wav = os.path.join(audio_out_dir, f"{sid}_raw.wav")
        final_wav = os.path.join(audio_out_dir, f"{sid}_punchy.wav")

        print(f"  -> Synthesizing {sid}...")
        # Step 1: Pocket TTS with high engagement temperature (0.70)
        cmd_tts = [
            "/usr/local/bin/pocket-tts", "generate",
            "--text", text,
            "--voice", voice_id,
            "--temperature", "0.70",
            "--output-path", raw_wav,
            "--device", "cpu",
            "-q"
        ]
        subprocess.run(cmd_tts, check=True)

        # Step 2: Broadcast vocal chain (1.12x tempo, vocal presence EQ, studio compression)
        filter_chain = "atempo=1.12,equalizer=f=3000:t=q:w=1:g=3.5,acompressor=threshold=-18dB:ratio=3:attack=5:release=50"
        cmd_proc = [
            "ffmpeg", "-y", "-i", raw_wav,
            "-af", filter_chain,
            final_wav
        ]
        subprocess.run(cmd_proc, check=True, stderr=subprocess.DEVNULL)
        audio_paths.append(final_wav)

    print(f"[+] All {len(scenes)} punchy voice tracks ready in: {audio_out_dir}")
    return audio_paths

def render_engaging_video(script_json_path, audio_dir, output_mp4, bgm_path, fps=60):
    with open(script_json_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    out_w, out_h = 1920, 1080
    encoder = get_h264_encoder()

    scene_data = []
    total_duration = 0.0

    print(f"[*] Loading scenes and punchy audio durations at {fps} FPS...")
    for sc in scenes:
        sid = sc["scene_id"]
        wav_path = os.path.join(audio_dir, f"{sid}_punchy.wav")
        dur = get_audio_duration(wav_path)
        img = cv2.imread(sc["panel_image"])
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
        print(f"  -> {sid}: dur={dur:.2f}s, frames={int(round(dur*fps))}, motion={sc.get('camera_motion')}")

    # Build master audio with procedural BGM
    master_voice = "temp_master_voice_engaging.wav"
    audio_concat_list = "temp_audio_list_engaging.txt"
    with open(audio_concat_list, "w") as f:
        for s in scene_data:
            f.write(f"file '{os.path.abspath(s['audio'])}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", audio_concat_list,
        "-c:a", "pcm_s16le", master_voice
    ], check=True, stderr=subprocess.DEVNULL)

    print(f"[*] Streaming 1080p60 frames and mixing procedural BGM (audible & balanced)...")
    ffmpeg_cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{out_w}x{out_h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-i", master_voice,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex",
        "[2:a]volume=0.28[bgm];[1:a][bgm]amix=inputs=2:duration=first:normalize=0[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", encoder,
        "-b:v", "16M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{total_duration:.4f}",
        output_mp4
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
    TRANS_FRAMES = int(round(0.35 * fps))

    for s_idx, sc in enumerate(scene_data):
        num_frames = sc["frames"]
        img = sc["img"]
        motion = sc["motion"]
        next_sc = scene_data[s_idx + 1] if s_idx + 1 < len(scene_data) else None
        trans_type = sc["transition"]
        overlay_text = sc["overlay_text"]

        print(f"  -> Rendering {sc['id']} ({num_frames} frames)...")

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

    if os.path.exists(master_voice):
        os.remove(master_voice)
    if os.path.exists(audio_concat_list):
        os.remove(audio_concat_list)

    print(f"\n[+] Master Video Successfully Rendered: {output_mp4}")
    return output_mp4

def main():
    script_path = "output/narrator_recap_production/narrator_script.json"
    audio_dir = "output/narrator_recap_production/punchy_voiceovers"
    out_video = "output/spiderman_recap_part1_engaging_60fps.mp4"
    bgm = "assets/procedural_action_bgm.wav"

    # Step 1: Synthesize punchy energetic voice
    synthesize_punchy_voiceovers(script_path, audio_dir, voice_id="george")

    # Step 2: Render 60 FPS video with procedural BGM
    render_engaging_video(script_path, audio_dir, out_video, bgm_path=bgm, fps=60)

if __name__ == "__main__":
    main()
