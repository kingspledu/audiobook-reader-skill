from pathlib import Path
import json,math
import numpy as np
from render_audiobook import decode,bounds,WORK,SITE,SR
p=WORK/'clip-levels.json';levels=json.loads(p.read_text('utf8'));added=0
for source in sorted(WORK.glob('ch??.json')):
 d=json.loads(source.read_text('utf8'));folder=SITE/f"volume-{d['volume']}/audio/ch{d['chapter']:02}"
 for s in d['segments']:
  if s['filename'] in levels:continue
  x=decode(folder/s['filename']);a,b=bounds(x);speech=x[a:b];levels[s['filename']]={'rms_db':20*math.log10(max(1e-8,float(np.sqrt(np.mean(speech**2))))),'samples':len(x),'trim_start':a,'trim_end':b};added+=1
p.write_text(json.dumps(levels),encoding='utf8');print(json.dumps({'new_clips_measured':added,'total':len(levels)}))
