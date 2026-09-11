#!/usr/bin/env python3
"""
generate_multivoice_script.py - Module 2: Cohesive Multi-Character Recap Script Generator
Generates a fluid, broadcast-style narrative with distinct character voices
(Narrator, Doctor Doom, Spider-Man) connecting the story beats seamlessly.
"""

import os
import sys
import json
import argparse
import re

DEFAULT_VOICE_MAP = {
    "doctor doom": "javert",
    "doom": "javert",
    "victor": "javert",
    "spider-man": "marius",
    "peter parker": "marius",
    "peter": "marius",
    "spidey": "marius",
    "aunt may": "fantine",
    "may": "fantine",
    "mrs. parker": "fantine",
    "human torch": "enjolras",
    "johnny storm": "enjolras",
    "johnny": "enjolras",
    "the thing": "javert",
    "ben grimm": "javert",
    "ben": "javert",
    "mr. fantastic": "marius",
    "reed richards": "marius",
    "reed": "marius",
    "invisible woman": "fantine",
    "sue storm": "fantine",
    "sue": "fantine",
    "vulture": "javert",
    "adrian toomes": "javert",
    "narrator": "alba"
}


def resolve_voice_for_speaker(speaker_name, custom_voice_map=None):
    """
    Resolves the best Pocket-TTS voice identifier for a given character name.
    Defaults to 'alba' for unknown characters or general narration.
    """
    if not speaker_name:
        return "alba"

    voice_map = DEFAULT_VOICE_MAP.copy()
    if custom_voice_map:
        voice_map.update(custom_voice_map)

    name_lower = speaker_name.lower().strip()
    # 1. Exact match
    if name_lower in voice_map:
        return voice_map[name_lower]

    # 2. Substring match
    for k, v in voice_map.items():
        if k in name_lower or name_lower in k:
            return v

    # 3. Default fallback
    return "alba"


def clean_script_line(text):
    """
    Cleans up OCR noise, double quotes, and formatting artifacts.
    """
    if not text:
        return ""
    text = text.strip(' "\'“”‘’')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def generate_cohesive_script(
    vision_json_path=None,
    output_script_path="output/modular_production/multivoice_script.json",
    style="hybrid",
    max_panels=None,
    custom_voice_map=None
):
    """
    Generates a multi-voice production script from vision extraction data.
    Styles:
      - 'hybrid': Narrator recaps establishing scenes + characters speak actual dialogue (default)
      - 'recap_only': High-speed broadcast recap narration only
      - 'dialogue_only': Dramatic character voice acting only
    """
    scenes = []

    # If vision JSON is provided and exists, generate dynamically
    if vision_json_path and os.path.exists(vision_json_path):
        print(f"[*] Ingesting multimodal vision context from: {vision_json_path}")
        with open(vision_json_path, "r", encoding="utf-8") as f:
            panels_vision = json.load(f)

        if max_panels:
            panels_vision = panels_vision[:max_panels]

        comic_dir = os.path.dirname(os.path.abspath(vision_json_path))
        scene_counter = 1

        for p in panels_vision:
            p_id = p.get("panel_id", f"panel_{p.get('global_index', 0):03d}")
            p_img = p.get("filename", "")
            if not os.path.isabs(p_img):
                p_img = os.path.join(comic_dir, p_img)

            vision = p.get("vision", {})
            v_ctx = vision.get("visual_context", {})
            d_analysis = vision.get("dialogue_analysis", {})
            c_staging = vision.get("cinematic_staging", {})

            scene_type = v_ctx.get("scene_type", "PANEL")
            cam_motion = c_staging.get("recommended_camera_motion", "push_in_zoom")
            pacing = c_staging.get("pacing_seconds", 3.5)
            recap_line = clean_script_line(c_staging.get("cinematic_narrator_recap", ""))
            spoken = d_analysis.get("spoken_dialogue", [])

            # 1. Narrator Lead-in / Recap
            include_narrator = False
            if style in ["hybrid", "recap_only"]:
                if style == "recap_only" or not spoken or scene_type in ["WIDE_ESTABLISHING", "DRAMATIC_REVEAL"]:
                    if recap_line:
                        include_narrator = True

            if include_narrator and recap_line:
                scenes.append({
                    "scene_id": f"scene_{scene_counter:03d}",
                    "panel_id": p_id,
                    "panel_index": p.get("global_index", scene_counter),
                    "panel_image": p_img,
                    "speaker": "Narrator",
                    "voice_id": "alba",
                    "line": recap_line,
                    "camera_motion": cam_motion,
                    "pacing_seconds": pacing,
                    "scene_type": scene_type
                })
                scene_counter += 1

            # 2. Spoken Dialogue Lines
            if style in ["hybrid", "dialogue_only"]:
                for d in spoken:
                    speaker = d.get("speaker", "Character")
                    line_text = clean_script_line(d.get("text", ""))
                    if not line_text or len(line_text) < 2:
                        continue

                    voice = resolve_voice_for_speaker(speaker, custom_voice_map)
                    scenes.append({
                        "scene_id": f"scene_{scene_counter:03d}",
                        "panel_id": p_id,
                        "panel_index": p.get("global_index", scene_counter),
                        "panel_image": p_img,
                        "speaker": speaker,
                        "voice_id": voice,
                        "line": line_text,
                        "camera_motion": cam_motion if not include_narrator else "snap_punch_zoom",
                        "pacing_seconds": max(2.5, len(line_text.split()) * 0.35),
                        "scene_type": scene_type
                    })
                    scene_counter += 1

    else:
        # Static curated fallback (for testing or bootstrapping)
        print(f"[*] Notice: No vision JSON provided or found. Using curated starter narrative.")
        panels_dir = "output/Challenges_of_Doom_Spider-Man_001"
        scenes = [
            {
                "scene_id": "scene_001",
                "panel_id": "panel_003_p03_01",
                "panel_index": 3,
                "panel_image": os.path.join(panels_dir, "panel_003_p03_01.png"),
                "speaker": "Narrator",
                "voice_id": "alba",
                "line": "Deep beneath his Latverian fortress, Doctor Doom sits staring at a chessboard of his greatest enemies.",
                "camera_motion": "push_in_zoom",
                "pacing_seconds": 3.5,
                "scene_type": "DRAMATIC_REVEAL"
            },
            {
                "scene_id": "scene_002",
                "panel_id": "panel_004_p03_02",
                "panel_index": 4,
                "panel_image": os.path.join(panels_dir, "panel_004_p03_02.png"),
                "speaker": "Doctor Doom",
                "voice_id": "javert",
                "line": "Richards continues to vex me! But perhaps it is time I introduce an unpredictable wild card to the board.",
                "camera_motion": "snap_punch_zoom",
                "pacing_seconds": 3.2,
                "scene_type": "DRAMATIC_REVEAL"
            },
            {
                "scene_id": "scene_003",
                "panel_id": "panel_006_p04_01",
                "panel_index": 6,
                "panel_image": os.path.join(panels_dir, "panel_006_p04_01.png"),
                "speaker": "Narrator",
                "voice_id": "alba",
                "line": "Meanwhile, Peter Parker is hanging upside down from his ceiling in Queens, having a blast testing his web-shooters!",
                "camera_motion": "slow_pan_down",
                "pacing_seconds": 3.5,
                "scene_type": "ACTION_COMBAT"
            },
            {
                "scene_id": "scene_004",
                "panel_id": "panel_008_p05_01",
                "panel_index": 8,
                "panel_image": os.path.join(panels_dir, "panel_008_p05_01.png"),
                "speaker": "Peter Parker",
                "voice_id": "marius",
                "line": "Nothing, Aunt May! Just tossing a baseball around!",
                "camera_motion": "snap_punch_zoom",
                "pacing_seconds": 2.8,
                "scene_type": "COMEDIC_BEAT"
            }
        ]

    os.makedirs(os.path.dirname(os.path.abspath(output_script_path)), exist_ok=True)
    with open(output_script_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[+] Cohesive narrative script ({len(scenes)} scenes) generated: {output_script_path}")
    return scenes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dynamic multi-voice comic script.")
    parser.add_argument("--vision-json", default="output/Challenges_of_Doom_Spider-Man_001/comic_scene_vision.json", help="Path to vision extraction JSON")
    parser.add_argument("--output", default="output/modular_production/multivoice_script.json", help="Output multivoice_script.json path")
    parser.add_argument("--style", choices=["hybrid", "recap_only", "dialogue_only"], default="hybrid", help="Script generation style")
    parser.add_argument("--max-panels", type=int, default=None, help="Limit number of panels")
    args = parser.parse_args()

    generate_cohesive_script(
        vision_json_path=args.vision_json,
        output_script_path=args.output,
        style=args.style,
        max_panels=args.max_panels
    )
