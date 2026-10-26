"""Select source-faithful sign pictures only for a checksum-identified reviewed handbook.

No downloads, model calls, filesystem writes, approximate caption matches or AI artwork.
The bundled PNGs are the reviewed crops from that exact public handbook edition.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
IMAGES=HERE.parent/'images'


def load_profile():
    return json.loads((HERE/'sign_assets.json').read_text(encoding='utf-8'))


def reviewed_questions(pdf_bytes, limit=60):
    if type(limit) is not int or not 1<=limit<=500:
        raise ValueError('Invalid picture count')
    if not isinstance(pdf_bytes,bytes):
        raise ValueError('PDF bytes required')
    profile=load_profile()
    if hashlib.sha256(pdf_bytes).hexdigest()!=profile['source_pdf_sha256']:
        return [],{
            'status':'unreviewed_source','images_count':0,
            'message':'This handbook edition has no reviewed picture profile. Uncertain pictures were not attached; text questions still require review.',
        }
    assets=profile['assets']
    questions=[]
    for asset in assets[:limit]:
        filename=asset['file']
        if not isinstance(filename,str) or not re.fullmatch(r'[a-z0-9-]+\.svg',filename):
            raise ValueError('Invalid reviewed picture filename')
        file=IMAGES/filename
        if file.is_symlink() or file.resolve().parent!=IMAGES.resolve() or file.stat().st_size>2*1024*1024:
            raise ValueError('Invalid reviewed picture asset')
        text=file.read_text(encoding='utf-8')
        match=re.search(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"',text)
        if not match:
            raise ValueError('Reviewed picture is missing its source PNG')
        png=base64.b64decode(match.group(1),validate=True)
        if not png.startswith(bytes.fromhex('89504e470d0a1a0a')) or hashlib.sha256(png).hexdigest()!=asset['png_sha256']:
            raise ValueError('Reviewed picture checksum failed')
        question=copy.deepcopy(asset['question'])
        options=question.get('options')
        answer=question.get('answer')
        if not isinstance(question.get('q'),str) or not isinstance(question.get('alt'),str) or not isinstance(options,list) or len(options)!=4 or not all(isinstance(option,str) and option for option in options) or type(answer) is not int or not 0<=answer<4:
            raise ValueError('Reviewed picture has no valid teaching mapping')
        question['image']='data:image/png;base64,'+base64.b64encode(png).decode('ascii')
        question['source']='Alberta Driver’s Guide 2026, p. %d (PDF page %d)' % (asset['printed_page'],asset['pdf_page'])
        question['grounding']='Reviewed source-handbook picture and question mapping; '+profile['attribution']
        question['imageProvenance']={
            'status':'reviewed_source','asset':filename,'source_url':profile['source_url'],
            'pdf_page':asset['pdf_page'],'printed_page':asset['printed_page'],
            'png_sha256':asset['png_sha256'],
        }
        questions.append(question)
    return questions,{
        'status':'reviewed_source','images_count':len(questions),'available_images':len(assets),
        'source_title':profile['source_title'],'source_url':profile['source_url'],
        'jurisdiction':profile['jurisdiction'],'test_format':profile['test_format'],
        'attribution':profile['attribution'],'licence_url':profile['licence_url'],
        'message':'Recognized the reviewed Alberta 2026 handbook. Pictures reuse the verified source crops and checked question mappings, not AI drawings.',
    }
