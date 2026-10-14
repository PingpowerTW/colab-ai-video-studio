import json

path = "assets/LTX_2_5_Colab.ipynb"
with open(path, "r", encoding="utf-8") as f:
    nb = json.load(f)

# Update cell 5 (index 4 or find code cell)
for cell in nb["cells"]:
    if cell.get("cell_type") == "code" and any("LTXImageToVideoPipeline" in line for line in cell.get("source", [])):
        new_source = []
        for line in cell["source"]:
            if "target_w = 704" in line:
                new_source.append("    target_w = 768\n")
            elif "target_h = 480" in line:
                new_source.append("    target_h = 512\n")
            elif "'guidance_scale': 3.0," in line:
                new_source.append("        'guidance_scale': 3.5,\n")
            elif "'negative_prompt':" in line:
                new_source.append("        'negative_prompt': 'worst quality, inconsistent motion, blurry, jittery, distorted, static, frozen frame, deformed, lowres',\n")
            elif "if is_i2v:" in line:
                new_source.append("    import inspect\n")
                new_source.append("    call_params = inspect.signature(pipe.__call__).parameters\n")
                new_source.append("    if 'decode_timestep' in call_params:\n")
                new_source.append("        kwargs['decode_timestep'] = 0.05\n")
                new_source.append("    if 'image_cond_noise_scale' in call_params:\n")
                new_source.append("        kwargs['image_cond_noise_scale'] = 0.025\n")
                new_source.append("    \n")
                new_source.append(line)
            else:
                new_source.append(line)
        cell["source"] = new_source
        break

with open(path, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

print("Updated LTX_2_5_Colab.ipynb with high-fidelity parameters successfully!")
