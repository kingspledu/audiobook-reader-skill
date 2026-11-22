from pathlib import Path
from bs4 import BeautifulSoup
import json,re,subprocess
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'story-reader';WORK=ROOT/'production/audiobook';total=words=matched=cuts=0;rows=[]
for vol in (1,2,3):
 folder=SITE/f'volume-{vol}';doc=BeautifulSoup((folder/'index.html').read_text('utf8'),'html.parser')
 old=subprocess.check_output(['git','-c',f'safe.directory={SITE.as_posix()}','show',f'HEAD:volume-{vol}/index.html'],cwd=SITE).decode('utf8');old=BeautifulSoup(old,'html.parser')
 def snapshot(s):return ([(x['data-sentence'],x.get_text()) for x in s.select('.reading-sentence')],[x.get('data-vocab') for x in s.select('[data-vocab]')],[x.get('src') for x in s.select('figure img')])
 assert snapshot(doc)==snapshot(old),'Reader source/vocabulary/art changed'
 ids={x['data-sentence']:len(re.findall(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*",x.get_text())) for x in doc.select('.reading-sentence')}
 cat=json.loads((folder/'audio/catalog.json').read_text('utf8'))
 for entry in cat['chapters']:
  ch=entry['chapter'];d=json.loads((folder/f'audio/ch{ch:02}/timing.json').read_text('utf8'));previous=0
  for i,s in enumerate(d['segments']):
   assert (folder/s['src']).exists() and '/clips/' in s['src'] and 'chapter.mp3' not in s['src']
   assert abs(s['offset']-previous)<.0001 and s['duration']>0;previous+=s['duration'];total+=1
   assert 0<=s['trim_start']<s['trim_end']<=s['original_duration']+.001
   for w in s['words']:
    assert w['sentence'] in ids and 0<=w['word']<ids[w['sentence']];words+=1
    if w['start'] is not None:assert 0<=w['start']<w['end']<=s['original_duration']+.002;matched+=1
   if i:
    prev=d['segments'][i-1];same=prev['words'] and s['words'] and prev['words'][-1]['sentence'].split('-s')[0]==s['words'][0]['sentence'].split('-s')[0]
    if not same:assert s['trim_start']==0 and abs(prev['trim_end']-prev['original_duration'])<.001
    else:cuts+=1
  assert abs(previous-d['duration'])<.0001;rows.append(ch)
result={'chapters':rows,'separate_mp3_count':total,'source_sentence_words':words,'timed_words':matched,'word_timing_coverage':matched/words,'same_paragraph_boundaries':cuts,'reader_text_vocabulary_illustrations_preserved':'PASS','paragraph_break_silence_preserved':'PASS','timing_references_and_ranges':'PASS','human_listening':False}
(WORK/'reader-validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
