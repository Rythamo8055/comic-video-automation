# Comic Video Automation Pipeline

This document outlines the complete automated architecture for converting comic books into motion-comic recap videos like the reference video.

```
┌───────────────────────────┐
│   Comic Book Source       │  (CBZ, PDF, or folder of page images)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 1. Panel Segmentation     │  (OpenCV gutter detection / contour slicing)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 2. Bubble & Text OCR      │  (OpenCV bubble crop + Manga-OCR / EasyOCR)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 3. Script & Audio (TTS)   │  (Pocket TTS / Local TTS -> panel audio clips)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 4. Motion Generation      │  (FFmpeg Ken Burns pan/zoom to match audio length)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ 5. Audio Mix & Render     │  (Narration + Ducked BGM + Sound Effects)
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│  Final 1080p Video        │
└───────────────────────────┘
```

---

## Detailed Stages

### Stage 1: Panel Slicing
- Uses OpenCV to detect black/white gutters dividing comic panels.
- Extracts individual panels in top-to-bottom, left-to-right sequence.
- Saves panels as `panel_001.png`, `panel_002.png`, etc.

### Stage 2: Dialogue & Text Extraction
- Extracts speech bubbles by detecting white closed contours.
- Transcribes text using `manga-ocr` or `easyocr`.
- Associates dialogue with corresponding panel ID.

### Stage 3: Audio Generation via Local TTS
- Runs Pocket TTS (or Kokoro / Piper) per dialogue/narration line.
- Obtains exact duration in seconds for each panel:
  $$\text{Duration} = \frac{\text{Audio Samples}}{\text{Sample Rate}}$$

### Stage 4: Motion Video Synthesis (Ken Burns)
- For each panel and its audio duration $D$:
  - **Tall Panels:** Vertical pan top-to-bottom over duration $D$.
  - **Wide Panels:** Slow zoom-in from $1.0\times$ to $1.15\times$ over duration $D$.
  - **Action Panels:** Short camera shake on impact points.
- Outputs individual sub-clips `clip_001.mp4`, `clip_002.mp4`, etc.

### Stage 5: Audio Mixing & Final Assembly
- Concatenates sub-clips using FFmpeg `concat` demuxer (zero re-encoding loss).
- Layers background music with auto-ducking:
  ```bash
  ffmpeg -i video.mp4 -i voice.wav -i bgm.mp3 \
    -filter_complex "[2:a]volume=0.2[bgm];[1:a][bgm]amix=inputs=2:duration=first[aout]" \
    -map 0:v -map "[aout]" final_comic_video.mp4
  ```
