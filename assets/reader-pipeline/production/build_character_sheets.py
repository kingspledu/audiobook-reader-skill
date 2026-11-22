"""Render supplied character consistency resources; never invent approved images."""
import argparse,hashlib,html,json,shutil
from pathlib import Path
def build(book,assets,out):
 out.mkdir(parents=True,exist_ok=True);(out/'assets').mkdir(exist_ok=True);e=lambda s:html.escape(str(s),quote=True);cards=[]
 for character in book.get('characters',[]):
  facts=character.get('description','');choices=character.get('visual_notes','');pictures=[]
  for source in character.get('sheets',[]):
   image=(assets/source).resolve();assert image.is_relative_to(assets) and image.is_file(),'Invalid character sheet path'
   name=hashlib.sha256(image.read_bytes()).hexdigest()[:16]+image.suffix.lower();shutil.copyfile(image,out/'assets'/name)
   pictures.append(f'<img src="assets/{name}" alt="{e(character["name"])} 캐릭터 시트" loading="lazy">')
  cards.append(f'<section><h2>{e(character["name"])}</h2><h3>원문 근거</h3><p>{e(facts)}</p><h3>승인된 외형·연속성 기준</h3><p>{e(choices)}</p>'+''.join(pictures)+('</section>'))
 page='<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(book['title'])+' 캐릭터 시트</title><style>body{max-width:1000px;margin:auto;padding:24px;background:#f5f1e8;color:#253e32;font:16px/1.7 system-ui}section{margin:30px 0;padding:20px;border:1px solid #cbd3c6;border-radius:12px}img{max-width:100%;height:auto}p{white-space:pre-line}</style><a href="../">읽기 사이트</a><h1>'+e(book['title'])+' 캐릭터 일관성</h1>'+''.join(cards)+'</html>'
 (out/'index.html').write_bytes(page.encode('utf8'))
 return len(cards)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--assets',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(build(json.loads(a.input.read_text('utf8')),(a.assets or a.input.parent).resolve(),a.output))
