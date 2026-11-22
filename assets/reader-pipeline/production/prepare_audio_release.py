from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];SITE=ROOT/'story-reader';WORK=ROOT/'production/audiobook';paths=[]
for vol in (1,2,3):
 for name in ['index.html','sw.js','clip-player.js','media-player.js','audiobook.js','audiobook.css','offline.js','offline-manifest.json','audio/catalog.json']:paths.append(f'volume-{vol}/{name}')
for p in sorted(WORK.glob('ch??.json')):
 d=json.loads(p.read_text('utf8'));vol=d['volume'];ch=d['chapter'];paths.append(f'volume-{vol}/audio/ch{ch:02}/timing.json')
 for s in d['segments']:paths.append(f"volume-{vol}/audio/ch{ch:02}/clips/{s['filename']}")
paths.append('audiobook-validation.json')
for name in ['normalization-report.json','asset-validation.json','reader-validation.json','browser-validation.json','offline-validation.json','new-audio-validation.json','offline-all-validation.json']:
 if (WORK/name).exists():shutil.copyfile(WORK/name,SITE/('audiobook-'+name));paths.append('audiobook-'+name)
for p in paths:assert (SITE/p).is_file(),p
assert all('chapter.mp3' not in p and (not p.endswith('.mp3') or '/clips/' in p) for p in paths)
(WORK/'stage-paths.txt').write_text('\n'.join(paths)+'\n',encoding='utf8')
print(json.dumps({'files':len(paths),'mp3':sum(p.endswith('.mp3') for p in paths),'bytes':sum((SITE/p).stat().st_size for p in paths),'merged_tracks':0}))
