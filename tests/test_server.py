import functools
import http.client
import importlib.util
import os
from pathlib import Path
import sys
import threading
import unittest
from http.server import ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import app_server


class PublicServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = app_server.create_server(port=0, password='')
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, method='GET', body=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        conn.request(method, path, body=body, headers=headers or {})
        response = conn.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        conn.close()
        return result

    def test_only_public_assets_are_served(self):
        for path in ['/docs/REQUIREMENTS.md', '/tools/app_server.py', '/.git/config', '/store/kv.json', '/images/', '/%2e%2e/README.md', '/images/../README.md']:
            with self.subTest(path=path):
                self.assertEqual(404, self.request(path)[0])
        self.assertEqual(200, self.request('/')[0])
        self.assertEqual(200, self.request('/images/stop.svg')[0])

    def test_public_mode_never_exposes_shared_data_or_generation(self):
        self.assertEqual(404, self.request('/api/kv/all')[0])
        self.assertEqual(404, self.request('/api/job?id=unknown')[0])
        self.assertEqual(404, self.request('/api/kv', 'POST', '{}', {'Content-Type': 'application/json'})[0])
        self.assertEqual(404, self.request('/api/generate', 'POST', '{}', {'Content-Type': 'application/json'})[0])

    def test_security_headers(self):
        status, headers, _ = self.request('/')
        self.assertEqual(200, status)
        self.assertIn("script-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual('no-store', headers['Cache-Control'])
        self.assertNotIn('Access-Control-Allow-Origin', headers)


class PrivateServerTests(PublicServerTests):
    @classmethod
    def setUpClass(cls):
        import secrets
        import tempfile
        cls.password = secrets.token_urlsafe(32)
        cls.temp = tempfile.TemporaryDirectory(dir=os.environ.get('AC7_TEST_TMP'))
        cls.server = app_server.create_server(port=0, password=cls.password, data_dir=cls.temp.name)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    def auth(self):
        import base64
        return {'Authorization': 'Basic ' + base64.b64encode(('user:' + self.password).encode()).decode(), 'X-AC7-Request':'1', 'Origin':'http://127.0.0.1:' + str(self.server.server_port)}

    def test_only_public_assets_are_served(self):
        self.assertEqual(401, self.request('/')[0])
        self.assertEqual(200, self.request('/', headers=self.auth())[0])
        self.assertEqual(401, self.request('/api/kv/all')[0])
        self.assertEqual(404, self.request('/store/kv.json', headers=self.auth())[0])

    def test_public_mode_never_exposes_shared_data_or_generation(self):
        self.assertEqual(403, self.request('/api/generate', 'POST', '{}', dict(self.auth(), **{'Content-Type': 'application/json'}))[0])

    def test_security_headers(self):
        self.assertEqual(403, self.request('/api/kv', 'POST', '{}', dict(self.auth(), **{'Origin': 'https://untrusted.invalid', 'Content-Type': 'application/json'}))[0])

    def test_private_store_roundtrip_and_delete(self):
        import json
        headers = dict(self.auth(), **{'Content-Type':'application/json'})
        body = json.dumps({'k':'ac7_profiles','v':json.dumps([{'id':'synthetic','name':'Test Learner'}])})
        self.assertEqual(200, self.request('/api/kv','POST',body,headers)[0])
        stored = json.loads(self.request('/api/kv/all',headers=self.auth())[2])
        self.assertEqual('Test Learner',json.loads(stored['ac7_profiles'])[0]['name'])
        self.assertEqual(404,self.request('/store/kv.json',headers=self.auth())[0])
        self.assertEqual(200,self.request('/api/kv','POST',json.dumps({'k':'ac7_profiles','delete':True}),headers)[0])
        self.assertNotIn('ac7_profiles',json.loads(self.request('/api/kv/all',headers=self.auth())[2]))

    def test_rejects_invalid_keys_and_missing_csrf_header(self):
        import json
        headers=dict(self.auth(), **{'Content-Type':'application/json'})
        for key in ['__proto__','../outside','ac7_bad/escape']:
            self.assertEqual(400,self.request('/api/kv','POST',json.dumps({'k':key,'v':'x'}),headers)[0])
        headers.pop('X-AC7-Request')
        self.assertEqual(403,self.request('/api/kv','POST','{}',headers)[0])

    def test_unauthorized_post_rejected_before_reading_body(self):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=2)
        try:
            conn.request('POST','/api/kv',headers={'Content-Type':'application/json','Content-Length':'16000000'})
            self.assertEqual(401,conn.getresponse().status)
        finally:
            conn.close()

    def test_missing_origin_is_rejected(self):
        headers=dict(self.auth(), **{'Content-Type':'application/json'})
        headers.pop('Origin')
        self.assertEqual(403,self.request('/api/kv','POST','{}',headers)[0])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.temp.cleanup()


if __name__ == '__main__':
    unittest.main()
