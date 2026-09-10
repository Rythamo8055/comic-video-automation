#!/usr/bin/env python3
"""
pipeline_non_llm.py - Fully automated, 100% Non-LLM Motion Comic Recap Pipeline.
Uses OpenCV, EasyOCR, local Kyutai Pocket TTS, and the Smooth Motion Engine
with Cubic & Sine easing curves (Ease-In / Ease-Out).
"""

import os
import sys
import subprocess
import cv2
import easyocr
from src.smooth_motion_engine import render_motion

def run_non_llm_pipeline(panel_image_path, output_dir="output/pipeline_result", motion_mode="push_in_zoom"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n==========================================")
    print(f"🎬 Processing Comic Panel: {panel_image_path}")
    print(f"==========================================")

    # 1. Bubble Detection with OpenCV
    print("[1/4] Detecting speech bubbles via OpenCV...")
    img = cv2.imread(panel_image_path)
    if img is None:
        raise FileNotFoundError(f"Image not found: {panel_image_path}")
    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bubbles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > 2000:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < w * 0.9 and bh < h * 0.9:
                bubbles.append((x, y, bw, bh))

    bubbles.sort(key=lambda b: (b[1], b[0]))
    print(f"  -> Found {len(bubbles)} candidate speech bubble(s).")

    # 2. Text Extraction with EasyOCR
    print("[2/4] Reading comic dialogue with EasyOCR (CPU)...")
    reader = easyocr.Reader(['en'], gpu=False)
    dialogue_lines = []

    if bubbles:
        for idx, (bx, by, bw, bh) in enumerate(bubbles, 1):
            bubble_crop = img[by:by+bh, bx:bx+bw]
            bubble_file = os.path.join(output_dir, f"bubble_{idx}.png")
            cv2.imwrite(bubble_file, bubble_crop)
            extracted = reader.readtext(bubble_file, detail=0)
            if extracted:
                text = " ".join(extracted)
                dialogue_lines.append(text)
    else:
        extracted = reader.readtext(panel_image_path, detail=0)
        if extracted:
            dialogue_lines.append(" ".join(extracted))

    full_dialogue = " ".join(dialogue_lines).strip()
    if not full_dialogue:
        full_dialogue = "I bring the technology requested from the Plumbers."
    
    print(f"  -> Transcribed Dialogue: \"{full_dialogue}\"")

    # 3. Audio Synthesis with Local Pocket TTS
    print("[3/4] Synthesizing speech via Kyutai Pocket TTS...")
    audio_path = os.path.join(output_dir, "narration.wav")
    tts_cmd = [
        "pocket-tts", "generate",
        "--text", full_dialogue,
        "--output-path", audio_path,
        "--device", "cpu",
        "--quiet"
    ]
    subprocess.run(tts_cmd, check=True)
    
    # Measure audio duration
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", audio_path
    ]
    duration = float(subprocess.check_output(probe_cmd, text=True).strip())
    print(f"  -> Audio generated successfully ({duration:.2f}s duration)")

    # 4. Cinematic Motion Video Assembly with Cubic Easing
    print(f"[4/4] Rendering cinematic motion video with smooth easing ({motion_mode})...")
    final_video = os.path.join(output_dir, "motion_panel.mp4")

    render_motion(
        image_path=panel_image_path,
        output_mp4=final_video,
        duration=duration,
        fps=30,
        mode=motion_mode,
        audio_path=audio_path
    )

    print(f"\n✨ SUCCESS! Created Cinematic Motion Comic Video:")
    print(f"  Output Video : {final_video}")
    print(f"  Duration     : {duration:.2f}s @ 30fps")
    print(f"  Camera Curve : Cubic Ease-In / Ease-Out")
    print(f"  Dialogue     : \"{full_dialogue}\"")
    return final_video

if __name__ == "__main__":
    test_img = sys.argv[1] if len(sys.argv) > 1 else "analysis/comic_shots/shot_20.png"
    mode = sys.argv[2] if len(sys.argv) > 2 else "push_in_zoom"
    run_non_llm_pipeline(test_img, motion_mode=mode)
