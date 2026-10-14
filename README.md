# Google AI 訂閱多送 Colab GPU 額度！透過本地調度，零顯卡門檻暢玩 MiniMax H3 與 Lightricks LTX-2.5 雙頂級 AI 影音模型

Google 為 Google AI 訂閱用戶（Google AI Pro / Ultra）贈送每月免費的 Google Colab GPU 運算額度（以 Google AI Pro 為例，每月提供 200 Compute Units 算力）。對於平常沒有在使用 Colab 寫程式的人來說，可能不知道這項福利能拿來做什麼；而如果想在本機電腦跑最新的開源 AI 影片模型，動輒需要 24GB~80GB 顯存的高階顯示卡，門檻相當高。

本專案提供了一套**「本地終端一鍵調度 ＋ Google Colab 雲端 A100 GPU 高速推論 ＋ 成品自動下載回本機 ＋ 自動關機防扣點」**的完整影音自動化流程。你只需要在自己的電腦準備好圖片與提示詞，打一行指令，就能調用雲端頂級算力生成影片，而且跑完會**自動關閉 Colab 工作階段（Active assignments: 0）**，徹底避免忘記關機導致額度被扣光的慘劇！

實測跑一部完整帶音效的短影片**僅耗費約 0.47 ~ 0.56 個運算單元（CU）**，換算下來，Google AI Pro 用戶每個月的 200 CU 足足可以生成接近 **400 部** 高畫質 AI 影片！

---

## 雙模型特色與應用情境深入解析

本專案支援目前開源界最頂級的兩款影音雙串流模型：**MiniMax H3 Turbo** 與 **Lightricks LTX-2.5 (22B)**。兩者架構與擅長的領域截然不同，以下分別為大家詳細拆解它們的應用優勢：

---

### 應用一：MiniMax H3 Turbo ——「社群短影音與電商帶貨一條龍神器」

#### 1. 什麼是 Ref2VA 架構？
MiniMax H3 Turbo 採用專屬的 **Ref2VA (Reference-to-Video+Audio)** 跨模態端到端生成架構。
傳統製作 AI 短影音的痛點在於：先跑圖片 ➔ 跑影片 ➔ 用外部 TTS 產生配音 ➔ 找音效庫剪輯 ➔ 在剪輯軟體對齊時間軸，耗時費力。

MiniMax H3 的最大突破在於**「原生同步生成畫面、中文語音口白與環境音效」**！
只要在提示詞內加入 `<d>[Chinese] 你的台詞口白</d>` 標籤，模型在去噪擴散的過程中，就會直接解碼出自然流暢的中文發音，並自動混入對應動作的環境音與背景節奏。

#### 2. 實測案例：屏東「黎明村手作醋溜泡果（芒果青）」產品開場 Hook
我們以台灣在地農產加工品「黎明村手作醋溜泡果」為實測對象：
- **視覺呈現**：木叉從玻璃罐中夾起晶瑩半透明的青芒果片，琥珀色醋汁緩緩滴落，罐身文字標籤極為穩定不變形。
- **原生音效與口白**：自動合成清脆爽口的咬斷咬碎聲（Crunch SFX）與倒醬汁音效，並同步配上充滿吸引力的中文口白：
  > *「你敢信？這酸爽清脆的芒果青，居然是鹹的！黎明村手作泡果，越吃越涮嘴！」*

```
【輸入參考圖 assets/paoguo_hero.png】
       │
       ▼ (Google Colab A100 GPU / MiniMax H3 Ref2VA)
【產出 outputs/paoguo_minimax_h3.mp4】
  ├── 視訊：1376×768 @ 24fps (6.58 秒)
  └── 音訊：原生中文台詞口白 + 清脆咬斷音效 + 開場輕快節奏
```

#### 3. 最佳適用場景
- **Instagram Reels / TikTok / YouTube Shorts 前 3 秒開場 Hook**。
- **在地農特產、伴手禮、餐飲電商商品動態展示**。
- **一人自媒體工作室批量產出產品介紹短片**。

#### 4. MiniMax H3 專用提示詞格式
提示詞採用結構化 YAML 格式，能精準指定主體定義與聲音設計：

```yaml
# prompts/paoguo_h3.txt
subject_definitions:
<Subject 1>: The clear glass jar with bamboo lid filled with artisanal pickled green mango slices (黎明村手作醋溜泡果) from <Picture 1>.

detailed_description:
[Shot 1] Ultra-appetizing food commercial. A rustic wooden fork gently lifts a crisp, translucent green mango slice out of the jar. Golden-amber vinegar sauce drips back into the jar. Camera slowly pushes in. <d>[Chinese] 你敢信？這酸爽清脆的芒果青，居然是鹹的！黎明村手作泡果，越吃越涮嘴！</d>

overall_soundscape:
Crisp satisfying crunch biting sound, gentle viscous liquid droplets dripping, soft kitchen ambiance, and upbeat inviting Chinese voiceover narration.
```

**一鍵執行指令**：
```bash
python scripts/run_minimax_paoguo.py
```

---

### 應用二：Lightricks LTX-2.5 (22B) ——「電影級 1.5K 畫質、微觀光影與動態張力之王」

#### 1. 什麼是 22B Dual-Stream DiT 與雙階段超解析？
由 Lightricks 推出的 LTX-2.5 是目前開源社群體量最龐大的影視級旗艦：
- **220 億參數骨幹**：採用 22B Distilled Transformer 搭配 Google Gemma 4 12B 文字編碼器，對物理世界規律與提示詞細節的理解力極強。
- **潛在空間雙階段超解析**：先在低解析度潛空間規劃長時序動態，再經由 `ltx-2.5-latent-spatial-upscaler-x2` 模組進行空間超解析放大，直接輸出高達 **1536×1024**（1.5K 畫質）的超清晰成品。
- **雙流音訊 VAE**：獨立音訊潛空間同步計算，產生沉浸式的動作環境音效。

#### 2. 實測案例：玄幻巨龍與美食微觀光影
- **案例 A：《金色巨龍雲海中咆哮》**：
  金色巨龍在雷雨積雨雲中翻江倒海，穿雲破霧向前衝刺並怒吼。金屬鱗片在閃電照耀下呈現細緻的反射光澤，龍鬚與鬃毛隨強風狂亂翻飛，運鏡具備強烈的立體景深變換。
- **案例 B：《晶瑩醋溜泡果特寫》**：
  在 1536×1024 解析度下，木叉的天然年輪紋路清晰可見，醃漬青芒果肉呈現半透明的嫩綠透光感，醋溜醬汁在果肉尖端因表面張力自然凝聚成水滴並沿重力滴下，逼真度直逼院線級商業廣告攝影。

```
【輸入參考圖 assets/paoguo_hero.png】
       │
       ▼ (Google Colab A100 GPU / LTX-2.5 22B DiT + Upscaler)
【產出 outputs/paoguo_ltx25_22b.mp4】
  ├── 視訊：1536×1024 超清 1.5K @ 24fps (5.04 秒 / 121 幀)
  └── 音訊：原生 Audio VAE 液體凝聚滴落與清脆環境音
```

#### 3. 最佳適用場景
- **精品品牌廣告、高階電視宣傳片 (CF) 與美食特寫鏡頭 (B-Roll)**。
- **科幻/玄幻電影概念預告片、動態分鏡 (Animatics) 與視覺特效 (VFX) 提案**。
- **需要在大螢幕播放、追求極致紋理與光影層次的視覺作品**。

#### 4. LTX-2.5 執行指令
```bash
python scripts/run_ltx25_paoguo.py
```
或自訂參數執行：
```bash
python scripts/runner.py single \
  --image assets/paoguo_hero.png \
  --prompt "Cinematic 4K commercial food video. A wooden fork gently lifts a crisp succulent translucent pale-green mango slice out of the glass jar, sparkling golden-amber vinegar sauce glistening and dripping down into the jar in warm morning sunlight, water condensation on glass, shallow depth of field, crisp crunch sound" \
  --output outputs/paoguo_ltx25_22b.mp4 \
  --gpu A100 --num-frames 121 --seed 42
```

---

## 雙模型規格與實測對比

| 評測項目 | MiniMax H3 Turbo | Lightricks LTX-2.5 (22B) | 特色與適用建議 |
| :--- | :--- | :--- | :--- |
| **模型規模** | 未公開 (約 8B~10B) | **22B DiT + 12B Gemma4** | LTX-2.5 參數量極大，光影層次與微觀細節極致豐富 |
| **輸出解析度** | 1376×768 (16:9 寬螢幕) | **1536×1024 (超清 1.5K)** | LTX-2.5 畫質細膩度領先，木紋纖維與果肉透光感極強 |
| **生成幀率 / 時長** | 24 fps / 6.58 秒 | 24 fps / 5.04 秒 (121 幀) | 兩者時長皆精準對應社群前置開場與廣告鏡頭節奏 |
| **原生中文口白** | 🟢 **完整支援 (自然對白)** | 🔴 僅環境音效 (需後製配音) | MiniMax 原生口白對白是一大殺手鐧，大幅節省剪輯時間 |
| **運鏡與動態幅度** | 穩健微推 (主體外觀穩定) | **大動態推進 (立體景深透視)** | 追求大片電影感選 LTX-2.5；追求商品文字標籤不變形選 H3 |
| **Colab A100 耗時** | 約 2 分鐘 (含權重拉取) | 約 1.5 分鐘 (權重快取) | 兩者在 A100 上運算速度皆極快 |
| **單次算力消耗** | **0.56 CU** | **0.47 CU** | 成本極低！Google AI Pro 200 CU 額度約可生成 **380~420 部** |

---

## 手把手安裝與使用教學

### 第一步：安裝環境與工具
本專案支援 Windows (PowerShell / CMD)、macOS 與 Linux。建議使用 Python 3.10 ~ 3.12 環境：

```bash
# 1. 複製專案庫
git clone https://github.com/PingpowerTW/colab-ai-video-studio.git
cd colab-ai-video-studio

# 2. 建立並啟動 Python 虛擬環境
python -m venv .venv
# Windows 啟動：
.venv\Scripts\activate
# macOS / Linux 啟動：
# source .venv/bin/activate

# 3. 安裝相依套件
pip install -r requirements.txt
```

---

### 第二步：登入 Google Colab CLI 與檢查額度
本工具依賴官方授權的 `google-colab-cli` 與雲端進行安全通訊：

```bash
colab --auth=oauth2 usage
```
執行後終端機會出現一組授權網址：
1. 複製該網址貼到瀏覽器，登入你的 Google 帳號（請確認該帳號具備 Google AI Pro/Ultra 或 Colab 額度）。
2. 同意存取授權後，畫面會顯示一串驗證碼。
3. 將驗證碼複製貼回終端機按 Enter。
4. 驗證成功後會顯示目前的運算額度，例如：
   ```
   Current balance: 200.00 compute units
   Usage rate: 0.00/hr
   Active assignments: 0
   ```

---

### 第三步：設定 Hugging Face Token (供 LTX-2.5 授權)
由於 Lightricks LTX-2.5 官方權重為 Gated Model，請先至以下頁面點選同意授權協議：
- [Lightricks/LTX-2.5 官方頁面](https://huggingface.co/Lightricks/LTX-2.5)

接著複製專案內的範本建立 `.env` 檔案：
```bash
cp .env.example .env
```
使用文字編輯器打開 `.env` 並填入你的 Hugging Face Token：
```ini
HF_TOKEN=hf_你的HuggingFace存取Token
COLAB_AUTH=oauth2
```

---

### 第四步：開始生成影片！

**生成 MiniMax H3 產品短片（自帶中文口白）**：
```bash
python scripts/run_minimax_paoguo.py
```

**生成 LTX-2.5 22B 電影級高畫質短片**：
```bash
python scripts/run_ltx25_paoguo.py
```

> **使用小技巧**：
> 影片生成完成後，調度腳本除了會在終端機印出詳細的解析度與時長資訊外，在 Windows 環境下還會**自動呼叫檔案總管並高亮選取剛下載好的 MP4 檔案**，直接按空白鍵或連點兩下即可馬上驗收成果！

---

## 算力消耗實測與省錢機制說明

很多讀者最關心的就是：「跑雲端 GPU 會不會不小心扣很多錢？」

答案是：**完全不用擔心！**

1. **秒級斷開保護機制**：
   本專案的 Python 調度器（`scripts/runner.py`）內建嚴格的工作階段生命週期防護。在推論結束、將 MP4 檔案完整下載回本地硬碟之後，會立即在 `finally` 區塊強制呼叫 `colab stop` 釋放雲端執行個體。
2. **極致低成本**：
   實測在 Colab A100 High-Mem 環境下：
   - MiniMax H3 跑一次消耗 **0.56 CU**。
   - LTX-2.5 22B 跑一次消耗 **0.47 CU**。
   每個月 Google AI Pro 贈送的 200 CU 算力，足以讓你從容產出超過 350 部以上的宣傳短影片，完全不需要額外花錢加購！

---

## 常見問題與除錯心得 (FAQ)

### Q1：下載大模型時出現 ReadTimeout 斷線錯誤？
- **解答**：`google-colab-cli` 預設的通訊 timeout 僅有 10 秒，當雲端在下載 60GB 規模的大模型時容易逾時。本專案已在核心腳本中全域注入 `REQUEST_TIMEOUT=300`（5 分鐘），並最佳化通訊層，確保權重下載過程穩定流暢。

### Q2：執行時出現 matplotlib inline 後端衝突？
- **解答**：Colab 預設會在 ipykernel 中注入 `module://matplotlib_inline.backend_inline`，這會導致部分在虛擬環境執行的腳本報錯。本專案的自動化 Notebook 已加入環境變數淨化邏輯（強制指定 `MPLBACKEND=Agg`），無需手動調整即可順暢運行。

### Q3：LTX-2.5 提示缺少 duration-head 權重？
- **解答**：LTX-2.5 22B 依賴專屬的時序補丁權重 `ltx-2.5-duration-head-bf16.safetensors`。本專案已將下載清單與推論參數全面對齊官方最新發布標準，一鍵即可完成所有模組拉取。

---

## 開源協議
- 本專案排程與本地調度程式庫採用 Apache 2.0 協議開源。
- 衍生生成之影片與各模型之商用權利，請遵循 [Lightricks LTX-2.5 授權規範](https://huggingface.co/Lightricks/LTX-2.5) 及 [MiniMax 開放社群規範](https://github.com/killkli/minimax-h3-colab-skill)。
