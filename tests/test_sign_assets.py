"""Provenance checks for handbook-derived sign pictures (no PDF/network required)."""
import base64
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]

class SignArtworkTests(unittest.TestCase):
    def test_reported_signs_use_reviewed_handbook_artwork(self):
        path=ROOT/'tools'/'sign_assets.json'
        self.assertTrue(path.is_file(),'A reviewed handbook crop manifest is required')
        manifest=json.loads(path.read_text())
        entries={row['file']:row for row in manifest['assets']}
        for file,page in [('yield-ahead.svg',33),('school.svg',31),('playground.svg',32)]:
            self.assertEqual(page,entries[file]['printed_page'])
            text=(ROOT/'images'/file).read_text()
            encoded=re.search(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"',text)
            self.assertIsNotNone(encoded,'Use the source handbook picture, not a redrawn symbol')
            assert encoded is not None
            png=base64.b64decode(encoded.group(1),validate=True)
            self.assertTrue(png.startswith(b'\x89PNG\r\n\x1a\n'))
            self.assertEqual(entries[file]['png_sha256'],hashlib.sha256(png).hexdigest())

    def test_all_official_crops_have_provenance_and_matching_hash(self):
        path=ROOT/'tools'/'sign_assets.json'
        self.assertTrue(path.exists())
        manifest=json.loads(path.read_text())
        self.assertTrue(manifest['source_url'].startswith('https://open.alberta.ca/'))
        for entry in manifest['assets']:
            with self.subTest(file=entry['file']):
                text=(ROOT/'images'/entry['file']).read_text()
                data=re.search(r'href="data:image/png;base64,([A-Za-z0-9+/=]+)"',text)
                self.assertIsNotNone(data)
                assert data is not None
                self.assertEqual(hashlib.sha256(base64.b64decode(data.group(1))).hexdigest(),entry['png_sha256'])
                self.assertEqual(entry['pdf_page']-2,entry['printed_page'])

if __name__=='__main__':unittest.main()
