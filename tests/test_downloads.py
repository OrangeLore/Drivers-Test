from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import fetch_signs

class DownloadSecurityTests(unittest.TestCase):
    def test_only_https_wikimedia_and_safe_filenames(self):
        for name,url in [('../escape.svg','https://upload.wikimedia.org/x.svg'),('x.js','https://upload.wikimedia.org/x.js'),('x.svg','file:///private'),('x.svg','http://127.0.0.1/'),('x.svg','https://tracker.invalid/x.svg')]:
            with self.subTest(name=name,url=url), self.assertRaises(ValueError):
                fetch_signs.validate_source(name,url)
        fetch_signs.validate_source('stop.svg','https://upload.wikimedia.org/x.svg')

    def test_svg_cannot_execute_or_track(self):
        for svg in [b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',b'<!DOCTYPE svg [<!ENTITY a "x">]><svg/>',b'<svg><image href="https://tracker.invalid/x"/></svg>']:
            with self.assertRaises(ValueError):
                fetch_signs.validate_svg(svg)
        for image in (Path(__file__).resolve().parents[1]/'images').glob('*.svg'):
            fetch_signs.validate_svg(image.read_bytes())

if __name__=='__main__':
    unittest.main()
