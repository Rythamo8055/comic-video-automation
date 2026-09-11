#!/usr/bin/env python3
"""
src/render_part2_and_part3_60fps.py
Renders Part 2 and Part 3 of Spider-Man: Challenges of Doom #1 in broadcast-grade 1080p60,
and compiles the Full Issue Movie Edition.
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

from src.render_cinematic_motion_master import (
    render_panel_to_canvas,
    draw_callout_banner,
    get_h264_encoder,
    get_audio_duration,
    ease_in_out_cubic,
    ease_in_out_sine
)
from src.render_comicsexplained_groove_video_60fps import draw_broadcast_title_card
from src.create_comic_thumbnail import generate_thumbnail

TEMPERATURE_MAP = {
    # Part 2
    "p2_scene_000": "0.50",
    "p2_scene_001": "0.40",
    "p2_scene_002": "0.42",
    "p2_scene_003": "0.45",
    "p2_scene_004": "0.65",
    "p2_scene_005": "0.55",
    "p2_scene_006": "0.50",
    "p2_scene_007": "0.62",
    "p2_scene_008": "0.68",
    "p2_scene_009": "0.60",
    "p2_scene_010": "0.52",
    # Part 3
    "p3_scene_000": "0.50",
    "p3_scene_001": "0.62",
    "p3_scene_002": "0.50",
    "p3_scene_003": "0.45",
    "p3_scene_004": "0.68",
    "p3_scene_005": "0.65",
    "p3_scene_006": "0.55",
    "p3_scene_007": "0.50",
    "p3_scene_008": "0.48",
    "p3_scene_009": "0.45",
    "p3_scene_010": "0.42",
    "p3_scene_011": "0.50",
}

def synthesize_episode_voices(script_json_path, audio_out_dir):
    os.makedirs(audio_out_dir, exist_ok=True)
    with open(script_json_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print(f"[*] Checking/Synthesizing {len(scenes)} scenes with Alba (Pocket TTS)...")
    for sc in scenes:
        sid = sc["scene_id"]
        text = sc["line"]
        raw_wav = os.path.join(audio_out_dir, f"{sid}_alba.wav")
        temp = TEMPERATURE_MAP.get(sid, "0.45")

        if os.path.exists(raw_wav) and os.path.getsize(raw_wav) > 10000:
            print(f"  -> {sid} already exists ({os.path.getsize(raw_wav)} bytes)")
        else:
            print(f"  -> Synthesizing {sid} (temp={temp}): \"{text[:45]}...\"")
            cmd = [
                "/usr/local/bin/pocket-tts", "generate",
                "--text", text,
                "--voice", "alba",
                "--temperature", temp,
                "--output-path", raw_wav,
                "-q"
            ]
            subprocess.run(cmd, check=True)

def render_episode_video(script_path, audio_dir, output_mp4, music_track):
    with open(script_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    fps = 60
    canvas_w = 1920
    canvas_h = 1080

    scene_meta = []
    concat_audio_list = os.path.join(audio_dir, "concat_voice_list.txt")
    with open(concat_audio_list, "w") as af_out:
        for sc in scenes:
            sid = sc["scene_id"]
            wav_path = os.path.join(audio_dir, f"{sid}_alba.wav")
            dur = get_audio_duration(wav_path) + 0.30
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
    print(f"[*] Total Duration: {total_duration:.2f}s ({total_frames} frames @ 60 FPS)")

    speech_master_wav = os.path.join(audio_dir, "speech_master.wav")
    cmd_concat = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat_audio_list, "-c:a", "pcm_s16le", speech_master_wav]
    subprocess.run(cmd_concat, check=True, stderr=subprocess.DEVNULL)

    master_audio_wav = os.path.join(audio_dir, "full_master_soundtrack.wav")
    print(f"[*] Mastering 48kHz True Stereo Soundtrack with sidechain ducking...")
    cmd_audio_mix = [
        "ffmpeg", "-y",
        "-i", speech_master_wav,
        "-stream_loop", "-1", "-i", music_track,
        "-filter_complex",
        "[0:a]highpass=f=80,equalizer=f=4500:t=q:w=1.5:g=3.5,equalizer=f=11000:t=h:g=2.5,acompressor=threshold=-18dB:ratio=3:attack=5:release=60,aresample=48000:resampler=soxr,aformat=channel_layouts=stereo,asplit=2[v_main][v_side];"
        "[1:a]equalizer=f=2500:t=q:w=1.5:g=-6.0,volume=0.22,aresample=48000:resampler=soxr,aformat=channel_layouts=stereo[m_pocket];"
        "[m_pocket][v_side]sidechaincompress=threshold=0.03:ratio=4:attack=10:release=250[m_ducked];"
        "[v_main][m_ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[final]",
        "-map", "[final]",
        "-c:a", "pcm_s16le",
        "-t", f"{total_duration:.3f}",
        master_audio_wav
    ]
    subprocess.run(cmd_audio_mix, check=True, stderr=subprocess.DEVNULL)

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

    base_frames = []
    for sm in scene_meta:
        sc = sm["scene"]
        p_img = sc["panel_image"]
        p_cv = cv2.imread(p_img)
        bf = render_panel_to_canvas(p_cv, canvas_w, canvas_h)
        base_frames.append(bf)

    print(f"[*] Streaming 1080p60 frames for {output_mp4}...")
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

        for f in range(frames_in_scene):
            t_norm = f / max(1, frames_in_scene - 1)

            if motion_type == "push_in_zoom":
                scale = 1.0 + 0.22 * ease_in_out_sine(t_norm)
                dx, dy = 0.0, 0.0
            elif motion_type == "snap_punch_zoom":
                scale = 1.0 + 0.20 * ease_in_out_cubic(t_norm)
                dx, dy = 0.0, 0.0
            elif motion_type == "vertical_pan":
                scale = 1.15
                dx = 0.0
                dy = (t_norm - 0.5) * 80.0
            elif motion_type == "impact_shake":
                scale = 1.05
                decay = math.exp(-t_norm * 4.0)
                dx = math.sin(t_norm * 48.0) * 30.0 * decay
                dy = math.cos(t_norm * 42.0) * 22.0 * decay
            elif motion_type == "pull_out_zoom":
                scale = 1.22 - 0.22 * ease_in_out_sine(t_norm)
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

            # Transitions
            trans_dur = int(0.35 * fps)
            from_end = frames_in_scene - f
            if from_end <= trans_dur and next_bf is not None:
                p_t = 1.0 - (from_end / trans_dur)
                p_e = ease_in_out_cubic(p_t)
                if trans_type == "white_flash":
                    fi = math.sin(p_t * math.pi)
                    fl = np.full((canvas_h, canvas_w, 3), 255, dtype=np.uint8)
                    if p_t < 0.5:
                        frame = cv2.addWeighted(frame, 1.0 - fi, fl, fi, 0)
                    else:
                        frame = cv2.addWeighted(next_bf, 1.0 - fi, fl, fi, 0)
                elif trans_type == "slide_left":
                    ox = int(p_e * canvas_w)
                    comb = np.zeros_like(frame)
                    w_c = canvas_w - ox
                    if w_c > 0:
                        comb[:, :w_c] = frame[:, ox:]
                    if ox > 0:
                        comb[:, w_c:] = next_bf[:, :ox]
                    frame = comb

            if overlay_title:
                frame = draw_broadcast_title_card(frame, overlay_title, overlay_subtitle, t_norm)

            if overlay_text and t_norm >= 0.25:
                frame = draw_callout_banner(frame, overlay_text)

            try:
                pipe.stdin.write(frame.tobytes())
            except (BrokenPipeError, IOError):
                break

    pipe.stdin.close()
    pipe.wait()
    print(f"[+] Render complete: {output_mp4}")

def compile_full_movie(p1_mp4, p2_mp4, p3_mp4, out_movie_mp4):
    print(f"\n[*] Compiling Full Issue Movie Edition from Parts 1, 2, 3...")
    concat_txt = os.path.join(PROJECT_ROOT, "output/production/concat_movie.txt")
    with open(concat_txt, "w") as f:
        f.write(f"file '{os.path.abspath(p1_mp4)}'\n")
        f.write(f"file '{os.path.abspath(p2_mp4)}'\n")
        f.write(f"file '{os.path.abspath(p3_mp4)}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", concat_txt,
        "-c", "copy",
        out_movie_mp4
    ]
    subprocess.run(cmd, check=True)
    print(f"[+] Full Movie Master Created: {out_movie_mp4}")

def generate_all_thumbnails():
    cover = "data/spider_man_001/pages/page_01.jpg"
    print("\n[*] Generating YouTube Thumbnails for Part 2, Part 3, and Full Movie...")
    generate_thumbnail(
        cover, "output/thumbnail_part_2.jpg",
        part_text="PART 2",
        subhook_text="THE LATVERIAN GAUNTLET",
        callout_text="⚡ WAIT FOR PART 3 FINALE COMING NEXT!"
    )
    generate_thumbnail(
        cover, "output/thumbnail_part_3.jpg",
        part_text="PART 3",
        subhook_text="DOOM'S ULTIMATUM (FINALE)",
        callout_text="⚡ FULL RECAP COMPLETE! SUBSCRIBE!"
    )
    generate_thumbnail(
        cover, "output/thumbnail_full_movie.jpg",
        part_text="FULL MOVIE",
        subhook_text="COMPLETE ISSUE #1 RECAP",
        callout_text="🎬 FULL STORY 1080P 60FPS"
    )

def main():
    music_track = os.path.join(PROJECT_ROOT, "assets/pro_creator_tracks/3_comicsexplained_narrative_groove.mp3")
    
    # 1. Part 2
    print("\n==================== [PRODUCING PART 2] ====================")
    p2_script = os.path.join(PROJECT_ROOT, "output/production/part2_script.json")
    p2_audio_dir = os.path.join(PROJECT_ROOT, "output/production/part2_audio")
    p2_mp4 = os.path.join(PROJECT_ROOT, "output/spiderman_recap_part2_60fps.mp4")
    synthesize_episode_voices(p2_script, p2_audio_dir)
    render_episode_video(p2_script, p2_audio_dir, p2_mp4, music_track)

    # 2. Part 3
    print("\n==================== [PRODUCING PART 3] ====================")
    p3_script = os.path.join(PROJECT_ROOT, "output/production/part3_script.json")
    p3_audio_dir = os.path.join(PROJECT_ROOT, "output/production/part3_audio")
    p3_mp4 = os.path.join(PROJECT_ROOT, "output/spiderman_recap_part3_60fps.mp4")
    synthesize_episode_voices(p3_script, p3_audio_dir)
    render_episode_video(p3_script, p3_audio_dir, p3_mp4, music_track)

    # 3. Full Movie Compilation
    print("\n==================== [PRODUCING FULL MOVIE] ====================")
    p1_mp4 = os.path.join(PROJECT_ROOT, "output/spiderman_recap_part1_comicsexplained_groove_60fps.mp4")
    movie_mp4 = os.path.join(PROJECT_ROOT, "output/spiderman_challenges_of_doom_full_movie_60fps.mp4")
    compile_full_movie(p1_mp4, p2_mp4, p3_mp4, movie_mp4)

    # 4. Thumbnails
    generate_all_thumbnails()
    print("\n[SUCCESS] Entire Full Comic Video Automation completed successfully!")

if __name__ == "__main__":
    main()
