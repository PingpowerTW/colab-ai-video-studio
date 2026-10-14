import zipfile
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

with zipfile.ZipFile(r'C:\Users\HYC\Downloads\期末報告_屏東縣黎明社區發展協會.docx', 'r') as z:
    content = z.read('word/document.xml').decode('utf-8')
    rels = z.read('word/_rels/document.xml.rels').decode('utf-8')

for f in ['image1.jpeg', 'image6.jpeg', 'image13.png', 'image15.png', 'image16.png', 'image17.png', 'image20.jpeg', 'image21.png', 'image25.jpeg', 'image31.jpeg', 'image36.jpeg', 'image37.jpeg']:
    m = re.search(r'Id="([^"]+)"[^>]*Target="media/' + f + r'"', rels)
    if m:
        rid = m.group(1)
        pos = content.find(rid)
        if pos != -1:
            p_start = content.rfind('<w:p ', 0, pos)
            p_end = content.find('</w:p>', pos)
            chunk = content[max(0, p_start-200):min(len(content), p_end+300)]
            clean = re.sub(r'<[^>]+>', ' ', chunk)
            clean = ' '.join(clean.split())
            print(f'{f} ({rid}): {clean[:120]}')
