#!/usr/bin/env python3
"""
figures.py — reviewed handbook pictures plus optional unverified crop inspection tools.

Idea: in every driver's handbook the sign PICTURE sits next to its CAPTION text ("Stop", "Yield",
"School zone", ...). So we:
  1. render each page and find the figure regions (raster images + vector-drawn signs via OpenCV),
  2. read the page's text with positions and attach the NEAREST caption to each figure,
  3. crop the real figure out of the page and pair it with its caption.

Nearest-caption pairs are unverified candidates, NOT reliable graded answers. Automatic questions
are supplied only by checksum-identified, reviewed handbook profiles in handbook_images.py.

Requires PyMuPDF (fitz), OpenCV, numpy. Degrades to no-op if they're missing.
"""
import os, re

def _available():
    try:
        import fitz, cv2, numpy  # noqa
        return True
    except Exception:
        return False

def extract_pairs(pdf_bytes, dpi=200, min_frac=0.008, max_frac=0.35):
    """Return list of {png_bytes, caption, page, bbox_pts} for figure regions with captions."""
    import io, fitz
    import numpy as np
    import cv2
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    zoom = dpi / 72.0
    pairs = []
    for pi in range(doc.page_count):
        page = doc[pi]
        # text blocks (points): (x0,y0,x1,y1, text, block_no, block_type)
        blocks = [b for b in page.get_text("blocks") if len(b) >= 6 and (len(b) < 7 or b[6] == 0)]
        cap_blocks = []
        for b in blocks:
            txt = (b[4] or "").strip().replace("\n", " ")
            if txt and 1 <= len(txt.split()) <= 7 and len(txt) <= 60:
                cap_blocks.append((b[0], b[1], b[2], b[3], txt))
        pm = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        arr = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
        rgb = arr[:, :, :3]
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        mask = (gray < 245).astype("uint8") * 255
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, pm.width // 120), max(3, pm.height // 120)))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        page_area = pm.width * pm.height
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            frac = (w * h) / page_area
            ar = w / float(h)
            if frac < min_frac or frac > max_frac or ar < 0.45 or ar > 2.4:
                continue
            sub = hsv[y:y + h, x:x + w]
            if ((sub[:, :, 1] > 70) & (sub[:, :, 2] > 60)).mean() < 0.12:
                continue  # signs are colourful — this drops black-on-white text blocks
            # region bbox in PDF points
            rx0, ry0, rx1, ry1 = x / zoom, y / zoom, (x + w) / zoom, (y + h) / zoom
            # nearest caption: prefer a short text block just below, else closest overall
            best, best_d = None, 1e9
            for (bx0, by0, bx1, by1, txt) in cap_blocks:
                horiz_overlap = min(rx1, bx1) - max(rx0, bx0)
                below_gap = by0 - ry1
                if horiz_overlap > -20 and -5 <= below_gap <= 40:
                    d = below_gap + max(0, -horiz_overlap)
                    if d < best_d:
                        best, best_d = txt, d
            if best is None:
                cx, cy = (rx0 + rx1) / 2, (ry0 + ry1) / 2
                for (bx0, by0, bx1, by1, txt) in cap_blocks:
                    d = abs(((bx0 + bx1) / 2) - cx) + abs(((by0 + by1) / 2) - cy)
                    if d < best_d:
                        best, best_d = txt, d
            if not best:
                continue
            crop = rgb[y:y + h, x:x + w]
            ok, buf = cv2.imencode(".png", cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
            if not ok:
                continue
            pairs.append({"png_bytes": buf.tobytes(), "caption": best.strip(" .:"),
                          "page": pi + 1, "bbox_pts": [rx0, ry0, rx1, ry1]})
    return pairs

_BAD_CAP = re.compile(
    r"(\bguide\b|\bavailable\b|\bshapes\b|regulatory signs|\bcontents\b|introduction|attitude|"
    r"www\.|tel:|fax:|^\s*(figure|fig\.|page|chapter|\d))", re.I)

def build_sign_questions(pdf_bytes, key, images_root, base_url="images/gen", dpi=200, limit=60):
    """Return reviewed source pictures only. Never guess a caption or write uploaded data."""
    if not isinstance(key, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,39}', key):
        raise ValueError('Invalid jurisdiction key')
    from handbook_images import reviewed_questions
    questions,_audit=reviewed_questions(pdf_bytes,limit=limit)
    return questions,[]
