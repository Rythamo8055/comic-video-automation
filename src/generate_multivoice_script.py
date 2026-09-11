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
import urllib.request
import urllib.error
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def load_groq_api_key():
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        env_file = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(env_file):
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GROQ_API_KEY="):
                        key = line.split("=", 1)[1].strip('"\'')
                        break
    return key or ""

GROQ_MODELS_CASCADE = ["qwen/qwen3.8-27b", "qwen/qwen3.6-27b"]

def generate_act_with_groq(compact_panels, act_name, context_bridge="", api_key=None, style="hybrid"):
    """
    Calls Groq Cloud Qwen model fleet with stateful narrative sliding bridge.
    Supports:
      - 'hybrid': Distinct character voice acting + Narrator bridge
      - 'storyteller': Single master charismatic YouTuber narrator (ComicsExplained style) quoting characters in-stride
    """
    key = api_key or load_groq_api_key()
    if not key:
        return None

    if style == "storyteller":
        system_prompt = (
            "You are Rob from ComicsExplained and Benny from Comicstorian.\n"
            "You are producing a high-retention, cinematic YouTube storytelling breakdown video.\n"
            "Deliver a continuous, high-energy, suspenseful recap spoken entirely by the MASTER STORYTELLER (Narrator).\n"
            "Rules:\n"
            "1. The speaker must ALWAYS be 'Narrator' (voice_id: 'alba').\n"
            "2. Dramatically quote characters with vivid personality inside your narration (e.g. 'And Doom looks down with cold fury, declaring: \"None shall defy me!\"').\n"
            "3. Explain the comic lore, build tension, and describe the action beats dynamically.\n"
            "4. Every panel must have a corresponding narrative beat maintaining 3.5s to 5.0s pacing.\n"
            "5. Output valid JSON: {\"scenes\": [{\"panel_id\": \"...\", \"speaker\": \"Narrator\", \"line\": \"...\", \"camera_motion\": \"push_in_zoom | snap_punch_zoom | slow_pan_down | impact_shake\", \"pacing_seconds\": 4.0}]}"
        )
    else:
        system_prompt = (
            "You are a master comic video recap showrunner in the style of ComicsExplained and Comicstorian.\n"
            "Transform the sequential comic panels into snappy, high-retention broadcast scenes with distinct character voices "
            "(e.g., Doctor Doom, Spider-Man, Aunt May, Narrator) and dynamic camera motions.\n"
            "Rules:\n"
            "1. Every panel must have at least one scene maintaining 1:1 or 1:2 pacing.\n"
            "2. Doctor Doom speaks with grand, Shakespearean ego and dark intellect.\n"
            "3. Spider-Man speaks with sarcastic, quick-witted Brooklyn comedic timing.\n"
            "4. The Narrator bridges visual action and maintains high suspense.\n"
            "5. Output valid JSON: {\"scenes\": [{\"panel_id\": \"...\", \"speaker\": \"Doctor Doom | Spider-Man | Narrator\", \"line\": \"...\", \"camera_motion\": \"push_in_zoom | snap_punch_zoom | slow_pan_down | impact_shake\", \"pacing_seconds\": 3.5}]}"
        )

    user_prompt = f"Act: {act_name}\n"
    if context_bridge:
        user_prompt += f"Story Continuity Bridge (What just happened in the preceding act):\n{context_bridge}\n\n"
    user_prompt += f"Panels to script:\n{json.dumps(compact_panels, indent=1)}\n\nGenerate script for this act in JSON:"

    url = "https://api.groq.com/openai/v1/chat/completions"

    for model in GROQ_MODELS_CASCADE:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 1000,
            "temperature": 0.35
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            }
        )

        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=40) as resp:
                    res_json = json.loads(resp.read().decode("utf-8"))
                    content_str = res_json["choices"][0]["message"]["content"]
                    parsed = json.loads(content_str)
                    scenes = parsed.get("scenes", [])
                    
                    # Check token reset headers to dynamically pace subsequent acts
                    rem_tokens = resp.headers.get("x-ratelimit-remaining-tokens")
                    reset_tokens = resp.headers.get("x-ratelimit-reset-tokens")
                    if rem_tokens and int(rem_tokens) < 2500 and reset_tokens:
                        wait_s = float(reset_tokens.rstrip("s")) + 1.0
                        print(f"    [i] Groq remaining token reservoir low ({rem_tokens}). Pacing {wait_s:.1f}s for reset...")
                        time.sleep(wait_s)
                    else:
                        time.sleep(2.0)

                    if scenes:
                        print(f"    ✓ Act [{act_name}] generated via Groq [{model}] ({len(scenes)} scenes)")
                        return scenes
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    retry_header = e.headers.get("retry-after") or e.headers.get("x-ratelimit-reset-tokens")
                    wait_s = float(retry_header.rstrip("s")) + 1.5 if retry_header else 15.0
                    print(f"  [!] Groq 429 on {model}. Rate limiter draining bucket, waiting {wait_s:.1f}s...")
                    time.sleep(wait_s)
                else:
                    print(f"  [!] Groq {model} HTTP {e.code}, cascading...")
                    break
            except Exception as e:
                print(f"  [!] Groq {model} connection error ({e}), cascading...")
                break

    return None


def generate_cohesive_script(
    vision_json_path=None,
    output_script_path="output/modular_production/multivoice_script.json",
    style="hybrid",
    max_panels=None,
    custom_voice_map=None,
    use_groq=True
):
    """
    Generates a multi-voice production script from vision extraction data.
    Uses Groq Qwen 3-Act sliding continuity when available, falling back to local hybrid.
    """
    scenes = []

    if vision_json_path and os.path.exists(vision_json_path):
        print(f"[*] Ingesting multimodal vision context from: {vision_json_path}")
        with open(vision_json_path, "r", encoding="utf-8") as f:
            panels_vision = json.load(f)

        if max_panels:
            panels_vision = panels_vision[:max_panels]

        comic_dir = os.path.dirname(os.path.abspath(vision_json_path))
        panel_map = {p["panel_id"]: p for p in panels_vision}

        groq_key = load_groq_api_key()
        groq_success = False

        if use_groq and groq_key:
            print(f"[*] Orchestrating 3-Act Sliding Sequence Scripting via Groq Cloud ({', '.join(GROQ_MODELS_CASCADE)})...")
            # Divide into 3 narrative acts
            n = len(panels_vision)
            chunk_size = max(1, (n + 2) // 3)
            acts = [
                ("Act 1: The Inciting Scheme", panels_vision[0:chunk_size]),
                ("Act 2: The Latverian Confrontation", panels_vision[chunk_size:chunk_size*2]),
                ("Act 3: The Climax & Web-Slinging Resolution", panels_vision[chunk_size*2:])
            ]

            groq_scenes = []
            context_bridge = ""

            for act_name, act_panels in acts:
                if not act_panels:
                    continue
                compact_panels = []
                for p in act_panels:
                    v = p.get("vision", {})
                    vc = v.get("visual_context", {})
                    da = v.get("dialogue_analysis", {})
                    cs = v.get("cinematic_staging", {})
                    compact_panels.append({
                        "panel_id": p["panel_id"],
                        "characters": vc.get("characters_present", []),
                        "action": vc.get("action_and_poses", ""),
                        "dialogue": [d.get("text") for d in da.get("spoken_dialogue", [])],
                        "recap": cs.get("cinematic_narrator_recap", ""),
                        "camera": cs.get("recommended_camera_motion", "push_in_zoom")
                    })

                act_result = generate_act_with_groq(compact_panels, act_name, context_bridge=context_bridge, api_key=groq_key, style=style)
                if act_result:
                    groq_scenes.extend(act_result)
                    # Create continuity bridge from the last 2 lines for next act
                    last_lines = [f"{s.get('speaker', 'Character')}: {s.get('line', '')}" for s in act_result[-2:]]
                    context_bridge = " -> ".join(last_lines)
                    # Pause 3.0s between acts to allow Groq token bucket to reset
                    time.sleep(3.0)
                else:
                    print(f"  [!] Groq failed for {act_name}, falling back to local extractor...")
                    groq_scenes = None
                    break

            if groq_scenes:
                groq_success = True
                scene_counter = 1
                for s in groq_scenes:
                    p_id = s.get("panel_id")
                    p_meta = panel_map.get(p_id, {})
                    p_img = p_meta.get("filename", "")
                    if p_img and not os.path.isabs(p_img):
                        p_img = os.path.join(comic_dir, p_img)

                    speaker = s.get("speaker", "Narrator")
                    voice = resolve_voice_for_speaker(speaker, custom_voice_map)

                    scenes.append({
                        "scene_id": f"scene_{scene_counter:03d}",
                        "panel_id": p_id,
                        "panel_index": p_meta.get("global_index", scene_counter),
                        "panel_image": p_img,
                        "speaker": speaker,
                        "voice_id": voice,
                        "line": clean_script_line(s.get("line", "")),
                        "camera_motion": s.get("camera_motion", "push_in_zoom"),
                        "pacing_seconds": s.get("pacing_seconds", 3.5),
                        "scene_type": p_meta.get("vision", {}).get("visual_context", {}).get("scene_type", "PANEL")
                    })
                    scene_counter += 1

        if not groq_success:
            print(f"[*] Generating multi-voice script using local structured rules...")
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

    os.makedirs(os.path.dirname(os.path.abspath(output_script_path)), exist_ok=True)
    with open(output_script_path, "w", encoding="utf-8") as f:
        json.dump(scenes, f, indent=2)

    print(f"\n[+] Cohesive multi-voice narrative script ({len(scenes)} scenes) generated: {output_script_path}")
    return scenes


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dynamic multi-voice comic script.")
    parser.add_argument("--vision-json", default="output/Challenges_of_Doom_Spider-Man_001/comic_scene_vision.json", help="Path to vision extraction JSON")
    parser.add_argument("--output", default="output/Challenges_of_Doom_Spider-Man_001/multivoice_script.json", help="Output multivoice_script.json path")
    parser.add_argument("--style", choices=["hybrid", "storyteller", "recap_only", "dialogue_only"], default="hybrid", help="Script generation style")
    parser.add_argument("--max-panels", type=int, default=None, help="Limit number of panels")
    parser.add_argument("--no-groq", action="store_true", help="Disable Groq and use local rules")
    args = parser.parse_args()

    generate_cohesive_script(
        vision_json_path=args.vision_json,
        output_script_path=args.output,
        style=args.style,
        max_panels=args.max_panels,
        use_groq=not args.no_groq
    )
