"""Rebuild reviewed sign illustrations from a pinned official Alberta handbook.
Requires optional PyMuPDF. Run with --pdf pointing to the official 2026 PDF.
Only approved image paths in the source-controlled manifest are generated.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]

def rebuild(pdf_path, manifest_path=None):
    import pymupdf
    manifest_path=Path(manifest_path or ROOT/'tools'/'sign_assets.json')
    manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    raw=Path(pdf_path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=manifest['source_pdf_sha256']:
        raise ValueError('Handbook checksum changed; review the source and crop positions before rebuilding')
    with pymupdf.open(stream=raw,filetype='pdf') as document:
        for asset in manifest['assets']:
            name=asset['file']
            if not re.fullmatch(r'[a-z0-9-]+\.svg',name):
                raise ValueError('Invalid output filename')
            page=document[asset['pdf_page']-1]
            x0,y0,x1,y1=asset['rect_reference_pixels']
            # Coordinates were visually reviewed on the 504 x 796 handbook-page rendering.
            clip=pymupdf.Rect(x0*page.rect.width/504,y0*page.rect.height/796,x1*page.rect.width/504,y1*page.rect.height/796)
            if clip.is_empty or not page.rect.contains(clip):
                raise ValueError('Crop is outside its source page')
            pixmap=page.get_pixmap(matrix=pymupdf.Matrix(4,4),clip=clip,alpha=False)
            png=pixmap.tobytes('png')
            asset['png_sha256']=hashlib.sha256(png).hexdigest()
            encoded=base64.b64encode(png).decode('ascii')
            svg=('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d">\n'
                 '<title>Driver handbook illustration, printed page %d</title>\n'
                 '<image width="%d" height="%d" href="data:image/png;base64,%s"/>\n</svg>\n') % (pixmap.width,pixmap.height,asset['printed_page'],pixmap.width,pixmap.height,encoded)
            (ROOT/'images'/name).write_text(svg,encoding='utf-8')
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return len(manifest['assets'])

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pdf',required=True)
    args=parser.parse_args()
    print('Rebuilt %d reviewed handbook illustrations.' % rebuild(args.pdf))
