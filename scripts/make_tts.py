import asyncio
import os
from pathlib import Path
import edge_tts

VOICEOVER_SCRIPTS = [
    ("shot1", "你敢信？這酸爽的一口，居然是「鹹」的！"),
    ("shot2", "台灣在地鮮果「芒果青」正式上市囉！用的是真正的青芒果，不是熟芒果喔！"),
    ("shot3", "以天然果酸搭配在地醋醃製，保留青芒果特有的脆口，酸香清爽，完全不會膩。"),
    ("shot4", "來自黎明村的滋味，由社區銀髮長者親手削皮切片。將疏果變身為永續美味，每一口都有溫度。"),
    ("shot5", "酸甜開胃，越吃越涮嘴！不管是當佐餐聖品，還是追劇零嘴，都超適合。"),
    ("shot6", "不加防腐劑，安心食用。每瓶 400公克只要 250元，趕快把握機會！"),
    ("shot7", "喜歡這口台灣好味道嗎？點擊連結帶回家！"),
]

OUTPUT_DIR = Path("d:/AI/Code/movie/assets/tts_audio")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

async def generate_all():
    # 使用台灣自然生動女聲
    voice = "zh-TW-HsiaoChenNeural"
    for name, text in VOICEOVER_SCRIPTS:
        out_file = OUTPUT_DIR / f"{name}.mp3"
        print(f"正在生成 {name}: {text}")
        communicate = edge_tts.Communicate(text, voice, rate="+5%")
        await communicate.save(str(out_file))
        print(f"  已儲存至 {out_file}")

if __name__ == "__main__":
    asyncio.run(generate_all())
