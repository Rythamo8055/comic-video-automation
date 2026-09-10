#!/usr/bin/env python3
"""
build_1080p_cinematic_recap.py - Full 1080p Cinematic Motion Comic Recap Generator.
Features:
  - 1080p Full HD resolution (1920x1080 @ 24fps)
  - Precision panel-by-panel story flow (travels through sub-panels P1->P2->P3)
  - Lively, dramatic storytelling script with comic dialogue
  - Procedural intense 135 BPM action score with auto-ducking
  - Smooth Cubic & Sine camera easing + impact physics
  - Native FFmpeg xfade transitions between every panel
"""

import os
import subprocess
from src.smooth_motion_engine import render_motion, get_h264_encoder
from src.comic_toolkit import transition_two_clips

def generate_voice(text, out_wav):
    cmd = [
        "pocket-tts", "generate",
        "--text", text,
        "--output-path", out_wav,
        "--device", "cpu",
        "--quiet"
    ]
    subprocess.run(cmd, check=True)
    probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", out_wav
    ]
    dur = float(subprocess.check_output(probe, text=True).strip())
    return dur

def build_1080p_recap(output_mp4="output/spiderman_doom_1080p_cinematic.mp4"):
    work_dir = "output/cinematic_1080p_work"
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.dirname(output_mp4), exist_ok=True)

    print("=====================================================================")
    print("🔥 PRODUCING FULL 1080p CINEMATIC PANEL-BY-PANEL RECAP VIDEO 🔥")
    print("=====================================================================")

    scenes = [
        {
            "id": "sc01_cover",
            "img": "data/spider_man_001/precise_panels/p01_panel_1.png",
            "text": "Welcome back, comic fans! Today, Doctor Doom tests the absolute limits of New York's friendly neighborhood hero in Marvel's Challenges of Doom: Spider-Man issue number one!",
            "mode": "push_in_zoom",
            "trans": "fadewhite"
        },
        {
            "id": "sc02_lore",
            "img": "data/spider_man_001/precise_panels/p02_panel_1.png",
            "text": "In Latveria, Doctor Victor Von Doom commands absolute dominion through ancient dark sorcery and bleeding-edge cybernetics. But across the world in Queens, young Peter Parker lives by a sacred code: with great power, there must also come great responsibility.",
            "mode": "vertical_pan",
            "trans": "smoothleft"
        },
        {
            "id": "sc03_doom_chess1",
            "img": "data/spider_man_001/precise_panels/p03_panel_1.png",
            "text": "Years ago, deep inside his subterranean castle lab, Doom stared down at a chessboard of his greatest enemies: the Fantastic Four. Richards continues to vex him. But Doom realizes that to checkmate the king, he must first eliminate the pawns.",
            "mode": "push_in_zoom",
            "trans": "zoomin"
        },
        {
            "id": "sc04_doom_chess2",
            "img": "data/spider_man_001/precise_panels/p03_panel_2.png",
            "text": "Doom sneers behind his iron faceplate: 'Perhaps it is time to introduce a brand-new piece to the board: an arachnid!'",
            "mode": "snap_punch_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "sc05_p4_ceiling",
            "img": "data/spider_man_001/precise_panels/p04_panel_1.png",
            "text": "Meanwhile in Queens, Peter Parker is hanging upside down from his bedroom ceiling, having the time of his life tinkering with his web-shooters! 'Woo-hoo! If the gang at the bowling alley could see me now! With these new controls, I can spray it like glue, or shoot a web-ball out like a baseball!'",
            "mode": "push_in_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "sc06_p4_thwip",
            "img": "data/spider_man_001/precise_panels/p04_panel_2.png",
            "text": "He aims at the wall and pulls the trigger—THWIP! The pressurized web-ball rockets across the room!",
            "mode": "snap_punch_zoom",
            "trans": "wipeleft"
        },
        {
            "id": "sc07_p4_thud",
            "img": "data/spider_man_001/precise_panels/p04_panel_3.png",
            "text": "THUD! The web-ball smashes directly into his study lamp, sending it tumbling off the desk! 'Uh-oh... Wonder if the Mets are looking for a new pitcher?'",
            "mode": "impact_shake",
            "trans": "smoothleft"
        },
        {
            "id": "sc08_p5_aunt_may",
            "img": "data/spider_man_001/precise_panels/p05_panel_1.png",
            "text": "Downstairs, Aunt May's voice echoes up: 'Peter? I can hear rough-housing!' Peter panics, firing a frantic strand: 'Oh boy!'",
            "mode": "push_in_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "sc09_p5_lamp_fall",
            "img": "data/spider_man_001/precise_panels/p05_panel_2.png",
            "text": "Aunt May calls out: 'What's going on up there?' Peter scrambles mid-air: 'N-nothing, Aunt May!'",
            "mode": "pull_out_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "sc10_p5_lamp_catch",
            "img": "data/spider_man_001/precise_panels/p05_panel_3.png",
            "text": "THWAP! Peter snatches the falling lamp just inches from the floor! 'Just... uh... tossing a baseball around!' Aunt May warns: 'Well don't! You'll cause yourself an injury!'",
            "mode": "push_in_zoom",
            "trans": "smoothleft"
        },
        {
            "id": "sc11_p5_bed_stress",
            "img": "data/spider_man_001/precise_panels/p05_panel_4.png",
            "text": "Peter collapses on his bed: 'More like I could cause her a coronary! What if she came up and found me dancing on the ceiling? Every cent Jonah pays me goes straight to rent! If I'd broken this, I'd be reading by candlelight!'",
            "mode": "vertical_pan",
            "trans": "fadewhite"
        },
        {
            "id": "sc12_p5_spidersense",
            "img": "data/spider_man_001/precise_panels/p05_panel_5.png",
            "text": "Suddenly, without any warning, Peter's spider-sense explodes inside his skull like a siren! 'SPIDER-MAN! HNNNHHH!' Danger has arrived!",
            "mode": "impact_shake",
            "trans": "fadewhite"
        },
        {
            "id": "sc13_p10_warehouse",
            "img": "data/spider_man_001/precise_panels/p10_panel_1.png",
            "text": "Drawn to an abandoned industrial facility by a distress beacon, Spider-Man drops through the skylight. But the moment his feet touch the ground, massive titanium blast doors slam shut, sealing him inside!",
            "mode": "impact_shake",
            "trans": "fadewhite"
        },
        {
            "id": "sc14_p13_gauntlet_left",
            "img": "data/spider_man_001/precise_panels/p13_panel_left.png",
            "text": "And the battle is joined! In this massive double-page gauntlet, Doom unleashes his full arsenal: magnetic force globes, electrified flooring, and floor-mounted heat rays!",
            "mode": "horizontal_pan",
            "trans": "zoomin"
        },
        {
            "id": "sc15_p13_gauntlet_right",
            "img": "data/spider_man_001/precise_panels/p13_panel_right.png",
            "text": "Spider-Man flips through the air at blinding speed, dodging disintegrator beams while smashing through duplicate Doombots with lethal precision!",
            "mode": "horizontal_pan",
            "trans": "smoothleft"
        },
        {
            "id": "sc16_p20_doom_holo",
            "img": "data/spider_man_001/precise_panels/p20_panel_1.png",
            "text": "A towering armored projection of Doctor Doom materializes before the wall-crawler. Doom coldly sneers: 'You survived this opening test, arachnid. But Latveria never forgets, and Doom never loses!'",
            "mode": "push_in_zoom",
            "trans": "fadeblack"
        },
        {
            "id": "sc17_p25_outro",
            "img": "data/spider_man_001/precise_panels/p25_panel_1.png",
            "text": "Spider-Man swings away into the Manhattan sunset, knowing Doctor Doom is plotting his next move. What will happen when these two titans clash again? Smash that like button, subscribe for part two, and we'll see you in the next recap!",
            "mode": "pull_out_zoom",
            "trans": "fadeblack"
        }
    ]

    rendered_clips = []
    print(f"[1/3] Generating 1080p clips and Pocket TTS voice for all {len(scenes)} panels...")

    for idx, sc in enumerate(scenes, 1):
        print(f"\n--- Panel {idx}/{len(scenes)}: {sc['id']} ({sc['mode']}) ---")
        wav_path = os.path.join(work_dir, f"{sc['id']}.wav")
        clip_path = os.path.join(work_dir, f"{sc['id']}_1080p.mp4")

        # Voiceover
        duration = generate_voice(sc["text"], wav_path)
        print(f"  Voice: {duration:.2f}s")

        # Render 1080p with smooth easing
        render_motion(
            image_path=sc["img"],
            output_mp4=clip_path,
            duration=duration,
            fps=24,
            mode=sc["mode"],
            audio_path=wav_path,
            out_w=1920,
            out_h=1080
        )
        rendered_clips.append((clip_path, wav_path, sc["trans"]))

    # Step 2: Chain all 1080p clips with transitions
    print(f"\n[2/3] Chaining {len(rendered_clips)} 1080p clips with native xfade transitions...")
    current_clip = rendered_clips[0][0]

    for i in range(1, len(rendered_clips)):
        next_clip = rendered_clips[i][0]
        trans_name = rendered_clips[i][2]
        step_out = os.path.join(work_dir, f"step_{i}_1080p.mp4")
        print(f"  -> Transition '{trans_name}' between Panel {i} and {i+1}...")
        transition_two_clips(current_clip, next_clip, step_out, transition=trans_name, duration=0.4)
        current_clip = step_out

    chained_video = os.path.join(work_dir, "master_chained_1080p.mp4")
    os.rename(current_clip, chained_video)

    # Step 3: Concatenate voiceover tracks & mix with procedural action score
    print("\n[3/3] Mixing master voiceover with 135 BPM procedural action score...")
    wav_list_file = os.path.join(work_dir, "wav_list.txt")
    with open(wav_list_file, "w") as f:
        for item in rendered_clips:
            f.write(f"file '{os.path.abspath(item[1])}'\n")

    master_voice = os.path.join(work_dir, "master_voice_1080p.wav")
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", wav_list_file,
        "-c", "copy", master_voice
    ], check=True)

    bgm = "assets/procedural_action_score.wav"
    encoder = get_h264_encoder()

    mix_cmd = [
        "ffmpeg", "-y",
        "-i", chained_video,
        "-i", master_voice,
        "-stream_loop", "-1", "-i", bgm,
        "-filter_complex",
        # Auto-duck procedural action score to 0.12 under voice
        "[2:a]volume=0.12[bgm];[1:a][bgm]amix=inputs=2:duration=first[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "256k",
        "-shortest",
        output_mp4
    ]
    subprocess.run(mix_cmd, check=True)

    print("\n🎉 1080p CINEMATIC RECAP COMPLETE!")
    print(f"  Master File: {output_mp4}")
    probe = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=width,height",
        "-of", "default=noprint_wrappers=1", output_mp4
    ]
    print(subprocess.check_output(probe, text=True).strip())
    return output_mp4

if __name__ == "__main__":
    build_1080p_recap()
