from pathlib import Path
from bs4 import BeautifulSoup
import json,shutil
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'story-reader';DEST=SITE/'landscape-test';DEST.mkdir(exist_ok=True)
chapters=[]
for vol in (1,2,3):
 doc=BeautifulSoup((SITE/f'volume-{vol}/index.html').read_text('utf8'),'html.parser')
 for section in doc.select('section.chapter'):
  ch=int(section['id'].split('-')[-1]);image=None;rows=[];paragraphs=[]
  for node in section.descendants:
   if getattr(node,'name',None)=='img':image={'src':f'../volume-{vol}/'+node['src'],'alt':node.get('alt','')}
   if getattr(node,'name',None)=='span' and 'reading-sentence' in node.get('class',[]):
    p=node.find_parent(class_='story-text');pid=p['id'];pid=pid.split('--')[0];rows.append({'id':node['data-sentence'],'text':node.get_text(),'paragraph':pid,'image':image})
  first=next((r['image'] for r in rows if r['image']),None)
  for r in rows:
   if not r['image']:r['image']=first
  chapters.append({'chapter':ch,'volume':vol,'sentences':rows})
(DEST/'chapters.json').write_text(json.dumps(chapters,ensure_ascii=False,separators=(',',':')),encoding='utf8')
for name in ['index.html','test.css','test.js']:shutil.copyfile(ROOT/'production/landscape-test'/name,DEST/name)
print(json.dumps({'chapters':len(chapters),'sentences':sum(len(c['sentences']) for c in chapters),'test_page':str(DEST)}))
