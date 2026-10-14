import json

path = "assets/LTX_2_5_Colab.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Cell 2: dependencies
nb["cells"][2]["source"] = [
    "# Install dependencies for LTX-Video\n",
    "!pip install -q --upgrade pip\n",
    "!pip uninstall -y torchao\n",
    '!pip install -q "diffusers>=0.41.0" "transformers>=4.48.0" accelerate sentencepiece torchvision torchaudio huggingface_hub\n',
    'print("Dependencies installed successfully.")\n'
]

# Cell 4: replace any non-ascii or tilde
cell4_src = []
for line in nb["cells"][4]["source"]:
    line = line.replace('\u2248', '~')
    cell4_src.append(line)
nb["cells"][4]["source"] = cell4_src

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Notebook updated cleanly!")
