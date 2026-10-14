import zipfile
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

pptx_path = r'C:\Users\HYC\Downloads\期末成果海報及展攤範例(給社區).pptx'
with zipfile.ZipFile(pptx_path, 'r') as z:
    for n in sorted(z.namelist()):
        if n.startswith('ppt/slides/_rels/'):
            rels = z.read(n).decode('utf-8')
            slide_xml_name = n.replace('_rels/', '').replace('.rels', '')
            slide_xml = z.read(slide_xml_name).decode('utf-8') if slide_xml_name in z.namelist() else ''
            print(f'=== {slide_xml_name} ===')
            targets = re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels)
            for rid, tgt in targets:
                if 'media/' in tgt:
                    pos = slide_xml.find(rid)
                    snippet = ''
                    if pos != -1:
                        raw = slide_xml[max(0, pos-200):min(len(slide_xml), pos+200)]
                        snippet = re.sub(r'<[^>]+>', ' ', raw).strip()
                    print(f'  {tgt} ({rid}): {snippet[:80]}')
