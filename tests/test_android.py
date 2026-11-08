"""Android packaging privacy contract; no SDK is required for asset tests."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from defusedxml import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
class AndroidPackageTests(unittest.TestCase):
 def test_android_manifest_has_no_network_permissions_and_no_cloud_backup(self):
  file=ROOT/'android'/'AndroidManifest.xml'
  self.assertTrue(file.exists(),'Offline Android manifest has not been implemented')
  manifest=ET.parse(file).getroot();android='{http://schemas.android.com/apk/res/android}'
  self.assertEqual([],manifest.findall('uses-permission'))
  app=manifest.find('application');assert app is not None
  self.assertEqual('false',app.get(android+'allowBackup'))
  self.assertEqual('false',app.get(android+'usesCleartextTraffic'))
 def test_packaged_learning_assets_have_no_server_code_or_generation_controls(self):
  file=ROOT/'tools'/'build_android.py'
  self.assertTrue(file.exists(),'Offline Android asset builder is missing')
  spec=importlib.util.spec_from_file_location('build_android',file);assert spec is not None and spec.loader is not None
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as d:
   module.build_assets(Path(d));html=(Path(d)/'index.html').read_text(encoding='utf-8')
   self.assertNotIn('/api/',html);self.assertNotIn('fetch(',html);self.assertNotIn('genFile',html)
   self.assertIn('RoadTripUI.mount',html);self.assertIn('connect-src',html)
   self.assertIn("dialog[open]",html,'Android Back must dismiss an achievement or consent dialog before navigating away')
   self.assertIn('removeProfileData(id)',html)
   self.assertTrue((Path(d)/'images'/'yield-ahead.svg').exists())
   self.assertFalse((Path(d)/'tools').exists());self.assertFalse((Path(d)/'.git').exists())
   self.assertLess(html.index('rewardUI=RoadTripUI.mount'),html.index("show('home');\n    window.roadTripBack"))
 def test_build_manifest_excludes_unrelated_files_already_in_the_output_folder(self):
  spec=importlib.util.spec_from_file_location('build_android',ROOT/'tools'/'build_android.py');assert spec is not None and spec.loader is not None
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'unrelated-private-record.txt').write_text('synthetic unit-test fixture')
   files=module.build_assets(Path(d));self.assertIsInstance(files,list)
   self.assertNotIn('unrelated-private-record.txt',files)
if __name__=='__main__':unittest.main()
