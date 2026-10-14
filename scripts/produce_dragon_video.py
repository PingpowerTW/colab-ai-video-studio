import os
import subprocess
import sys
import shutil
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

raw_video = OUTPUTS_DIR / "golden_dragon_ltx_raw.mp4"
final_video = OUTPUTS_DIR / "golden_dragon_final.mp4"
final_1080p = OUTPUTS_DIR / "golden_dragon_final_1080p.mp4"
audio_file = BASE_DIR / "assets" / "audio" / "dragon_roar_wind.wav"
image_file = BASE_DIR / "assets" / "golden_dragon.png"

prompt = (
    "A colossal oriental golden giant dragon lunging forward through thunderous stormy clouds and vivid lightning, "
    "opening its massive jaws and roaring with blinding golden energy, whiskers and mane billowing in fierce gale winds, "
    "intricate glistening golden scales, dynamic cinematic motion, epic fantasy masterpiece"
)

print("=" * 60)
print("[LTX Pipeline] 啟動一條龍金龍咆哮 LTX 影音生成流水線 (Colab A100)")
print("=" * 60)

# 1. 執行 Colab 推論
cmd = [
    sys.executable,
    str(BASE_DIR / "scripts" / "runner.py"),
    "single",
    "--prompt", prompt,
    "--image", str(image_file),
    "--output", str(raw_video),
    "--gpu", "A100",
    "--num-frames", "97",
    "--seed", "42"
]

print(f"正在調度 Colab A100 推論...")
res = subprocess.run(cmd)
if res.returncode != 0:
    print(f"Colab 推論失敗 (代碼 {res.returncode})")
    sys.exit(res.returncode)

if not raw_video.exists():
    print(f"未找到 raw video: {raw_video}")
    sys.exit(1)

print("\n" + "=" * 60)
print("[Post-process] 正在進行影音同步混音與 1080p 高畫質轉碼...")
print("=" * 60)

# 2. 原生解析度混音
cmd_mux_native = [
    "ffmpeg", "-y",
    "-i", str(raw_video),
    "-i", str(audio_file),
    "-filter_complex", "[1:a]afade=t=out:st=3.5:d=0.54[a]",
    "-map", "0:v", "-map", "[a]",
    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
    "-c:a", "aac", "-b:a", "192k",
    "-movflags", "+faststart",
    "-shortest",
    str(final_video)
]
subprocess.run(cmd_mux_native, check=True)

# 3. 1080p 超解析混音 (Lanczos scaling + faststart)
cmd_mux_1080p = [
    "ffmpeg", "-y",
    "-i", str(raw_video),
    "-i", str(audio_file),
    "-filter_complex", "[0:v]scale=1920:1080:flags=lanczos[v];[1:a]afade=t=out:st=3.5:d=0.54[a]",
    "-map", "[v]", "-map", "[a]",
    "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
    "-c:a", "aac", "-b:a", "256k",
    "-movflags", "+faststart",
    "-shortest",
    str(final_1080p)
]
subprocess.run(cmd_mux_1080p, check=True)

print("\n" + "=" * 60)
print("[Done] 生成與轉碼成功！")
print(f"  原生版: {final_video} ({round(final_video.stat().st_size / 1024 / 1024, 2)} MB)")
print(f"  1080p版: {final_1080p} ({round(final_1080p.stat().st_size / 1024 / 1024, 2)} MB)")
print("=" * 60)

# 4. 在 Windows 中自動彈出檔案總管並選取該影片
if sys.platform == "win32":
    try:
        subprocess.run(["explorer.exe", f"/select,{str(final_1080p)}"])
        print("已在 Windows 檔案總管中為您打開並選取影片！")
    except Exception as e:
        print(f"自動打開檔案總管略過: {e}")
