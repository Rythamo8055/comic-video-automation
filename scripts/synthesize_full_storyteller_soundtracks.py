import os
import json
import time
import torch
import numpy as np
import soundfile as sf
from pocket_tts import TTSModel

SCRIPT_PATH = "output/Challenges_of_Doom_Spider-Man_001/full_storyteller_script.json"
BASE_OUT = "output/Challenges_of_Doom_Spider-Man_001"

TARGET_VOICES = [
    {
        "id": "stuart_bell",
        "name": "Stuart Bell (Main Storyteller)",
        "role": "High-Urgency Action Narrator",
        "temp": 0.55
    },
    {
        "id": "alba",
        "name": "Alba (Classic Storyteller)",
        "role": "Clear, Warm Documentary Narrator",
        "temp": 0.35
    },
    {
        "id": "charles",
        "name": "Charles (Intellectual Storyteller)",
        "role": "Calculated, Strategic Storyteller",
        "temp": 0.45
    }
]

def main():
    with open(SCRIPT_PATH, "r", encoding="utf-8") as f:
        scenes = json.load(f)

    print("=" * 65)
    print(f"POCKET-TTS FULL EXPLANATION SOUNDTRACK SYNTHESIZER (CPU)")
    print(f"Total Scenes to Synthesize: {len(scenes)}")
    print(f"Voices: {', '.join(v['name'] for v in TARGET_VOICES)}")
    print("=" * 65)

    print("Loading base Pocket-TTS model...")
    model = TTSModel.load_model()
    sample_rate = model.config.mimi.sample_rate
    pause_samples = np.zeros(int(sample_rate * 0.35), dtype=np.float32) # 350ms pause

    summary_results = []

    for v_info in TARGET_VOICES:
        v_id = v_info["id"]
        v_name = v_info["name"]
        print(f"\n[>>>] Starting Full Narration Synthesis for: {v_name} (voice_id: '{v_id}')")
        
        voice_dir = os.path.join(BASE_OUT, "voiceovers", v_id)
        os.makedirs(voice_dir, exist_ok=True)

        state = model.get_state_for_audio_prompt(v_id)
        full_audio_pieces = []
        t_start_voice = time.time()

        for idx, scene in enumerate(scenes, 1):
            line_text = scene["line"].strip()
            scene_id = scene["scene_id"]
            scene_wav_path = os.path.join(voice_dir, f"{scene_id}_{v_id}.wav")

            t0 = time.time()
            chunks = list(model.generate_audio_stream(state, line_text))
            audio_np = torch.cat(chunks).cpu().numpy()

            sf.write(scene_wav_path, audio_np, sample_rate)
            full_audio_pieces.append(audio_np)
            full_audio_pieces.append(pause_samples)

            dur_s = len(audio_np) / sample_rate
            elapsed_s = time.time() - t0
            rtf = dur_s / elapsed_s if elapsed_s > 0 else 0
            if idx % 5 == 0 or idx == len(scenes):
                print(f"  [{idx:02d}/{len(scenes)}] Scene {scene_id}: {dur_s:.2f}s audio in {elapsed_s:.2f}s ({rtf:.2f}x RTF)")

        # Concatenate complete continuous soundtrack
        full_master = np.concatenate(full_audio_pieces)
        master_path = os.path.join(BASE_OUT, f"full_narration_{v_id}.wav")
        sf.write(master_path, full_master, sample_rate)

        total_dur = len(full_master) / sample_rate
        total_time = time.time() - t_start_voice
        overall_rtf = total_dur / total_time if total_time > 0 else 0

        print(f"  [✓] Complete Track Exported: {master_path}")
        print(f"      Total Audio: {total_dur:.2f}s | Elapsed Time: {total_time:.2f}s | Speedup: {overall_rtf:.2f}x RTF")

        summary_results.append({
            "voice_id": v_id,
            "name": v_name,
            "master_file": master_path,
            "duration_seconds": round(total_dur, 2),
            "generation_time_seconds": round(total_time, 2),
            "rtf": round(overall_rtf, 2)
        })

    print("\n" + "=" * 65)
    print("ALL 3 MASTER SOUNDTRACKS SYNTHESIZED SUCCESSFULLY!")
    for s in summary_results:
        print(f" - {s['name']}: {s['duration_seconds']}s audio at {s['rtf']}x RTF -> {s['master_file']}")
    print("=" * 65)

if __name__ == "__main__":
    main()
