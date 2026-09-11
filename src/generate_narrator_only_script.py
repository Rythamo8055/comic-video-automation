#!/usr/bin/env python3
"""
generate_narrator_only_script.py
Generates a 100% Narrator-Only engaging recap script in the style of top comic recap YouTube channels.
Explains the visual narrative, stakes, humor, and story flow with zero character dialogue acting.
"""

import os
import json
import argparse

def generate_narrator_script(output_path="output/modular_production/narrator_only_script.json"):
    panels_dir = "output/Challenges_of_Doom_Spider-Man_001"

    scenes = [
        {
            "scene_id": "scene_001",
            "panel_index": 3,
            "panel_image": os.path.join(panels_dir, "panel_003_p03_01.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Our story kicks off deep beneath Latveria, where Doctor Doom is obsessing over a chessboard of his greatest rivals, the Fantastic Four. Reed Richards has been outsmarting him at every turn, so Doom realizes brute force won't work: he needs to distract the pawns to take down the king.",
            "camera_motion": "push_in_zoom"
        },
        {
            "scene_id": "scene_002",
            "panel_index": 4,
            "panel_image": os.path.join(panels_dir, "panel_004_p03_02.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "And with a sinister smile, Doom knocks Reed's chess piece off the board with a brand-new wild card: an arachnid! Doom has officially decided that Spider-Man is the perfect pawn to throw his enemies into absolute chaos.",
            "camera_motion": "snap_punch_zoom"
        },
        {
            "scene_id": "scene_003",
            "panel_index": 5,
            "panel_image": os.path.join(panels_dir, "panel_005_p04_01.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Cut across the Atlantic to Queens, New York, where Peter Parker has zero clue he's being targeted by one of Marvel's deadliest villains! Instead, Peter is literally chilling upside-down on his bedroom ceiling, having the absolute time of his life.",
            "camera_motion": "vertical_pan"
        },
        {
            "scene_id": "scene_004",
            "panel_index": 5,
            "panel_image": os.path.join(panels_dir, "panel_005_p04_01.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "He's been tinkering with his web-shooters all afternoon, showing off that with these brand-new pressure controls, he can spray glue-like nets or launch dense web pellets like major league fastballs.",
            "camera_motion": "push_in_zoom"
        },
        {
            "scene_id": "scene_005",
            "panel_index": 6,
            "panel_image": os.path.join(panels_dir, "panel_006_p04_02.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Peter decides to test his aim and fires a shot across the room, only for the web pellet to ricochet wildly and send his favorite study lamp flying off the desk!",
            "camera_motion": "impact_shake"
        },
        {
            "scene_id": "scene_006",
            "panel_index": 7,
            "panel_image": os.path.join(panels_dir, "panel_007_p05_01.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Panic mode instantly sets in, but Peter's reflexes are on another level! He flips down mid-air, firing a web line and snagging the lamp mere inches before it shatters all over Aunt May's floor.",
            "camera_motion": "push_in_zoom"
        },
        {
            "scene_id": "scene_007",
            "panel_index": 8,
            "panel_image": os.path.join(panels_dir, "panel_008_p05_02.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Peter breathes a huge sigh of relief, but before he can even celebrate, his Spider-Sense suddenly goes completely nuclear! It's not danger from Aunt May: it's an overwhelming psychic alarm ringing through his skull.",
            "camera_motion": "impact_shake"
        },
        {
            "scene_id": "scene_008",
            "panel_index": 9,
            "panel_image": os.path.join(panels_dir, "panel_009_p05_03.png"),
            "speaker": "Narrator",
            "voice_id": "alba",
            "line": "Clutching his head in agony, Peter realizes someone is broadcasting a high-frequency tactical pulse straight into his web-shooters, luring him directly toward a trap in an abandoned warehouse across town!",
            "camera_motion": "pull_out_zoom"
        }
    ]

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[+] Narrator-only recap script saved to: {output_path}")
    return scenes

if __name__ == "__main__":
    generate_narrator_script()
