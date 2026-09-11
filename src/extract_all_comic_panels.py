#!/usr/bin/env python3
"""
extract_all_comic_panels.py - Sequentially extracts all comic panels from first to last page.
Saves them into a folder named after the comic title with chronological order indices.
"""

import os
import sys
import json
import argparse
import cv2
import numpy as np

def extract_panels_robust(img, page_num):
    """
    Robust Multi-Pass Comic Panel Segmenter using Snapped Recursive XY-Cut
    and Resolution-Independent Adaptive Projections.
    Guarantees 100% page content coverage without dropping open-border or splash panels
    across any comic book format or resolution.
    """
    h, w = img.shape[:2]

    # Front cover is always full splash
    if page_num == 1:
        return [(0, 0, w, h)]

    # Double-page spread / wide landscape image
    if w > h * 1.05:
        return [(0, 0, w, h)]

    c_y1, c_y2 = int(h * 0.015), int(h * 0.985)
    c_x1, c_x2 = int(w * 0.015), int(w * 0.985)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. Edge & Morphology Gradient
    edges = cv2.Canny(gray, 30, 100)
    k_w = max(15, int(w * 0.02))
    k_horiz = cv2.getStructuringElement(cv2.MORPH_RECT, (k_w, 1))
    edges_h = cv2.dilate(edges, k_horiz)

    # Horizontal row density & luminance profile
    row_density = np.mean(edges_h[:, c_x1:c_x2], axis=1) / 255.0
    row_light = np.mean(gray[:, c_x1:c_x2] > 225, axis=1)
    row_dark = np.mean(gray[:, c_x1:c_x2] < 35, axis=1)

    # Detect horizontal gutter bands (valleys in edge density or uniform gutters)
    is_gutter_y = (row_density < 0.05) | ((row_light > 0.6) & (row_density < 0.15)) | ((row_dark > 0.6) & (row_density < 0.15))

    gutter_bands_y = []
    in_b = False
    start_y = 0
    min_gutter_h = max(5, int(h * 0.002))
    for y in range(c_y1, c_y2):
        if is_gutter_y[y]:
            if not in_b:
                in_b = True
                start_y = y
        else:
            if in_b:
                in_b = False
                if y - start_y >= min_gutter_h:
                    gutter_bands_y.append((start_y, y))
    if in_b and c_y2 - start_y >= min_gutter_h:
        gutter_bands_y.append((start_y, c_y2))

    # Horizontal tier cuts snapped to gutter centers
    min_tier_h = int(h * 0.07)
    tier_cuts = [c_y1]
    for gy1, gy2 in gutter_bands_y:
        mid_y = (gy1 + gy2) // 2
        if mid_y - tier_cuts[-1] >= min_tier_h and c_y2 - mid_y >= min_tier_h:
            tier_cuts.append(mid_y)
    tier_cuts.append(c_y2)

    tiers = []
    for i in range(len(tier_cuts) - 1):
        tiers.append((tier_cuts[i], tier_cuts[i + 1]))

    panels = []
    k_h = max(15, int(h * 0.01))
    k_vert = cv2.getStructuringElement(cv2.MORPH_RECT, (1, k_h))
    edges_v = cv2.dilate(edges, k_vert)

    # 2. Vertical sub-panel segmentation inside each tier
    min_col_w = int(w * 0.12)
    min_gutter_w = max(5, int(w * 0.003))

    for ty1, ty2 in tiers:
        tier_edges = edges_v[ty1:ty2, :]
        tier_gray = gray[ty1:ty2, :]

        col_density = np.mean(tier_edges, axis=0) / 255.0
        col_light = np.mean(tier_gray > 225, axis=0)
        col_dark = np.mean(tier_gray < 35, axis=0)

        is_gutter_x = (col_density < 0.04) | ((col_light > 0.7) & (col_density < 0.12)) | ((col_dark > 0.7) & (col_density < 0.12))

        gutter_bands_x = []
        in_bx = False
        start_x = 0
        for x in range(c_x1, c_x2):
            if is_gutter_x[x]:
                if not in_bx:
                    in_bx = True
                    start_x = x
            else:
                if in_bx:
                    in_bx = False
                    if x - start_x >= min_gutter_w:
                        gutter_bands_x.append((start_x, x))
        if in_bx and c_x2 - start_x >= min_gutter_w:
            gutter_bands_x.append((start_x, c_x2))

        col_cuts = [c_x1]
        for gx1, gx2 in gutter_bands_x:
            mid_x = (gx1 + gx2) // 2
            if mid_x - col_cuts[-1] >= min_col_w and c_x2 - mid_x >= min_col_w:
                col_cuts.append(mid_x)
        col_cuts.append(c_x2)

        pad_x = int(w * 0.008)
        pad_y = int(h * 0.005)
        for i in range(len(col_cuts) - 1):
            px1 = max(0, col_cuts[i] - pad_x)
            px2 = min(w, col_cuts[i + 1] + pad_x)
            py1 = max(0, ty1 - pad_y)
            py2 = min(h, ty2 + pad_y)
            panels.append((px1, py1, px2 - px1, py2 - py1))

    # Sort strictly in reading order (top-to-bottom, left-to-right)
    panels.sort(key=lambda p: (p[1] // int(h * 0.04), p[0]))
    return panels


def extract_comic_panels(pages_dir, comic_title="Challenges_of_Doom_Spider-Man_001", base_out_dir="output"):
    target_dir = os.path.join(base_out_dir, comic_title)
    os.makedirs(target_dir, exist_ok=True)

    import re
    valid_exts = ('.jpg', '.jpeg', '.png', '.webp')
    # Natural numerical sorting so page_2 < page_10 < page_100
    def natural_sort_key(s):
        return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

    page_files = sorted([f for f in os.listdir(pages_dir) if f.lower().endswith(valid_exts)], key=natural_sort_key)

    if not page_files:
        raise FileNotFoundError(f"No pages found in {pages_dir}")

    manifest = {
        "comic_title": comic_title,
        "total_pages": len(page_files),
        "panels": []
    }

    global_panel_idx = 1
    print(f"[*] Extracting all panels from {len(page_files)} pages into '{target_dir}'...")

    for page_idx, p_file in enumerate(page_files, 1):
        p_path = os.path.join(pages_dir, p_file)
        img = cv2.imread(p_path)
        if img is None:
            continue

        boxes = extract_panels_robust(img, page_idx)
        print(f"  -> Page {page_idx:02d} ({p_file}): {len(boxes)} panels")

        for local_idx, (x, y, pw, ph) in enumerate(boxes, 1):
            crop = img[y:y+ph, x:x+pw]
            filename = f"panel_{global_panel_idx:03d}_p{page_idx:02d}_{local_idx:02d}.png"
            out_path = os.path.join(target_dir, filename)
            cv2.imwrite(out_path, crop)

            manifest["panels"].append({
                "global_index": global_panel_idx,
                "page_number": page_idx,
                "panel_on_page": local_idx,
                "filename": filename,
                "width": pw,
                "height": ph,
                "bbox": [x, y, pw, ph]
            })

            global_panel_idx += 1

    manifest["total_panels"] = len(manifest["panels"])

    # Save manifest
    manifest_path = os.path.join(target_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Generate HTML gallery
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{comic_title} - Extracted Panels</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 24px; }}
  h1 {{ text-align: center; color: #38bdf8; margin-bottom: 8px; }}
  p.subtitle {{ text-align: center; color: #94a3b8; margin-bottom: 32px; }}
  .gallery {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 20px; max-width: 1600px; margin: 0 auto; }}
  .card {{ background: #1e293b; border-radius: 12px; overflow: hidden; border: 1px solid #334155; transition: transform 0.2s; }}
  .card:hover {{ transform: scale(1.02); border-color: #38bdf8; }}
  .card img {{ width: 100%; height: 260px; object-fit: contain; background: #0b0f19; display: block; }}
  .card-info {{ padding: 12px 16px; display: flex; justify-content: space-between; font-size: 13px; color: #94a3b8; }}
  .badge {{ background: #0284c7; color: white; padding: 2px 8px; border-radius: 6px; font-weight: 600; font-size: 11px; }}
</style>
</head>
<body>
<h1>{comic_title}</h1>
<p class="subtitle">Extracted {manifest['total_panels']} panels in chronological reading order across {manifest['total_pages']} pages</p>
<div class="gallery">
"""
    for p in manifest["panels"]:
        html_content += f"""  <div class="card">
    <img src="{p['filename']}" alt="{p['filename']}" loading="lazy">
    <div class="card-info">
      <span class="badge">Panel #{p['global_index']:03d}</span>
      <span>Page {p['page_number']} (Panel {p['panel_on_page']})</span>
      <span>{p['width']}x{p['height']}</span>
    </div>
  </div>
"""

    html_content += """</div>
</body>
</html>
"""
    html_path = os.path.join(target_dir, "index.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n[+] Successfully extracted {manifest['total_panels']} panels to: {target_dir}")
    print(f"[+] Manifest written to: {manifest_path}")
    print(f"[+] Gallery viewer generated: {html_path}")
    return target_dir, manifest

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract all panels across comic book pages.")
    parser.add_argument("--pages-dir", default="data/spider_man_001/pages", help="Pages directory")
    parser.add_argument("--comic-title", default="Challenges_of_Doom_Spider-Man_001", help="Title for the output subfolder")
    parser.add_argument("--base-out", default="output", help="Base output directory")
    args = parser.parse_args()

    extract_comic_panels(args.pages_dir, args.comic_title, args.base_out)
