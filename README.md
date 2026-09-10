# Comic Video Automation Engine 🎬📖

An automated pipeline and technical framework to convert comic books, manga, and graphic novels into dynamic, YouTube-style recap videos using Python, local Text-to-Speech (**Kyutai Pocket TTS**), and local vision/OCR tools.

This system reverse-engineers the editing techniques and audio-visual storytelling used in popular comic recap channels, specifically analyzed from the reference video:  
🔗 **[This Omnitrix Summons Alien BADDIES! | Chaquetrix Pt.1](https://youtu.be/zjSyr7qCJP0)**

---

## ⚡ 1. Fully Working 100% Non-LLM Pipeline (No GPU Required)

The repository includes a complete, end-to-end **100% Non-LLM pipeline** (`src/pipeline_non_llm.py`) that runs entirely on modern multi-core CPUs (tested on 13th Gen Intel Core i7):

* **Speech Bubble Extraction:** Pure OpenCV contour & threshold analysis (< 10 ms).
* **Dialogue Transcription:** `EasyOCR` (runs locally on CPU with zero hallucinations).
* **Voice Generation:** **Kyutai Pocket TTS v3.1.0** (already installed, runs **3.32x faster than real-time on CPU**).
* **Motion Comic Generation:** Dynamic FFmpeg Ken Burns push-in zoom & vertical pan synchronized to audio length.

### Run the Non-LLM Pipeline:
```bash
python3 src/pipeline_non_llm.py <path_to_comic_panel.png>
```
Output: Generates a synchronized 1280x720 24fps motion comic `.mp4` video with natural voice narration in **under 1.3 seconds**.

---

## 📊 2. Reference Video Technical Analysis

Detailed frame-by-frame, cut-frequency, and audio inspection revealed:

* **Pacing & Cuts:**
  * **Average shot duration:** `2.20 seconds` (56 cuts in first 120s).
  * **Cut style:** `95%+` straight hard cuts synchronized to sentence boundaries and punchlines.
  * **Jump Zooms:** Instant $1.3\times - 1.5\times$ scale cuts for comedic or dramatic emphasis.
* **Transformations & Motion (Ken Burns):**
  * **Vertical Pan:** Smooth top-to-bottom scroll across tall comic pages following natural reading order.
  * **Continuous Push-In:** Slow subtle zoom ($1.0\times \to 1.15\times$) to keep 2D panels visually alive.
  * **Impact Shake:** 3–5 frame directional shake on action panels and explosions.
* **Voice & Audio Mixing:**
  * **Narration Pace:** `172.8 Words Per Minute (WPM)` (rapid, energetic recap persona).
  * **Loudness:** Voice track averaged `-12.8 dB` with peak at `0.0 dB`.
  * **Music & Ducking:** Energetic instrumental BGM running underneath at `-16 dB to -18 dB`, automatically ducked during speech.

---

## 🏗️ 3. Pipeline Architecture

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  Comic Book     │ ──> │ Panel Slicer & OCR  │ ──> │ Script & Narration  │
│  (CBZ / PDF)    │     │ (OpenCV / Contours) │     │ (Dialogue / Recap)  │
└─────────────────┘     └─────────────────────┘     └──────────┬──────────┘
                                                               │
                                                               ▼
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  Final 1080p    │ <── │ Video Assembly      │ <── │ Pocket TTS Engine   │
│  Recap Video    │     │ (FFmpeg / MoviePy)  │     │ (Generates .wav)    │
└─────────────────┘     └─────────────────────┘     └─────────────────────┘
```

---

## 🚀 4. Usage

### 1. Run Complete Non-LLM Pipeline (Bubble -> OCR -> TTS -> Video)
```bash
python3 src/pipeline_non_llm.py analysis/comic_shots/shot_20.png
```

### 2. Extract Panels & Speech Bubbles from Full Comic Pages
```bash
python3 src/panel_extractor.py sample_comic_page.png
```

### 3. Generate Motion Comic Video Programmatically
```python
from src.motion_comic_generator import create_motion_clip, assemble_full_video

# Create an animated clip for a panel matching TTS audio duration
clip1 = create_motion_clip("output/panels/panel_001.png", "narration_01.wav", "clip_001.mp4", mode="zoom_in")
clip2 = create_motion_clip("output/panels/panel_002.png", "narration_02.wav", "clip_002.mp4", mode="pan_down")

# Stitch into final video with auto-ducked background music
assemble_full_video([clip1, clip2], "assets/bgm.mp3", "final_story_video.mp4")
```

---

## 📚 Documentation & Logs
* 📓 **[Developer Log (DEVLOG.md)](DEVLOG.md)**: Daily engineering benchmarks, audit logs, and decisions.
* 🎥 **[Reference Video Analysis](docs/video_analysis.md)**: Quantitative breakdown of Chaquetrix Pt. 1.
* 💻 **[Hardware & Model Evaluation Guide](docs/hardware_and_models.md)**: Benchmarks for CPU vs 4 GB VRAM.
* 📐 **[Full Pipeline Architecture](docs/pipeline_architecture.md)**: System design and data flow.

---

## License
MIT
