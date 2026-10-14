#!/usr/bin/env python3
"""
LTX-2.5 Colab Video Automation Runner
Cross-platform dispatcher for orchestrating LTX-2.5 inference on Google Colab from Windows/macOS/Linux.
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Callable

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_NOTEBOOK = BASE_DIR / "assets" / "LTX_2_5_Colab.ipynb"
DEFAULT_FLUX_NOTEBOOK = BASE_DIR / "assets" / "FLUX_Colab.ipynb"
DEFAULT_IDEOGRAM_NOTEBOOK = BASE_DIR / "assets" / "Ideogram_Colab.ipynb"

# 自動讀取專案根目錄的 .env 檔案 (無需額外套件)
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    for _line in _env_file.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            _k, _v = _k.strip(), _v.strip().strip("\"'")
            if _k not in os.environ:
                os.environ[_k] = _v
os.environ.setdefault("REQUEST_TIMEOUT", "300")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
AUTH = os.environ.get("COLAB_AUTH", "oauth2")


class ColabCommandError(RuntimeError):
    def __init__(self, label: str, returncode: int, output: list[str]):
        self.label = label
        self.returncode = returncode
        self.output = output
        tail = "\n".join(line for line in output[-15:] if line)
        super().__init__(f"[{label}] failed (exit code {returncode})" + (f":\n{tail}" if tail else ""))


class ColabTimeoutError(TimeoutError):
    pass


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def clean_output(value: str) -> str:
    return ANSI_RE.sub("", value).replace("\r", "").strip()


def find_colab_executable() -> str:
    path = shutil.which("colab")
    if not path and sys.platform == "win32":
        # Check standard user local bin in Windows uv environment
        candidate = Path.home() / ".local" / "bin" / "colab.exe"
        if candidate.exists():
            return str(candidate)
    if not path:
        raise FileNotFoundError(
            "Colab CLI is not found on PATH. Please ensure google-colab-cli is installed via 'uv tool install google-colab-cli'."
        )
    return path


def kill_process_tree(child: subprocess.Popen) -> None:
    """Cross-platform safe termination of subprocess and its children."""
    pid = child.pid
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            child.terminate()
    else:
        try:
            child.terminate()
            child.wait(timeout=3)
        except Exception:
            try:
                child.kill()
            except Exception:
                pass


def call_colab(
    arguments: list[str],
    *,
    label: str,
    timeout: float = 300,
    on_line: Callable[[str], None] | None = None,
) -> str:
    """Executes a Colab CLI command with real-time output capture and timeout handling."""
    colab_bin = find_colab_executable()
    command = [colab_bin, f"--auth={AUTH}", *arguments]

    # In Windows, avoid start_new_session with os.killpg
    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

    sub_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}

    child = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
        env=sub_env,
    )

    lines: queue.Queue[str | None] = queue.Queue()

    def stream_reader() -> None:
        if child.stdout is not None:
            for line in child.stdout:
                lines.put(line.rstrip("\n"))
        lines.put(None)

    reader = threading.Thread(target=stream_reader, daemon=True)
    reader.start()

    output_lines: list[str] = []
    started_at = time.monotonic()
    eof = False

    while not eof or child.poll() is None:
        if time.monotonic() - started_at > timeout and child.poll() is None:
            kill_process_tree(child)
            reader.join(timeout=2)
            if child.stdout is not None:
                child.stdout.close()
            raise ColabTimeoutError(f"[{label}] exceeded timeout of {timeout} seconds. Process was terminated.")

        try:
            item = lines.get(timeout=0.2)
        except queue.Empty:
            continue

        if item is None:
            eof = True
            continue

        cleaned = clean_output(item)
        output_lines.append(cleaned)
        if on_line and cleaned:
            on_line(cleaned)

    returncode = child.wait()
    reader.join(timeout=2)
    if child.stdout is not None:
        child.stdout.close()

    if returncode != 0:
        raise ColabCommandError(label, returncode, output_lines)

    return "\n".join(output_lines)


def parse_usage(raw_output: str) -> dict[str, Any]:
    """Parse output of `colab usage`."""
    normalized = clean_output(raw_output)

    def extract_float(pattern: str, default: float = 0.0) -> float:
        match = re.search(pattern, normalized, re.IGNORECASE | re.MULTILINE)
        return float(match.group(1).replace(",", "")) if match else default

    def extract_int(pattern: str, default: int = 0) -> int:
        match = re.search(pattern, normalized, re.IGNORECASE | re.MULTILINE)
        return int(match.group(1)) if match else default

    balance = extract_float(r"Current balance:\s*([\d,]+(?:\.\d+)?)\s*compute units", 0.0)
    rate = extract_float(r"Usage rate:\s*([\d,]+(?:\.\d+)?)\s*/\s*hr", 0.0)
    assignments = extract_int(r"Active assignments:\s*(\d+)", 0)

    return {
        "balance": balance,
        "rate_per_hour": rate,
        "active_assignments": assignments,
        "checked_at": now_iso(),
    }


def get_current_usage() -> dict[str, Any]:
    raw = call_colab(["usage"], label="colab usage", timeout=30)
    return parse_usage(raw)


def run_single(
    prompt: str,
    output_path: str,
    *,
    image_path: str | None = None,
    gpu: str = "A100",
    num_frames: int = 121,
    seed: int = 42,
    hf_token: str | None = None,
    timeout: float = 3600,
    keep_session: bool = False,
) -> str:
    """Executes a single LTX-2.5 video generation job."""
    session_id = f"ltx-{uuid.uuid4().hex[:8]}"
    out_target = Path(output_path).resolve()
    out_target.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n==================================================")
    print(f"🚀 啟動 LTX-2.5 影片生成任務")
    print(f"  工作階段名稱: {session_id}")
    print(f"  配置 GPU: {gpu}")
    print(f"  影格數: {num_frames} 幀 (約 {round(num_frames/24, 2)} 秒)")
    print(f"  隨機種子: {seed}")
    print(f"  輸出目標: {out_target}")
    print(f"==================================================")

    # 1. 查詢起始 Compute Units
    try:
        usage = get_current_usage()
        print(f"📊 目前可用餘額: {usage['balance']} Compute Units (作用中作業: {usage['active_assignments']})")
    except Exception as e:
        print(f"⚠️ 無法讀取起始餘額: {e}")

    try:
        # 2. 開啟 Colab 工作階段
        print(f"\n[1/5] 正在向 Google Colab 申請 {gpu} 工作階段...")
        call_colab(["new", "--session", session_id, "--gpu", gpu, "--high-mem"], label="colab new", timeout=600)
        print("✅ 工作階段啟動成功！")

        # 3. 準備並上傳素材
        print("\n[2/5] 正在打包並上傳提示詞與素材...")
        # 建立本地暫存 prompt 檔
        temp_prompt = BASE_DIR / "assets" / f"_temp_prompt_{session_id}.txt"
        temp_prompt.write_text(prompt, encoding="utf-8")
        try:
            call_colab(["upload", "--session", session_id, str(temp_prompt), "/content/prompt.txt"], label="upload prompt", timeout=60)
        finally:
            if temp_prompt.exists():
                temp_prompt.unlink()

        remote_image_path = ""
        if image_path and Path(image_path).exists():
            remote_image_path = f"/content/{Path(image_path).name}"
            print(f"  上傳參考首格圖片: {image_path} -> {remote_image_path}")
            call_colab(["upload", "--session", session_id, str(image_path), remote_image_path], label="upload image", timeout=120)

        # 4. 執行 Notebook 推論
        print(f"\n[3/5] 開始遠端執行 LTX-2.5 推論 (逾時上限: {timeout} 秒)...")
        token = hf_token or os.environ.get("HF_TOKEN", "")

        env_args = [
            f"LTX_PROMPT_FILE=/content/prompt.txt",
            f"LTX_IMAGE_FILE={remote_image_path}",
            f"LTX_OUTPUT_PATH=/content/output.mp4",
            f"LTX_NUM_FRAMES={num_frames}",
            f"LTX_SEED={seed}",
            "USE_DRIVE_CACHE=0",
        ]
        if token:
            env_args.append(f"HF_TOKEN={token}")

        exec_cmd = ["exec", "--session", session_id, "--file", str(DEFAULT_NOTEBOOK), "--timeout", str(int(timeout))]
        for env in env_args:
            exec_cmd.extend(["--env", env])

        def on_log(line: str) -> None:
            if line and line.strip():
                print(f"  [Colab] {line}")

        call_colab(exec_cmd, label="colab exec", timeout=timeout + 60, on_line=on_log)
        print("✅ Colab 遠端推論成功完成！")

        # 5. 下載成果 MP4
        print(f"\n[4/5] 正在下載生成的影音成品回本地: {out_target}...")
        call_colab(["download", "--session", session_id, "/content/output.mp4", str(out_target)], label="download mp4", timeout=300)

        if out_target.exists():
            size_mb = round(out_target.stat().st_size / (1024 * 1024), 2)
            print(f"🎉 影片下載完成！本地路徑: {out_target} (大小: {size_mb} MB)")
        else:
            raise FileNotFoundError(f"下載完成但找不到本地檔案: {out_target}")

    finally:
        # 6. 關閉工作階段以防額度持續扣款
        if not keep_session:
            print(f"\n[5/5] 正在釋放 Colab 工作階段以保護 Compute Units...")
            try:
                call_colab(["stop", "--session", session_id], label="colab stop", timeout=60)
                print("✅ 工作階段已安全關閉。")
            except Exception as e:
                print(f"⚠️ 關閉工作階段時發生警告: {e}")

        try:
            end_usage = get_current_usage()
            print(f"📊 目前剩餘額度: {end_usage['balance']} Compute Units\n")
        except Exception:
            pass

    return str(out_target)


def run_batch(
    manifest_path: str,
    output_dir: str,
    *,
    gpu: str = "A100",
    hf_token: str | None = None,
    timeout_per_job: float = 3600,
) -> None:
    """Executes a batch of video generation jobs using a single reused Colab session."""
    manifest_file = Path(manifest_path).resolve()
    if not manifest_file.exists():
        raise FileNotFoundError(f"找不到 Manifest 檔案: {manifest_file}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        jobs: list[dict[str, Any]] = json.load(f)

    out_folder = Path(output_dir).resolve()
    out_folder.mkdir(parents=True, exist_ok=True)

    print(f"\n==================================================")
    print(f"📦 啟動 LTX-2.5 批次生成 (共 {len(jobs)} 個任務)")
    print(f"  輸出資料夾: {out_folder}")
    print(f"  共用 Colab 工作階段模式: 模型僅載入一次")
    print(f"==================================================")

    session_id = f"ltx-batch-{uuid.uuid4().hex[:8]}"

    try:
        print(f"\n[1/3] 正在申請批次專用 {gpu} 工作階段...")
        call_colab(["new", "--session", session_id, "--gpu", gpu, "--high-mem"], label="colab new batch", timeout=600)
        print("✅ 批次工作階段啟動成功！")

        for idx, job in enumerate(jobs, 1):
            job_id = job.get("id", f"job_{idx}")
            prompt = job.get("prompt", "")
            image_path = job.get("image", None)
            num_frames = job.get("num_frames", 121)
            seed = job.get("seed", 42 + idx)
            out_file = out_folder / (job.get("output", f"{job_id}.mp4").split("/")[-1])

            print(f"\n--- 執行任務 [{idx}/{len(jobs)}]: {job_id} ---")
            temp_prompt = BASE_DIR / "assets" / f"_temp_{job_id}.txt"
            temp_prompt.write_text(prompt, encoding="utf-8")

            try:
                call_colab(["upload", "--session", session_id, str(temp_prompt), "/content/prompt.txt"], label="upload prompt", timeout=60)
            finally:
                if temp_prompt.exists():
                    temp_prompt.unlink()

            remote_img = ""
            if image_path and Path(image_path).exists():
                remote_img = f"/content/{Path(image_path).name}"
                call_colab(["upload", "--session", session_id, str(image_path), remote_img], label="upload img", timeout=120)

            token = hf_token or os.environ.get("HF_TOKEN", "")
            env_args = [
                f"LTX_PROMPT_FILE=/content/prompt.txt",
                f"LTX_IMAGE_FILE={remote_img}",
                f"LTX_OUTPUT_PATH=/content/output.mp4",
                f"LTX_NUM_FRAMES={num_frames}",
                f"LTX_SEED={seed}",
            ]
            if token:
                env_args.append(f"HF_TOKEN={token}")

            exec_cmd = ["exec", "--session", session_id, "--file", str(DEFAULT_NOTEBOOK), "--timeout", str(int(timeout_per_job))]
            for env in env_args:
                exec_cmd.extend(["--env", env])

            print("  正在推論中...")
            call_colab(exec_cmd, label=f"exec {job_id}", timeout=timeout_per_job + 60)

            print(f"  下載成果至: {out_file}...")
            call_colab(["download", "--session", session_id, "/content/output.mp4", str(out_file)], label=f"download {job_id}", timeout=300)
            print(f"  ✅ 任務 {job_id} 成功完成！")

    finally:
        print(f"\n[3/3] 正在釋放批次 Colab 工作階段...")
        try:
            call_colab(["stop", "--session", session_id], label="colab stop", timeout=60)
            print("✅ 批次工作階段已安全釋放。")
        except Exception as e:
            print(f"⚠️ 釋放工作階段警告: {e}")


def run_image(
    prompt: str,
    output_path: str,
    *,
    model: str = "flux",
    width: int = 1280,
    height: int = 720,
    steps: int | None = None,
    seed: int = 42,
    gpu: str = "A100",
    hf_token: str | None = None,
    timeout: float = 1200,
    keep_session: bool = False,
    session_id: str | None = None,
) -> str:
    """Executes an image generation job on Colab using FLUX.1 or Ideogram 4.0."""
    own_session = session_id is None
    is_ideogram = model.lower() == "ideogram"
    model_label = "Ideogram 4.0 (專精排版文字)" if is_ideogram else "FLUX.1 [schnell]"
    prefix = "ideogram" if is_ideogram else "flux"
    sess_id = session_id or f"{prefix}-{uuid.uuid4().hex[:8]}"
    out_target = Path(output_path).resolve()
    out_target.parent.mkdir(parents=True, exist_ok=True)

    actual_steps = steps if steps is not None else (30 if is_ideogram else 4)

    print(f"\n==================================================")
    print(f"🎨 啟動 {model_label} 視覺資產生成任務")
    print(f"  工作階段: {sess_id}")
    print(f"  解析度: {width}x{height}")
    print(f"  推論步數: {actual_steps}")
    print(f"  種子: {seed}")
    print(f"  輸出目標: {out_target}")
    print(f"==================================================")

    try:
        if own_session:
            print(f"\n[1/4] 正在申請 Colab {gpu} 工作階段...")
            call_colab(["new", "--session", sess_id, "--gpu", gpu], label=f"colab new {prefix}", timeout=600)
            print("✅ 工作階段啟動成功！")

        print("\n[2/4] 上傳生圖提示詞...")
        temp_prompt = BASE_DIR / "assets" / f"_temp_{prefix}_{sess_id}.txt"
        temp_prompt.write_text(prompt, encoding="utf-8")
        try:
            call_colab(["upload", "--session", sess_id, str(temp_prompt), "/content/prompt.txt"], label=f"upload {prefix} prompt", timeout=60)
        finally:
            if temp_prompt.exists():
                temp_prompt.unlink()

        print(f"\n[3/4] 執行 {model_label} 推論 (逾時上限: {timeout} 秒)...")
        token = hf_token or os.environ.get("HF_TOKEN", "")

        if is_ideogram:
            notebook_file = DEFAULT_IDEOGRAM_NOTEBOOK
            env_args = [
                "IDEOGRAM_PROMPT_FILE=/content/prompt.txt",
                "IDEOGRAM_OUTPUT_PATH=/content/output.png",
                f"IDEOGRAM_WIDTH={width}",
                f"IDEOGRAM_HEIGHT={height}",
                f"IDEOGRAM_STEPS={actual_steps}",
                f"IDEOGRAM_SEED={seed}",
            ]
        else:
            notebook_file = DEFAULT_FLUX_NOTEBOOK
            env_args = [
                "FLUX_PROMPT_FILE=/content/prompt.txt",
                "FLUX_OUTPUT_PATH=/content/output.png",
                f"FLUX_WIDTH={width}",
                f"FLUX_HEIGHT={height}",
                f"FLUX_STEPS={actual_steps}",
                f"FLUX_SEED={seed}",
            ]

        if token:
            env_args.append(f"HF_TOKEN={token}")

        exec_cmd = ["exec", "--session", sess_id, "--file", str(notebook_file), "--timeout", str(int(timeout))]
        for env in env_args:
            exec_cmd.extend(["--env", env])

        def on_log(line: str) -> None:
            if any(k in line for k in ["[GPU]", "依賴", "正在載入", "開始", "生成完畢", "檔案大小"]):
                print(f"  [Colab {prefix.upper()}] {line}")

        call_colab(exec_cmd, label=f"colab exec {prefix}", timeout=timeout + 60, on_line=on_log)
        print(f"✅ {model_label} 生圖完成！")

        print(f"\n[4/4] 下載視覺資產回本地: {out_target}...")
        call_colab(["download", "--session", sess_id, "/content/output.png", str(out_target)], label="download png", timeout=120)

        if out_target.exists():
            size_kb = round(out_target.stat().st_size / 1024, 1)
            print(f"🎉 圖片下載完成！本地路徑: {out_target} (大小: {size_kb} KB)")
        else:
            raise FileNotFoundError(f"未找到本地檔案: {out_target}")

    finally:
        if own_session and not keep_session:
            print("釋放 Colab 工作階段...")
            try:
                call_colab(["stop", "--session", sess_id], label=f"colab stop {prefix}", timeout=60)
                print("✅ 工作階段已安全關閉。")
            except Exception as e:
                print(f"⚠️ 關閉警告: {e}")

    return str(out_target)


def run_pipeline(
    image_prompt: str,
    video_prompt: str,
    output_video: str,
    *,
    image_model: str = "flux",
    output_image: str | None = None,
    gpu: str = "A100",
    num_frames: int = 121,
    seed: int = 42,
    hf_token: str | None = None,
    timeout: float = 3600,
) -> tuple[str, str]:
    """End-to-end: (FLUX or Ideogram) Image Asset -> LTX-2.5 Video Generation in ONE reused Colab session."""
    session_id = f"studio-{uuid.uuid4().hex[:8]}"
    out_video_target = Path(output_video).resolve()
    out_video_target.parent.mkdir(parents=True, exist_ok=True)

    out_image_target = (
        Path(output_image).resolve()
        if output_image
        else out_video_target.parent / f"{out_video_target.stem}_keyframe.png"
    )

    img_label = "Ideogram 4.0" if image_model.lower() == "ideogram" else "FLUX.1"

    print(f"\n==================================================")
    print(f"🎬 啟動 一條龍影視工坊流水線 ({img_label} 資產 ➔ LTX 影音)")
    print(f"  共用 Colab 工作階段: {session_id}")
    print(f"  首格生圖模型: {img_label}")
    print(f"  生圖目標: {out_image_target}")
    print(f"  最終影片目標: {out_video_target}")
    print(f"==================================================")

    try:
        # 1. 建立單一 Colab 工作階段
        print(f"\n[階段 1/3] 申請 Colab {gpu} 高階工作階段...")
        call_colab(["new", "--session", session_id, "--gpu", gpu, "--high-mem"], label="colab new pipeline", timeout=600)
        print("✅ 工作階段啟動成功！")

        # 2. 執行生圖 (FLUX 或 Ideogram 4.0)
        print(f"\n[階段 2/3] 生產首影格概念資產 ({img_label})...")
        run_image(
            image_prompt,
            str(out_image_target),
            model=image_model,
            width=1280,
            height=720,
            seed=seed,
            hf_token=hf_token,
            session_id=session_id,
        )

        # 3. 執行 LTX-2.5 圖生影音 (直接使用 Colab 上的 /content/output.png 作為輸入)
        print(f"\n[階段 3/3] 轉化為動態連續影片與同步音效 (LTX-2.5)...")
        temp_prompt = BASE_DIR / "assets" / f"_temp_pipe_{session_id}.txt"
        temp_prompt.write_text(video_prompt, encoding="utf-8")
        try:
            call_colab(["upload", "--session", session_id, str(temp_prompt), "/content/prompt.txt"], label="upload pipe prompt", timeout=60)
        finally:
            if temp_prompt.exists():
                temp_prompt.unlink()

        token = hf_token or os.environ.get("HF_TOKEN", "")
        env_args = [
            "LTX_PROMPT_FILE=/content/prompt.txt",
            "LTX_IMAGE_FILE=/content/output.png",  # 直接使用剛才產出的圖片
            "LTX_OUTPUT_PATH=/content/output.mp4",
            f"LTX_NUM_FRAMES={num_frames}",
            f"LTX_SEED={seed}",
            "USE_DRIVE_CACHE=0",
        ]
        if token:
            env_args.append(f"HF_TOKEN={token}")

        exec_cmd = ["exec", "--session", session_id, "--file", str(DEFAULT_NOTEBOOK), "--timeout", str(int(timeout))]
        for env in env_args:
            exec_cmd.extend(["--env", env])

        def on_log(line: str) -> None:
            if any(k in line for k in ["[GPU]", "正在載入", "開始執行", "生成完畢", "包含串流"]):
                print(f"  [Colab LTX] {line}")

        call_colab(exec_cmd, label="colab exec pipe ltx", timeout=timeout + 60, on_line=on_log)

        # 4. 下載成品影片
        print(f"下載成品影片回本地: {out_video_target}...")
        call_colab(["download", "--session", session_id, "/content/output.mp4", str(out_video_target)], label="download pipe mp4", timeout=300)
        print(f"🎉 一條龍生產大功告成！")
        print(f"  視覺資產首格圖: {out_image_target}")
        print(f"  最終動態影音影片: {out_video_target}")

    finally:
        print("\n釋放 Colab 工作階段以保護 Compute Units...")
        try:
            call_colab(["stop", "--session", session_id], label="colab stop pipeline", timeout=60)
            print("✅ 工作階段已安全關閉。")
        except Exception as e:
            print(f"⚠️ 關閉警告: {e}")

    return str(out_image_target), str(out_video_target)


def main() -> None:
    parser = argparse.ArgumentParser(description="LTX-2.5 Colab Video Automation Dispatcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # 1. usage
    subparsers.add_parser("usage", help="查詢 Google Colab 目前可用額度與費率")

    # 2. single
    single_p = subparsers.add_parser("single", help="執行單一影片生成任務")
    single_p.add_argument("--prompt", type=str, default="", help="提示詞文字")
    single_p.add_argument("--prompt-file", type=str, default="", help="提示詞文字檔路徑")
    single_p.add_argument("--image", type=str, default=None, help="參考首格圖片路徑 (Image-to-Video)")
    single_p.add_argument("--output", type=str, default="outputs/result.mp4", help="輸出 MP4 本地路徑")
    single_p.add_argument("--gpu", type=str, default="A100", choices=["A100", "L4", "H100"], help="Colab GPU 加速器類型")
    single_p.add_argument("--num-frames", type=int, default=121, help="影格數 (預設 121，約 5.04 秒)")
    single_p.add_argument("--seed", type=int, default=42, help="隨機種子")
    single_p.add_argument("--hf-token", type=str, default=None, help="Hugging Face Token (可用環境變數 HF_TOKEN)")
    single_p.add_argument("--timeout", type=float, default=3600, help="推論逾時秒數上限")
    single_p.add_argument("--keep-session", action="store_true", help="任務結束後保留工作階段不關閉")

    # 3. batch
    batch_p = subparsers.add_parser("batch", help="批次執行影片生成任務清單")
    batch_p.add_argument("--manifest", type=str, required=True, help="任務清單 JSON 檔案路徑")
    batch_p.add_argument("--output-dir", type=str, default="outputs", help="輸出資料夾")
    batch_p.add_argument("--gpu", type=str, default="A100", choices=["A100", "L4", "H100"], help="Colab GPU 加速器類型")
    batch_p.add_argument("--hf-token", type=str, default=None, help="Hugging Face Token")
    batch_p.add_argument("--timeout-per-job", type=float, default=3600, help="每個任務逾時上限")

    # 4. image (FLUX.1 or Ideogram 4.0)
    image_p = subparsers.add_parser("image", help="執行視覺資產生圖任務 (支援 FLUX.1 與 Ideogram 4.0)")
    image_p.add_argument("--model", type=str, default="flux", choices=["flux", "ideogram"], help="模型選擇：flux (極速光影) 或 ideogram (Ideogram 4.0 專精文字招牌排版)")
    image_p.add_argument("--prompt", type=str, default="", help="生圖提示詞")
    image_p.add_argument("--prompt-file", type=str, default="", help="提示詞文字檔")
    image_p.add_argument("--output", type=str, default="outputs/asset.png", help="輸出圖片路徑")
    image_p.add_argument("--width", type=int, default=1280, help="圖片寬度")
    image_p.add_argument("--height", type=int, default=720, help="圖片高度")
    image_p.add_argument("--steps", type=int, default=None, help="推論步數 (預設: flux=4, ideogram=30)")
    image_p.add_argument("--seed", type=int, default=42, help="隨機種子")
    image_p.add_argument("--gpu", type=str, default="A100", choices=["A100", "L4", "H100"], help="GPU 類型")
    image_p.add_argument("--hf-token", type=str, default=None, help="Hugging Face Token")
    image_p.add_argument("--timeout", type=float, default=1200, help="逾時上限")

    # 5. pipeline (Image Asset -> LTX-2.5 Video)
    pipe_p = subparsers.add_parser("pipeline", help="一條龍任務：先用 (FLUX 或 Ideogram) 生圖，再以該圖作為首格用 LTX 生成連續影片與同步音效")
    pipe_p.add_argument("--image-model", type=str, default="flux", choices=["flux", "ideogram"], help="首格生圖模型：flux (極速) 或 ideogram (排版文字)")
    pipe_p.add_argument("--image-prompt", type=str, required=True, help="生圖提示詞 (定義角色/場景外觀)")
    pipe_p.add_argument("--video-prompt", type=str, required=True, help="影片與音訊動作提示詞 (定義動態與聲音)")
    pipe_p.add_argument("--output-video", type=str, default="outputs/final_video.mp4", help="輸出 MP4 路徑")
    pipe_p.add_argument("--output-image", type=str, default=None, help="輸出首格圖片路徑 (選填)")
    pipe_p.add_argument("--gpu", type=str, default="A100", choices=["A100", "L4", "H100"], help="GPU 類型")
    pipe_p.add_argument("--num-frames", type=int, default=121, help="影格數 (預設 121)")
    pipe_p.add_argument("--seed", type=int, default=42, help="隨機種子")
    pipe_p.add_argument("--hf-token", type=str, default=None, help="Hugging Face Token")
    pipe_p.add_argument("--timeout", type=float, default=3600, help="逾時上限")

    args = parser.parse_args()

    if args.command == "usage":
        usage = get_current_usage()
        print("\n=== Google Colab 資源狀態 ===")
        print(f"剩餘額度 (Balance): {usage['balance']} Compute Units")
        print(f"目前費率 (Usage Rate): {usage['rate_per_hour']:.2f} CU / hr")
        print(f"作用中工作階段 (Assignments): {usage['active_assignments']}")
        print(f"查詢時間: {usage['checked_at']}\n")

    elif args.command == "image":
        prompt_text = args.prompt
        if args.prompt_file and Path(args.prompt_file).exists():
            prompt_text = Path(args.prompt_file).read_text(encoding="utf-8").strip()
        if not prompt_text:
            print("錯誤：必須提供 --prompt 或 --prompt-file。")
            sys.exit(1)

        run_image(
            prompt_text,
            args.output,
            model=args.model,
            width=args.width,
            height=args.height,
            steps=args.steps,
            seed=args.seed,
            gpu=args.gpu,
            hf_token=args.hf_token,
            timeout=args.timeout,
        )

    elif args.command == "pipeline":
        run_pipeline(
            args.image_prompt,
            args.video_prompt,
            args.output_video,
            image_model=args.image_model,
            output_image=args.output_image,
            gpu=args.gpu,
            num_frames=args.num_frames,
            seed=args.seed,
            hf_token=args.hf_token,
            timeout=args.timeout,
        )

    elif args.command == "single":
        prompt_text = args.prompt
        if args.prompt_file and Path(args.prompt_file).exists():
            prompt_text = Path(args.prompt_file).read_text(encoding="utf-8").strip()
        if not prompt_text:
            print("錯誤：必須提供 --prompt 或 --prompt-file。")
            sys.exit(1)

        run_single(
            prompt_text,
            args.output,
            image_path=args.image,
            gpu=args.gpu,
            num_frames=args.num_frames,
            seed=args.seed,
            hf_token=args.hf_token,
            timeout=args.timeout,
            keep_session=args.keep_session,
        )

    elif args.command == "batch":
        run_batch(
            args.manifest,
            args.output_dir,
            gpu=args.gpu,
            hf_token=args.hf_token,
            timeout_per_job=args.timeout_per_job,
        )


if __name__ == "__main__":
    main()
