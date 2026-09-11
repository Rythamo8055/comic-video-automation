#!/usr/bin/env python3
"""
src/script_generator_engine.py
Generalized Script Generation Engine for Comic Video Automation.
Transforms raw panel OCR & layout annotations (comic_breakdown.json) into a cohesive,
YouTube-style Narrator Recap Script (narrator_script.json).
"""

import os
import json
import re

def build_greeting_line(comic_title, issue_num=1, part_num=1):
    return (
        f"What is up comic fans, and welcome back to the channel! Today, we are breaking down "
        f"{comic_title}, Issue Number {issue_num}. When our heroes are pushed to their absolute limits, "
        f"everything hangs in the balance. Let's get right into Part {part_num}!"
    )

def build_outro_line(part_num=1):
    next_part = part_num + 1
    return (
        f"What insane twists are waiting around the corner? Can our heroes survive the trials ahead? "
        f"Subscribe, hit that notification bell, and wait for the next video coming right up in Part {next_part}!"
    )

def assign_camera_motion_and_tone(ocr_text, panel_idx, total_panels):
    text_lower = ocr_text.lower()
    
    # Impact / Action
    if any(k in text_lower for k in ["boom", "crash", "smash", "thwip", "attack", "danger", "warning", "!"]):
        return "impact_shake", "white_flash", "0.62"
    
    # Reveal / Shock
    if any(k in text_lower for k in ["dead", "kill", "trap", "alarm", "behold", "impossible"]):
        return "snap_punch_zoom", "white_flash", "0.58"
        
    # Tall or wide reading panel
    if panel_idx % 3 == 0:
        return "vertical_pan", "slide_left", "0.40"
    elif panel_idx % 4 == 0:
        return "pull_out_zoom", "slide_left", "0.45"
        
    # Default slow push-in zoom
    return "push_in_zoom", "white_flash", "0.38"

def generate_narrator_script_from_breakdown(
    breakdown_json_path,
    output_script_path,
    cover_image_path=None,
    comic_title="Comic Story",
    issue_num=1,
    part_num=1,
    voice_id="alba"
):
    """
    Reads comic_breakdown.json (panel metadata + OCR text) and creates narrator_script.json.
    """
    panels = []
    if os.path.exists(breakdown_json_path):
        with open(breakdown_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                panels = data
            elif isinstance(data, dict) and "panels" in data:
                panels = data["panels"]

    scenes = []

    # 1. Option 2: Cover Greeting Scene (scene_000)
    if cover_image_path and os.path.exists(cover_image_path):
        scenes.append({
            "scene_id": "scene_000",
            "panel_index": 0,
            "panel_image": cover_image_path,
            "speaker": "Narrator",
            "voice_id": voice_id,
            "line": build_greeting_line(comic_title, issue_num, part_num),
            "camera_motion": "push_in_zoom",
            "transition": "white_flash",
            "overlay_title": f"{comic_title.upper()} #{issue_num}",
            "overlay_subtitle": f"PART {part_num} FULL RECAP",
            "overlay_text": ""
        })

    # 2. Body Scenes from Panels
    for idx, p in enumerate(panels, 1):
        sid = f"scene_{idx:03d}"
        p_img = p.get("panel_image") or p.get("image_path") or p.get("path")
        p_text = p.get("text") or p.get("ocr_text") or ""
        
        # If human/agent refined line exists, use it; else adapt OCR text
        rec_line = p.get("narrator_line")
        if not rec_line:
            clean_text = re.sub(r'[\r\n]+', ' ', p_text).strip()
            if clean_text and len(clean_text) > 10:
                rec_line = f"As the scene unfolds, we see that {clean_text}."
            else:
                rec_line = f"The tension continues to build as our characters face the unexpected."

        motion, trans, temp = assign_camera_motion_and_tone(p_text, idx, len(panels))
        
        scenes.append({
            "scene_id": sid,
            "panel_index": idx,
            "panel_image": p_img,
            "speaker": "Narrator",
            "voice_id": voice_id,
            "line": rec_line,
            "camera_motion": motion,
            "transition": trans,
            "overlay_title": "",
            "overlay_subtitle": "",
            "overlay_text": ""
        })

    # 3. Outro Scene (scene_outro)
    outro_img = cover_image_path if cover_image_path and os.path.exists(cover_image_path) else (scenes[-1]["panel_image"] if scenes else "")
    scenes.append({
        "scene_id": f"scene_{(len(scenes)):03d}",
        "panel_index": len(scenes),
        "panel_image": outro_img,
        "speaker": "Narrator",
        "voice_id": voice_id,
        "line": build_outro_line(part_num),
        "camera_motion": "push_in_zoom",
        "transition": "none",
        "overlay_title": "",
        "overlay_subtitle": "",
        "overlay_text": f"WAIT FOR THE NEXT VIDEO! PART {part_num + 1} COMING NEXT"
    })

    os.makedirs(os.path.dirname(os.path.abspath(output_script_path)), exist_ok=True)
    with open(output_script_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"[+] Replicable master recap script created with {len(scenes)} scenes at: {output_script_path}")
    return scenes

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate narrator recap script from comic breakdown.")
    parser.add_argument("--breakdown", default="output/comic_breakdown.json")
    parser.add_argument("--output", default="output/narrator_script.json")
    parser.add_argument("--cover", default=None)
    parser.add_argument("--title", default="Spider-Man: Challenges of Doom")
    parser.add_argument("--issue", type=int, default=1)
    parser.add_argument("--part", type=int, default=1)
    args = parser.parse_args()

    generate_narrator_script_from_breakdown(
        args.breakdown, args.output, args.cover, args.title, args.issue, args.part
    )
