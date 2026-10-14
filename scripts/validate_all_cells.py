import json

nb = json.load(open("assets/LTX_2_5_Colab.ipynb", encoding="utf-8"))
for i, cell in enumerate(nb["cells"]):
    if cell.get("cell_type") == "code":
        raw = "".join(cell.get("source", []))
        # Remove shell lines starting with !
        py_lines = []
        for line in raw.splitlines():
            if line.strip().startswith("!"):
                py_lines.append("# " + line)
            else:
                py_lines.append(line)
        code = "\n".join(py_lines)
        try:
            compile(code, f"cell_{i}", "exec")
            print(f"Cell {i} syntax OK")
        except Exception as e:
            print(f"Cell {i} ERROR: {e}")
            raise
print("ALL CELLS ARE 100% SYNTACTICALLY VALID!")
