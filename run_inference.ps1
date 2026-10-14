# LTX-2.5, FLUX.1 & Ideogram 4.0 Colab Studio Launcher for PowerShell
param (
    [string]$Mode = "single", # "image", "single", "pipeline", "batch", "usage"
    [string]$Model = "flux",  # "flux" (極速自然光影) 或 "ideogram" (Ideogram 4.0 專精文字排版)
    [string]$Prompt = "",
    [string]$PromptFile = "",
    [string]$ImagePrompt = "",
    [string]$VideoPrompt = "",
    [string]$Image = "",
    [string]$Output = "",
    [string]$Gpu = "A100",
    [int]$NumFrames = 121,
    [int]$Seed = 42,
    [string]$HfToken = $env:HF_TOKEN
)

$argsList = @("scripts/runner.py", $Mode)

if ($Mode -eq "usage") {
    python @argsList
    exit 0
}

if ($Mode -eq "image") {
    if ($Output -eq "") { $Output = "outputs/asset.png" }
    $argsList += @("--model", $Model, "--output", $Output, "--gpu", $Gpu, "--seed", $Seed)
    if ($Prompt -ne "") { $argsList += @("--prompt", $Prompt) }
    elseif ($PromptFile -ne "") { $argsList += @("--prompt-file", $PromptFile) }
    else {
        Write-Host "生圖模式請提供 -Prompt。" -ForegroundColor Red
        exit 1
    }
}
elseif ($Mode -eq "pipeline") {
    if ($Output -eq "") { $Output = "outputs/final_video.mp4" }
    if ($ImagePrompt -eq "" -or $VideoPrompt -eq "") {
        Write-Host "一條龍模式請同時提供 -ImagePrompt 與 -VideoPrompt。" -ForegroundColor Red
        exit 1
    }
    $argsList += @("--image-model", $Model, "--image-prompt", $ImagePrompt, "--video-prompt", $VideoPrompt, "--output-video", $Output, "--gpu", $Gpu, "--num-frames", $NumFrames, "--seed", $Seed)
}
elseif ($Mode -eq "single") {
    if ($Output -eq "") { $Output = "outputs/result.mp4" }
    $argsList += @("--output", $Output, "--gpu", $Gpu, "--num-frames", $NumFrames, "--seed", $Seed)
    if ($Prompt -ne "") { $argsList += @("--prompt", $Prompt) }
    elseif ($PromptFile -ne "") { $argsList += @("--prompt-file", $PromptFile) }
    else { $argsList += @("--prompt-file", "prompts/example_prompt.txt") }
    if ($Image -ne "") { $argsList += @("--image", $Image) }
}

if ($HfToken -ne "" -and $null -ne $HfToken) {
    $argsList += @("--hf-token", $HfToken)
}

Write-Host "啟動 Colab 影視工坊流水線 (模式: $Mode, 模型: $Model)..." -ForegroundColor Cyan
python @argsList
