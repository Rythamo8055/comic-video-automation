#!/usr/bin/env python3
"""
slice_all_panels_precise.py - Precision panel slicer for Spider-Man: Challenges of Doom #001.
Slices each page into its exact individual narrative panels (P1, P2, P3...) so the camera
travels from panel to panel as the story flows.
"""

import os
import cv2
import numpy as np

def slice_precise_panels():
    pages_dir = "data/spider_man_001/pages"
    out_dir = "data/spider_man_001/precise_panels"
    os.makedirs(out_dir, exist_ok=True)

    # Page specific panel bounding boxes (normalized or exact coordinates)
    # Page 1: Cover (Full splash)
    # Page 2: Lore (Full recap page)
    # Page 3: 2 Panels (Top: FF chess pieces, Bottom: Spider piece knocks Reed)
    # Page 4: 3 Panels (Top: Peter on ceiling, Mid: Thwip, Bottom: Thud into lamp)
    # Page 5: 5 Panels (P1: Oh boy Thwip, P2: Lamp falling, P3: Catching lamp, P4: Bed monologue, P5: Spider-Sense headache!)
    
    pages = sorted([f for f in os.listdir(pages_dir) if f.startswith("page_") and f.endswith(".jpg")])
    total_panels = 0

    for p_file in pages:
        p_num = int(p_file.split("_")[1].split(".")[0])
        img = cv2.imread(os.path.join(pages_dir, p_file))
        h, w = img.shape[:2]

        if p_num == 1:
            # Full Cover
            cv2.imwrite(os.path.join(out_dir, "p01_panel_1.png"), img)
            total_panels += 1

        elif p_num == 2:
            # Lore Recap Page
            cv2.imwrite(os.path.join(out_dir, "p02_panel_1.png"), img)
            total_panels += 1

        elif p_num == 3:
            # Page 3: Two distinct widescreen panels
            # Panel 1: Top (FF Chess Pieces)
            # Panel 2: Bottom (Spider Piece)
            p1 = img[70:1530, 40:w-40]
            p2 = img[1550:3000, 40:w-40]
            cv2.imwrite(os.path.join(out_dir, "p03_panel_1.png"), p1)
            cv2.imwrite(os.path.join(out_dir, "p03_panel_2.png"), p2)
            total_panels += 2

        elif p_num == 4:
            # Page 4: Three tiers
            # P1: Peter on ceiling with web-shooters
            # P2: Peter shooting web ball (Thwip!)
            # P3: Lamp knocked over (Thud!)
            p1 = img[70:1750, 40:w-40]
            p2 = img[1760:2450, 40:w-40]
            p3 = img[2460:3000, 40:w-40]
            cv2.imwrite(os.path.join(out_dir, "p04_panel_1.png"), p1)
            cv2.imwrite(os.path.join(out_dir, "p04_panel_2.png"), p2)
            cv2.imwrite(os.path.join(out_dir, "p04_panel_3.png"), p3)
            total_panels += 3

        elif p_num == 5:
            # Page 5: Five distinct panels
            # Tier 1: 3 panels across (P1: Left Peter hand, P2: Mid falling lamp, P3: Right catch)
            # Tier 2: P4 Wide Peter on bed
            # Tier 3: P5 Spider-Sense headache!
            t1_y1, t1_y2 = 80, 1020
            p1 = img[t1_y1:t1_y2, 40:650]       # Thwip hand
            p2 = img[t1_y1:t1_y2, 660:1280]     # Falling lamp
            p3 = img[t1_y1:t1_y2, 1290:w-40]    # Catching lamp
            p4 = img[1040:1920, 40:w-40]        # Bed monologue
            p5 = img[1930:3000, 40:w-40]        # SPIDER-MAN! Headache!
            cv2.imwrite(os.path.join(out_dir, "p05_panel_1.png"), p1)
            cv2.imwrite(os.path.join(out_dir, "p05_panel_2.png"), p2)
            cv2.imwrite(os.path.join(out_dir, "p05_panel_3.png"), p3)
            cv2.imwrite(os.path.join(out_dir, "p05_panel_4.png"), p4)
            cv2.imwrite(os.path.join(out_dir, "p05_panel_5.png"), p5)
            total_panels += 5

        elif p_num == 13:
            # Page 13: Double-Page Spread (Left half vs Right half vs Full Spread)
            cv2.imwrite(os.path.join(out_dir, "p13_spread_full.png"), img)
            # Sub-panel close ups
            p_left = img[:, :w//2]
            p_right = img[:, w//2:]
            cv2.imwrite(os.path.join(out_dir, "p13_panel_left.png"), p_left)
            cv2.imwrite(os.path.join(out_dir, "p13_panel_right.png"), p_right)
            total_panels += 3

        else:
            # Standard comic grid detection or half tiers
            p_top = img[70:h//2, 40:w-40]
            p_bottom = img[h//2:h-70, 40:w-40]
            cv2.imwrite(os.path.join(out_dir, f"p{p_num:02d}_panel_1.png"), p_top)
            cv2.imwrite(os.path.join(out_dir, f"p{p_num:02d}_panel_2.png"), p_bottom)
            total_panels += 2

    print(f"Successfully sliced {total_panels} individual panels into {out_dir}")

if __name__ == "__main__":
    slice_precise_panels()
