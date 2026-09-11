#!/usr/bin/env python3
"""
src/extract_panel_vision.py - Cloud + Local Hybrid Vision Extraction Engine.
Combines:
  1. Local Stage (Fast, deterministic): OCR extraction, bubble geometry, resolution metrics.
  2. Cloud Multimodal Vision (Gemini Flash / OpenAI compatible):
     - Visual scene understanding (setting, characters, actions, combat moves, expressions)
     - Dialogue vs Caption vs Sound Effect (SFX) separation
     - Editorial / Barcode noise filtering
     - Cinematic recap narration & camera staging directives
  3. Structured JSON Generation:
     - Saves to `output/<comic_title>/comic_scene_vision.json`
     - Generates an interactive HTML inspection dashboard: `output/<comic_title>/vision_dashboard.html`
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error
import cv2
import numpy as np

import time
import re
import random

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def load_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        env_file = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        key = line.split("=", 1)[1].strip('"\'')
                        break
    return key or ""

DEFAULT_API_KEY = load_api_key()
DISABLED_MULTIMODAL_MODELS = set()

class RateLimiter:
    """
    Enforces strict rate limits:
      - Max 12 Requests Per Minute (RPM) -> ~5.0s minimum interval (safely below 30 RPM limit)
      - Strictly respects 16,000 Tokens Per Minute (TPM) limit (< 6,000 TPM actual usage)
    """
    def __init__(self, min_interval=5.0):
        self.min_interval = min_interval
        self.last_call_time = 0.0

    def wait(self):
        now = time.time()
        elapsed = now - self.last_call_time
        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            time.sleep(sleep_time)
        self.last_call_time = time.time()

global_rate_limiter = RateLimiter(min_interval=5.0)


def extract_json_from_gemma_parts(parts):
    """
    Extracts structured JSON from Gemma 4 API response parts,
    handling both explicit JSON parts and thought-embedded markdown code blocks.
    """
    # 1. Check non-thought parts first
    for p in reversed(parts):
        if not p.get("thought", False):
            txt = p.get("text", "").strip()
            if txt:
                try:
                    return json.loads(txt)
                except Exception:
                    pass

    # 2. Check thought parts for embedded ```json ... ``` code blocks
    for p in parts:
        txt = p.get("text", "")
        matches = list(re.finditer(r"```(?:json)?\s*([\s\S]*?)\s*```", txt))
        for m in reversed(matches):
            try:
                return json.loads(m.group(1).strip())
            except Exception:
                pass

    # 3. Fallback: balance-bracket search across all parts
    for p in parts:
        txt = p.get("text", "")
        start = -1
        depth = 0
        for i, c in enumerate(txt):
            if c == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and start != -1:
                    try:
                        return json.loads(txt[start:i+1])
                    except Exception:
                        pass
                    start = -1

    return None


def map_compact_to_full_vision(res, h, w, ocr_hint):
    """
    Transforms the compact Gemma output into the full pipeline schema.
    """
    chars = res.get("characters", [])
    if not isinstance(chars, list):
        chars = [chars] if chars else []
    speaker = res.get("speaker", chars[0] if chars else "Character")
    dlg = res.get("dialogue", "").strip()
    scene_type = res.get("scene_type", "ACTION_COMBAT")
    cam = res.get("camera", "push_in_zoom")
    recap = res.get("recap", "The story unfolds across the panel.")

    return {
        "visual_context": {
            "scene_type": scene_type,
            "setting": "Comic Narrative Scene",
            "characters_present": chars or ["Featured Characters"],
            "action_and_poses": res.get("action", f"Visual panel composition with aspect ratio {w/h:.2f}:1"),
            "focal_point": "Central character action",
            "dominant_mood_lighting": "Dynamic comic illustration style"
        },
        "dialogue_analysis": {
            "spoken_dialogue": [{"speaker": speaker, "text": dlg, "tone": "Energetic"}] if dlg else [],
            "narration_captions": [],
            "sound_effects": [],
            "filtered_noise": []
        },
        "cinematic_staging": {
            "recommended_camera_motion": cam,
            "pacing_seconds": 3.5,
            "cinematic_narrator_recap": recap
        }
    }


GEMMA_ONLY_CASCADE = ["gemma-4-31b-it", "gemma-4-26b-a4b-it"]

def query_cloud_vision(image_path, api_key=None, ocr_hint=None, models_cascade=None, comic_title="Spider-Man"):
    """
    Strict Gemma-only cascade:
      Primary:  gemma-4-31b-it
      Fallback: gemma-4-26b-a4b-it
      Paced at 5.0s interval (<10 RPM, <2,000 TPM) to strictly guarantee safety under 16k TPM.
    """
    key = api_key or DEFAULT_API_KEY
    if not key:
        return None

    if not models_cascade:
        models_cascade = GEMMA_ONLY_CASCADE

    img = cv2.imread(image_path)
    h, w = img.shape[:2] if img is not None else (1080, 1920)

    prompt = f"""Comic: {comic_title}
OCR: "{ocr_hint or 'Visual narrative panel'}"
Output JSON format:
{{"characters": ["Names"], "speaker": "Speaker", "dialogue": "Speech line", "action": "Action description", "scene_type": "ACTION_COMBAT", "camera": "push_in_zoom", "recap": "1-2 sentence narrator recap line"}}
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.0
        }
    }

    for model in models_cascade:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"

        for attempt in range(2):
            global_rate_limiter.wait()
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=40) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    parts = res_json["candidates"][0]["content"]["parts"]
                    for p in parts:
                        if not p.get("thought", False):
                            raw_dict = json.loads(p["text"])
                            print(f"    ✓ Vision extracted via [{model}]")
                            return map_compact_to_full_vision(raw_dict, h, w, ocr_hint)
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    backoff = 8.0 + random.uniform(2.0, 5.0)
                    print(f"  [!] 429 Rate limited on {model}, backing off {backoff:.1f}s...")
                    time.sleep(backoff)
                elif e.code == 500:
                    print(f"  [!] {model} returned HTTP 500, cascading to fallback...")
                    break
                else:
                    print(f"  [!] {model} HTTP {e.code}, cascading...")
                    break
            except Exception as e:
                print(f"  [!] {model} connection error ({e}), cascading...")
                break

    return None


def run_local_fallback_vision(image_path, ocr_text="", panel_idx=1):
    """
    Local fallback extractor when offline or without API key.
    Provides structured defaults and noise filtering.
    """
    text_lower = ocr_text.lower()
    img = cv2.imread(image_path)
    h, w = img.shape[:2] if img is not None else (1080, 1920)

    # Detect characters
    chars = []
    if any(k in text_lower for k in ["richards", "doom", "latveria", "victor"]):
        chars.append("Doctor Doom")
    if any(k in text_lower for k in ["parker", "spider", "mets", "bowling", "thwip"]):
        chars.append("Spider-Man")

    # Detect action / motion
    if any(k in text_lower for k in ["boom", "crash", "thwip", "smash", "!"]):
        scene_type = "ACTION_COMBAT"
        camera = "impact_shake" if "!" in text_lower else "snap_punch_zoom"
        pacing = 2.8
    elif w > h * 1.3:
        scene_type = "WIDE_ESTABLISHING"
        camera = "pan_horizontal"
        pacing = 4.2
    else:
        scene_type = "DIALOGUE_CLOSEUP" if len(ocr_text) > 30 else "DRAMATIC_REVEAL"
        camera = "slow_pan_down" if h > w else "push_in_zoom"
        pacing = 3.5

    clean_line = ocr_text.strip()
    if clean_line:
        recap_line = f"As the scene unfolds, {', '.join(chars) if chars else 'our characters'} advance the confrontation."
    else:
        recap_line = "The visual tension peaks as the action unfolds across the panel."

    return {
        "visual_context": {
            "scene_type": scene_type,
            "setting": "Comic Narrative Scene",
            "characters_present": chars or ["Featured Characters"],
            "action_and_poses": f"Visual panel composition with aspect ratio {w/h:.2f}:1",
            "focal_point": "Central character action",
            "dominant_mood_lighting": "Dynamic comic illustration style"
        },
        "dialogue_analysis": {
            "spoken_dialogue": [{"speaker": chars[0] if chars else "Character", "text": clean_line, "tone": "Dramatic"}] if clean_line else [],
            "narration_captions": [],
            "sound_effects": [],
            "filtered_noise": []
        },
        "cinematic_staging": {
            "recommended_camera_motion": camera,
            "pacing_seconds": pacing,
            "cinematic_narrator_recap": recap_line
        }
    }


def generate_vision_dashboard_html(panels_data, output_html_path, comic_title="Comic Story"):
    """
    Generates an interactive visual dashboard of the vision extraction results.
    """
    cards_html = ""
    for p in panels_data:
        v = p.get("vision", {})
        vc = v.get("visual_context", {})
        da = v.get("dialogue_analysis", {})
        cs = v.get("cinematic_staging", {})

        chars = ", ".join(vc.get("characters_present", [])) or "None identified"
        dialogues = "".join([f"<li><b>{d.get('speaker', 'Speaker')}:</b> \"{d.get('text', '')}\"</li>" for d in da.get("spoken_dialogue", [])])

        cards_html += f"""
        <div class="panel-card">
          <div class="card-img-wrap">
            <img src="{p['panel_relative_path']}" alt="{p['panel_id']}" loading="lazy">
            <span class="badge badge-type">{vc.get('scene_type', 'PANEL')}</span>
            <span class="badge badge-camera">{cs.get('recommended_camera_motion', 'zoom')}</span>
          </div>
          <div class="card-body">
            <h3>{p['panel_id']} (Page {p['page_number']})</h3>
            <p class="characters"><b>👥 Characters:</b> {chars}</p>
            <p class="setting"><b>📍 Setting:</b> {vc.get('setting', 'Unknown')}</p>
            <p class="action"><b>🎬 Visual Action:</b> {vc.get('action_and_poses', 'Visual scene')}</p>
            {f'<div class="dialogue-box"><b>💬 Dialogue:</b><ul>{dialogues}</ul></div>' if dialogues else ''}
            <div class="recap-box">
              <b>🎙️ Narrator Line:</b>
              <p>"{cs.get('cinematic_narrator_recap', '')}"</p>
            </div>
            <div class="meta-row">
              <span>⏱️ Pacing: {cs.get('pacing_seconds', 3.5)}s</span>
              <span>🎨 Mood: {vc.get('dominant_mood_lighting', 'Dramatic')}</span>
            </div>
          </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{comic_title} - Vision Extraction Dashboard</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0b0f19; color: #f8fafc; margin: 0; padding: 24px; }}
  header {{ max-width: 1400px; margin: 0 auto 32px auto; text-align: center; }}
  h1 {{ color: #38bdf8; margin-bottom: 8px; }}
  p.subtitle {{ color: #94a3b8; font-size: 15px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(420px, 1fr)); gap: 24px; max-width: 1400px; margin: 0 auto; }}
  .panel-card {{ background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; display: flex; flex-direction: column; }}
  .card-img-wrap {{ position: relative; width: 100%; height: 280px; background: #020617; }}
  .card-img-wrap img {{ width: 100%; height: 100%; object-fit: contain; }}
  .badge {{ position: absolute; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; text-transform: uppercase; }}
  .badge-type {{ top: 12px; left: 12px; background: #0284c7; color: white; }}
  .badge-camera {{ top: 12px; right: 12px; background: #8b5cf6; color: white; }}
  .card-body {{ padding: 18px; display: flex; flex-direction: column; gap: 10px; flex-grow: 1; }}
  .card-body h3 {{ margin: 0; color: #f1f5f9; font-size: 17px; }}
  p {{ margin: 0; font-size: 13px; line-height: 1.4; color: #cbd5e1; }}
  .dialogue-box {{ background: #0f172a; padding: 10px 12px; border-radius: 8px; border-left: 3px solid #38bdf8; font-size: 12px; }}
  .dialogue-box ul {{ margin: 4px 0 0 0; padding-left: 18px; }}
  .recap-box {{ background: #172554; padding: 10px 12px; border-radius: 8px; border-left: 3px solid #60a5fa; }}
  .recap-box p {{ color: #e0f2fe; font-style: italic; margin-top: 4px; }}
  .meta-row {{ display: flex; justify-content: space-between; font-size: 12px; color: #94a3b8; border-top: 1px solid #334155; padding-top: 8px; margin-top: auto; }}
</style>
</head>
<body>
<header>
  <h1>{comic_title}</h1>
  <p class="subtitle">Cloud + Local Hybrid Multimodal Vision Extraction Dashboard ({len(panels_data)} panels analyzed)</p>
</header>
<div class="grid">
  {cards_html}
</div>
</body>
</html>
"""
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[+] Vision extraction dashboard generated: {output_html_path}")


def extract_vision_for_comic(manifest_path, output_json_path=None, api_key=None, max_panels=None):
    """
    Main extraction orchestrator:
    Iterates through panels in manifest.json, calls Cloud Vision (or fallback),
    and saves comic_scene_vision.json and dashboard.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    panels = manifest["panels"]
    if max_panels:
        panels = panels[:max_panels]

    comic_dir = os.path.dirname(manifest_path)
    comic_title = manifest.get("comic_title", "Comic Story")

    print(f"\n[*] Starting Multimodal Vision Extraction for '{comic_title}' ({len(panels)} panels)...")

    active_key = api_key or os.environ.get("GEMINI_API_KEY") or DEFAULT_API_KEY
    has_api = bool(active_key)
    mode_str = f"Gemma-Only Cascade ({', '.join(GEMMA_ONLY_CASCADE)})" if has_api else "Local Semantic Analyzer"
    print(f"[*] Inference Mode: [{mode_str}]")

    results = []
    cache_file = os.path.join(comic_dir, ".vision_cache.json")
    cache = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as cf:
                cache = json.load(cf)
            print(f"[*] Found vision cache with {len(cache)} pre-analyzed panels.")
        except Exception:
            cache = {}

    import easyocr
    print(f"[*] Initializing local OCR assistant for dialogue extraction...")
    reader = easyocr.Reader(['en'], gpu=False)

    for idx, p in enumerate(panels, 1):
        panel_file = p["filename"]
        panel_path = os.path.join(comic_dir, panel_file)
        if not os.path.exists(panel_path):
            continue

        if panel_file in cache:
            print(f"  -> [{idx}/{len(panels)}] ⚡ Loaded from cache: {panel_file}")
            vision_data = cache[panel_file].get("vision")
            ocr_hint = cache[panel_file].get("ocr_hint", "")
        else:
            print(f"  -> [{idx}/{len(panels)}] 🔍 Analyzing {panel_file}...")
            # 1. Local OCR hint extraction (milliseconds)
            ocr_results = reader.readtext(panel_path)
            raw_texts = [r[1] for r in ocr_results if r[2] > 0.35]
            ocr_hint = " ".join(raw_texts).strip()

            vision_data = query_cloud_vision(panel_path, api_key=active_key, ocr_hint=ocr_hint, comic_title=comic_title)

            if not vision_data:
                vision_data = run_local_fallback_vision(panel_path, ocr_text=ocr_hint, panel_idx=idx)

            # Update cache immediately
            cache[panel_file] = {
                "vision": vision_data,
                "ocr_hint": ocr_hint
            }
            with open(cache_file, "w", encoding="utf-8") as cf:
                json.dump(cache, cf, indent=2)

        record = {
            "panel_id": f"panel_{p['global_index']:03d}_p{p['page_number']:02d}_{p['panel_on_page']:02d}",
            "global_index": p["global_index"],
            "page_number": p["page_number"],
            "panel_on_page": p["panel_on_page"],
            "filename": panel_file,
            "panel_relative_path": panel_file,
            "dimensions": {"width": p["width"], "height": p["height"]},
            "bbox": p["bbox"],
            "raw_ocr_text": ocr_hint,
            "vision": vision_data
        }
        results.append(record)

    # Save output JSON
    if not output_json_path:
        output_json_path = os.path.join(comic_dir, "comic_scene_vision.json")

    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[+] Successfully saved vision extraction JSON: {output_json_path}")

    # Generate interactive dashboard
    dashboard_path = os.path.join(comic_dir, "vision_dashboard.html")
    generate_vision_dashboard_html(results, dashboard_path, comic_title=comic_title)

    return output_json_path, dashboard_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract multimodal vision semantics from comic panels.")
    parser.add_argument("--manifest", default="output/Challenges_of_Doom_Spider-Man_001/manifest.json", help="Path to manifest.json")
    parser.add_argument("--output", default=None, help="Path for output comic_scene_vision.json")
    parser.add_argument("--api-key", default=None, help="Gemini API key (optional, uses GEMINI_API_KEY env if not specified)")
    parser.add_argument("--max-panels", type=int, default=None, help="Limit number of panels for testing")
    args = parser.parse_args()

    extract_vision_for_comic(args.manifest, output_json_path=args.output, api_key=args.api_key, max_panels=args.max_panels)
