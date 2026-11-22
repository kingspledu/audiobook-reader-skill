import copy,unittest
from sentence_contract import validate_sentence
class Tests(unittest.TestCase):
 def setUp(self):
  self.s=dict(text='정말 당신이에요?',sentence_id='s1',paragraph_id='p1',context_before=[],context_after=['s2'],review={**{k:'confirmed' for k in ['attribution','classification','performance','speaker_pass','cue_pass','continuity_pass']},'evidence':'화자가 상대를 확인하는 직접 질문','sentence_boundary_evidence':'단일 의문문'},performance=dict(sentence_persona='상대를 확인하려는 불안한 목소리',cue_links=[],design={k:'문맥 근거를 반영한 지침' for k in ['addressee_intention','outer_inner','pivot','prosody','nonverbal','continuation']}))
 def test_single(self):self.assertTrue(validate_sentence(self.s))
 def test_multiple(self):
  self.s['text']='안녕하세요. 누구세요?'
  with self.assertRaises(ValueError):validate_sentence(self.s)
 def test_unresolved(self):
  self.s['review']['attribution']='user_review_required'
  with self.assertRaises(ValueError):validate_sentence(self.s)
 def test_no_persona(self):
  del self.s['performance']['sentence_persona']
  with self.assertRaises(ValueError):validate_sentence(self.s)
 def test_wrong_cue(self):
  self.s['performance']['cue_links']=[dict(source_sentence_id='s0',target_sentence_id='other',cue_text='울었다',instruction='목소리에 울음 반영')]
  with self.assertRaises(ValueError):validate_sentence(self.s)
 def test_unreviewed_continuity(self):
  self.s['review']['continuity_pass']='pending'
  with self.assertRaises(ValueError):validate_sentence(self.s)
if __name__=='__main__':unittest.main()
