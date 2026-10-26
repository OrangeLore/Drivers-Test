"""Safe automatic pictures must come from an identified, reviewed handbook profile."""
import base64
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import generator
import figures

class AutomaticHandbookImageTests(unittest.TestCase):
    def test_recognized_source_automatically_reuses_all_reviewed_pictures(self):
        import copy
        import handbook_images
        source=b'%PDF-reviewed-unit-fixture'
        profile=copy.deepcopy(json.loads((ROOT/'tools'/'sign_assets.json').read_text()))
        profile['source_pdf_sha256']=hashlib.sha256(source).hexdigest()
        with patch.object(handbook_images,'load_profile',return_value=profile):
            questions,audit=handbook_images.reviewed_questions(source)
            with patch.object(generator,'extract_text_from_bytes',return_value=[(1,'Reviewed handbook unit test text.')]), patch.object(generator,'llm_chat',side_effect=AssertionError('Reviewed pictures must not need an LLM')):
                dataset=generator.run_full(meta={'key':'sample','name':'Sample'},pdf_bytes=source,model='not-running',target=36)
        self.assertEqual(36,len(dataset['questions']))
        self.assertEqual(25,dataset['passMark'])
        self.assertEqual('reviewed_source',audit['status'])
        self.assertEqual(36,len(questions))
        self.assertTrue(all(q['image'].startswith('data:image/png;base64,') for q in questions))
        yield_ahead=next(q for q in questions if 'upward arrow' in q['alt'] and 'triangle' in q['alt'])
        self.assertIn('yield',yield_ahead['options'][yield_ahead['answer']].lower())
        for question,asset in zip(questions,profile['assets']):
            png=base64.b64decode(question['image'].split(',',1)[1],validate=True)
            self.assertEqual(asset['png_sha256'],hashlib.sha256(png).hexdigest())

    def test_changed_edition_is_flagged_instead_of_reusing_old_pictures(self):
        import handbook_images
        questions,audit=handbook_images.reviewed_questions(b'%PDF-a-new-unreviewed-edition')
        self.assertEqual([],questions)
        self.assertEqual('unreviewed_source',audit['status'])

    def test_corrupted_reviewed_picture_is_not_accepted(self):
        import handbook_images
        source=b'%PDF-reviewed-unit-fixture'
        profile=json.loads((ROOT/'tools'/'sign_assets.json').read_text())
        profile['source_pdf_sha256']=hashlib.sha256(source).hexdigest()
        profile['assets'][0]['png_sha256']='0'*64
        with patch.object(handbook_images,'load_profile',return_value=profile):
            with self.assertRaisesRegex(ValueError,'checksum'):
                handbook_images.reviewed_questions(source)

    def test_unrecognized_pdf_never_turns_nearest_captions_into_graded_answers(self):
        candidates=[{'caption':label,'png_bytes':b'not-a-png','page':1,'bbox_pts':[0,0,20,20]} for label in ['Yield','School area','Stop','No parking']]
        with patch.object(figures,'_available',return_value=True), patch.object(figures,'extract_pairs',return_value=candidates):
            questions,_=figures.build_sign_questions(b'%PDF-unknown','sample',None)
        self.assertEqual([],questions,'An unreviewed caption pairing must not become a graded sign question')

    def test_generated_datasets_do_not_substitute_library_images_for_unknown_books(self):
        question={'q':'What does a school sign warn of?','options':['Children','Hospital','Fuel','Parking'],'answer':0,'sign':'school area'}
        dataset=generator.build_dataset({'key':'sample','name':'Sample'},[question])
        self.assertNotIn('image',dataset['questions'][0])

    def test_same_question_text_with_different_sign_pictures_is_not_a_duplicate(self):
        questions=[{'q':'What does this sign mean?','image':'source-picture-one'}, {'q':'What does this sign mean?','image':'source-picture-two'}]
        self.assertEqual(2,len(generator.dedupe(questions)))

    def test_text_model_cannot_supply_its_own_image(self):
        source='Drivers must stop completely at red traffic lights before the stop line.'
        model_question={'q':'What must a driver do at a red traffic light?','options':['Stop completely','Speed up','Honk','Ignore it'],'answer':0,'quote':source,'image':'https://untrusted.invalid/sign.png'}
        with patch.object(generator,'llm_chat',return_value=json.dumps([model_question])):
            questions=generator.generate('local',[(1,1,source)],1)
        self.assertEqual(1,len(questions))
        self.assertNotIn('image',questions[0])

    def test_text_only_generation_drops_questions_that_require_an_unavailable_picture(self):
        source='Drivers must stop completely at red traffic lights before the stop line.'
        model_question={'q':'What does this sign mean?','options':['Stop completely','Speed up','Honk','Ignore it'],'answer':0,'quote':source}
        with patch.object(generator,'llm_chat',return_value=json.dumps([model_question])):
            self.assertEqual([],generator.generate('local',[(1,1,source)],1))

    def test_official_sample_without_its_required_picture_is_not_imported(self):
        text='1. What does this sign mean?\na) Stop\nb) Yield\nc) Parking\nd) Hospital\nAnswer Key: 1-a'
        self.assertEqual([],generator.ingest_samples(text))

    def test_cli_preserves_automatic_source_format_unless_user_overrides_it(self):
        import generate_dataset
        question={'q':'Unit test question','options':['A','B','C','D'],'answer':0}
        dataset={'questions':[question]*36,'testSize':30,'passMark':25}
        for extra in ([],['--testsize','30','--passmark','25']):
            with self.subTest(arguments=extra):
                args=['generate_dataset','--pdf','fixture.pdf','--key','sample','--name','Sample','--n','36','--out','fixture.json']+extra
                with patch.object(sys,'argv',args), patch.object(Path,'read_bytes',return_value=b'%PDF-unit-fixture'), patch.object(Path,'write_text'), patch.object(generator,'run_full',return_value=dataset) as run:
                    generate_dataset.main()
                meta=run.call_args.kwargs['meta']
                if extra:
                    self.assertEqual(25,meta['passMark'])
                else:
                    self.assertNotIn('testSize',meta)
                    self.assertNotIn('passMark',meta)

    def test_reviewed_profile_has_a_complete_teaching_mapping(self):
        profile=json.loads((ROOT/'tools'/'sign_assets.json').read_text())
        for image in profile['assets']:
            with self.subTest(file=image['file']):
                self.assertIn('question',image,'Every automatic image needs a reviewed question/answer, not a guessed caption')
                question=image['question']
                self.assertEqual(4,len(question['options']))
                self.assertTrue(0<=question['answer']<4)
                self.assertTrue(question['alt'])

if __name__=='__main__':unittest.main()
