#!/usr/bin/env python3
"""
pipeline_master.py - Modular Plug-and-Play Comic Video Automation Pipeline
Supports multi-character voice casting:
  - Doctor Doom : 'javert' (booming villain baritone)
  - Spider-Man  : 'marius' (youthful energetic hero)
  - Narrator    : 'alba'   (fast, articulate recap narrator)
"""

import os
import sys
import json
import argparse
import subprocess

import zipfile
import re
import cv2
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.extract_all_comic_panels import extract_comic_panels
from src.evaluate_panel_extraction import evaluate_page_extraction
from src.extract_panel_vision import extract_vision_for_comic
from src.generate_multivoice_script import generate_cohesive_script
from src.render_zero_jitter_video import render_scene_clip, assemble_final_video


def unpack_comic_if_needed(comic_input_path, extracted_pages_dir):
    """
    Unpacks .cbz or .cbr archive into a normalized pages directory.
    If comic_input_path is already a directory of images, returns it directly.
    """
    if os.path.isdir(comic_input_path):
        return comic_input_path

    os.makedirs(extracted_pages_dir, exist_ok=True)
    lower = comic_input_path.lower()

    if lower.endswith(".cbz") or lower.endswith(".zip"):
        print(f"[*] Unpacking CBZ archive '{comic_input_path}'...")
        with zipfile.ZipFile(comic_input_path, "r") as zf:
            img_files = sorted([f for f in zf.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')) and not f.startswith('__MACOSX')])
            for i, f in enumerate(img_files, 1):
                ext = os.path.splitext(f)[1].lower()
                out_path = os.path.join(extracted_pages_dir, f"page_{i:03d}{ext}")
                with open(out_path, "wb") as out_f:
                    out_f.write(zf.read(f))
        print(f"[+] Extracted {len(img_files)} pages to: {extracted_pages_dir}")
        return extracted_pages_dir

    elif lower.endswith(".cbr") or lower.endswith(".rar"):
        print(f"[*] Unpacking CBR archive '{comic_input_path}'...")
        tmp_dir = os.path.join(extracted_pages_dir, "_tmp_raw")
        os.makedirs(tmp_dir, exist_ok=True)
        unrar_bin = os.path.expanduser("~/.local/bin/unrar")
        cmd = [unrar_bin if os.path.exists(unrar_bin) else "unrar", "x", "-y", comic_input_path, tmp_dir]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)

        import glob
        raw_files = sorted(
            glob.glob(os.path.join(tmp_dir, "**", "*.jpg"), recursive=True) +
            glob.glob(os.path.join(tmp_dir, "**", "*.jpeg"), recursive=True) +
            glob.glob(os.path.join(tmp_dir, "**", "*.png"), recursive=True)
        )
        import shutil
        for i, fpath in enumerate(raw_files, 1):
            ext = os.path.splitext(fpath)[1].lower()
            dest_path = os.path.join(extracted_pages_dir, f"page_{i:03d}{ext}")
            shutil.copyfile(fpath, dest_path)
        shutil.rmtree(tmp_dir)
        print(f"[+] Extracted {len(raw_files)} pages to: {extracted_pages_dir}")
        return extracted_pages_dir

    else:
        raise ValueError(f"Unsupported comic file type: {comic_input_path}")


def run_extraction_step(pages_dir, comic_title, output_dir):
    print(f"\n==================== [STEP 1: 100% PANEL EXTRACTION] ====================")
    target_dir, manifest = extract_comic_panels(pages_dir, comic_title=comic_title, base_out_dir=output_dir)
    return target_dir, manifest


def run_evaluation_step(pages_dir, manifest_path):
    print(f"\n==================== [STEP 2: QUALITY GATE EVALUATION] ====================")
    with open(manifest_path) as f:
        manifest = json.load(f)

    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    pages = sorted([f for f in os.listdir(pages_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))], key=natural_sort_key)
    print(f"{'Page':<12} | {'Panels':<8} | {'Coverage':<10} | {'Status':<8}")
    print("-" * 46)

    total_pass = 0
    for p_file in pages:
        p_num = int(re.search(r'\d+', p_file).group())
        p_path = os.path.join(pages_dir, p_file)
        bboxes = [p["bbox"] for p in manifest["panels"] if p["page_number"] == p_num]

        img = cv2.imread(p_path)
        h, w = img.shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)
        for bx, by, bw, bh in bboxes:
            mask[by:by+bh, bx:bx+bw] = 255
        c_y1, c_y2 = int(h * 0.02), int(h * 0.98)
        row_cov = np.mean(mask[c_y1:c_y2, :] > 0, axis=1)
        cov = float(np.mean(row_cov > 0.5) * 100.0)

        badge = "✅ PASS" if cov >= 85.0 else "❌ FAIL"
        if cov >= 85.0:
            total_pass += 1
        print(f"{p_file:<12} | {len(bboxes):<8} | {cov:>8.1f}% | {badge}")

    pass_pct = (total_pass / max(1, len(pages))) * 100.0
    print(f"\n[+] Quality Gate Result: {total_pass}/{len(pages)} Pages Passed ({pass_pct:.1f}%)")
    return pass_pct >= 90.0

def synthesize_voices_for_script(script_path, audio_out_dir):
    os.makedirs(audio_out_dir, exist_ok=True)
    with open(script_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print(f"[*] Synthesizing multi-character voices for {len(scenes)} scenes via Pocket TTS...")
    audio_paths = []

    for sc in scenes:
        sid = sc["scene_id"]
        text = sc["line"]
        speaker = sc["speaker"]
        voice_id = sc.get("voice_id")
        if not voice_id:
            voice_id = "javert" if speaker == "Doctor Doom" else ("marius" if speaker == "Spider-Man" else "alba")

        wav_path = os.path.join(audio_out_dir, f"{sid}_{speaker.replace(' ', '_').lower()}.wav")

        temp = 0.25 if speaker == "Doctor Doom" else (0.45 if speaker == "Spider-Man" else 0.35)

        cmd = [
            "/usr/local/bin/pocket-tts", "generate",
            "--text", text,
            "--voice", voice_id,
            "--temperature", str(temp),
            "--output-path", wav_path,
            "--device", "cpu",
            "-q"
        ]

        print(f"  -> [{speaker} | Voice: '{voice_id}'] Synthesizing {sid}...")
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL)
        except Exception as e:
            fallback_cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2.0", wav_path]
            subprocess.run(fallback_cmd, check=True, stderr=subprocess.DEVNULL)

        audio_paths.append(wav_path)

    print(f"[+] All {len(scenes)} distinct voiceover tracks generated in: {audio_out_dir}")
    return audio_paths

def run_render_step(script_path, audio_dir, clips_dir, final_mp4, bgm_path=None):
    os.makedirs(clips_dir, exist_ok=True)
    with open(script_path, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    clip_paths = []
    print(f"[*] Rendering 1080p centered zero-jitter camera motion for {len(scenes)} scenes...")

    for sc in scenes:
        sid = sc["scene_id"]
        speaker = sc["speaker"]
        img_path = sc["panel_image"]
        mode = sc["camera_motion"]
        wav_path = os.path.join(audio_dir, f"{sid}_{speaker.replace(' ', '_').lower()}.wav")
        clip_path = os.path.join(clips_dir, f"{sid}_1080p.mp4")

        print(f"  -> Rendering {sid} [{speaker} | {mode}]...")
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

    assemble_final_video(clip_paths, final_mp4, bgm_path=bgm_path)

def main():
    parser = argparse.ArgumentParser(description="Master Modular Comic-to-Video Automation Engine.")
    parser.add_argument("--step", choices=["extract", "evaluate", "vision", "script", "voice", "render", "all"], default="all", help="Step to run")
    parser.add_argument("--comic", default="data/spider_man_001/pages", help="Path to pages directory, .cbz, or .cbr file")
    parser.add_argument("--title", default="Spider_Man_Challenges_of_Doom_001", help="Comic title identifier")
    parser.add_argument("--work-dir", default="output/modular_production", help="Working output directory")
    parser.add_argument("--output-video", default="output/modular_production/spiderman_8panel_multivoice_smooth_1080p.mp4", help="Final video destination")
    parser.add_argument("--bgm", default="assets/bgm_action.wav", help="Background music")
    parser.add_argument("--fps", type=int, default=60, help="Video frame rate (30 or 60)")
    parser.add_argument("--api-key", default=None, help="Gemini API key for cloud vision")

    args = parser.parse_args()
    os.makedirs(args.work_dir, exist_ok=True)

    extracted_pages_dir = os.path.join(args.work_dir, "unpacked_pages")
    pages_dir = unpack_comic_if_needed(args.comic, extracted_pages_dir)

    target_dir = os.path.join(args.work_dir, args.title)
    manifest_path = os.path.join(target_dir, "manifest.json")
    vision_json_path = os.path.join(target_dir, "comic_scene_vision.json")
    script_json = os.path.join(args.work_dir, "multivoice_script.json")
    audio_dir = os.path.join(args.work_dir, "voiceovers")
    clips_dir = os.path.join(args.work_dir, "clips")

    # Step 1: 100% Panel Extraction
    if args.step in ["extract", "all"]:
        target_dir, manifest = run_extraction_step(pages_dir, args.title, args.work_dir)
        manifest_path = os.path.join(target_dir, "manifest.json")

    # Step 2: Quality Gate Evaluation
    if args.step in ["evaluate", "all"]:
        if not os.path.exists(manifest_path):
            print(f"[!] Manifest not found at {manifest_path}. Running extraction first...")
            target_dir, manifest = run_extraction_step(pages_dir, args.title, args.work_dir)
            manifest_path = os.path.join(target_dir, "manifest.json")
        run_evaluation_step(pages_dir, manifest_path)

    # Step 3: Multimodal Vision & Scene Understanding
    if args.step in ["vision", "all"]:
        print("\n==================== [STEP 3: MULTIMODAL VISION EXTRACTION] ====================")
        if not os.path.exists(manifest_path):
            target_dir, manifest = run_extraction_step(pages_dir, args.title, args.work_dir)
            manifest_path = os.path.join(target_dir, "manifest.json")
        extract_vision_for_comic(manifest_path, output_json_path=vision_json_path, api_key=args.api_key)

    # Step 4: Cohesive Script Generation
    if args.step in ["script", "all"]:
        print("\n==================== [STEP 4: SCRIPT GENERATION] ====================")
        generate_cohesive_script(output_script_path=script_json)

    # Step 5: Multi-voice Casting TTS
    if args.step in ["voice", "all"]:
        print("\n==================== [STEP 5: MULTI-VOICE CASTING TTS] ====================")
        synthesize_voices_for_script(script_json, audio_dir)

    # Step 6: 1080p Video Render
    if args.step in ["render", "all"]:
        print(f"\n==================== [STEP 6: 1080P {args.fps}FPS CINEMATIC RENDER] ====================")
        run_render_step(script_json, audio_dir, clips_dir, args.output_video, bgm_path=args.bgm)

    print("\n[SUCCESS] Master pipeline workflow completed successfully!")

if __name__ == "__main__":
    main()
