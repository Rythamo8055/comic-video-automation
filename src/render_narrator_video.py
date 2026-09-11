#!/usr/bin/env python3
"""
render_narrator_video.py
Renders the complete 100% Narrator-Only Engaging Recap Video (1080p Full HD Zero-Jitter).
"""

import os
import sys
import json
import subprocess

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.generate_narrator_only_script import generate_narrator_script
from src.render_zero_jitter_video import render_scene_clip, assemble_final_video

def main():
    work_dir = "output/narrator_recap_production"
    audio_dir = os.path.join(work_dir, "voiceovers")
    clips_dir = os.path.join(work_dir, "clips")
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(clips_dir, exist_ok=True)

    script_file = os.path.join(work_dir, "narrator_script.json")
    scenes = generate_narrator_script(script_file)

    # 1. Synthesize Audio
    print(f"\n[Step 1/2] Synthesizing Narrator voiceover for {len(scenes)} scenes via Pocket TTS...")
    for sc in scenes:
        sid = sc["scene_id"]
        text = sc["line"]
        voice_id = sc["voice_id"]
        wav_path = os.path.join(audio_dir, f"{sid}_narrator.wav")

        print(f"  -> Synthesizing {sid}...")
        cmd = [
            "/usr/local/bin/pocket-tts", "generate",
            "--text", text,
            "--voice", voice_id,
            "--temperature", "0.30",
            "--output-path", wav_path,
            "--device", "cpu",
            "-q"
        ]
        subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)

    # 2. Render Zero-Jitter 1080p Centered Clips
    print(f"\n[Step 2/2] Rendering 1080p centered zero-jitter camera motion...")
    clip_paths = []
    for sc in scenes:
        sid = sc["scene_id"]
        img_path = sc["panel_image"]
        mode = sc["camera_motion"]
        wav_path = os.path.join(audio_dir, f"{sid}_narrator.wav")
        clip_path = os.path.join(clips_dir, f"{sid}_1080p.mp4")

        print(f"  -> Rendering {sid} [{mode}]...")
        render_scene_clip(
            image_path=img_path,
            audio_path=wav_path,
            output_clip_path=clip_path,
            mode=mode,
            fps=30,
            out_w=1920,
            out_h=1080
        )
        clip_paths.append(clip_path)

    final_video = "output/spiderman_narrator_recap_1080p.mp4"
    bgm_path = "assets/bgm_action.wav"
    assemble_final_video(clip_paths, final_video, bgm_path=bgm_path)
    print(f"\n[SUCCESS] Final Narrator-Only 1080p Video Created: {final_video}")

if __name__ == "__main__":
    main()
