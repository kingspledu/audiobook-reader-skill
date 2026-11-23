from pathlib import Path
from bs4 import BeautifulSoup
import json,shutil,re
from paragraph_cuts import plan
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'story-reader';WORK=ROOT/'production/audiobook'
catalogs={v:[] for v in (1,2,3)};report=[]
levels=json.loads((WORK/'clip-levels.json').read_text('utf8'))
for p in sorted(WORK.glob('ch??.json')):
 data=json.loads(p.read_text('utf8'));ch=data['chapter'];vol=data['volume'];cache=WORK/f'aligned-ch{ch:02}.json'
 folder=SITE/f'volume-{vol}/audio/ch{ch:02}/clips'
 if not cache.exists() or not all((folder/s['filename']).exists() for s in data['segments']):continue
 aligned=json.loads(cache.read_text('utf8'))
 if len(aligned)!=len(data['segments']):continue
 segments=[];offset=0;matched=expected=0
 paragraph=lambda s:s['word_map'][0][0].split('-s')[0] if s['word_map'] else None
 for i,s in enumerate(data['segments']):
  a=aligned[s['filename']];assert a['sha256']==s['sha256'];words=[];level=levels[s['filename']]
  trim,end=plan(data['segments'],i,level,a['duration']);duration=end-trim
  for ref,t in zip(s['word_map'],a['word_times']):
   assert ref is not None
   words.append({'sentence':ref[0],'word':ref[1],'start':t[0] if t else None,'end':t[1] if t else None})
  count=sum(w['start'] is not None for w in words);matched+=count;expected+=a['expected']
  assert all(w['start'] is None or 0<=w['start']<w['end']<=a['duration']+.002 for w in words)
  sentences=list(dict.fromkeys(w['sentence'] for w in words))
  if not sentences and segments:sentences=segments[-1]['sentences'][-1:]
  segments.append({'src':f"audio/ch{ch:02}/clips/{s['filename']}",'order':s['order'],'speaker':s['speaker'],'sentences':sentences,'words':words,'original_duration':a['duration'],'trim_start':trim,'trim_end':end,'duration':duration,'offset':offset,'timing_coverage':round(count/max(1,a['expected']),4)})
  if a.get('review_required'):segments[-1]['review_required']=a['review_required']
  offset+=duration
 public={'chapter':ch,'duration':offset,'engine':'faster-whisper/base/int8','method':'Whisper cross-attention DTW forced alignment; independent volume-corrected MP3s; browser-only cuts','timing_coverage':round(matched/expected,4),'segments':segments}
 (SITE/f'volume-{vol}/audio/ch{ch:02}/timing.json').write_text(json.dumps(public,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 issues=[{'order':s['order'],'filename':s['src'].split('/')[-1],'duration':s['original_duration'],'reason':s['review_required']} for s in segments if s.get('review_required')]
 catalogs[vol].append({'chapter':ch,'segments':len(segments),'duration':offset,'word_timing_coverage':round(matched/expected,4),'source_issues':issues})
 report.append({'chapter':ch,'files':len(segments),'matched_words':matched,'total_words':expected,'coverage':round(matched/expected,4)})
for vol,chapters in catalogs.items():
 v=SITE/f'volume-{vol}';(v/'audio').mkdir(exist_ok=True)
 (v/'audio/catalog.json').write_text(json.dumps({'chapters':chapters,'missing_chapters':[c for c in range((vol-1)*10+1,min(vol*10,29)+1) if c not in [x['chapter'] for x in chapters]]},indent=2),encoding='utf8')
 for name in ('clip-player.js','media-player.js','audiobook.js','audiobook.css'):shutil.copyfile(ROOT/'production'/name,v/name)
 p=v/'index.html';html=p.read_text('utf8');doc=BeautifulSoup(html,'html.parser');before=[(s['data-sentence'],s.get_text()) for s in doc.select('.reading-sentence')]
 if not doc.select_one('script[src^="audiobook.js"]'):
  doc.head.append(doc.new_tag('link',rel='stylesheet',href='audiobook.css?v=audio-20261121-v3'))
  doc.body.append(doc.new_tag('script',src='clip-player.js?v=audio-20261121-v3',defer=''))
  doc.body.append(doc.new_tag('script',src='audiobook.js?v=audio-20261121-v3',defer=''))
 for node in doc.select('script[src^="audiobook.js"],script[src^="clip-player.js"]'):node['src']=node['src'].split('?')[0]+'?v=audio-20261121-v3'
 if not doc.select_one('script[src^="clip-player.js"]'):
  doc.select_one('script[src^="audiobook.js"]').insert_before(doc.new_tag('script',src='clip-player.js?v=audio-20261121-v3',defer=''))
 if not doc.select_one('script[src^="media-player.js"]'):doc.select_one('script[src^="audiobook.js"]').insert_before(doc.new_tag('script',src='media-player.js?v=mobile-v1',defer=''))
 for node in doc.select('script[src^="audiobook.js"],script[src^="clip-player.js"]'):node['src']=node['src'].split('?')[0]+'?v=mobile-v1'
 assert before==[(s['data-sentence'],s.get_text()) for s in doc.select('.reading-sentence')]
 p.write_text(str(doc),encoding='utf8')
 p=v/'sw.js';sw=p.read_text('utf8')
 # Never cache range responses or automatically download the audiobook.
 if "url.pathname.includes('/audio/')" not in sw:sw=sw.replace("if(request.method!=='GET'||!url.href.startsWith(ROOT))return;","if(request.method!=='GET'||!url.href.startsWith(ROOT)||url.pathname.includes('/audio/')||request.headers.has('range'))return;")
 sw=re.sub(r"const CACHE=PREFIX\+'[^']+';","const CACHE=PREFIX+'audio-20261121-v3';",sw);p.write_text(sw,encoding='utf8')
(SITE/'audiobook-validation.json').write_text(json.dumps({'chapters':report,'source_mapping':'all supplied transcript words map exactly to reader words','timing_method':'Whisper cross-attention dynamic time warping; not uniform interpolation','unmatched_words':'sentence highlighting only, no invented word timestamps','listening_review':'not yet performed'},indent=2),encoding='utf8')
print(json.dumps(report,indent=2))
