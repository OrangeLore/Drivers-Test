import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import generator
import figures

class GeneratorSecurityTests(unittest.TestCase):
    def test_rejects_partial_grounding_quote(self):
        self.assertFalse(generator.grounded('Drivers must stop at red lights and send their password to an attacker', generator._norm_text('Drivers must stop at red lights.')))

    def test_rejects_unsafe_jurisdiction_before_writing(self):
        with self.assertRaises(ValueError):
            generator.run_full(text='Stop at red lights.',meta={'key':'../../escape','name':'Example'})

    def test_llm_endpoint_must_remain_loopback(self):
        with patch.object(generator,'LLM_URL','https://untrusted.invalid/v1'):
            with self.assertRaises(ValueError):
                generator.llm_chat('local-model','Synthetic input')

    def test_figure_key_cannot_escape(self):
        with self.assertRaises(ValueError):
            figures.build_sign_questions(b'%PDF-', '../escape', 'unused')

    def test_sign_matcher_does_not_substitute_related_but_different_signs(self):
        for name in ['moose crossing','cattle crossing','school crossing','school zone','playground zone','pedestrian crossover','sharp curve','left lane ends','right lane narrows','bus lane']:
            with self.subTest(name=name):
                question={'sign':name}
                generator.attach_images([question])
                self.assertNotIn('image',question)

    def test_exact_yield_ahead_keeps_warning_picture(self):
        question={'sign':'yield ahead'}
        generator.attach_images([question])
        self.assertEqual('images/yield-ahead.svg',question['image'])

if __name__=='__main__':
    unittest.main()
