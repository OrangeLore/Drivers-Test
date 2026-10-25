#!/usr/bin/env python3
"""
extract_figures.py — pull REAL sign/diagram figures out of a handbook PDF so they can be
shown on the test (instead of only matched SVGs).

Two strategies, run together:
  (A) embedded rasters  — page.get_images(): clean, per-figure. Works when the handbook stores
      each sign as its own bitmap (common in many US state handbooks).
  (B) rendered regions  — render each page to a bitmap (PyMuPDF), then use OpenCV to find
      figure-sized coloured/graphic regions and crop them. Needed for vector-drawn signs, but
      noisier (text and multi-sign pages produce imperfect crops).

Outputs PNG crops + a manifest.json mapping {file, page, bbox, source}. OCR (tesseract) is used
only to label crops if the binary is installed; it's optional.

Usage:
  python tools/extract_figures.py --pdf handbook.pdf --out figures_out [--pages 26-40] [--dpi 200]
"""
import argparse, json, os, sys

def parse_pages(spec, n):
    if not spec:
        return range(n)
    out = set()
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-"); out.update(range(int(a) - 1, int(b)))
        else:
            out.add(int(part) - 1)
    return sorted(p for p in out if 0 <= p < n)

def main():
    import fitz            # PyMuPDF
    import numpy as np
    import cv2
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pages", default="")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--min-frac", type=float, default=0.02, help="min region area as fraction of page")
    ap.add_argument("--max-frac", type=float, default=0.45, help="max region area as fraction of page")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    doc = fitz.open(a.pdf)
    pages = parse_pages(a.pages, doc.page_count)
    manifest, n_embed, n_render = [], 0, 0

    for pi in pages:
        page = doc[pi]
        # (A) embedded raster images
        for j, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            try:
                pix = fitz.Pixmap(doc, xref)
                if pix.n >= 5:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                if pix.width < 40 or pix.height < 40:
                    continue
                fn = "p%03d_embed_%d.png" % (pi + 1, j)
                pix.save(os.path.join(a.out, fn))
                manifest.append({"file": fn, "page": pi + 1, "type": "embedded",
                                 "w": pix.width, "h": pix.height})
                n_embed += 1
            except Exception:
                continue

        # (B) rendered-region crops
        zoom = a.dpi / 72.0
        pm = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        arr = np.frombuffer(pm.samples, dtype=np.uint8).reshape(pm.height, pm.width, pm.n)
        rgb = arr[:, :, :3]
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        # graphic mask: non-white pixels; dilate to join sign parts, ignore thin text via close/open
        mask = (gray < 245).astype("uint8") * 255
        k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, pm.width // 120), max(3, pm.height // 120)))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2)
        cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        page_area = pm.width * pm.height
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            area = w * h
            frac = area / page_area
            ar = w / float(h)
            if frac < a.min_frac or frac > a.max_frac:
                continue
            if ar < 0.4 or ar > 2.6:   # signs are roughly squarish; skip long text bands
                continue
            crop = rgb[y:y + h, x:x + w]
            fn = "p%03d_region_%d_%d.png" % (pi + 1, x, y)
            cv2.imwrite(os.path.join(a.out, fn), cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
            manifest.append({"file": fn, "page": pi + 1, "type": "render",
                             "bbox": [int(x), int(y), int(w), int(h)]})
            n_render += 1

    json.dump({"pdf": os.path.basename(a.pdf), "pages": len(pages),
               "embedded": n_embed, "render_regions": n_render, "items": manifest},
              open(os.path.join(a.out, "manifest.json"), "w"), indent=2)
    print("pages=%d embedded=%d render_regions=%d -> %s" % (len(pages), n_embed, n_render, a.out))

if __name__ == "__main__":
    main()
