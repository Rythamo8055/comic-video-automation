# Antigravity Production Dev Log: Spider-Man Challenges of Doom #001 Motion Comic Recap

## System Architecture & Milestone Status

### Current Production State
- **Narrator Voice Model**: Kyutai Pocket TTS `alba` (Natural storytelling tone with scene-by-scene variable emotional temperature).
- **Soundtrack Selection**: **ComicsExplained Style Dark Cinematic Narrative Hip-Hop Groove** (`assets/pro_creator_tracks/3_comicsexplained_narrative_groove.mp3`).
- **Video Format**: 1080p (`1920x1080`), 60.00 FPS Constant Frame Rate, Baseline H.264 High-Profile, 12 Mbps video bitrate, 320 kbps AAC stereo audio.
- **Visual Staging**: 100% full, uncropped original comic panels centered on a 16:9 canvas with balanced breathing margins (no edge clipping or speech bubble cropping).
- **Camera Movement Engine**: 64-bit floating-point affine matrix transformations (`cv2.warpAffine` + `INTER_CUBIC`) delivering continuous, zero-jitter sub-pixel camera zooms, vertical pans, and impact shakes.
- **Scene Transitions**: In-engine White Flash impact transitions and lateral panel slide cuts.
- **Outro Hook**: Scene 9 outro dialogue + animated graphic callout: *"WAIT FOR THE NEXT VIDEO! PART 2 COMING NEXT"*.

---

## Technical Problem Solving & Quality Log

### 1. The "Audio Not Crisp" Bug & Broadcast Studio Solution
* **Problem Observed**: Audio mixes sounded muffled, "underwater", and lacked crisp articulation when background music was blended with voice.
* **Root Causes Diagnosed**:
  1. *Default MP3 Bitrate Bottleneck*: FFmpeg's `amix` command into `.mp3` without explicit bitrate flags defaulted to **32 kbps** (`32,000 bps`), aggressively cutting high frequencies and introducing watery compression artifacts.
  2. *Sample Rate & Channel Mismatch*: Pocket TTS generated 24 kHz mono while music was 48 kHz stereo; basic mixing collapsed everything into a low-fidelity mono box.
  3. *Frequency Masking*: The music's instruments (guitars, keyboards, snares) produced heavy energy in the $1.5\text{ kHz}-3.5\text{ kHz}$ vocal band, masking the speech consonants (`t`, `k`, `s`, `p`).
* **Studio Mastering Implementation**:
  - Captured voice directly as uncompressed 24-bit PCM `.wav` from Pocket TTS.
  - Upsampled to **48,000 Hz** using SOXR 28-bit sinc interpolation.
  - Applied a surgical **$-6\text{ dB}$ Vocal Pocket notch at $2.5\text{ kHz}$** on the music track.
  - Added vocal presence excitation (`+3.5 dB @ 4.5 kHz`, `+2.5 dB @ 11 kHz`) and high-pass filter at $80\text{ Hz}$.
  - Configured real-time **dynamic sidechain compression ducking**: music automatically ducks by $-6\text{ dB}$ whenever Alba speaks, and smoothly blooms during pauses.
  - Mastered at full **320 kbps True Stereo**.

### 2. Elimination of Annoying Rhythmic Clicks
* **Problem Observed**: Previous procedural tension track contained an 8th-note transient tick at 120 BPM that caused ear fatigue.
* **Solution**: Completely removed procedural ticking synthesis; replaced with real professional creator-grade narrative music.

### 3. Emotion Control via Scene-by-Scene Temperature Mapping
* Kyutai Pocket TTS FlowLM sampling temperature dynamically adjusted per scene:
  - `scene_001` (Doom Chessboard plan): `0.35` (Mysterious & calculated)
  - `scene_002` (Wildcard knock): `0.45` (Intriguing plot turn)
  - `scene_003` (Peter in Queens): `0.38` (Playful & relaxed)
  - `scene_004` (Web-shooter tech): `0.40` (Energetic explanation)
  - `scene_005` (Lamp ricochet shock): `0.58` (Surprise & sudden reaction)
  - `scene_006` (Mid-air reflex save): `0.62` (High urgency & relief)
  - `scene_007` (Spider-Sense goes nuclear): `0.68` (Psychic alarm & danger)
  - `scene_008` (Tactical pulse trap): `0.55` (Ominous revelation)
  - `scene_009` (Outro & Part 2 CTA): `0.50` (Enthusiastic hook)

---

## Production Deliverables Inventory

| Asset | Path | Specs |
| :--- | :--- | :--- |
| **Final Video (60 FPS)** | `output/spiderman_recap_part1_comicsexplained_groove_60fps.mp4` | 1080p, 60.00 fps, ~143s, 320k AAC Stereo |
| **YouTube 1080p Thumbnail** | `output/thumbnail_part_1.jpg` | 1920x1080, High-CTR Marvel Badge + "PART 1" |
| **Selected Music Track** | `assets/pro_creator_tracks/3_comicsexplained_narrative_groove.mp3` | ComicsExplained narrative boom-bap beat |
| **Master Production Script** | `output/narrator_recap_production/narrator_script.json` | 9 scenes, narrator-only dramatic storytelling |
| **Master 60FPS Renderer** | `src/render_comicsexplained_groove_video_60fps.py` | Full synthesis, studio mastering, and video stream |
