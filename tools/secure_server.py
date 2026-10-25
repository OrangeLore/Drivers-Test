"""Loopback-first server. Public mode has no shared data or generation APIs."""
import base64
import binascii
from collections import deque
from functools import partial
import hmac
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time
from urllib.parse import unquote, urlsplit, parse_qs

import generator

PROJECT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = frozenset(('index.html', 'questions.js', 'questions_more.js', 'ontario.js', 'app.js', 'app.css', 'security.js'))
MAX_BODY = 16 * 1024 * 1024
MAX_STORE = 4 * 1024 * 1024


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 16

    def __init__(self, address, handler, password, data_dir, generation, allowed_hosts):
        self.password = password
        self.data_dir = Path(data_dir).resolve()
        self.generation = bool(password) and generation
        self.allowed_hosts = set(allowed_hosts)
        self.allow_tunnel = os.environ.get('AC7_ALLOW_TUNNEL') == '1'
        self.lock = threading.RLock()
        self.jobs = {}
        self.auth_failures = deque(maxlen=100)
        self.slots = threading.BoundedSemaphore(24)
        html = (PROJECT / 'index.html').read_text(encoding='utf-8')
        self.script_hashes = ' '.join("'sha256-" + base64.b64encode(hashlib.sha256(script.encode()).digest()).decode() + "'" for script in re.findall(r'<script>(.*?)</script>', html, re.S))
        super().__init__(address, handler)
        self.allowed_origins = {'http://127.0.0.1:' + str(self.server_port), 'http://localhost:' + str(self.server_port)} | {o.strip() for o in os.environ.get('AC7_ALLOWED_ORIGINS', '').split(',') if o.strip()}

    def process_request(self, request, address):
        if not self.slots.acquire(blocking=False):
            request.close()
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.slots.release()

    def load_store(self):
        file = self.data_dir / 'kv.json'
        if not file.exists():
            return {}
        if file.stat().st_size > MAX_STORE:
            raise ValueError('Store exceeds limit')
        with file.open(encoding='utf-8') as handle:
            value = json.load(handle)
        if not isinstance(value, dict):
            raise ValueError('Invalid store')
        return value

    def save_store(self, value):
        data = json.dumps(value, ensure_ascii=True).encode()
        if len(data) > MAX_STORE:
            raise ValueError('Store exceeds limit')
        self.data_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary = self.data_dir / ('kv-' + secrets.token_hex(8) + '.tmp')
        try:
            with temporary.open('xb') as handle:
                handle.write(data)
            os.replace(temporary, self.data_dir / 'kv.json')
        finally:
            temporary.unlink(missing_ok=True)


class Handler(SimpleHTTPRequestHandler):
    server_version = 'PracticeServer'
    sys_version = ''

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def end_headers(self):
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self' " + self.server.script_hashes + "; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; font-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'; object-src 'none'")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def log_message(self, *args):
        pass  # Never log request contents, credentials, profile names or paths.

    def _json(self, value, status=200):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(data)

    def _host_ok(self):
        try:
            host = urlsplit('//' + self.headers.get('Host', '')).hostname
        except ValueError:
            return False
        return bool(host) and (host in self.server.allowed_hosts or (self.server.allow_tunnel and host.endswith('.trycloudflare.com')))

    def _authorize(self):
        if not self._host_ok():
            self._json({'error': 'Host not allowed'}, 403)
            return False
        if not self.server.password:
            return True
        with self.server.lock:
            now = time.monotonic()
            while self.server.auth_failures and self.server.auth_failures[0] < now - 60:
                self.server.auth_failures.popleft()
            limited = len(self.server.auth_failures) >= 20
        if limited:
            self._json({'error': 'Too many authentication failures; retry later'}, 429)
            return False
        try:
            kind, encoded = self.headers.get('Authorization', '').split(' ', 1)
            decoded = base64.b64decode(encoded, validate=True).decode('utf-8')
            valid = kind.lower() == 'basic' and hmac.compare_digest(decoded.encode(), ('user:' + self.server.password).encode())
        except (ValueError, UnicodeError, binascii.Error):
            valid = False
        if valid:
            return True
        with self.server.lock:
            self.server.auth_failures.append(now)
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Private practice", charset="UTF-8"')
        self.send_header('Content-Length', '0')
        self.end_headers()
        return False

    def _asset(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/':
            path = '/index.html'
        parts = path.lstrip('/').split('/')
        if '\\' in path or any(not p or p.startswith('.') or ':' in p for p in parts):
            return False
        relative = '/'.join(parts)
        allowed = relative in PUBLIC_FILES or (len(parts) == 2 and parts[0] == 'images' and Path(parts[-1]).suffix.lower() in ('.svg', '.png', '.jpg', '.jpeg', '.webp'))
        root = Path(self.directory).resolve()
        target = root.joinpath(*parts)
        return allowed and not target.is_symlink() and target.resolve().is_relative_to(root) and target.is_file()

    def do_HEAD(self):
        if not self._authorize():
            return
        if not self._asset():
            return self._json({'error': 'Not found'}, 404)
        return super().do_HEAD()

    def do_GET(self):
        if not self._authorize():
            return
        parsed = urlsplit(self.path)
        route = parsed.path
        if route == '/api/health':
            return self._json({'ok': True, 'storage': 'shared' if self.server.password else 'browser', 'generation': self.server.generation, 'ollama': self.server.generation, 'model': 'local-model' if self.server.generation else ''})
        if route.startswith('/api/'):
            if not self.server.password:
                return self._json({'error': 'Not found'}, 404)
            if route == '/api/kv/all':
                try:
                    with self.server.lock:
                        return self._json(self.server.load_store())
                except (OSError, ValueError):
                    return self._json({'error': 'Store unavailable'}, 503)
            if route == '/api/job':
                job_id = (parse_qs(parsed.query).get('id') or [''])[0]
                with self.server.lock:
                    job = self.server.jobs.get(job_id)
                    return self._json(dict(job) if job else {'error': 'Not found'}, 200 if job else 404)
            return self._json({'error': 'Not found'}, 404)
        if not self._asset():
            return self._json({'error': 'Not found'}, 404)
        return super().do_GET()

    def _body(self):
        if self.headers.get('Transfer-Encoding'):
            raise ValueError('Transfer encoding not supported')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            raise ValueError('Invalid content length')
        if not 0 < length <= MAX_BODY:
            raise ValueError('Body size out of range')
        data = self.rfile.read(length)
        if len(data) != length:
            raise ValueError('Incomplete request')
        if self.headers.get_content_type() != 'application/json':
            raise ValueError('JSON required')
        value = json.loads(data)
        if not isinstance(value, dict):
            raise ValueError('JSON object required')
        return value

    def do_OPTIONS(self):
        return self._json({'error': 'Not allowed'}, 405)

    def do_POST(self):
        # Authenticate before allocating or waiting for an upload body.
        if not self._authorize():
            return
        if not self.server.password:
            # Public mode accepts no uploads; drain only already-small requests for clean TCP close.
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if 0 < length <= 8192:
                    self.rfile.read(length)
            except (ValueError, OSError):
                pass
            return self._json({'error': 'Not found'}, 404)
        try:
            body = self._body()
        except (ValueError, OSError):
            return self._json({'error': 'Invalid request body'}, 400)
        origin = self.headers.get('Origin')
        if not origin or origin not in self.server.allowed_origins:
            return self._json({'error': 'Origin not allowed'}, 403)
        if self.headers.get('Sec-Fetch-Site') in ('cross-site', 'same-site') or self.headers.get('X-AC7-Request') != '1':
            return self._json({'error': 'Same-origin application request required'}, 403)
        route = urlsplit(self.path).path
        if route == '/api/kv':
            key = body.get('k')
            if not isinstance(key, str) or not re.fullmatch(r'ac7_[a-zA-Z0-9_-]{1,120}', key):
                return self._json({'error': 'Invalid key'}, 400)
            if not body.get('delete') and (not isinstance(body.get('v'), str) or len(body['v']) > MAX_STORE):
                return self._json({'error': 'Invalid value'}, 400)
            try:
                with self.server.lock:
                    store = self.server.load_store()
                    if body.get('delete'):
                        store.pop(key, None)
                    else:
                        store[key] = body['v']
                    self.server.save_store(store)
                return self._json({'ok': True})
            except (OSError, ValueError):
                return self._json({'error': 'Store unavailable or limit exceeded'}, 503)
        if route != '/api/generate':
            return self._json({'error': 'Not found'}, 404)
        if not self.server.generation:
            return self._json({'error': 'Generation disabled'}, 403)
        key = body.get('key')
        name = body.get('name')
        target = body.get('target', 330)
        if not isinstance(key, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,39}', key) or not isinstance(name, str) or not 1 <= len(name) <= 100 or type(target) is not int or not 1 <= target <= 500:
            return self._json({'error': 'Invalid generation parameters'}, 400)
        try:
            pdf = base64.b64decode(body['pdf_base64'], validate=True) if body.get('pdf_base64') else None
            text = body.get('text')
            if pdf and (len(pdf) > 10 * 1024 * 1024 or not pdf.startswith(b'%PDF-')):
                raise ValueError()
            if not pdf and (not isinstance(text, str) or not 1 <= len(text) <= 200000):
                raise ValueError()
        except (ValueError, TypeError, binascii.Error):
            return self._json({'error': 'Invalid source document'}, 400)
        with self.server.lock:
            now = time.monotonic()
            for jid in list(self.server.jobs):
                if self.server.jobs[jid].get('_expires', now + 1) < now:
                    del self.server.jobs[jid]
            if any(job['status'] == 'running' for job in self.server.jobs.values()) or len(self.server.jobs) >= 4:
                return self._json({'error': 'Generator busy; retry later'}, 429)
            jid = secrets.token_hex(16)
            self.server.jobs[jid] = {'status': 'running', 'progress': 0, 'count': 0, 'message': 'Starting'}
        threading.Thread(target=self._generate, args=(jid, body, pdf, text), daemon=True).start()
        return self._json({'jobId': jid})

    def _generate(self, jid, body, pdf, text):
        def progress(i, total, count, message):
            with self.server.lock:
                self.server.jobs[jid].update(progress=int(i / total * 100) if total else 0, count=count, message='Processing handbook')
        try:
            meta = {k: body[k] for k in ('key', 'name', 'jurisdiction', 'testSize', 'passMark', 'sections') if k in body}
            dataset = generator.run_full(pdf_bytes=pdf, text=text, meta=meta, model=os.environ.get('AC7_MODEL', 'local-model'), target=body.get('target', 330), progress=progress)
            if not dataset['questions']:
                raise ValueError('No supported questions')
            update = {'status': 'done', 'progress': 100, 'count': len(dataset['questions']), 'message': 'Complete', 'dataset': dataset}
        except Exception:
            update = {'status': 'error', 'error': 'Generation failed; check your local model and handbook', 'message': 'Generation failed'}
        with self.server.lock:
            self.server.jobs[jid].update(update, _expires=time.monotonic() + 1800)


def create_server(port=8000, password=None, data_dir=None, generation=None):
    password = os.environ.get('AC7_PASSWORD', '') if password is None else password
    if password and len(password) < 16:
        raise ValueError('AC7_PASSWORD must contain at least 16 characters')
    default_data = Path(os.environ.get('LOCALAPPDATA', str(Path.home() / '.local' / 'share'))) / 'driver-practice' / 'store'
    data_dir = data_dir or os.environ.get('AC7_DATA_DIR') or default_data
    if Path(data_dir).resolve().is_relative_to(PROJECT):
        raise ValueError('Data directory must be outside the source tree')
    host = os.environ.get('AC7_BIND', '127.0.0.1')
    if host not in ('127.0.0.1', '::1'):
        raise ValueError('Only loopback binding is supported; use an HTTPS tunnel')
    allowed = {'localhost', '127.0.0.1', '::1'} | {h.strip().lower() for h in os.environ.get('AC7_ALLOWED_HOSTS', '').split(',') if h.strip()}
    generation = os.environ.get('AC7_ENABLE_GENERATION') == '1' if generation is None else generation
    return Server((host, port), partial(Handler, directory=str(PROJECT)), password, data_dir, generation, allowed)


def main():
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get('AC7_PORT', '8000'))
    with create_server(port) as server:
        mode = 'password-protected shared' if server.password else 'public browser-only'
        print('Practice app on http://127.0.0.1:%d (%s)' % (server.server_port, mode), flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
