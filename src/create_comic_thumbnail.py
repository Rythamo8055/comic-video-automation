#!/usr/bin/env python3
"""
create_comic_thumbnail.py
Generates a high-CTR, 1080p YouTube thumbnail using the comic cover with
large, stylized comic book typography: 'PART 1'.
"""

import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

def draw_text_with_outline(draw, pos, text, font, fill_color, outline_color, outline_width=8, shadow_offset=(8, 8), shadow_color=(0, 0, 0, 220)):
    x, y = pos
    
    # 1. Drop shadow
    sx, sy = x + shadow_offset[0], y + shadow_offset[1]
    for ox in range(-outline_width, outline_width + 1):
        for oy in range(-outline_width, outline_width + 1):
            draw.text((sx + ox, sy + oy), text, font=font, fill=shadow_color)
            
    # 2. Black outline
    for ox in range(-outline_width, outline_width + 1):
        for oy in range(-outline_width, outline_width + 1):
            if ox != 0 or oy != 0:
                draw.text((x + ox, y + oy), text, font=font, fill=outline_color)
                
    # 3. Main fill text
    draw.text((x, y), text, font=font, fill=fill_color)

def generate_thumbnail(
    cover_path,
    output_path="output/thumbnail_part_1.jpg",
    part_text="PART 1",
    subhook_text="THE SPIDER-MAN TRAP",
    callout_text="⚡ WAIT FOR PART 2 COMING NEXT!"
):
    out_w, out_h = 1920, 1080
    
    cover = Image.open(cover_path).convert("RGB")
    cw, ch = cover.size
    
    # Scale cover to dramatically fill the canvas
    scale = max(out_w / cw, out_h / ch) * 1.15
    nw, nh = int(cw * scale), int(ch * scale)
    cover_resized = cover.resize((nw, nh), Image.Resampling.LANCZOS)
    
    # Position: shift slightly right to give text room on the left
    offset_x = (out_w - nw) // 2 + 120
    offset_y = (out_h - nh) // 2
    
    canvas = Image.new("RGB", (out_w, out_h), (15, 20, 28))
    canvas.paste(cover_resized, (offset_x, offset_y))
    
    # Apply cinematic vignette / dark gradient overlay on the left for text contrast
    gradient = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(gradient)
    for x in range(out_w):
        # Darkness fades from left (85% dark) to right (0% dark)
        alpha = int(max(0, 230 * (1.0 - (x / (out_w * 0.75)))))
        g_draw.line([(x, 0), (x, out_h)], fill=(10, 15, 25, alpha))
    
    # Bottom vignette for badges
    for y in range(out_h - 220, out_h):
        alpha = int(200 * ((y - (out_h - 220)) / 220))
        g_draw.line([(0, y), (out_w, y)], fill=(10, 15, 25, alpha))
        
    canvas.paste(gradient, (0, 0), gradient)
    
    # Fonts
    font_path = "/usr/share/fonts/julietaula-montserrat-fonts/Montserrat-Bold.otf"
    if not os.path.exists(font_path):
        font_path = "/usr/share/fonts/google-droid-sans-fonts/DroidSans-Bold.ttf"
        
    font_title = ImageFont.truetype(font_path, 170 if len(part_text) <= 6 else 140)
    font_badge = ImageFont.truetype(font_path, 52)
    font_sub = ImageFont.truetype(font_path, 40)
    
    draw = ImageDraw.Draw(canvas)
    
    # 1. Top Category Badge: "CHALLENGES OF DOOM"
    badge_bg = (230, 36, 41)  # Marvel Red
    draw.rounded_rectangle([70, 75, 780, 155], radius=12, fill=badge_bg, outline=(255, 255, 255), width=3)
    draw.text((95, 87), "CHALLENGES OF DOOM", font=font_badge, fill=(255, 255, 255))
    
    # 2. Main High-Impact Typography
    draw_text_with_outline(
        draw=draw,
        pos=(70, 185),
        text=part_text,
        font=font_title,
        fill_color=(255, 222, 0),
        outline_color=(0, 0, 0),
        outline_width=12,
        shadow_offset=(12, 12)
    )
    
    # 3. Sub-hook
    draw_text_with_outline(
        draw=draw,
        pos=(75, 410),
        text=subhook_text,
        font=ImageFont.truetype(font_path, 58),
        fill_color=(255, 255, 255),
        outline_color=(0, 0, 0),
        outline_width=6,
        shadow_offset=(6, 6)
    )
    
    # 4. Bottom Banner
    if callout_text:
        callout_bg = (255, 222, 0)
        draw.rounded_rectangle([70, 920, 920, 1005], radius=16, fill=callout_bg, outline=(0, 0, 0), width=4)
        draw.text((95, 935), callout_text, font=font_sub, fill=(10, 10, 10))
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    canvas.save(output_path, quality=95)
    print(f"[+] 1080p High-Impact Thumbnail Created: {output_path} ({out_w}x{out_h})")
    return output_path

if __name__ == "__main__":
    cover = "output/Challenges_of_Doom_Spider-Man_001/panel_001_p01_01.png"
    out = "output/thumbnail_part_1.jpg"
    generate_thumbnail(cover, out)
