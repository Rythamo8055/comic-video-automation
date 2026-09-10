# Developer Log (DevLog) 📓

Engineering diary, technical benchmarks, and architecture decisions for the **Comic Video Automation Engine**.

---

## [Entry 01] - Reference Video Deconstruction & Engineering Specs
*Date: 2026-09-10*

### Context
Analyzed reference YouTube recap video:
`https://youtu.be/zjSyr7qCJP0` (*This Omnitrix Summons Alien BADDIES! | Chaquetrix Pt.1*).

### Key Findings & Measurements
1. **Editorial Cuts & Pace:**
   - Total length: `519.9s` (~8.66 min).
   - Cut density: `56 cuts` in first 120 seconds.
   - Mean shot duration: `2.20 seconds`.
   - Transition: `95%+` straight hard cuts synchronized strictly to voice sentence boundaries.
2. **Transformations:**
   - Ken Burns Vertical Pan for tall/multi-panel comics (top-to-bottom).
   - Continuous Push-In zoom ($1.0\times \to 1.15\times$) on single panels.
   - Instant jump zoom ($1.35\times$) on punchline reactions.
   - Screen shake on impact shots.
3. **Voice Narration & Audio:**
   - Narration speaking rate: `172.8 WPM` (energetic, rapid recap persona).
   - Mean vocal volume: `-12.8 dB` (peaks at `0.0 dB`).
   - Instrumental BGM running at `-16 dB to -18 dB` with sidechain ducking under dialogue.

---

## [Entry 02] - Local Machine Audit & Tool Discovery (No-GPU Setup)
*Date: 2026-09-10*

### Hardware Profile
- **Host OS:** Fedora Linux 44 (Workstation Edition)
- **CPU:** 13th Gen Intel Core i7-1360P (12 cores / 16 threads)
- **RAM:** 16 GB (approx. 9 GB available)
- **GPU:** Intel Iris Xe (Integrated graphics, CPU-bound inference)
- **Encoder:** FFmpeg with `libopenh264`, `h264_qsv`

### Installed Tools Discovered & Tested
1. **Kyutai Pocket TTS v3.1.0 (`/usr/local/bin/pocket-tts`):**
   - Already present on system!
   - Tested on CPU: Generated `5.92s` of high-fidelity audio in `1.78s`.
   - **Performance:** Runs **3.32x faster than real-time** on this machine's CPU with zero GPU requirement.
2. **FFmpeg & FFprobe (`/usr/bin/ffmpeg`):**
   - Configured with `libopenh264` hardware/software acceleration.
   - Encoded 720p 24fps motion comic clips in `0.26s` (>11x real-time).
3. **Computer Vision & OCR:**
   - `cv2` (OpenCV) and `PIL` installed.
   - Installed `easyocr` (CRAFT + CRNN). Successfully executed CPU-only text recognition without CUDA.

---

## [Entry 03] - 100% Non-LLM Pipeline Implementation
*Date: 2026-09-10*

### Objective
Create a deterministic, lightweight comic-to-video pipeline requiring **0 MB LLM weights**, **0 GPU VRAM**, and **zero hallucination**.

### Pipeline Implementation (`src/pipeline_non_llm.py`)
1. **Speech Bubble Detection (`OpenCV`):**
   - High-contrast thresholding ($>225$ white level) + contour bounding boxes.
   - Cleanly isolated comic speech bubble `x=212, y=380, w=336, h=281`.
2. **Text Transcription (`EasyOCR`):**
   - Extracted text from bubble: `"BRING THE TECHNOLOGY REQUESTED FROM THE PLUMBERS"`.
3. **Audio Generation (`Pocket TTS`):**
   - Synthesized natural voice `.wav` (duration `2.84s`).
4. **Motion Video Synthesis (`FFmpeg`):**
   - Generated Ken Burns slow push-in zoom synchronized dynamically to `2.84s` duration.
   - Output: `output/pipeline_result/motion_panel.mp4` (1280x720 @ 24fps, H.264/AAC).

### Benchmark Results
- Bubble extraction: `< 10 ms`
- Text recognition: `~100 ms`
- TTS synthesis: `~850 ms` (3.3x real-time)
- Video rendering: `~260 ms` (11x real-time)
- **Total turnaround time per comic panel:** **< 1.3 seconds** on pure CPU!

---

## [Roadmap / Next Steps]
- [ ] Multi-panel sequential stitching (processing complete comic pages).
- [ ] Aspect-ratio auto-fitting (handling tall webtoons vs standard comic spreads).
- [ ] Animated word-by-word subtitle burn-in.
- [ ] Background music mixer with automatic sidechain compression.

---

## [Entry 04] - 7 Dynamic Motion & Transition Modes Implemented
*Date: 2026-09-10*

### Context
Expanded the motion comic engine from a single zoom to a full catalog of **7 camera movements and transition types** modeled directly after the *Chaquetrix Pt. 1* reference video.

### Implemented Modes
1. **`zoom_in` (Push-In Zoom):** Slow scale ($1.0\times \to 1.15\times$) into panel center for dialogue and character focus.
2. **`zoom_out` (Pull-Out Reveal):** Reverse scale ($1.25\times \to 1.0\times$) revealing the environment or new incoming character.
3. **`pan_down` (Vertical Pan):** Reading order scroll ($Y_0 \to Y_{\max}$) for tall panels and webtoons.
4. **`pan_horizontal` (Panoramic Track):** Lateral glide ($X_0 \to X_{\max}$) across wide double-page battle spreads.
5. **`shake` (Camera Shake):** Dynamic sinusoidal displacement ($X, Y \pm 15\text{px}$) for punches, blasts, and impact SFX.
6. **`snap_zoom` (Punch/Jump Zoom):** 0-frame jump cut ($1.0\times \to 1.35\times$) for shock or punchlines.
7. **`white_flash` (Impact Flash Cut):** 2–3 frame white burst between high-energy scene cuts.

### Visual Verification
- All 7 modes rendered directly from comic screenshots (`analysis/comic_shots/`).
- Render speed: **~0.15s to 0.29s** per clip using CPU FFmpeg.
- Interactive showcase created: `transitions_showcase.html`.
