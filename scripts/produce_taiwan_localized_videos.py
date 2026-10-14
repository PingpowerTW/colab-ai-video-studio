# -*- coding: utf-8 -*-
"""
Produce fully localized Taiwanese commercial videos for Paoguo:
1. 100% Traditional Chinese on-screen titles & subtitle overlays (繁體中文字幕與品牌標章)
2. Authentic Taiwanese Mandarin Neural Voiceover (台灣口音說話方式)
3. Background music ducking + audio mix
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parents[1]
ASSETS_DIR = BASE_DIR / "assets"
OUTPUTS_DIR = BASE_DIR / "outputs"
TTS_DIR = ASSETS_DIR / "tts_audio"
TTS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH_TITLE = "C:/Windows/Fonts/msjhbd.ttc"
FONT_PATH_KAI = "C:/Windows/Fonts/kaiu.ttf"

def create_traditional_chinese_overlay(width: int, height: int, out_path: Path):
    """Create high-contrast, professional Traditional Chinese commercial overlay"""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 字體大小動態調整
    font_badge = ImageFont.truetype(FONT_PATH_TITLE, int(height * 0.038))
    font_main = ImageFont.truetype(FONT_PATH_TITLE, int(height * 0.052))
    font_sub = ImageFont.truetype(FONT_PATH_TITLE, int(height * 0.032))
    
    # 1. 頂部品牌標章：【屏東黎明村手作】醋溜泡果
    badge_text = "【屏東黎明村】手作醋溜泡果"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw, bh = bbox_b[2] - bbox_b[0], bbox_b[3] - bbox_b[1]
    bx0, by0 = int(width * 0.04), int(height * 0.05)
    pad_x, pad_y = int(height * 0.024), int(height * 0.014)
    
    # 綠金色調圓角卡片底板
    draw.rounded_rectangle(
        [bx0, by0, bx0 + bw + pad_x * 2, by0 + bh + pad_y * 2],
        radius=int(height * 0.015),
        fill=(18, 48, 25, 235),
        outline=(245, 195, 55, 245),
        width=3
    )
    draw.text((bx0 + pad_x, by0 + pad_y - 2), badge_text, font=font_badge, fill=(255, 255, 255, 255))
    
    # 2. 底部字幕橫幅卡
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
    
    # 深墨綠近黑底板 + 琥珀金邊框
    draw.rounded_rectangle(
        [banner_x0, banner_y, banner_x1, banner_y + banner_h],
        radius=int(height * 0.02),
        fill=(10, 16, 12, 230),
        outline=(245, 190, 50, 235),
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
    
    img.save(str(out_path))
    print(f"  已生成繁體中文透明圖層: {out_path} ({width}x{height})")


async def generate_taiwan_voices():
    """使用微軟繁體中文台灣神經語音生成自然道地口音"""
    print("\n[語音生成] 正在生成道地台灣國語配音 (zh-TW-HsiaoChenNeural)...")
    
    # 針對 LTX-2.5 (時長約 5.04 秒)
    # 語速稍微活潑輕快，精確貼合 4.7~4.9 秒
    text_ltx = "你敢信？這酸爽清脆的芒果青，居然是鹹的！"
    comm_ltx = edge_tts.Communicate(text_ltx, "zh-TW-HsiaoChenNeural", rate="+8%")
    out_ltx_voice = TTS_DIR / "paoguo_tw_ltx.mp3"
    await comm_ltx.save(str(out_ltx_voice))
    print(f"  LTX 配音生成完成: {out_ltx_voice}")
    
    # 針對 MiniMax H3 (時長約 6.58 秒)
    # 完整產品介紹與讚嘆口吻
    text_h3 = "你敢信？這酸爽清脆的芒果青居然是鹹的！越吃越涮嘴喔！"
    comm_h3 = edge_tts.Communicate(text_h3, "zh-TW-HsiaoChenNeural", rate="+10%")
    out_h3_voice = TTS_DIR / "paoguo_tw_h3.mp3"
    await comm_h3.save(str(out_h3_voice))
    print(f"  MiniMax H3 配音生成完成: {out_h3_voice}")


def render_composite(raw_video: Path, overlay_png: Path, voice_audio: Path, output_video: Path):
    """將原影片、繁體中文字幕圖層、台灣口音配音與背景音樂混音整合"""
    bgm_path = ASSETS_DIR / "bgm_acoustic.wav"
    
    # 測量視訊長度
    probe_v = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(raw_video)],
        capture_output=True, text=True
    )
    v_dur = float(json.loads(probe_v.stdout)["format"]["duration"])
    
    print(f"\n[影音合成] 正在處理 {output_video.name} (時長: {v_dur:.2f}s)...")
    
    # 混音邏輯：
    # 1. 視訊上疊加透明字幕圖層
    # 2. 配音 (voice) 音量放大 1.25 倍
    # 3. 襯底 BGM 音量調降至 0.15 (輕快不搶話)，結尾 1 秒淡出
    fade_start = max(0.0, v_dur - 1.0)
    filter_complex = (
        f"[0:v][1:v]overlay=0:0[vout];"
        f"[2:a]volume=1.3[vo];"
        f"[3:a]volume=0.15,afade=t=out:st={fade_start:.2f}:d=1.0[bgm];"
        f"[vo][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(raw_video),
        "-i", str(overlay_png),
        "-i", str(voice_audio),
        "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "[vout]",
        "-map", "[aout]",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", f"{v_dur:.2f}",
        "-movflags", "+faststart",
        str(output_video)
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    size_mb = round(output_video.stat().st_size / (1024 * 1024), 2)
    print(f"🎉 合成完成: {output_video} ({size_mb} MB)")


async def main():
    print("=" * 65)
    print("🎬 開始製作「黎明村手作醋溜泡果」全繁體中文 + 台灣在地配音影片")
    print("=" * 65)
    
    # Step 1: 生成繁體中文透明圖層
    overlay_ltx = ASSETS_DIR / "overlay_ltx_1536x1024.png"
    overlay_h3 = ASSETS_DIR / "overlay_h3_1376x768.png"
    create_traditional_chinese_overlay(1536, 1024, overlay_ltx)
    create_traditional_chinese_overlay(1376, 768, overlay_h3)
    
    # Step 2: 生成台灣在地語音配音
    await generate_taiwan_voices()
    
    # Step 3: 合成 LTX-2.5 影片 (解決原影片吵雜與無配音問題)
    raw_ltx = OUTPUTS_DIR / "paoguo_ltx25_22b.mp4"
    out_ltx = OUTPUTS_DIR / "paoguo_ltx25_taiwan.mp4"
    voice_ltx = TTS_DIR / "paoguo_tw_ltx.mp3"
    render_composite(raw_ltx, overlay_ltx, voice_ltx, out_ltx)
    
    # Step 4: 合成 MiniMax H3 影片 (解決原影片大陸口音問題)
    raw_h3 = OUTPUTS_DIR / "paoguo_minimax_h3.mp4"
    out_h3 = OUTPUTS_DIR / "paoguo_minimax_taiwan.mp4"
    voice_h3 = TTS_DIR / "paoguo_tw_h3.mp3"
    render_composite(raw_h3, overlay_h3, voice_h3, out_h3)
    
    print("\n" + "=" * 65)
    print("🎉 兩部台灣在地化（全繁體中文 + 台灣口音配音）影片全部製作完成！")
    print(f"  1. LTX-2.5 (1.5K 超清): {out_ltx}")
    print(f"  2. MiniMax H3 (電商動態): {out_h3}")
    print("=" * 65)
    
    if sys.platform == "win32":
        try:
            subprocess.run(["explorer.exe", f"/select,{str(out_ltx)}"])
            print("已在 Windows 檔案總管中為您打開並選取影片！")
        except Exception as e:
            print(f"檔案總管略過: {e}")

if __name__ == "__main__":
    asyncio.run(main())
