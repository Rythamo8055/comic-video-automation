# Comic Video Automation Engine 🎬📖

An automated pipeline and technical framework to convert comic books, manga, and graphic novels into dynamic, YouTube-style recap videos using Python, local Text-to-Speech (Pocket TTS), and local vision/OCR models.

This system reverse-engineers the editing techniques and audio-visual storytelling used in popular comic recap channels, specifically analyzed from the reference video:  
🔗 **[This Omnitrix Summons Alien BADDIES! | Chaquetrix Pt.1](https://youtu.be/zjSyr7qCJP0)**

---

## 📊 1. Reference Video Analysis Summary

Detailed frame-by-frame, cut-frequency, and audio inspection revealed the following production parameters:

* **Pacing & Cuts:**
  * **Average shot duration:** `2.20 seconds` (56 cuts in first 120s).
  * **Cut style:** `95%+` straight hard cuts synchronized to sentence boundaries and punchlines.
  * **Jump Zooms:** Instant $1.3\times - 1.5\times$ scale cuts for comedic or dramatic emphasis.
* **Transformations & Motion (Ken Burns):**
  * **Vertical Pan:** Smooth top-to-bottom scroll across tall comic pages following natural reading order.
  * **Continuous Push-In:** Slow subtle zoom ($1.0\times \to 1.15\times$) to prevent static 2D panels from feeling frozen.
  * **Impact Shake:** 3–5 frame directional shake on action panels and explosions.
* **Voice & Audio Mixing:**
  * **Narration Pace:** `172.8 Words Per Minute (WPM)` (rapid, engaging recap persona).
  * **Loudness:** Voice track averaged `-12.8 dB` with peak at `0.0 dB`.
  * **Music & Ducking:** Energetic instrumental BGM running underneath at `-16 dB to -18 dB`, automatically ducked during speech.

---

## 🏗️ 2. Automation Architecture

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

1. **Panel & Bubble Slicing (`src/panel_extractor.py`):** Uses OpenCV morphological operators and gutter detection to extract panels and crop speech bubbles in reading order.
2. **Text Extraction (Non-LLM OCR vs VLM):** Transcribes dialogue text.
3. **Voice Synthesis (Pocket TTS):** Generates voice lines for each panel and measures the exact audio duration.
4. **Motion Video Generation (`src/motion_comic_generator.py`):** Dynamically animates each panel (pan/zoom) to match the audio clip length.
5. **Final Mix:** Stitches panel clips with hard cuts and mixes background music with automatic sidechain ducking.

---

## 💻 3. Local Model Recommendations

### Non-LLM Options (Zero Hallucination, Under 500 MB RAM)
* **`Manga-OCR` ⭐ (Top Pick for Comics):** Specially trained on comic/manga typography, hand-drawn fonts, and speech balloons. Runs in **15 ms** on GPU and **50 ms** on CPU.
* **`EasyOCR` / `PaddleOCR`:** Reliable multi-language text detection and recognition.
* **`BLIP Captioner`:** Lightweight encoder-decoder (~500 MB) if you need factual scene descriptions without an LLM.
* **`OpenCV`:** Pure computer vision to isolate panels and white speech bubbles with 0 MB model download.

### What Fits Best on 4 GB VRAM?
* **Dialogue Reading:** **Manga-OCR** (~400 MB VRAM)
* **Story Narration (VLM):** **Qwen2.5-VL-3B (4-bit Q4_K_M)** (~2.2 GB VRAM) — reads dialogue, interprets characters and actions, and writes recap lines in 0.5–1.0s.

---

## 🚀 4. Quick Start

### Installation
```bash
git clone https://github.com/Rythamo8055/comic-video-automation.git
cd comic-video-automation
pip install -r requirements.txt
```

### 1. Extract Panels & Speech Bubbles
```bash
python3 src/panel_extractor.py sample_comic_page.png
```
Extracted panels will be saved into `output/panels/` and bubbles into `output/bubbles/`.

### 2. Generate Motion Comic Video
```python
from src.motion_comic_generator import create_motion_clip, assemble_full_video

# Create a dynamic animated clip for a panel matching TTS audio duration
clip1 = create_motion_clip("output/panels/panel_001.png", "narration_01.wav", "clip_001.mp4", mode="zoom_in")
clip2 = create_motion_clip("output/panels/panel_002.png", "narration_02.wav", "clip_002.mp4", mode="pan_down")

# Stitch into final video with auto-ducked background music
assemble_full_video([clip1, clip2], "assets/bgm.mp3", "final_story_video.mp4")
```

### 3. Analyze Any Reference YouTube Video
```bash
python3 src/video_analyzer.py path_to_video.mp4
```

---

## 📚 Detailed Documentation
* [Reference Video Technical Analysis](docs/video_analysis.md)
* [Hardware & Model Evaluation Guide](docs/hardware_and_models.md)
* [Full Pipeline Architecture](docs/pipeline_architecture.md)

---

## License
MIT
