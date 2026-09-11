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

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def encode_image_base64(image_path, max_dim=1024):
    """
    Downsamples image for fast, bandwidth-efficient cloud multimodal inference.
    """
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    h, w = img.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / float(max(h, w))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    success, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not success:
        raise RuntimeError("Failed to encode image to JPEG")
    return base64.b64encode(buffer).decode("utf-8")


VISION_EXTRACTION_PROMPT = """You are an expert Comic Book Analyst and YouTube Video Producer (in the style of ComicsExplained and Variant Comics).
Analyze this comic book panel image thoroughly and extract structured visual and narrative data.

Return ONLY a valid JSON object matching this schema:
{
  "visual_context": {
    "scene_type": "ACTION_COMBAT | DRAMATIC_REVEAL | DIALOGUE_CLOSEUP | WIDE_ESTABLISHING | COMEDIC_BEAT",
    "setting": "Specific environment/location name and description",
    "characters_present": ["List of character names visible in the panel"],
    "action_and_poses": "Detailed description of what characters are physically doing, their body language and expressions",
    "focal_point": "The primary visual element the viewer's eyes are drawn to",
    "dominant_mood_lighting": "Atmosphere, color palette, lighting style"
  },
  "dialogue_analysis": {
    "spoken_dialogue": [
      {
        "speaker": "Name of character speaking",
        "text": "Exact clean dialogue spoken in the speech balloon (no OCR typos)",
        "tone": "Whispering / Shouting / Sarcastic / Threatening / Confident"
      }
    ],
    "narration_captions": ["List of any narrative/journal/captions on the panel"],
    "sound_effects": ["List of sound effects/onomatopoeia e.g. THWIP, KRAK, BOOM"],
    "filtered_noise": ["List of publishing credits, page numbers, barcodes, or rating logos ignored"]
  },
  "cinematic_staging": {
    "recommended_camera_motion": "slow_pan_down | push_in_zoom | pull_out_zoom | snap_punch_zoom | impact_shake | pan_horizontal",
    "pacing_seconds": 3.5,
    "cinematic_narrator_recap": "A compelling, high-retention 1-2 sentence YouTube narrator script describing the visual action and story momentum of this panel"
  }
}
"""


def query_cloud_vision(image_path, api_key=None, ocr_hint=None):
    """
    Calls Gemini Multimodal API with image and structured JSON schema.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        return None

    b64_data = encode_image_base64(image_path)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={key}"

    prompt_text = VISION_EXTRACTION_PROMPT
    if ocr_hint:
        prompt_text += f"\nLocal OCR detected text hints: \"{ocr_hint}\""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": b64_data
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.2
        }
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(raw_text)
    except Exception as e:
        print(f"[!] Cloud Vision API call failed: {e}")
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

    results = []
    has_api = bool(api_key or os.environ.get("GEMINI_API_KEY"))
    mode_str = "Cloud Multimodal API (Gemini Flash)" if has_api else "Local Semantic Analyzer"
    print(f"[*] Inference Mode: [{mode_str}]")

    import easyocr
    print(f"[*] Initializing local OCR assistant for dialogue extraction...")
    reader = easyocr.Reader(['en'], gpu=False)

    for idx, p in enumerate(panels, 1):
        panel_file = p["filename"]
        panel_path = os.path.join(comic_dir, panel_file)
        if not os.path.exists(panel_path):
            continue

        print(f"  -> [{idx}/{len(panels)}] Analyzing {panel_file}...")

        # 1. Local OCR hint extraction (milliseconds)
        ocr_results = reader.readtext(panel_path)
        raw_texts = [r[1] for r in ocr_results if r[2] > 0.35]
        ocr_hint = " ".join(raw_texts).strip()

        vision_data = None
        if has_api:
            vision_data = query_cloud_vision(panel_path, api_key=api_key, ocr_hint=ocr_hint)

        if not vision_data:
            vision_data = run_local_fallback_vision(panel_path, ocr_text=ocr_hint, panel_idx=idx)

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
