#!/usr/bin/env python3
"""
panel_extractor.py - Automatically extracts comic panels and speech bubbles from comic pages.
Uses pure OpenCV (no heavy models required).
"""

import os
import cv2
import numpy as np

def extract_panels(image_path, output_dir="output/panels", min_area_ratio=0.03):
    """
    Detects individual comic panels on a comic book page and saves them in reading order.
    """
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    h, w, _ = img.shape
    total_area = h * w
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Edge detection and morphological closing to connect panel outlines
    edges = cv2.Canny(gray, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    panels = []

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > total_area * min_area_ratio:
            x, y, pw, ph = cv2.boundingRect(cnt)
            # Avoid full page borders
            if pw < w * 0.98 and ph < h * 0.98:
                panels.append((x, y, pw, ph))

    # Sort panels into natural comic reading order (top-to-bottom, left-to-right)
    panels.sort(key=lambda p: (p[1] // 150, p[0]))

    saved_paths = []
    for idx, (x, y, pw, ph) in enumerate(panels, 1):
        panel_crop = img[y:y+ph, x:x+pw]
        out_path = os.path.join(output_dir, f"panel_{idx:03d}.png")
        cv2.imwrite(out_path, panel_crop)
        saved_paths.append(out_path)

    print(f"Extracted {len(saved_paths)} panels to {output_dir}")
    return saved_paths

def extract_speech_bubbles(panel_image_path, output_dir="output/bubbles", min_area=1500):
    """
    Detects and crops speech bubbles inside a comic panel.
    Comic bubbles are typically bright white (>225) surrounded by dark boundaries.
    """
    os.makedirs(output_dir, exist_ok=True)
    img = cv2.imread(panel_image_path)
    if img is None:
        return []

    h, w, _ = img.shape
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Threshold for white speech bubble interior
    _, thresh = cv2.threshold(gray, 225, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    bubbles = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > min_area:
            x, y, bw, bh = cv2.boundingRect(cnt)
            if bw < w * 0.9 and bh < h * 0.9:
                bubbles.append((x, y, bw, bh))

    # Sort bubbles left-to-right, top-to-bottom
    bubbles.sort(key=lambda b: (b[1], b[0]))

    base_name = os.path.splitext(os.path.basename(panel_image_path))[0]
    saved_paths = []
    for idx, (x, y, bw, bh) in enumerate(bubbles, 1):
        bubble_crop = img[y:y+bh, x:x+bw]
        out_path = os.path.join(output_dir, f"{base_name}_bubble_{idx:02d}.png")
        cv2.imwrite(out_path, bubble_crop)
        saved_paths.append(out_path)

    return saved_paths

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        extract_panels(sys.argv[1])
    else:
        print("Usage: python panel_extractor.py <path_to_comic_page>")
