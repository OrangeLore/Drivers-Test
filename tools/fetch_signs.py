#!/usr/bin/env python3
"""
fetch_signs.py — download REAL, public-domain official road-sign images into images/ so the app
shows genuine signs (US MUTCD / Wikimedia Commons), never hand-drawn or synthesized ones.

Driven by tools/sign_sources.json:  { "stop.svg": "https://.../Stop_sign.svg", ... }
Only put public-domain / freely-licensed source URLs in that file. Run once:

    python tools/fetch_signs.py

Filenames must match what the question sets reference (see tools/sign_library.json). Diagram-style
illustrations (intersection/right-of-way scenarios) have no standard public-domain equivalent and
are intentionally left out — those questions stay text-only unless a real figure is extracted from a
handbook PDF via extract_figures.py.
"""
import json, os, re, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
IMAGES = os.path.join(os.path.dirname(HERE), "images")
SOURCES = os.path.join(HERE, "sign_sources.json")

def validate_source(filename, url):
    parsed = urllib.parse.urlsplit(url)
    if not re.fullmatch(r'[a-zA-Z0-9_-]+\.svg', filename) or parsed.scheme != 'https' or parsed.hostname not in ('commons.wikimedia.org', 'upload.wikimedia.org') or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Only safe SVG filenames and HTTPS Wikimedia sources are allowed')

def validate_svg(data):
    from defusedxml import ElementTree as ET
    text = data.decode('utf-8')
    # Parse only UTF-8 text after rejecting NULs and all DTD/entity declarations.
    # This prevents entity expansion and alternate-encoding declaration bypasses.
    if '\x00' in text or '<!DOCTYPE' in text.upper() or '<!ENTITY' in text.upper():
        raise ValueError('SVG declarations are not allowed')
    root = ET.fromstring(text)
    if root.tag.split('}')[-1] != 'svg':
        raise ValueError('SVG required')
    for element in root.iter():
        if element.tag.split('}')[-1].lower() in ('script', 'foreignobject', 'iframe', 'style', 'animate', 'set', 'animatetransform', 'animatemotion'):
            raise ValueError('Active SVG content is not allowed')
        for key, value in element.attrib.items():
            name = key.split('}')[-1].lower()
            if name.startswith('on') or (name in ('href', 'src') and not value.startswith('#')) or 'javascript:' in value.lower() or re.search(r'url\(\s*[\'"]?[^#]', value, re.I):
                raise ValueError('External or active SVG attributes are not allowed')

def main():
    src = json.load(open(SOURCES, encoding="utf-8"))
    os.makedirs(IMAGES, exist_ok=True)
    ok = fail = skip = 0
    for fn, url in src.items():
        if fn.startswith("_"):
            continue
        if not url:
            print("skip (no url yet):", fn); skip += 1; continue
        try:
            validate_source(fn, url)
            class SafeRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    validate_source(fn, newurl)
                    return super().redirect_request(req, fp, code, msg, headers, newurl)
            req = urllib.request.Request(url, headers={"User-Agent": "driver-practice-test/1.0"})
            opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), SafeRedirect())
            with opener.open(req, timeout=30) as response:
                data = response.read(2 * 1024 * 1024 + 1)
            if len(data) > 2 * 1024 * 1024:
                raise ValueError('Image exceeds limit')
            validate_svg(data)
            with open(os.path.join(IMAGES, fn), "wb") as f:
                f.write(data)
            print("saved", fn, "(%d bytes)" % len(data)); ok += 1
        except Exception as e:
            print("FAIL", fn, "->", e); fail += 1
    print("done: %d saved, %d skipped, %d failed" % (ok, skip, fail))

if __name__ == "__main__":
    main()
