from pathlib import Path
from bs4 import BeautifulSoup
from difflib import SequenceMatcher
import zipfile,json,re,hashlib

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'story-reader'
WORK=ROOT/'production/audiobook'
WORK.mkdir(exist_ok=True)
TOKEN=re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")
def tokens(s):return [m.group().lower().replace('’',"'") for m in TOKEN.finditer(s)]
chapters=[]
for archive in sorted((ROOT/'public-tiger/tts zip').glob('*.zip')):
 with zipfile.ZipFile(archive) as z:
  index=json.loads(z.read(next(n for n in z.namelist() if n.endswith('_INDEX.json'))))
  ch=index['chapter'];vol=1 if ch<=10 else 2 if ch<=20 else 3
  folder=SITE/f'volume-{vol}'/'audio'/f'ch{ch:02}'
  folder.mkdir(parents=True,exist_ok=True)
  doc=BeautifulSoup((SITE/f'volume-{vol}/index.html').read_text('utf8'),'html.parser')
  sec=doc.select_one(f'#chapter-{ch:03}');web=[];webrefs=[]
  for span in sec.select('.reading-sentence'):
   for wi,t in enumerate(tokens(span.get_text())):web.append(t);webrefs.append([span['data-sentence'],wi])
  segments=sorted(index['segments'],key=lambda s:s['order']);spoken=[];owners=[]
  for si,seg in enumerate(segments):
   name=seg['filename'];assert Path(name).name==name and name.endswith('.mp3')
   raw=z.read(name);target=folder/name
   if not target.exists():target.write_bytes(raw)
   seg['sha256']=hashlib.sha256(raw).hexdigest();seg['word_map']=[None]*len(tokens(seg['text']))
   for wi,t in enumerate(tokens(seg['text'])):spoken.append(t);owners.append((si,wi))
  matcher=SequenceMatcher(None,spoken,web,autojunk=False)
  for a,b,n in matcher.get_matching_blocks():
   for k in range(n):
    si,wi=owners[a+k];segments[si]['word_map'][wi]=webrefs[b+k]
  unmatched=[{'order':s['order'],'text':s['text'],'unmapped_words':[tokens(s['text'])[i] for i,x in enumerate(s['word_map']) if x is None]} for s in segments if None in s['word_map']]
  data={'chapter':ch,'volume':vol,'segments':segments,'web_word_count':len(web),'spoken_word_count':len(spoken),'unmatched':unmatched,'missing':index.get('missing',[]),'complete':index.get('complete')}
  (WORK/f'ch{ch:02}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
  chapters.append({'chapter':ch,'segments':len(segments),'mp3_bytes':sum((folder/x['filename']).stat().st_size for x in segments),'spoken_words':len(spoken),'unmapped_words':sum(len(x['unmapped_words']) for x in unmatched),'unmapped_segments':len(unmatched),'complete':data['complete'],'missing':data['missing']})
(WORK/'inventory.json').write_text(json.dumps(chapters,indent=2),encoding='utf8')
print(json.dumps(chapters,indent=2))
