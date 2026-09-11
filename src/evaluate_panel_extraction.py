#!/usr/bin/env python3
"""
src/evaluate_panel_extraction.py
Automated Quantitative Quality & Evaluation Engine for Comic Panel Extraction.
Calculates:
  1. Page Coverage Score (%) - Checks if any panels were dropped or missed.
  2. Balloon / Text Truncation Score (%) - Detects if cut lines sliced through dialogue.
  3. Gutter Alignment Score (%) - Verifies cuts align with true borders.
  4. Composite Overall Grade (PASS / WARNING / FAIL)
"""

import os
import sys
import json
import cv2
import numpy as np
import easyocr

def evaluate_page_extraction(page_image_path, panel_bboxes, reader=None):
    """
    Evaluates panel extraction quality for a single comic page.
    panel_bboxes: list of [x, y, w, h]
    """
    img = cv2.imread(page_image_path)
    if img is None:
        raise FileNotFoundError(f"Cannot load {page_image_path}")

    h, w = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. PAGE COVERAGE SCORE
    # Valid content area usually between y=60 and y=h-60
    content_y1 = 60
    content_y2 = h - 60
    content_h = content_y2 - content_y1

    # Create binary mask of covered area
    covered_mask = np.zeros((h, w), dtype=np.uint8)
    for bx, by, bw, bh in panel_bboxes:
        cv2.rectangle(covered_mask, (bx, by), (bx + bw, by + bh), 255, -1)

    # Calculate vertical row coverage in content area
    row_covered = np.mean(covered_mask[content_y1:content_y2, :] > 0, axis=1)
    coverage_score = float(np.mean(row_covered > 0.5) * 100.0)

    # 2. SPEECH BUBBLE & TEXT TRUNCATION SCORE
    if reader is None:
        reader = easyocr.Reader(['en'], gpu=False)

    ocr_res = reader.readtext(page_image_path)
    text_boxes = []
    for r in ocr_res:
        pts = np.array(r[0], dtype=np.int32)
        tx = int(np.min(pts[:, 0]))
        ty = int(np.min(pts[:, 1]))
        tw = int(np.max(pts[:, 0]) - tx)
        th = int(np.max(pts[:, 1]) - ty)
        if r[2] > 0.25 and tw > 15 and th > 10:
            text_boxes.append((tx, ty, tw, th, r[1]))

    # Check if cut lines slice through text
    cut_violations = []
    for tx, ty, tw, th, text in text_boxes:
        # Check if text box is split across panel boundaries
        contained = False
        for bx, by, bw, bh in panel_bboxes:
            if bx <= tx and by <= ty and (bx + bw) >= (tx + tw) and (by + bh) >= (ty + th):
                contained = True
                break
        if not contained:
            cut_violations.append({
                "text": text,
                "bbox": [tx, ty, tw, th]
            })

    total_text = max(1, len(text_boxes))
    text_integrity_score = float(max(0.0, (1.0 - (len(cut_violations) / total_text))) * 100.0)

    # 3. GUTTER ALIGNMENT SCORE
    # Evaluates if cut lines fall into dark/light gutter regions
    gutter_hits = 0
    total_cuts = 0
    for bx, by, bw, bh in panel_bboxes:
        for cut_y in [by, by + bh]:
            if 80 < cut_y < h - 80:
                total_cuts += 1
                row_dark = np.mean(gray[max(0, cut_y - 8):min(h, cut_y + 8), :] < 45)
                row_light = np.mean(gray[max(0, cut_y - 8):min(h, cut_y + 8), :] > 215)
                if row_dark > 0.60 or row_light > 0.60:
                    gutter_hits += 1

    gutter_score = float((gutter_hits / max(1, total_cuts)) * 100.0) if total_cuts > 0 else 100.0

    # 4. COMPOSITE QUALITY SCORE
    # Coverage is heavily weighted (50%), Text integrity (35%), Gutter alignment (15%)
    composite_score = 0.50 * coverage_score + 0.35 * text_integrity_score + 0.15 * gutter_score

    grade = "PASS" if composite_score >= 88.0 else ("WARNING" if composite_score >= 65.0 else "FAIL")

    return {
        "page": os.path.basename(page_image_path),
        "panels_extracted": len(panel_bboxes),
        "coverage_score": round(coverage_score, 1),
        "text_integrity_score": round(text_integrity_score, 1),
        "gutter_score": round(gutter_score, 1),
        "composite_score": round(composite_score, 1),
        "grade": grade,
        "cut_violations_count": len(cut_violations),
        "violations": cut_violations[:5]
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate panel extraction quality.")
    parser.add_argument("--page", default=None, help="Evaluate a single page")
    parser.add_argument("--batch", action="store_true", help="Evaluate all 25 pages")
    parser.add_argument("--fast", action="store_true", help="Fast coverage evaluation without OCR")
    parser.add_argument("--manifest", default="output/Challenges_of_Doom_Spider-Man_001/manifest.json")
    parser.add_argument("--pages-dir", default="data/spider_man_001/pages")
    args = parser.parse_args()

    with open(args.manifest) as f:
        manifest = json.load(f)

    if args.batch:
        reader = None if args.fast else easyocr.Reader(['en'], gpu=False)
        pages = sorted([f for f in os.listdir(args.pages_dir) if f.startswith("page_") and f.endswith(".jpg")])
        
        print("\n" + "=" * 78)
        print("📊 BATCH EXTRACTION EVALUATION AUDIT ACROSS ALL PAGES")
        print("=" * 78)
        print(f"{'Page':<10} | {'Panels':<8} | {'Coverage':<10} | {'Text Int.':<10} | {'Score':<8} | {'Grade':<8}")
        print("-" * 78)

        total_pass = 0
        total_warn = 0
        total_fail = 0

        for p_file in pages:
            p_num = int(p_file.split("_")[1].split(".")[0])
            p_path = os.path.join(args.pages_dir, p_file)
            bboxes = [p["bbox"] for p in manifest["panels"] if p["page_number"] == p_num]

            if args.fast:
                img = cv2.imread(p_path)
                h, w = img.shape[:2]
                mask = np.zeros((h, w), dtype=np.uint8)
                for bx, by, bw, bh in bboxes:
                    mask[by:by+bh, bx:bx+bw] = 255
                c_y1, c_y2 = 60, h - 60
                row_cov = np.mean(mask[c_y1:c_y2, :] > 0, axis=1)
                cov = float(np.mean(row_cov > 0.5) * 100.0)
                score = cov
                grade = "PASS" if score >= 88.0 else ("WARNING" if score >= 65.0 else "FAIL")
                text_int = 100.0
            else:
                rep = evaluate_page_extraction(p_path, bboxes, reader=reader)
                cov = rep['coverage_score']
                text_int = rep['text_integrity_score']
                score = rep['composite_score']
                grade = rep['grade']

            if grade == "PASS":
                total_pass += 1
                badge = "✅ PASS"
            elif grade == "WARNING":
                total_warn += 1
                badge = "⚠️ WARN"
            else:
                total_fail += 1
                badge = "❌ FAIL"

            print(f"{p_file:<10} | {len(bboxes):<8} | {cov:>8.1f}% | {text_int:>8.1f}% | {score:>7.1f}% | {badge}")

        print("=" * 78)
        print(f"Summary: {total_pass}/{len(pages)} Passed ({total_pass/len(pages)*100:.1f}%), {total_warn} Warnings, {total_fail} Fails.")
        print("=" * 78)

    else:
        target_page = args.page or "data/spider_man_001/pages/page_03.jpg"
        page_num = int(os.path.basename(target_page).split("_")[1].split(".")[0])
        bboxes = [p["bbox"] for p in manifest["panels"] if p["page_number"] == page_num]
        report = evaluate_page_extraction(target_page, bboxes)
        print("\n" + "=" * 60)
        print(f"📊 EXTRACTION EVALUATION REPORT: {report['page']}")
        print("=" * 60)
        print(f"  Panels Extracted:       {report['panels_extracted']}")
        print(f"  Page Coverage Score:    {report['coverage_score']}%")
        print(f"  Text Integrity Score:   {report['text_integrity_score']}%")
        print(f"  Gutter Alignment Score: {report['gutter_score']}%")
        print(f"  Overall Composite Score:{report['composite_score']} / 100")
        print(f"  Status / Grade:         [{report['grade']}]")
        if report['violations']:
            print("\n  ❌ Sliced/Clipped Text Samples:")
            for v in report['violations']:
                print(f"     - \"{v['text']}\" at {v['bbox']}")
        print("=" * 60)
