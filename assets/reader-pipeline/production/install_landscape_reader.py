"""Install shared landscape enhancement; preserve chapter payload and media files."""
import argparse,hashlib,json,re,shutil
from pathlib import Path
from bs4 import BeautifulSoup
SOURCE=Path(__file__).resolve().parent
VERSION='landscape-20261122-v2'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def install(site):
 report=[]
 for v in (1,2,3):
  folder=site/f'volume-{v}';p=folder/'index.html';original=p.read_text('utf8')
  manifestp=folder/'offline-manifest.json';manifest=json.loads(manifestp.read_text('utf8'))
  changed=['index.html','audiobook.js','sw.js','landscape-reader.js','landscape-reader.css']
  old_sizes={name:(folder/name).stat().st_size if name in manifest['files'] and (folder/name).exists() else 0 for name in changed}
  before=BeautifulSoup(original,'html.parser');baseline=[(s['data-sentence'],s.get_text()) for s in before.select('.reading-sentence')]
  for name in ['landscape-reader.js','landscape-reader.css']:shutil.copyfile(SOURCE/name,folder/name)
  if 'landscape-reader.css' not in original:
   original=original.replace('</head>',f'<link rel="stylesheet" href="landscape-reader.css?v={VERSION}"></head>')
   original=original.replace('</body>',f'<script src="landscape-reader.js?v={VERSION}"></script></body>')
  original=re.sub(r'landscape-reader\.(css|js)\?v=[^"\s>]+',lambda m:'landscape-reader.'+m[1]+'?v='+VERSION,original)
  p.write_bytes(original.encode('utf8'))
  after=BeautifulSoup(original,'html.parser');assert [(s['data-sentence'],s.get_text()) for s in after.select('.reading-sentence')]==baseline
  audio=folder/'audiobook.js';js=audio.read_text('utf8')
  if "dispatchEvent(new CustomEvent('tiger-active-sentence'" not in js:
   js=js.replace("const current=next[0];if(follow.checked", "const current=next[0];dispatchEvent(new CustomEvent('tiger-active-sentence',{detail:{sentence:current,follow:follow.checked,chapter:track.chapter,index,time:absolute}}));if(!root.classList.contains('reader-landscape')&&follow.checked")
   assert "tiger-active-sentence" in js
   audio.write_bytes(js.encode('utf8'))
  sw=folder/'sw.js';js=re.sub(r"const CORE=PREFIX\+'[^']+';",f"const CORE=PREFIX+'{VERSION}';",sw.read_text('utf8'))
  if "'./landscape-reader.js'" not in js:js=js.replace("'./offline.js']","'./offline.js','./landscape-reader.js','./landscape-reader.css']")
  # App shell comes from the new core on offline fallback, without purging saved MP3s.
  js=js.replace("catch{return await saved()||await caches.match(request,{ignoreSearch:true})||Response.error();}","catch{const core=await caches.open(CORE);return await core.match(request,{ignoreSearch:true})||await saved()||Response.error();}")
  sw.write_bytes(js.encode('utf8'))
  for name in ['landscape-reader.js','landscape-reader.css']:
   if name not in manifest['files']:manifest['files'].append(name)
  hashes=manifest.get('sha256',manifest.get('hashes'))
  assert isinstance(hashes,dict),manifest.keys()
  for name in ['index.html','audiobook.js','sw.js','landscape-reader.js','landscape-reader.css']:
   if (folder/name).exists():hashes[name]=digest(folder/name)
  if './' in manifest['files']:hashes['./']=digest(folder/'index.html')
  if isinstance(manifest.get('bytes'),dict):
   for name in hashes:
    if (folder/name).exists():manifest['bytes'][name]=(folder/name).stat().st_size
  elif isinstance(manifest.get('bytes'),int):
   manifest['bytes']+=sum((folder/name).stat().st_size-old_sizes[name] for name in changed if name in manifest['files'])
   if './' in manifest['files']:manifest['bytes']+=(folder/'index.html').stat().st_size-old_sizes['index.html']
  manifestp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
  report.append(dict(volume=v,chapters=len(before.select('section.chapter')),sentences=len(baseline),text_ids_preserved=True))
 return report
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('site',type=Path);a=p.parse_args();print(json.dumps(install(a.site)))
