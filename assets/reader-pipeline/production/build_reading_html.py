"""Build the reading HTML FIRST. Compatible with the current three-volume profile."""
from pathlib import Path
from string import Template
import argparse,json,html,re,shutil,zlib,struct,hashlib

def make_icon(path,size):
 # A simple generated book icon, not book illustration content.
 rows=[]
 for y in range(size):
  row=bytearray()
  for x in range(size):
   page=size*.22<x<size*.78 and size*.2<y<size*.8
   row.extend((244,239,220) if page else (38,77,58))
  rows.append(b'\0'+row)
 def chunk(tag,data):return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
 path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(rows)))+chunk(b'IEND',b''))

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--input',default='book.json');parser.add_argument('--output',default='story-reader');parser.add_argument('--assets');args=parser.parse_args()
 source=Path(args.input).resolve();out=Path(args.output).resolve();data=json.loads(source.read_text('utf8'));template=Path(__file__).resolve().parent/'reader-template'
 assert re.fullmatch(r'[a-z0-9-]+',data['book_id']),'Use a unique lowercase book_id'
 numbers=[c['number'] for c in data['chapters']];assert len(set(numbers))==len(numbers) and all(1<=n<=29 for n in numbers),'Current profile supports chapter numbers 1..29'
 assert not any((out/f'volume-{v}/index.html').exists() for v in (1,2,3)),'Output already contains a reader; use a fresh output directory'
 groups={v:[] for v in (1,2,3)};vocabulary={f'v{i:04}':item for i,item in enumerate(data.get('vocabulary',[]),1)};pid=0;sentence_total=0;assetroot=Path(args.assets).resolve() if args.assets else source.parent
 e=lambda text:html.escape(text,quote=True)
 for ch in sorted(data['chapters'],key=lambda c:c['number']):
  n=ch['number'];vol=1 if n<=10 else 2 if n<=20 else 3;folder=out/f'volume-{vol}';folder.mkdir(parents=True,exist_ok=True);(folder/'assets').mkdir(exist_ok=True)
  parts=[f'<section class="chapter" id="chapter-{n:03}" lang="{e(data.get("language","en"))}"><header class="chapter-head"><span>CHAPTER {n:02}</span><h3>{e(ch.get("title",f"Chapter {n}"))}</h3></header>']
  for paragraph in ch['paragraphs']:
   pid+=1;paragraph_id=f'p{pid:04}';sentences=paragraph['sentences'];assert sentences and all(isinstance(s,str) and s.strip() for s in sentences)
   if paragraph.get('image'):
    image=(assetroot/paragraph['image']).resolve();assert image.is_relative_to(assetroot) and image.is_file(),'Invalid image path'
    name=hashlib.sha256(image.read_bytes()).hexdigest()[:16]+image.suffix.lower();shutil.copyfile(image,folder/'assets'/name)
    parts.append(f'<figure><img src="assets/{name}" alt="{e(paragraph.get("alt","Scene illustration"))}" loading="lazy"></figure>')
   parts.append(f'<div class="story-text" id="{paragraph_id}" data-paragraph="true">')
   for i,text in enumerate(sentences,1):
    rendered=e(text)
    # One vocabulary term per sentence, never alter original text content.
    for key,item in vocabulary.items():
     term=e(item['term'])
     if term and term in rendered:
      rendered=rendered.replace(term,f'<button class="vocab-word" data-vocab="{key}" aria-expanded="false" type="button">{term}</button>',1);break
    parts.append(f'<span class="reading-sentence" data-sentence="{paragraph_id}-s{i}">{rendered}</span>');sentence_total+=1
   parts.append('</div>')
  parts.append('</section>');groups[vol].append((n,''.join(parts)))
 for vol,chapters in groups.items():
  folder=out/f'volume-{vol}';(folder/'assets').mkdir(parents=True,exist_ok=True)
  for name in ['style.css','app.js']:shutil.copyfile(template/name,folder/name)
  for size in (192,512):make_icon(folder/f'assets/app-icon-{size}.png',size)
  toc=''.join(f'<a href="#chapter-{n:03}">Chapter {n}</a>' for n,_ in chapters)
  if not chapters:toc='<span>아직 본문이 없는 권입니다.</span>'
  body=Template((template/'index.html').read_text('utf8')).substitute(story_id=e(data['book_id']+f'-volume-{vol}'),title=e(data['title']),description=f'Volume {vol}',toc=toc,volumes=' '.join(f'<a href="../volume-{v}/">Volume {v}</a>' for v in groups),chapters=''.join(content for _,content in chapters),vocabulary=json.dumps(vocabulary,ensure_ascii=False).replace('<','\\u003c'))
  (folder/'index.html').write_text(body,encoding='utf8')
  (folder/'pwa.js').write_text("if('serviceWorker'in navigator)addEventListener('load',()=>navigator.serviceWorker.register('./sw.js',{scope:'./'}).catch(()=>{}));",encoding='utf8')
  (folder/'sw.js').write_text("self.addEventListener('fetch',()=>{});",encoding='utf8')
  (folder/'manifest.webmanifest').write_text(json.dumps({'id':data['book_id']+f'-{vol}','name':data['title'],'short_name':data['title'][:20],'start_url':'./','scope':'./','display':'standalone','icons':[{'src':'assets/app-icon-192.png','sizes':'192x192','type':'image/png'},{'src':'assets/app-icon-512.png','sizes':'512x512','type':'image/png'}]}),encoding='utf8')
 (out/'.nojekyll').touch();(out/'index.html').write_text('<!doctype html><meta charset="utf-8"><title>'+e(data['title'])+'</title><a href="volume-1/">Open reader</a>',encoding='utf8')
 print(json.dumps({'reading_html_created_first':True,'chapters':len(numbers),'sentences':sentence_total,'volumes':3,'input':str(source),'output':str(out)}))
if __name__=='__main__':main()
