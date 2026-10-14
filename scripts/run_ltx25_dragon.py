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

os.environ["REQUEST_TIMEOUT"] = "300"
image_file = BASE_DIR / "assets" / "golden_dragon.png"
output_video = OUTPUTS_DIR / "golden_dragon_ltx25_22b.mp4"

prompt = (
    "A colossal oriental golden giant dragon surging forward through thunderous storm clouds and vivid lightning, "
    "opening its massive jaws and roaring ferociously with blinding golden energy, whiskers and fiery mane billowing in the violent tempest, "
    "intricate glistening gold scales, fierce glowing amber eyes, dynamic cinematic motion, cinematic fantasy masterpiece"
)

print("=" * 65)
print("[LTX-2.5 22B] 啟動旗艦級 22B Dual-Stream DiT 影音同步生成流水線")
print(f"  模型: Lightricks/LTX-2.5 (22B Distilled Transformer + Gemma 4 12B)")
print(f"  參考圖片: {image_file}")
print(f"  提示詞: {prompt}")
print(f"  輸出目標: {output_video}")
print(f"  時長: 121 幀 (約 5.04 秒 @ 24fps)")
print(f"  GPU 規格: Colab A100 (High-Mem)")
print("=" * 65)

cmd = [
    sys.executable,
    str(BASE_DIR / "scripts" / "runner.py"),
    "single",
    "--image", str(image_file),
    "--prompt", prompt,
    "--output", str(output_video),
    "--gpu", "A100",
    "--num-frames", "121",
    "--seed", "42",
    "--timeout", "3600"
]

print("\n正在調度 Google Colab A100 執行 LTX-2.5 22B 推論...")
print("（包含官方 66GB 核心權重下載、uv 虛擬環境同調與雙階段超解析生成）\n")

res = subprocess.run(cmd)

if res.returncode != 0:
    print(f"\n❌ LTX-2.5 22B 推論失敗 (結束代碼 {res.returncode})")
    sys.exit(res.returncode)

if output_video.exists():
    size_mb = round(output_video.stat().st_size / (1024 * 1024), 2)
    print("\n" + "=" * 65)
    print("🎉 LTX-2.5 22B 影片生成成功！")
    print(f"  成品路徑: {output_video} ({size_mb} MB)")
    print("=" * 65)
    
    # 探測音訊與視訊串流
    try:
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height,r_frame_rate", "-of", "json", str(output_video)],
            capture_output=True,
            text=True
        )
        print("  媒體規格:")
        import json
        info = json.loads(probe.stdout)
        for s in info.get("streams", []):
            print(f"    - 串流 [{s.get('codec_type')}]: {s.get('width', '')}x{s.get('height', '')} @ {s.get('r_frame_rate', '')}")
    except Exception as e:
        print(f"  ffprobe 探測略過: {e}")

    if sys.platform == "win32":
        try:
            subprocess.run(["explorer.exe", f"/select,{str(output_video)}"])
            print("已在 Windows 檔案總管中為您打開並選取 LTX-2.5 22B 影片！")
        except Exception as e:
            print(f"檔案總管開啟略過: {e}")
else:
    print(f"\n❌ 未找到輸出檔案: {output_video}")
    sys.exit(1)
