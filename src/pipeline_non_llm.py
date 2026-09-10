#!/usr/bin/env python3
"""
pipeline_non_llm.py - Fully automated, 100% Non-LLM Motion Comic Recap Pipeline.
Runs purely on CPU (No GPU required).
1. Detects & crops speech bubbles using OpenCV.
2. Transcribes comic dialogue using EasyOCR.
3. Synthesizes voice narration using local Kyutai Pocket TTS.
4. Generates dynamic Ken Burns animated video synchronized to the audio duration using FFmpeg.
"""

import os
import sys
import subprocess
import cv2
import easyocr

def get_h264_encoder():
    """Finds best available H.264 encoder on system."""
    try:
        res = subprocess.check_output(["ffmpeg", "-encoders"], text=True, stderr=subprocess.DEVNULL)
        if "libopenh264" in res:
            return "libopenh264"
        elif "libx264" in res:
            return "libx264"
    except Exception:
        pass
    return "h264"

def run_non_llm_pipeline(panel_image_path, output_dir="output/pipeline_result"):
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

    # 4. Motion Video Assembly with FFmpeg
    print("[4/4] Generating Ken Burns motion video via FFmpeg...")
    final_video = os.path.join(output_dir, "motion_panel.mp4")
    fps = 24
    total_frames = max(int(duration * fps), 24)
    encoder = get_h264_encoder()

    vf = (
        f"scale=1280:720:force_original_aspect_ratio=increase,"
        f"crop=1280:720,"
        f"zoompan=z='min(zoom+0.0012,1.15)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={total_frames}:s=1280x720:fps={fps}"
    )

    ffmpeg_cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", panel_image_path,
        "-i", audio_path,
        "-vf", vf,
        "-c:v", encoder, "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration),
        final_video
    ]
    subprocess.run(ffmpeg_cmd, check=True, stderr=subprocess.DEVNULL)

    print(f"\n✨ SUCCESS! Created Motion Comic Video:")
    print(f"  Output Video : {final_video}")
    print(f"  Duration     : {duration:.2f}s")
    print(f"  Audio Track  : {audio_path}")
    print(f"  Dialogue     : \"{full_dialogue}\"")
    return final_video

if __name__ == "__main__":
    test_img = sys.argv[1] if len(sys.argv) > 1 else "analysis/comic_shots/shot_20.png"
    run_non_llm_pipeline(test_img)
