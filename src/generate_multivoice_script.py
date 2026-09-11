#!/usr/bin/env python3
"""
generate_multivoice_script.py - Module 2: Cohesive Multi-Character Recap Script Generator
Generates a fluid, broadcast-style narrative with distinct character voices
(Narrator, Doctor Doom, Spider-Man) connecting the story beats seamlessly.
"""

import os
import json
import argparse

def generate_cohesive_script(output_script_path="output/modular_production/multivoice_script.json"):
    panels_dir = "output/Challenges_of_Doom_Spider-Man_001"

    scenes = [
        {
            "scene_id": "scene_001",
            "panel_index": 3,
            "panel_image": os.path.join(panels_dir, "panel_003_p03_01.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Deep beneath his Latverian fortress, Doctor Doom sits staring at a chessboard of his greatest enemies. He knows brute force won't break Reed Richards. He needs to distract the pawns.",
            "camera_motion": "push_in_zoom"
        },
        {
            "scene_id": "scene_002",
            "panel_index": 4,
            "panel_image": os.path.join(panels_dir, "panel_004_p03_02.png"),
            "speaker": "Doctor Doom",
            "voice_id": "javert",
            "line": "Richards continues to vex me! But perhaps it is time I introduce an unpredictable wild card to the board.",
            "camera_motion": "snap_punch_zoom"
        },
        {
            "scene_id": "scene_003",
            "panel_index": 5,
            "panel_image": os.path.join(panels_dir, "panel_005_p04_01.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Meanwhile, completely unaware he's Doom's next target, Peter Parker is hanging upside down from his bedroom ceiling in Queens, having a blast testing his web-shooters!",
            "camera_motion": "vertical_pan"
        },
        {
            "scene_id": "scene_004",
            "panel_index": 5,
            "panel_image": os.path.join(panels_dir, "panel_005_p04_01.png"),
            "speaker": "Spider-Man",
            "voice_id": "marius",
            "line": "Woo-hoo! If the gang at the bowling alley could see me now! With these new controls, I can spray glue or launch web-balls like baseballs!",
            "camera_motion": "push_in_zoom"
        },
        {
            "scene_id": "scene_005",
            "panel_index": 6,
            "panel_image": os.path.join(panels_dir, "panel_006_p04_02.png"),
            "speaker": "Spider-Man",
            "voice_id": "marius",
            "line": "Wonder if the Mets are looking for a new pitcher? Wait, oh no, the study lamp!",
            "camera_motion": "impact_shake"
        },
        {
            "scene_id": "scene_006",
            "panel_index": 7,
            "panel_image": os.path.join(panels_dir, "panel_007_p05_01.png"),
            "speaker": "Spider-Man",
            "voice_id": "marius",
            "line": "Caught it! Not bad, Parker. Still got lightning-fast reflexes!",
            "camera_motion": "push_in_zoom"
        },
        {
            "scene_id": "scene_007",
            "panel_index": 8,
            "panel_image": os.path.join(panels_dir, "panel_008_p05_02.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Peter catches the lamp with inches to spare. But before he can even catch his breath, his Spider-Sense blares like an air-raid siren!",
            "camera_motion": "impact_shake"
        },
        {
            "scene_id": "scene_008",
            "panel_index": 9,
            "panel_image": os.path.join(panels_dir, "panel_009_p05_03.png"),
            "speaker": "Spider-Man",
            "voice_id": "marius",
            "line": "Ugh, my head! Somebody's broadcasting a high-frequency pulse straight through my web-shooters... and it's coming from across town!",
            "camera_motion": "pull_out_zoom"
        }
    ]

    os.makedirs(os.path.dirname(os.path.abspath(output_script_path)), exist_ok=True)
    with open(output_script_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[+] Cohesive 8-scene narrative script generated: {output_script_path}")
    return scenes

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="output/modular_production/multivoice_script.json")
    args = parser.parse_args()
    generate_cohesive_script(args.output)
