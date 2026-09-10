# Local Models & Hardware Guide: Image-to-Text for Comics

## 1. Machine Hardware Profile

- **CPU:** 13th Gen Intel Core i7-1360P (12 cores / 16 threads)
- **RAM:** 16 GB (approx. 9 GB usable/free)
- **GPU (Current):** Integrated Intel Iris Xe (CPU-accelerated inference)
- **Storage:** NVMe SSD (fast model checkpoint loading)

---

## 2. Non-LLM Options (Recommended for Pure Speed & Dialogue Extraction)

Non-LLM engines are deterministic, use negligible RAM (< 500 MB), run in milliseconds, and never hallucinate.

### A. Comic OCR Engines (Reading Dialogue Bubbles)
| Tool | Size | Speed (CPU) | Speed (4GB VRAM GPU) | Pros & Best Use Case |
| :--- | :--- | :--- | :--- | :--- |
| **Manga-OCR** ⭐ | ~300 MB | ~50 ms | ~15 ms | **Best comic text accuracy.** Trained on stylized manga/comic lettering fonts and bubble shapes. |
| **PaddleOCR** | ~150 MB | ~80 ms | ~20 ms | High accuracy on angled, vertical, and complex multi-line text boxes. |
| **EasyOCR** | ~200 MB | ~100 ms | ~25 ms | PyTorch-based (CRAFT). Easy Python installation; reliable on clean bubbles. |
| **Tesseract** | ~30 MB | ~30 ms | N/A (CPU) | Traditional C++ OCR. Works best on standard font text. |

### B. Traditional Image Captioning (Describing Panels without LLMs)
| Model | Size / VRAM | Speed | Purpose |
| :--- | :--- | :--- | :--- |
| **BLIP Base** (`Salesforce/blip-image-captioning-base`) | ~500 MB (1.1 GB VRAM) | ~150 ms | Generates a 1-sentence factual summary of the image (e.g., *"two characters conversing inside a control room"*). |

### C. Pure Computer Vision (Zero Models)
- **OpenCV Bubble & Panel Detection:**
  - Standard morphological filters, color thresholding (bubbles are $>230$ intensity white), and contour finding isolate panels and bubbles instantly with 0 MB model download.

---

## 3. Best Choices if You Have 4 GB VRAM

When running on a dedicated 4 GB VRAM GPU (e.g., GTX 1650, RTX 3050):

1. **Strict Dialogue Extraction:**
   - **Manga-OCR**: Uses ~400 MB VRAM, transcribes bubbles in 15 ms.
2. **YouTube Recap Storytelling (Scene Understanding + Dialogue):**
   - **Qwen2.5-VL-3B (Q4_K_M)**: Uses ~2.2 GB VRAM.
   - Reads bubbles, recognizes character actions/expressions, and drafts recap narration in 0.5–1.0s.
3. **Audio Generation:**
   - **Pocket TTS / Kokoro**: Lightweight local TTS generating `.wav` narration files.
4. **Video Encoding:**
   - **FFmpeg (`h264_nvenc`)**: Fast GPU-accelerated video rendering.
