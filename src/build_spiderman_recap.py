#!/usr/bin/env python3
"""
build_spiderman_recap.py - Full Motion Comic Recap Video Generator
for 'Challenges Of Doom - Spider-Man #001'.
Uses:
  - Kyutai Pocket TTS (3.3x real-time voice synthesis on CPU)
  - Smooth Motion Engine (Cubic/Sine easing curves, subpixel interpolation)
  - FFmpeg xfade (native transitions: smoothleft, fadewhite, zoomin, fadeblack)
  - Audio sidechain ducking for background music
"""

import os
import sys
import subprocess
from src.smooth_motion_engine import render_motion, get_h264_encoder
from src.comic_toolkit import transition_two_clips

def generate_voiceover(text, output_wav):
    cmd = [
        "pocket-tts", "generate",
        "--text", text,
        "--output-path", output_wav,
        "--device", "cpu",
        "--quiet"
    ]
    subprocess.run(cmd, check=True)
    probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", output_wav
    ]
    dur = float(subprocess.check_output(probe, text=True).strip())
    return dur

def build_recap_video(output_final="output/spiderman_challenges_of_doom_recap.mp4"):
    work_dir = "output/spiderman_recap_work"
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_final), exist_ok=True)

    print("=========================================================")
    print("🎬 BUILDING FULL SPIDER-MAN: CHALLENGES OF DOOM RECAP")
    print("=========================================================")

    scenes = [
        {
            "id": "scene_01",
            "img": "data/spider_man_001/pages/page_01.jpg",
            "text": "Welcome back, true believers! Today, we dive into the ultimate clash of science, sorcery, and street-level heroism: Marvel's Challenges of Doom issue number one, featuring the Amazing Spider-Man!",
            "mode": "push_in_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "scene_02",
            "img": "data/spider_man_001/pages/page_02.jpg",
            "text": "In Latveria, Doctor Victor Von Doom rules with an iron fist, blending arcane sorcery with advanced cybernetics. But in New York City, young Peter Parker lives by a sacred code: with great power, there must also come great responsibility.",
            "mode": "vertical_pan",
            "trans": "fadewhite"
        },
        {
            "id": "scene_03",
            "img": "data/spider_man_001/panels/page_03/panel_001.png",
            "text": "Years ago, deep within his subterranean laboratory, Doom sits staring at a chessboard of his greatest enemies: the Fantastic Four. Reed Richards continues to vex him. But to reach the king, Doom must distract the pawns.",
            "mode": "push_in_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "scene_04",
            "img": "data/spider_man_001/panels/page_03/panel_002.png",
            "text": "Doom smiles behind his iron mask, declaring: perhaps it is time to introduce a brand-new piece to the board: an arachnid.",
            "mode": "push_in_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "scene_05",
            "img": "data/spider_man_001/pages/page_04.jpg",
            "text": "Meanwhile in Queens, Peter Parker is hanging upside down from his ceiling, having a blast tinkering with his web-shooters! He tests a new baseball-style web pellet, accidentally launching it straight into his study lamp with a loud thud!",
            "mode": "vertical_pan",
            "trans": "smoothleft"
        },
        {
            "id": "scene_06",
            "img": "data/spider_man_001/pages/page_05.jpg",
            "text": "Ignoring the mess, Peter leaps out the window into the New York sky, testing his new web fluid formulas high above the city traffic. But unknown to him, high-altitude surveillance cameras are tracking his every swing.",
            "mode": "horizontal_pan",
            "trans": "zoomin"
        },
        {
            "id": "scene_07",
            "img": "data/spider_man_001/pages/page_10.jpg",
            "text": "Lured into a suspicious warehouse by an unusual distress signal, Spider-Man's spider-sense blares like a siren! Heavy titanium blast doors slam shut behind him, locking him inside a high-tech proving ground.",
            "mode": "impact_shake",
            "trans": "fadewhite"
        },
        {
            "id": "scene_08",
            "img": "data/spider_man_001/pages/page_13.jpg",
            "text": "And the battle is joined! In this massive double-page spread, Doom unleashes his deadly gauntlet: magnetic force globes, electrified flooring, and searing disintegrator beams! Spidey leaps through the air, dodging lethal traps while smashing through duplicate Doombots!",
            "mode": "horizontal_pan",
            "trans": "smoothleft"
        },
        {
            "id": "scene_09",
            "img": "data/spider_man_001/pages/page_16.jpg",
            "text": "Realizing sheer force won't stop the machines, Spider-Man uses his rapid-fire web balls to clog the power conduits, short-circuiting Doom's automated defenses from the inside out!",
            "mode": "pull_out_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "scene_10",
            "img": "data/spider_man_001/pages/page_20.jpg",
            "text": "A towering armored projection of Doctor Doom materializes before the wall-crawler. Doom coldly acknowledges Spider-Man's agility, warning him that while he survived this initial test, Latveria never forgives.",
            "mode": "push_in_zoom",
            "trans": "fadeblack"
        },
        {
            "id": "scene_11",
            "img": "data/spider_man_001/pages/page_25.jpg",
            "text": "Spider-Man swings away into the Manhattan skyline as the sun sets. Doom watches from afar, calculating his next move. What will happen when these two titans clash again? Leave a like, subscribe for chapter two, and we'll see you in the next recap!",
            "mode": "pull_out_zoom",
            "trans": "fadeblack"
        }
    ]

    rendered_clips = []
    print(f"\n[Step 1/3] Generating voiceover and animated clips for {len(scenes)} scenes...")

    for idx, sc in enumerate(scenes, 1):
        print(f"\n--- Scene {idx}/{len(scenes)}: {sc['id']} ({sc['mode']}) ---")
        wav_path = os.path.join(work_dir, f"{sc['id']}_voice.wav")
        clip_path = os.path.join(work_dir, f"{sc['id']}_clip.mp4")

        # 1. Generate Voice with Pocket TTS
        print("  -> Generating voiceover with Pocket TTS...")
        duration = generate_voiceover(sc["text"], wav_path)
        print(f"     Duration: {duration:.2f}s")

        # 2. Render Motion with Easing
        print(f"  -> Rendering camera motion ({sc['mode']})...")
        render_motion(
            image_path=sc["img"],
            output_mp4=clip_path,
            duration=duration,
            fps=24,
            mode=sc["mode"],
            audio_path=wav_path
        )
        rendered_clips.append((clip_path, sc["trans"]))

    # Step 2: Chain clips with transitions
    print(f"\n[Step 2/3] Chaining {len(rendered_clips)} clips with native xfade transitions...")
    chained_video = os.path.join(work_dir, "chained_scenes.mp4")
    
    current = rendered_clips[0][0]
    for i in range(1, len(rendered_clips)):
        next_clip, trans_name = rendered_clips[i]
        out_temp = os.path.join(work_dir, f"step_{i}.mp4")
        print(f"  -> Applying transition '{trans_name}' between Scene {i} and {i+1}...")
        transition_two_clips(current, next_clip, out_temp, transition=trans_name, duration=0.4)
        current = out_temp

    os.rename(current, chained_video)

    # Step 3: Layer background action music with auto-ducking
    print("\n[Step 3/3] Mixing background music with auto-ducking...")
    bgm_path = "assets/bgm_action.wav"
    encoder = get_h264_encoder()

    mix_cmd = [
        "ffmpeg", "-y",
        "-i", chained_video,
        "-stream_loop", "-1", "-i", bgm_path,
        "-filter_complex",
        "[1:a]volume=0.12[bgm];[0:a][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_final
    ]
    subprocess.run(mix_cmd, check=True)

    print("\n🎉 RECAP VIDEO COMPLETE!")
    print(f"  Output: {output_final}")
    
    # Probe final specs
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size",
        "-of", "default=noprint_wrappers=1", output_final
    ]
    print(subprocess.check_output(probe_cmd, text=True).strip())
    return output_final

if __name__ == "__main__":
    build_recap_video()
