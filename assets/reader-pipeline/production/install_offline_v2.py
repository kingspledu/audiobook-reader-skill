from pathlib import Path
from bs4 import BeautifulSoup
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'story-reader'
for vol in (1,2,3):
 v=SITE/f'volume-{vol}';shutil.copyfile(ROOT/'production/offline-v2.js',v/'offline.js');p=v/'index.html';doc=BeautifulSoup(p.read_text('utf8'),'html.parser')
 node=doc.select_one('script[src^="offline.js"]')
 if not node:node=doc.new_tag('script',defer='');doc.body.append(node)
 node['src']='offline.js?v=2';p.write_text(str(doc),encoding='utf8')
 sw="""'use strict';
const ROOT=new URL('./',self.location).href;
const PREFIX='story-reader-tiger-volume-VOLUME-';
const CORE=PREFIX+'mobile-v1';
const SAVED='tiger-offline:'+new URL(ROOT).pathname+'offline-v2';
self.addEventListener('install',event=>{event.waitUntil(caches.open(CORE).then(c=>c.addAll(['./','./style.css','./app.js','./pwa.js','./clip-player.js','./media-player.js','./audiobook.js','./audiobook.css','./offline.js'])).then(()=>self.skipWaiting()))});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k.startsWith(PREFIX)&&k!==CORE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()))});
self.addEventListener('fetch',event=>{
const request=event.request,url=new URL(request.url);
if(request.method!=='GET'||!url.href.startsWith(ROOT))return;
event.respondWith((async()=>{
 const cache=await caches.open(SAVED);const saved=()=>cache.match(request,{ignoreSearch:true});
 if(request.headers.has('range')){const full=await saved();if(full){const data=await full.arrayBuffer(),range=request.headers.get('range').match(/^bytes=(\\d*)-(\\d*)$/);if(!range)return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+data.byteLength}});let start=range[1]?Number(range[1]):Math.max(0,data.byteLength-Number(range[2])),end=range[1]?(range[2]?Math.min(Number(range[2]),data.byteLength-1):data.byteLength-1):data.byteLength-1;if(start>end||start>=data.byteLength)return new Response(null,{status:416,headers:{'Content-Range':'bytes */'+data.byteLength}});return new Response(data.slice(start,end+1),{status:206,headers:{'Content-Type':full.headers.get('Content-Type')||'audio/mpeg','Accept-Ranges':'bytes','Content-Range':`bytes ${start}-${end}/${data.byteLength}`,'Content-Length':String(end-start+1)}});}return fetch(request);}
 if(request.cache!=='no-store'&&(url.pathname.endsWith('.mp3')||url.pathname.includes('/assets/'))){const existing=await saved();if(existing)return existing;}
 try{const response=await fetch(request);if(response.ok)return response;return await saved()||response;}
 catch{return await saved()||await caches.match(request,{ignoreSearch:true})||Response.error();}
})());
});
""".replace('VOLUME',str(vol))
 (v/'sw.js').write_text(sw,encoding='utf8')
 files={'./','index.html','style.css','app.js','pwa.js','manifest.webmanifest','clip-player.js','media-player.js','audiobook.js','audiobook.css','offline.js','audio/catalog.json'}
 files.update(x['src'] for x in doc.select('img[src]') if not x['src'].startswith(('http','data:')))
 for p in v.glob('audio/ch*/timing.json'):
  files.add(p.relative_to(v).as_posix());d=json.loads(p.read_text('utf8'));files.update(s['src'] for s in d['segments'])
 files.update(p.relative_to(v).as_posix() for p in (v/'assets').glob('app-icon-*.png'))
 digests={};size=0
 for f in sorted(files):
  raw=(v/('index.html' if f=='./' else f.split('?')[0])).read_bytes();size+=len(raw);digests[f]=hashlib.sha256(raw).hexdigest()
 (v/'offline-manifest.json').write_text(json.dumps({'files':sorted(files),'bytes':size,'sha256':digests},indent=2),encoding='utf8')
 print(vol,len(files),size)
