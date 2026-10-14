import os
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

image_file = BASE_DIR / "assets" / "paoguo_hero.png"
prompt_file = BASE_DIR / "prompts" / "paoguo_h3.txt"
output_video = OUTPUTS_DIR / "paoguo_minimax_h3.mp4"

os.environ["H3_DURATION_SECONDS"] = "6"
os.environ["COLAB_GPU"] = "A100"

print("=" * 65)
print("[MiniMax H3] 啟動 MiniMax H3 Turbo Ref2VA 影音生成流水線 (泡果產品介紹)")
print(f"  參考圖片: {image_file}")
print(f"  提示詞: {prompt_file}")
print(f"  輸出目標: {output_video}")
print(f"  時長: 6 秒 (約 148 幀 @ 24fps)")
print(f"  GPU 規格: Colab A100 (High-Mem)")
print("=" * 65)

cmd = [
    sys.executable,
    str(BASE_DIR / "minimax_h3" / "scripts" / "runner.py"),
    "single",
    "--image", str(image_file),
    "--prompt", str(prompt_file),
    "--output", str(output_video),
    "--gpu", "A100",
    "--timeout", "3600"
]

print("正在調度 Google Colab A100 GPU 執行 MiniMax H3 推論...")
res = subprocess.run(cmd)

if res.returncode != 0:
    print(f"\n❌ MiniMax H3 推論失敗 (代碼 {res.returncode})")
    sys.exit(res.returncode)

if output_video.exists():
    size_mb = round(output_video.stat().st_size / (1024 * 1024), 2)
    print("\n" + "=" * 65)
    print("🎉 MiniMax H3 泡果介紹影片生成成功！")
    print(f"  成品路徑: {output_video} ({size_mb} MB)")
    print("=" * 65)
    
    # 探測音訊與視訊串流
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate,duration", "-of", "json", str(output_video)],
            capture_output=True,
            text=True
        )
        print("  媒體規格:")
        import json
        info = json.loads(probe.stdout)
        for s in info.get("streams", []):
            print(f"    - 串流 [{s.get('codec_type')}]: {s.get('width', '')}x{s.get('height', '')} @ {s.get('r_frame_rate', '')} (長度 {s.get('duration', '')}s)")
    except Exception as e:
        print(f"  ffprobe 探測略過: {e}")

    if sys.platform == "win32":
        try:
            subprocess.run(["explorer.exe", f"/select,{str(output_video)}"])
            print("已在 Windows 檔案總管中為您打開並選取 MiniMax H3 影片！")
        except Exception as e:
            print(f"檔案總管開啟略過: {e}")
else:
    print(f"❌ 未找到輸出檔案: {output_video}")
    sys.exit(1)
