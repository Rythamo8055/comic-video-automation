#!/usr/bin/env python3
"""
find_story_start.py - Autonomous Story Beginning & First Panel Finder

Automatically inspects comic pages, identifies and skips:
  1. Cover Pages (Issue markings, barcodes, logos, full splash)
  2. Lore / Recap / Credits / Editorial Pages (Prose synopses, legal/staff credits)

Detects the exact first page of the REAL story, and extracts its FIRST narrative panel.
"""

import os
import sys
import json
import argparse
import cv2
import numpy as np
import easyocr

# Text signals for classification
COVER_SIGNALS = [
    'rated', 'marvel', 'dc', 'issue', 'vol', 'variant', 'direct edition',
    '$', 'rated t+', 'rated t', 'comic code'
]

RECAP_CREDITS_SIGNALS = [
    'born to a', 'previously', 'recap', 'story so far', 'this is the tale',
    'editor in chief', 'editor', 'letterer', 'colorist', 'penciler', 'penciller',
    'writer', 'published by', 'copyright', 'all rights reserved', 'special thanks',
    'cover artist', 'production manager', 'executive editor'
]

def classify_page(page_index, ocr_texts, img_shape):
    """
    Classifies a comic page as COVER, RECAP_CREDITS, or STORY_START.
    """
    text_joined = ' '.join(ocr_texts).lower()
    h, w = img_shape[:2]

    # 1. Cover Page Detection (Always page index 0 / first page)
    if page_index == 0:
        cover_hits = [sig for sig in COVER_SIGNALS if sig in text_joined]
        if cover_hits or len(ocr_texts) < 25:
            return "COVER", f"Cover detected (Index 0, signals: {cover_hits})"

    # 2. Lore / Recap / Editorial Credits Detection
    recap_hits = [sig for sig in RECAP_CREDITS_SIGNALS if sig in text_joined]
    if len(recap_hits) >= 2 or any(k in text_joined for k in ['previously', 'this is the tale', 'story so far', 'recap']):
        return "RECAP_CREDITS", f"Recap/Credits detected (Signals: {recap_hits})"

    # 3. Default: Real Story Start
    return "STORY_START", "Narrative sequential story start"


def extract_first_panel(page_img, min_area_ratio=0.03):
    """
    Extracts the first panel in reading order (top-to-bottom, left-to-right).
    """
    h, w = page_img.shape[:2]
    total_area = h * w
    gray = cv2.cvtColor(page_img, cv2.COLOR_BGR2GRAY)

    # Detect gutters and panel bounding boxes
    edges = cv2.Canny(gray, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidate_panels = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > total_area * min_area_ratio:
            x, y, pw, ph = cv2.boundingRect(cnt)
            # Avoid full page border artifacts
            if pw < w * 0.98 and ph < h * 0.98:
                candidate_panels.append((x, y, pw, ph))

    if not candidate_panels:
        # Fallback: check horizontal dividing gutters (dark or light)
        row_dark = np.mean(gray < 35, axis=1) > 0.65
        row_light = np.mean(gray > 220, axis=1) > 0.65
        gutter_rows = np.where(row_dark | row_light)[0]
        
        # Split at the first detected horizontal gutter
        if len(gutter_rows) > 0:
            diffs = np.diff(gutter_rows)
            split_indices = np.where(diffs > 10)[0]
            if len(split_indices) > 0:
                mid_gutter = gutter_rows[split_indices[0]]
                if mid_gutter > h * 0.15:
                    candidate_panels.append((40, 60, w - 80, mid_gutter - 60))

    if not candidate_panels:
        # Final fallback: top half
        candidate_panels.append((40, 60, w - 80, int(h * 0.48)))

    # Sort into comic reading order: top-to-bottom, left-to-right
    candidate_panels.sort(key=lambda p: (p[1] // 120, p[0]))
    first_panel_bbox = candidate_panels[0]
    fx, fy, fw, fh = first_panel_bbox

    first_panel_crop = page_img[fy:fy+fh, fx:fx+fw]
    return first_panel_crop, first_panel_bbox


def find_first_story_page_and_panel(pages_dir, output_dir="output/story_start", max_scan_pages=6):
    """
    Main pipeline:
    1. Scans candidate pages
    2. Classifies each page
    3. Finds first story page
    4. Extracts first panel & text
    """
    os.makedirs(output_dir, exist_ok=True)

    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    page_files = sorted([f for f in os.listdir(pages_dir) if f.lower().endswith(valid_exts)])

    if not page_files:
        raise FileNotFoundError(f"No image files found in {pages_dir}")

    print(f"[*] Initializing EasyOCR engine (CPU-optimized)...")
    reader = easyocr.Reader(['en'], gpu=False)

    print(f"[*] Scanning first up to {min(max_scan_pages, len(page_files))} pages to find story start...")
    analysis_log = []
    found_page_file = None
    found_page_path = None
    found_page_idx = -1

    for idx, p_file in enumerate(page_files[:max_scan_pages]):
        p_path = os.path.join(pages_dir, p_file)
        img = cv2.imread(p_path)
        if img is None:
            continue

        # Run OCR
        ocr_res = reader.readtext(p_path, detail=0)
        page_type, reason = classify_page(idx, ocr_res, img.shape)

        analysis_log.append({
            "page_index": idx + 1,
            "filename": p_file,
            "type": page_type,
            "reason": reason,
            "ocr_sample": ' '.join(ocr_res[:10])
        })

        print(f"  -> Page {idx + 1:02d} ({p_file}): [{page_type}] - {reason}")

        if page_type == "STORY_START":
            found_page_file = p_file
            found_page_path = p_path
            found_page_idx = idx + 1
            break

    if not found_page_path:
        raise RuntimeError("Could not find story starting page within scanned range.")

    print(f"\n[+] Real Story Starts On: Page {found_page_idx:02d} ({found_page_file})")

    # Save copy of the detected story page
    story_page_img = cv2.imread(found_page_path)
    story_page_out_path = os.path.join(output_dir, f"detected_story_page_{found_page_idx:02d}.png")
    cv2.imwrite(story_page_out_path, story_page_img)

    # Extract first panel
    first_panel_crop, (px, py, pw, ph) = extract_first_panel(story_page_img)
    first_panel_out_path = os.path.join(output_dir, "first_panel.png")
    cv2.imwrite(first_panel_out_path, first_panel_crop)

    # Run OCR on the first panel
    panel_ocr_res = reader.readtext(first_panel_out_path, detail=0)
    panel_text = ' '.join(panel_ocr_res)

    result = {
        "status": "success",
        "story_page": {
            "page_number": found_page_idx,
            "filename": found_page_file,
            "source_path": found_page_path,
            "saved_copy_path": story_page_out_path,
            "dimensions": {
                "width": story_page_img.shape[1],
                "height": story_page_img.shape[0]
            }
        },
        "first_panel": {
            "saved_path": first_panel_out_path,
            "bbox": {
                "x": px,
                "y": py,
                "width": pw,
                "height": ph
            },
            "dimensions": {
                "width": first_panel_crop.shape[1],
                "height": first_panel_crop.shape[0]
            },
            "transcribed_text": panel_text
        },
        "analysis_log": analysis_log
    }

    meta_file = os.path.join(output_dir, "story_start_meta.json")
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[+] Saved First Story Page to: {story_page_out_path}")
    print(f"[+] Saved First Story Panel to: {first_panel_out_path}")
    print(f"[+] First Panel Dimensions: {first_panel_crop.shape[1]}x{first_panel_crop.shape[0]}")
    print(f"[+] First Panel Text:\n    \"{panel_text}\"")

    return result


def main():
    parser = argparse.ArgumentParser(description="Find the first page of the real comic story and extract its first panel.")
    parser.add_argument("--pages-dir", default="data/spider_man_001/pages", help="Directory containing comic page images")
    parser.add_argument("--output-dir", default="output/story_start", help="Output directory for results")
    parser.add_argument("--max-scan", type=int, default=6, help="Max pages to scan")
    parser.add_argument("--json", action="store_true", help="Print result as JSON")

    args = parser.parse_args()

    result = find_first_story_page_and_panel(
        pages_dir=args.pages_dir,
        output_dir=args.output_dir,
        max_scan_pages=args.max_scan
    )

    if args.json:
        print("\n" + json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
