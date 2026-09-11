#!/usr/bin/env python3
"""
render_comicsexplained_groove_video_60fps.py
Renders a broadcast-grade 1080p60 motion comic recap with:
  1. Voice: 'alba' with scene-by-scene variable emotional temperature
  2. Music: ComicsExplained style dark cinematic narrative hip-hop groove
  3. Audio Mastering: 48kHz SOXR, Vocal Pocket EQ (-6dB @ 2.5kHz), dynamic sidechain ducking, 320kbps stereo
  4. Video: 60 FPS sub-pixel anti-aliased floating-point camera motion with zero jitter
  5. Transitions: White Flash impact cuts, smooth lateral slides
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

# Variable emotional temperatures per scene
TEMPERATURE_MAP = {
    "scene_000": "0.50",  # Upbeat, energetic greeting hook
    "scene_001": "0.35",  # Mysterious & calculated
    "scene_002": "0.45",  # Intriguing plot twist
    "scene_003": "0.38",  # Relaxed Queens bedroom
    "scene_004": "0.40",  # Tech explanation
    "scene_005": "0.58",  # Lamp ricochet shock
    "scene_006": "0.62",  # High reflex mid-air save
    "scene_007": "0.68",  # Spider-sense goes nuclear
    "scene_008": "0.55",  # Tactical pulse revelation
    "scene_009": "0.50",  # Climax & Outro CTA
}

def draw_broadcast_title_card(frame, title, subtitle, t_norm):
    """
    Renders a high-end broadcast comic title card with smooth fade/slide in:
    - Dark frosted glass banner in lower-third
    - Red Marvel accent pill
    - High-contrast comic typography
    """
    h, w = frame.shape[:2]
    fade = min(1.0, t_norm / 0.12)
    if fade <= 0.01:
        return frame

    cw, ch = 1480, 155
    cx1 = (w - cw) // 2
    cy1 = h - ch - 60
    cx2 = cx1 + cw
    cy2 = cy1 + ch

    # Glass background overlay
    sub_img = frame[cy1:cy2, cx1:cx2].astype(np.float32)
    card_bg = np.zeros_like(sub_img)
    card_bg[:] = (18, 20, 26)
    blended = cv2.addWeighted(sub_img, 0.22, card_bg, 0.78, 0)
    frame[cy1:cy2, cx1:cx2] = blended.astype(np.uint8)

    # Red Marvel accent bar on left
    cv2.rectangle(frame, (cx1, cy1), (cx1 + 18, cy2), (35, 35, 220), -1)

    # Subtle slate border
    cv2.rectangle(frame, (cx1, cy1), (cx2, cy2), (80, 95, 120), 2)

    font = cv2.FONT_HERSHEY_DUPLEX
    # Subtitle / Episode badge
    sub_text = subtitle.upper() if subtitle else "FULL STORY RECAP"
    cv2.putText(frame, sub_text, (cx1 + 45, cy1 + 48), font, 0.85, (0, 215, 255), 2, cv2.LINE_AA)

    # Main Title
    main_text = title.upper()
    cv2.putText(frame, main_text, (cx1 + 45, cy1 + 112), font, 1.35, (255, 255, 255), 3, cv2.LINE_AA)

    return frame

def synthesize_alba_variable_emotion(script_json_path, audio_out_dir):
    os.makedirs(audio_out_dir, exist_ok=True)
    with open(script_json_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print(f"[*] Checking/Synthesizing {len(scenes)} scenes with Alba (Variable Emotional Temperatures)...")
    audio_paths = []

    for sc in scenes:
        sid = sc["scene_id"]
        text = sc["line"]
        raw_wav = os.path.join(audio_out_dir, f"{sid}_alba.wav")
        temp = TEMPERATURE_MAP.get(sid, "0.45")

        if os.path.exists(raw_wav) and os.path.getsize(raw_wav) > 10000:
            print(f"  -> {sid} already synthesized ({os.path.getsize(raw_wav)} bytes)")
        else:
            print(f"  -> Synthesizing {sid} (temp={temp}): \"{text[:45]}...\"")
            cmd_tts = [
                "/usr/local/bin/pocket-tts", "generate",
                "--text", text,
                "--voice", "alba",
                "--temperature", temp,
                "--output-path", raw_wav,
                "-q"
            ]
            subprocess.run(cmd_tts, check=True)
        audio_paths.append((sid, raw_wav))

    return audio_paths

def render_full_groove_recap_60fps():
    script_path = os.path.join(PROJECT_ROOT, "output/narrator_recap_production/narrator_script.json")
    audio_dir = os.path.join(PROJECT_ROOT, "output/narrator_recap_production/alba_groove_voiceovers")
    music_track = os.path.join(PROJECT_ROOT, "assets/pro_creator_tracks/3_comicsexplained_narrative_groove.mp3")
    output_mp4 = os.path.join(PROJECT_ROOT, "output/spiderman_recap_part1_comicsexplained_groove_60fps.mp4")

    os.makedirs("output", exist_ok=True)

    # 1. Synthesize Alba variable-temperature voiceovers
    voice_files = synthesize_alba_variable_emotion(script_path, audio_dir)

    with open(script_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    fps = 60
    canvas_w = 1920
    canvas_h = 1080

    # 2. Build scene metadata & duration
    scene_meta = []
    concat_audio_list = os.path.join(audio_dir, "concat_voice_list.txt")
    with open(concat_audio_list, "w") as af_out:
        for i, sc in enumerate(scenes):
            sid = sc["scene_id"]
            wav_path = os.path.join(audio_dir, f"{sid}_alba.wav")
            dur = get_audio_duration(wav_path)
            # Add small 0.3s breathing tail
            dur += 0.30
            num_frames = int(math.ceil(dur * fps))
            scene_meta.append({
                "scene": sc,
                "audio_path": wav_path,
                "duration": dur,
                "frames": num_frames
            })
            af_out.write(f"file '{os.path.abspath(wav_path)}'\n")

    total_frames = sum(s["frames"] for s in scene_meta)
    total_duration = total_frames / fps
    print(f"[*] Total Recap Duration: {total_duration:.2f}s ({total_frames} frames @ 60 FPS)")

    # 3. Concatenate all voices into a pristine speech master track
    speech_master_wav = os.path.join(audio_dir, "speech_master.wav")
    cmd_concat = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_audio_list,
        "-c:a", "pcm_s16le",
        speech_master_wav
    ]
    subprocess.run(cmd_concat, check=True, stderr=subprocess.DEVNULL)

    # 4. Master full soundtrack: Voice Chain + Music Pocket + Dynamic Sidechain Ducking
    master_audio_wav = os.path.join(audio_dir, "full_master_soundtrack.wav")
    print(f"[*] Mastering 48kHz True Stereo Soundtrack with ComicsExplained Groove BGM...")
    cmd_audio_mix = [
        "ffmpeg", "-y",
        "-i", speech_master_wav,
        "-stream_loop", "-1", "-i", music_track,
        "-filter_complex",
        # Voice Chain: Highpass 80Hz -> presence EQ -> comp -> SOXR 48k stereo -> split
        "[0:a]highpass=f=80,equalizer=f=4500:t=q:w=1.5:g=3.5,equalizer=f=11000:t=h:g=2.5,acompressor=threshold=-18dB:ratio=3:attack=5:release=60,aresample=48000:resampler=soxr,aformat=channel_layouts=stereo,asplit=2[v_main][v_side];"
        # Music Chain: Vocal Pocket cut (-6dB at 2.5kHz) -> volume 0.22 -> 48k stereo
        "[1:a]equalizer=f=2500:t=q:w=1.5:g=-6.0,volume=0.22,aresample=48000:resampler=soxr,aformat=channel_layouts=stereo[m_pocket];"
        # Dynamic Sidechain: duck music when voice speaks
        "[m_pocket][v_side]sidechaincompress=threshold=0.03:ratio=4:attack=10:release=250[m_ducked];"
        # Mix together in full stereo
        "[v_main][m_ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[final]",
        "-map", "[final]",
        "-c:a", "pcm_s16le",
        "-t", f"{total_duration:.3f}",
        master_audio_wav
    ]
    subprocess.run(cmd_audio_mix, check=True, stderr=subprocess.DEVNULL)

    # 5. Open video stream pipeline
    encoder = get_h264_encoder()
    cmd_vid = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{canvas_w}x{canvas_h}",
        "-pix_fmt", "bgr24",
        "-r", str(fps),
        "-i", "-",
        "-i", master_audio_wav,
        "-c:v", encoder,
        "-pix_fmt", "yuv420p",
        "-b:v", "14M",
        "-c:a", "aac",
        "-b:a", "320k",
        "-t", f"{total_duration:.4f}",
        output_mp4
    ]

    pipe = subprocess.Popen(cmd_vid, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # 6. Pre-render base frames
    base_frames = []
    for sm in scene_meta:
        sc = sm["scene"]
        p_img = sc["panel_image"]
        p_cv = cv2.imread(p_img)
        bf = render_panel_to_canvas(p_cv, canvas_w, canvas_h)
        base_frames.append(bf)

    # 7. Render 60 FPS frames
    print("[*] Streaming 1080p60 frames with sub-pixel zero-jitter camera moves...")
    for s_idx, sm in enumerate(scene_meta):
        sc = sm["scene"]
        frames_in_scene = sm["frames"]
        cur_bf = base_frames[s_idx]
        next_bf = base_frames[s_idx + 1] if s_idx + 1 < len(base_frames) else None

        motion_type = sc.get("camera_motion", "push_in_zoom")
        trans_type = sc.get("transition", "none")
        overlay_text = sc.get("overlay_text", "")
        overlay_title = sc.get("overlay_title", "")
        overlay_subtitle = sc.get("overlay_subtitle", "")
        print(f"  -> Rendering {sc['scene_id']} ({frames_in_scene} frames, motion={motion_type}, trans={trans_type})...")

        for f in range(frames_in_scene):
            t_norm = f / max(1, frames_in_scene - 1)

            # Sub-pixel float transformations
            if motion_type == "push_in_zoom":
                scale = 1.0 + 0.25 * ease_in_out_sine(t_norm)
                dx, dy = 0.0, 0.0
            elif motion_type == "snap_punch_zoom":
                scale = 1.0 + 0.22 * ease_in_out_cubic(t_norm)
                dx, dy = 0.0, 0.0
            elif motion_type == "vertical_pan":
                scale = 1.15
                dx = 0.0
                dy = (t_norm - 0.5) * 80.0
            elif motion_type == "impact_shake":
                scale = 1.05
                shake_decay = math.exp(-t_norm * 4.0)
                dx = math.sin(t_norm * 48.0) * 32.0 * shake_decay
                dy = math.cos(t_norm * 42.0) * 24.0 * shake_decay
            elif motion_type == "pull_out_zoom":
                scale = 1.25 - 0.25 * ease_in_out_sine(t_norm)
                dx, dy = 0.0, 0.0
            else:
                scale = 1.0 + 0.15 * t_norm
                dx, dy = 0.0, 0.0

            center_x = canvas_w / 2.0
            center_y = canvas_h / 2.0
            M = cv2.getRotationMatrix2D((center_x, center_y), 0, scale)
            M[0, 2] += dx
            M[1, 2] += dy

            frame = cv2.warpAffine(
                cur_bf, M, (canvas_w, canvas_h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(10, 10, 12)
            )

            # In-Engine Transitions
            trans_dur_frames = int(0.35 * fps)  # 21 frames
            frames_from_end = frames_in_scene - f

            if frames_from_end <= trans_dur_frames and next_bf is not None:
                p_trans = 1.0 - (frames_from_end / trans_dur_frames)
                p_ease = ease_in_out_cubic(p_trans)

                if trans_type == "white_flash":
                    flash_intensity = math.sin(p_trans * math.pi)
                    flash_layer = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)
                    if p_trans < 0.5:
                        frame = cv2.addWeighted(frame, 1.0 - flash_intensity, flash_layer, flash_intensity, 0)
                    else:
                        frame = cv2.addWeighted(next_bf, 1.0 - flash_intensity, flash_layer, flash_intensity, 0)
                elif trans_type == "slide_left":
                    offset_x = int(p_ease * canvas_w)
                    combined = np.zeros_like(frame)
                    w_curr = canvas_w - offset_x
                    if w_curr > 0:
                        combined[:, :w_curr] = frame[:, offset_x:]
                    if offset_x > 0:
                        combined[:, w_curr:] = next_bf[:, :offset_x]
                    frame = combined

            # Broadcast Title Card (Intro Scene)
            if overlay_title:
                frame = draw_broadcast_title_card(frame, overlay_title, overlay_subtitle, t_norm)

            # Outro Callout Banner
            if overlay_text and t_norm >= 0.25:
                banner_norm = min(1.0, (t_norm - 0.25) / 0.15)
                frame = draw_callout_banner(frame, overlay_text)

            try:
                pipe.stdin.write(frame.tobytes())
            except (BrokenPipeError, IOError):
                break

    pipe.stdin.close()
    pipe.wait()
    print(f"\n[+] Final ComicsExplained Groove 60 FPS Recap Video Created: {output_mp4}")
    return output_mp4

if __name__ == "__main__":
    render_full_groove_recap_60fps()
