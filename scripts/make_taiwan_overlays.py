# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

def create_overlay(width: int, height: int, out_path: str):
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    font_path = "C:/Windows/Fonts/msjhbd.ttc"
    font_main = ImageFont.truetype(font_path, int(height * 0.052))
    font_sub = ImageFont.truetype(font_path, int(height * 0.033))
    font_badge = ImageFont.truetype(font_path, int(height * 0.036))
    
    # 頂部品牌標章：【屏東黎明村】手作醋溜泡果
    badge_text = "【屏東黎明村】手作醋溜泡果"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox_b[2] - bbox_b[0], bbox_b[3] - bbox_b[1]
    bx0, by0 = int(width * 0.04), int(height * 0.05)
    pad_x, pad_y = int(height * 0.025), int(height * 0.015)
    
    # 綠金配色的品牌標章底色
    draw.rounded_rectangle(
        [bx0, by0, bx0 + bw + pad_x * 2, by0 + bh + pad_y * 2],
        radius=int(height * 0.016),
        fill=(20, 52, 28, 230),
        outline=(240, 195, 60, 245),
        width=3
    )
    draw.text((bx0 + pad_x, by0 + pad_y - 2), badge_text, font=font_badge, fill=(255, 255, 255, 255))
    
    # 底部字幕卡
    text_main = "你敢信？這酸爽清脆的芒果青，居然是「鹹」的！"
    text_sub = "在地鮮採青芒果 · 純天然醋醃開胃 · 越吃越涮嘴"
    
    bbox_m = draw.textbbox((0, 0), text_main, font=font_main)
    mw, mh = bbox_m[2] - bbox_m[0], bbox_m[3] - bbox_m[1]
    
    bbox_s = draw.textbbox((0, 0), text_sub, font=font_sub)
    sw, sh = bbox_s[2] - bbox_s[0], bbox_s[3] - bbox_s[1]
    
    banner_h = int(height * 0.165)
    banner_y = height - banner_h - int(height * 0.04)
    banner_x0 = int(width * 0.035)
    banner_x1 = width - banner_x0
    
    # 半透明深墨綠黑色卡片底板，搭配金色邊框
    draw.rounded_rectangle(
        [banner_x0, banner_y, banner_x1, banner_y + banner_h],
        radius=int(height * 0.022),
        fill=(10, 16, 12, 225),
        outline=(245, 195, 50, 230),
        width=3
    )
    
    # 主字幕：金黃琥珀色帶陰影
    mx = (width - mw) // 2
    my = banner_y + int(banner_h * 0.16)
    draw.text((mx + 2, my + 2), text_main, font=font_main, fill=(0, 0, 0, 220))
    draw.text((mx, my), text_main, font=font_main, fill=(255, 230, 80, 255))
    
    # 副標：溫暖米白色
    sx = (width - sw) // 2
    sy = my + mh + int(banner_h * 0.15)
    draw.text((sx + 1, sy + 1), text_sub, font=font_sub, fill=(0, 0, 0, 200))
    draw.text((sx, sy), text_sub, font=font_sub, fill=(245, 245, 235, 245))
    
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    print(f"Generated clean Traditional Chinese overlay: {out_path} ({width}x{height})")

if __name__ == "__main__":
    create_overlay(1536, 1024, "assets/overlay_ltx_1536x1024.png")
    create_overlay(1376, 768, "assets/overlay_h3_1376x768.png")
