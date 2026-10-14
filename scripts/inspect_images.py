import zipfile
import re
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

docx_path = r'C:\Users\HYC\Downloads\期末報告_屏東縣黎明社區發展協會.docx'
with zipfile.ZipFile(docx_path, 'r') as z:
    content = z.read('word/document.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')

targets = [
    'image42.jpeg', 'image43.jpeg', 'image44.jpeg', 'image52.jpeg',
    'image55.jpeg', 'image56.jpeg', 'image57.jpeg', 'image58.jpeg',
    'image20.jpeg', 'image25.jpeg', 'image31.jpeg', 'image36.jpeg', 'image6.jpeg'
]

for target_img in targets:
    pattern = r'Id="([^"]+)"[^>]*Target="media/' + target_img + r'"'
    m = re.search(pattern, rels)
    if m:
        rid = m.group(1)
        pos = content.find(rid)
        if pos != -1:
            snippet = content[max(0, pos-200):min(len(content), pos+400)]
            clean = re.sub(r'<[^>]+>', '', snippet)
            print(f"=== {target_img} ({rid}) ===")
            print(clean.strip())
