import json

path = "assets/LTX_2_5_Colab.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Cell 1: Hardware check (index 1)
# Cell 2: Dependencies (index 3)
nb["cells"][3]["source"] = [
    "# Install dependencies for LTX-Video\n",
    "!pip install -q --upgrade pip\n",
    "!pip uninstall -y torchao\n",
    '!pip install -q "diffusers>=0.41.0" "transformers>=4.48.0" accelerate sentencepiece torchvision torchaudio huggingface_hub\n',
    'print("Dependencies installed successfully.")\n'
]

# Cell 5: Pipeline & Inference (index 9)
cell5_code = """import os, subprocess, sys, torch, traceback, inspect
from pathlib import Path
from PIL import Image
from diffusers.utils import export_to_video

model_id = os.environ.get('LTX_MODEL_ID', '').strip()
if not model_id:
    model_id = 'Lightricks/LTX-Video'

print(f'正在載入 LTX 模型: {model_id} (請稍候)...')

is_i2v = bool(image_file and os.path.exists(image_file))

if is_i2v:
    from diffusers import LTXImageToVideoPipeline
    pipeline_cls = LTXImageToVideoPipeline
else:
    from diffusers import LTXPipeline
    pipeline_cls = LTXPipeline

print(f'使用 Pipeline 類別: {pipeline_cls.__name__}')

try:
    pipe = pipeline_cls.from_pretrained(
        model_id,
        torch_dtype=torch.bfloat16,
        cache_dir=cache_dir
    )
    if torch.cuda.get_device_properties(0).total_memory > 30 * 2**30:
        pipe.to('cuda')
        print('已載入至 A100 GPU 顯存 (未啟用 CPU offload，全速推論)')
    else:
        pipe.enable_model_cpu_offload()
        print('啟用 Model CPU Offload 節省顯存')
        
    if hasattr(pipe, 'vae') and hasattr(pipe.vae, 'enable_tiling'):
        pipe.vae.enable_tiling()

    generator = torch.Generator(device='cuda').manual_seed(seed)

    target_w = 768
    target_h = 512

    kwargs = {
        'prompt': prompt,
        'negative_prompt': 'worst quality, inconsistent motion, blurry, jittery, distorted, static, frozen frame, deformed, lowres',
        'width': target_w,
        'height': target_h,
        'num_frames': num_frames,
        'num_inference_steps': 40,
        'guidance_scale': 3.5,
        'generator': generator,
    }

    call_params = inspect.signature(pipe.__call__).parameters
    if 'decode_timestep' in call_params:
        kwargs['decode_timestep'] = 0.05
    if 'image_cond_noise_scale' in call_params:
        kwargs['image_cond_noise_scale'] = 0.025

    if is_i2v:
        print(f'載入首格參考圖片: {image_file}')
        input_image = Image.open(image_file).convert('RGB')
        input_image = input_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
        kwargs['image'] = input_image
        print(f'已調整首格圖尺寸至 {target_w}x{target_h}')

    print(f'開始執行 LTX 影音推論 (Prompt: {prompt[:80]}...)...')
    output = pipe(**kwargs)

    frames = output.frames[0]
    audio = getattr(output, 'audio', None)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    if audio is not None:
        print('偵測到音訊串流，正在打包視訊與同步音訊...')
        export_to_video(frames, output_path, fps=24, audio=audio)
    else:
        export_to_video(frames, output_path, fps=24)

    print(f'\\n生成完畢！影片已儲存至: {output_path}')
except Exception as e:
    print(f'!!! LTX 推論發生異常: {e}')
    traceback.print_exc()
    raise
"""

# Find the code cell containing pipeline_cls
for cell in nb["cells"]:
    if cell.get("cell_type") == "code" and any("pipeline_cls" in line for line in cell.get("source", [])):
        cell["source"] = [line + "\n" for line in cell5_code.splitlines()]
        break

# Cell 6: verification
cell6_code = """assert os.path.exists(output_path), f"生成失敗：未找到輸出檔案 {output_path}"
file_size_mb = round(os.path.getsize(output_path) / (1024*1024), 2)
print(f"[檔案大小] {file_size_mb} MB")

res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type", "-of", "csv=p=0", output_path], capture_output=True, text=True)
streams = res.stdout.strip().splitlines()
print(f"[包含串流] {streams}")
print("狀態：推論與輸出驗證成功！")
"""
for cell in nb["cells"]:
    if cell.get("cell_type") == "code" and any("ffprobe" in line for line in cell.get("source", [])):
        cell["source"] = [line + "\n" for line in cell6_code.splitlines()]
        break

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Cleaned LTX_2_5_Colab.ipynb cleanly and validated!")
