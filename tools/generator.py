#!/usr/bin/env python3
"""
generator.py — the ONE generic pipeline that turns ANY driver's-handbook PDF (or text)
into a complete test set for the app. Used by both the in-app import server (app_server.py)
and the CLI (generate_dataset.py). Offline: local Ollama model only.

Stages: identify reviewed source pictures -> extract/chunk -> grounded text generation ->
dedupe (including picture identity) -> dataset. No guessed or AI-drawn sign attachments.
"""
import base64, io, json, os, re, urllib.request

LLM_URL = os.environ.get("AC7_LLM_URL", "http://localhost:1234/v1")  # LM Studio (OpenAI-compatible)
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)

def _load_library():
    try:
        lib = json.load(open(os.path.join(HERE, "sign_library.json"), encoding="utf-8"))
        syn = []
        for s in lib.get("signs", []):
            for name in s.get("synonyms", []):
                syn.append((name.lower(), s["file"]))
        # longest synonyms first for better matching
        syn.sort(key=lambda x: -len(x[0]))
        return syn
    except Exception:
        return []

SIGN_SYNONYMS = _load_library()

PROMPT = """You are writing a multiple-choice practice test for a driver's licence knowledge exam.
You are given ONE passage from an official handbook. Derive questions ONLY from THIS passage.
Do NOT use any outside knowledge. If the passage does not clearly support a question, do not write it.

Write up to {n} clear multiple-choice questions that a new driver must know.
For EACH question:
- Exactly 4 options; exactly ONE correct; wrong options plausible but clearly wrong per the passage.
- Include a "quote": a SHORT word-for-word snippet copied verbatim from the passage that proves the
  correct answer (5-20 words, copied exactly, no paraphrasing). If you cannot copy such a quote from
  THIS passage, do not include that question.
- Write text-only questions that stand on their own. Do not refer to "this sign", a picture,
  a diagram or an illustration; do not invent or supply image URLs or sign artwork.
- "section":"signs" for sign-identification questions, else "section":"rules".
Return STRICT JSON only — a JSON array; each element:
  {{"q":"...","options":["A","B","C","D"],"answer":<0-3>,"topic":"short topic","difficulty":"easy|standard|hard","section":"signs|rules","quote":"verbatim snippet from the passage"}}
No prose, no markdown fences — JSON array only.

PASSAGE:
\"\"\"
{chunk}
\"\"\"
"""

# ---------- extraction ----------
def extract_text_from_bytes(pdf_bytes):
    from pypdf import PdfReader
    r = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for i, p in enumerate(r.pages):
        t = p.extract_text() or ""
        if t.strip():
            pages.append((i + 1, t))
    return pages

def extract_text_from_pdf(path):
    return extract_text_from_bytes(open(path, "rb").read())

def pages_from_plaintext(text):
    # split long text into pseudo-pages of ~3000 chars
    out, i, n = [], 0, 0
    while i < len(text):
        n += 1
        out.append((n, text[i:i + 3000]))
        i += 3000
    return out

def chunk_pages(pages, target_chars=6000):
    chunks, buf, start = [], "", None
    for pn, t in pages:
        if start is None:
            start = pn
        buf += "\n[page %s]\n%s" % (pn, t)
        if len(buf) >= target_chars:
            chunks.append((start, pn, buf)); buf, start = "", None
    if buf.strip():
        chunks.append((start, pages[-1][0] if pages else 0, buf))
    return chunks

# ---------- format auto-detect ----------
def detect_format(full_text):
    t = full_text.lower()
    fmt = {"testSize": 30, "passMark": 24, "sections": None, "confidence": "low"}
    # two-section (Ontario-style): "20 ... signs" and "20 ... rules"
    if re.search(r"20\s+(questions\s+)?(on\s+)?(road\s+)?signs", t) and re.search(r"20\s+(questions\s+)?(on\s+)?(the\s+)?(road\s+)?rules", t):
        fmt = {"testSize": 40, "passMark": 32,
               "sections": [{"key": "signs", "name": "Signs", "size": 20, "pass": 16},
                            {"key": "rules", "name": "Rules of the Road", "size": 20, "pass": 16}],
               "confidence": "medium"}
        return fmt
    m = re.search(r"(\d{2,3})\s+(multiple[- ]choice\s+)?questions", t)
    if m:
        fmt["testSize"] = int(m.group(1)); fmt["confidence"] = "medium"
    pm = re.search(r"(\d{2})\s*%|(\d{1,2})\s+(?:out\s+of|correct)", t)
    if "80" in t and "%" in t:
        fmt["passMark"] = round(fmt["testSize"] * 0.8)
    elif "75" in t and "%" in t:
        fmt["passMark"] = round(fmt["testSize"] * 0.75)
    else:
        fmt["passMark"] = round(fmt["testSize"] * 0.8)
    return fmt

# ---------- LLM ----------
def llm_chat(model, content, timeout=90):
    # Any local OpenAI-compatible server (LM Studio, Ollama /v1, etc.) via AC7_LLM_URL.
    endpoint = urllib.parse.urlsplit(LLM_URL)
    if endpoint.scheme != 'http' or endpoint.hostname not in ('127.0.0.1', 'localhost', '::1') or endpoint.username or endpoint.password:
        raise ValueError('Only local HTTP model endpoints are supported')
    body = {"model": model or "local-model", "messages": [{"role": "user", "content": content}], "temperature": 0.2, "stream": False, "max_tokens": 4096}
    req = urllib.request.Request(LLM_URL.rstrip("/") + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError('Model redirects are disabled')
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=timeout) as resp:
        raw = resp.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('Model response exceeds limit')
        return json.loads(raw.decode())["choices"][0]["message"]["content"]

def parse_json_array(text):
    m = re.search(r"\[.*\]", text, re.S)
    if not m:
        return []
    for attempt in (m.group(0), re.sub(r",\s*([\]}])", r"\1", m.group(0))):
        try:
            return json.loads(attempt)
        except Exception:
            continue
    return []

def valid_q(q):
    return (isinstance(q, dict) and isinstance(q.get("q"), str) and q["q"].strip()
            and isinstance(q.get("options"), list) and len(q["options"]) == 4
            and all(isinstance(o, str) and o.strip() for o in q["options"])
            and len(set(o.strip().lower() for o in q["options"])) == 4
            and isinstance(q.get("answer"), int) and 0 <= q["answer"] < 4)

def _norm_text(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def grounded(quote, chunk_norm):
    """True only if the model's verbatim quote really appears in the source passage."""
    qn = _norm_text(quote)
    words = qn.split()
    if len(words) < 3 or len(qn) < 12:
        return False
    return qn in chunk_norm

def needs_picture(text):
    return bool(re.search(r'\b(?:this|that|pictured|shown|following|the)\s+(?:road\s+)?sign\b|\bsign\s+(?:shown|pictured|illustrated|above|below)\b|\b(?:picture|diagram|illustration|image)\b',text,re.I))

def ingest_samples(full_text):
    """Ingest official 'Test yourself / Answer Key' sample questions verbatim, if present.
    Conservative: only returns questions that parse cleanly with a matching answer key."""
    t = full_text
    mkey = re.search(r"answer\s*key\s*[:\-]?\s*(.+)", t, re.I)
    if not mkey:
        return []
    keymap = {}
    for num, lett in re.findall(r"(\d+)\s*[-.\s]\s*([a-dA-D])", mkey.group(1)[:400]):
        keymap[int(num)] = "abcd".index(lett.lower())
    if not keymap:
        return []
    body = t[:mkey.start()]
    blocks = re.split(r"(?m)^\s*(\d+)\.\s+", body)
    out = []
    for i in range(1, len(blocks) - 1, 2):
        num = int(blocks[i]); seg = blocks[i + 1]
        if num not in keymap:
            continue
        opts = re.findall(r"(?m)^\s*(?:[1-4]\.|[a-dA-D]\)|[a-dA-D]\.)\s*(.+)$", seg)
        qtext = seg.strip().split("\n")[0].strip()
        if len(opts) >= 4 and qtext and keymap[num] < 4 and not needs_picture(qtext):
            out.append({"q": qtext, "options": [o.strip() for o in opts[:4]],
                        "answer": keymap[num], "topic": "Sample question",
                        "diff": "standard", "section": "rules",
                        "source": "official sample questions", "grounding": "official sample question (verbatim)"})
    return out

# ---------- images ----------
def _speed_svg(num, unit="km/h"):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 240">'
           '<rect width="200" height="240" fill="#fff"/>'
           '<rect x="12" y="12" width="176" height="216" rx="14" fill="#fff" stroke="#000" stroke-width="9"/>'
           '<text x="100" y="60" font-family="Arial" font-size="26" font-weight="bold" fill="#000" text-anchor="middle">MAXIMUM</text>'
           '<text x="100" y="170" font-family="Arial" font-size="110" font-weight="bold" fill="#000" text-anchor="middle">%s</text>'
           '<text x="100" y="210" font-family="Arial" font-size="22" fill="#000" text-anchor="middle">%s</text></svg>') % (num, unit)
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)

import urllib.parse
def attach_images(questions, unit="km/h"):
    attached = 0
    for q in questions:
        sign = (q.get("sign") or "").strip().lower()
        # Use exact curated sign names, never substring guesses such as moose -> deer
        # or left lane ends -> right lane ends. Imported sets still need jurisdiction review.
        matched = None
        if sign:
            for name, file in SIGN_SYNONYMS:
                if name == sign:
                    matched = (name, file); break
        if matched:
            q["image"] = matched[1]
            q.setdefault("alt", "A standard road sign: %s." % matched[0])
            attached += 1
        q.pop("sign", None)
    return attached

# ---------- dedupe / build ----------
def _norm(s):
    return re.sub(r"[^a-z0-9 ]", "", s.lower()).strip()

def dedupe(questions):
    seen, out = set(), []
    for q in questions:
        k = (_norm(q["q"]), q.get('image') or '')
        if k in seen:
            continue
        seen.add(k); out.append(q)
    return out

def generate(model, chunks, target, per_chunk=6, progress=None):
    questions, rejected = [], 0
    for ci, (p0, p1, chunk) in enumerate(chunks):
        if len(questions) >= target:
            break
        chunk_norm = _norm_text(chunk)
        try:
            out = llm_chat(model, PROMPT.format(n=per_chunk, chunk=chunk[:12000]))
        except Exception as e:
            if progress: progress(ci, len(chunks), len(questions), "model error: %s" % e)
            continue
        for q in parse_json_array(out):
            if not valid_q(q):
                rejected += 1; continue
            if not grounded(q.get("quote", ""), chunk_norm):   # REJECT ungrounded (not in source)
                rejected += 1; continue
            # Text generation cannot supply or invent the source picture.
            if needs_picture(q['q']):
                rejected += 1; continue
            for field in ('image','imageProvenance','alt','sign'):
                q.pop(field,None)
            q["source"] = "pp. %s-%s" % (p0, p1)
            q["grounding"] = "pp. %s-%s · \"%s\"" % (p0, p1, (q.get("quote", "") or "").strip()[:120])
            q.pop("quote", None)
            q.setdefault("topic", "General")
            q["diff"] = q.pop("difficulty", "standard")
            q.setdefault("section", "rules")
            questions.append(q)
        if progress:
            progress(ci + 1, len(chunks), len(questions),
                     "generated %d grounded (rejected %d ungrounded)" % (len(questions), rejected))
    return questions[:target]

def build_dataset(meta, questions, unit="km/h"):
    questions = dedupe(questions)
    # Reviewed visual questions already contain their actual source picture.
    # Never attach a library look-alike to LLM text from an unidentified handbook.
    for question in questions:
        question.pop('sign', None)
    for i, q in enumerate(questions):
        q["id"] = i + 1
    ds = {
        "key": meta["key"], "name": meta["name"], "jurisdiction": meta.get("jurisdiction", ""),
        "testSize": meta.get("testSize", 30), "passMark": meta.get("passMark", 24),
        "sections": meta.get("sections"),
        "source": meta.get("source", "Generated from handbook via local LLM"),
        "builtin": False, "generated": True, "questions": questions,
    }
    return ds

def run_full(pdf_bytes=None, text=None, meta=None, model=None, target=330, progress=None):
    """One call: bytes/text -> full validated dataset with images and format."""
    meta = dict(meta or {})
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,39}', meta.get('key', '')):
        raise ValueError('Invalid jurisdiction key')
    if type(target) is not int or not 1 <= target <= 500:
        raise ValueError('Target must be between 1 and 500')
    model = model or os.environ.get('AC7_MODEL', 'local-model')
    pages = extract_text_from_bytes(pdf_bytes) if pdf_bytes else pages_from_plaintext(text or "")
    if not pages:
        raise RuntimeError("No extractable text (scanned PDF? needs OCR).")
    full = " ".join(t for _, t in pages)
    visual = []
    image_audit = {'status':'no_pdf','images_count':0,'message':'No source PDF was supplied; no sign pictures were guessed.'}
    if pdf_bytes:
        from handbook_images import reviewed_questions
        try:
            visual,image_audit=reviewed_questions(pdf_bytes,limit=target)
        except (OSError, ValueError, KeyError):
            image_audit={'status':'image_error','images_count':0,'message':'Reviewed picture assets are unavailable or failed validation. No substitute pictures were used.'}
    fmt = image_audit.get('test_format') or detect_format(full)
    if image_audit.get('source_title'):
        meta.setdefault('source',image_audit['source_title'])
    for k in ("testSize", "passMark", "sections"):
        meta.setdefault(k, fmt[k])
    samples = ingest_samples(full)       # official sample questions, verbatim (if any)
    if progress: progress(0,1,len(visual),image_audit['message'])
    chunks = chunk_pages(pages)
    if progress: progress(0, len(chunks), len(samples) + len(visual), "%d pages, %d chunks, %d samples, %d real-image signs; format: %s" % (len(pages), len(chunks), len(samples), len(visual), fmt))
    remaining=max(0,target-len(samples)-len(visual))
    qs=generate(model,chunks,remaining,progress=progress) if remaining else []
    ds = build_dataset(meta, (visual + samples + qs)[:target], unit=meta.get("unit", "km/h"))
    image_audit['images_count']=sum(bool(q.get('image')) for q in ds['questions'])
    ds['imageAudit']=image_audit
    if progress: progress(len(chunks), len(chunks), len(ds["questions"]), "done")
    return ds
