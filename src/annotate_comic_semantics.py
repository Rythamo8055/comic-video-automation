#!/usr/bin/env python3
"""
annotate_comic_semantics.py - Module 1: Multimodal Semantic Data Annotation
Extracts text, classifies semantic roles (Caption, Dialogue, SFX), detects character
speakers, emotions, and pacing across extracted comic panels.
Can be used standalone or as part of the video automation pipeline.
"""

import os
import sys
import json
import argparse
import cv2
import easyocr

def classify_role(box, text, panel_shape):
    x, y, bw, bh = box
    ph, pw = panel_shape[:2]
    text_lower = text.lower()

    sfx_words = ["thwip", "boom", "crack", "crash", "thud", "smash", "bam", "zap", "wham", "kachow"]
    if any(sw in text_lower for sw in sfx_words) or (len(text.split()) <= 2 and "!" in text and bh > 60):
        return "SOUND_EFFECT", 0.95

    caption_cues = ["journal", "update", "years ago", "meanwhile", "later", "transcribed", "chapter", "chapter one"]
    if y < ph * 0.35 and (any(c in text_lower for c in caption_cues) or (bw > pw * 0.4 and y < 140)):
        return "NARRATOR_CAPTION", 0.92

    return "CHARACTER_DIALOGUE", 0.90

def extract_character_and_tone(text, role, panel_idx):
    text_lower = text.lower()

    # Character Attribution
    if any(k in text_lower for k in ["richards", "doom", "latveria", "victor", "vex", "pawns", "king", "ruler"]):
        speaker = "Doctor Doom"
        voice_persona = "villain_baritone"
        speech_rate = 140  # WPM (deliberate, theatrical)
    elif any(k in text_lower for k in ["parker", "spider", "mets", "bowling", "thwip", "homework", "aunt may", "gang"]):
        speaker = "Spider-Man"
        voice_persona = "youthful_hero"
        speech_rate = 175  # WPM (energetic, rapid)
    elif role == "SOUND_EFFECT":
        speaker = "SFX_AUDIO"
        voice_persona = "sfx"
        speech_rate = 0
    else:
        speaker = "Narrator"
        voice_persona = "recap_narrator"
        speech_rate = 172

    # Emotion & Tone Detection
    if any(w in text_lower for w in ["vex", "dead", "distract", "pawns", "kill", "destroy", "doom"]):
        tone = "Calculating & Sinister"
        camera_motion = "push_in_zoom"
    elif any(w in text_lower for w in ["woo-hoo", "mets", "bowling", "fun", "easy"]):
        tone = "Playful & Energetic"
        camera_motion = "snap_punch_zoom"
    elif role == "SOUND_EFFECT" or any(w in text_lower for w in ["look out", "danger", "behind", "warning"]):
        tone = "Shock & Impact"
        camera_motion = "impact_shake"
    else:
        tone = "Dramatic Exposition"
        camera_motion = "pan_horizontal" if panel_idx % 2 == 0 else "push_in_zoom"

    return speaker, voice_persona, speech_rate, tone, camera_motion

def annotate_panels(panels_dir, manifest_path=None, output_json=None, max_panels=25):
    valid_exts = ('.png', '.jpg', '.jpeg')
    panel_files = sorted([f for f in os.listdir(panels_dir) if f.startswith('panel_') and f.endswith(valid_exts)])

    if not panel_files:
        raise FileNotFoundError(f"No panels found in {panels_dir}")

    print(f"[*] Initializing EasyOCR engine (CPU-optimized)...")
    reader = easyocr.Reader(['en'], gpu=False)

    annotated_story = []
    print(f"[*] Annotating semantics for {min(len(panel_files), max_panels)} story panels...")

    for idx, p_file in enumerate(panel_files[:max_panels], 1):
        p_path = os.path.join(panels_dir, p_file)
        img = cv2.imread(p_path)
        if img is None:
            continue

        h, w = img.shape[:2]
        ocr_results = reader.readtext(p_path)
        
        # Aggregate text inside panel
        texts = [res[1] for res in ocr_results if res[2] > 0.3]
        combined_text = " ".join(texts)

        if not combined_text:
            # Action / visual combat panel without dialogue
            role = "VISUAL_ACTION"
            speaker = "Narrator"
            voice_persona = "recap_narrator"
            speech_rate = 172
            tone = "High Action Combat"
            camera_motion = "horizontal_pan" if w > h * 1.5 else "impact_shake"
            elements = []
        else:
            # Group into primary dialogue / caption element
            box = (40, 40, w - 80, h // 3)
            role, conf = classify_role(box, combined_text, img.shape)
            speaker, voice_persona, speech_rate, tone, camera_motion = extract_character_and_tone(combined_text, role, idx)
            elements = [{
                "text": combined_text,
                "role": role,
                "confidence": conf
            }]

        entry = {
            "panel_index": idx,
            "filename": p_file,
            "path": p_path,
            "dimensions": {"width": w, "height": h},
            "primary_role": role,
            "speaker": speaker,
            "voice_persona": voice_persona,
            "speech_rate_wpm": speech_rate,
            "emotional_tone": tone,
            "recommended_camera": camera_motion,
            "dialogue_text": combined_text,
            "elements": elements
        }
        annotated_story.append(entry)
        print(f"  -> Panel #{idx:02d} ({p_file}): [{speaker} | {role}] Tone: {tone} -> Camera: {camera_motion}")

    if output_json:
        os.makedirs(os.path.dirname(os.path.abspath(output_json)), exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(annotated_story, f, indent=2)
        print(f"\n[+] Semantic annotations saved to: {output_json}")

    return annotated_story

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Annotate semantic dialogue and roles in comic panels.")
    parser.add_argument("--panels-dir", default="output/Challenges_of_Doom_Spider-Man_001", help="Directory of panels")
    parser.add_argument("--output", default="output/Challenges_of_Doom_Spider-Man_001/story_semantics_annotated.json", help="Output JSON")
    parser.add_argument("--max-panels", type=int, default=15, help="Number of key panels to annotate")
    args = parser.parse_args()

    annotate_panels(args.panels_dir, output_json=args.output, max_panels=args.max_panels)
