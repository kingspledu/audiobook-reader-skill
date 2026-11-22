"""Content-based invalidation. Backup only affected book outputs; never delete originals."""
from pathlib import Path
import json,hashlib,zipfile,shutil,datetime,importlib.metadata
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'production/audiobook';SITE=ROOT/'story-reader'
def digest(data):return hashlib.sha256(data).hexdigest()
def filehash(path):return digest(path.read_bytes()) if path.exists() else None
def main():
 WORK.mkdir(parents=True,exist_ok=True);registry=WORK/'cache-registry.json';old=json.loads(registry.read_text('utf8')) if registry.exists() else {};new={};events=[]
 backup=WORK/'cache-backups'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
 def archive(path):
  if path.exists():
   target=backup/path.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(path),str(target))
 config={name:filehash(ROOT/'production'/name) for name in ['prepare_audiobook.py','measure_new_clips.py','render_audiobook.py','normalize_clips.py','whisper_force_align.py']}
 config['gains']=filehash(WORK/'normalization-report.json')
 # Only gain values affect normalization; chapter inventory in report must not invalidate it.
 if (WORK/'normalization-report.json').exists():config['gains']=digest(json.dumps(json.loads((WORK/'normalization-report.json').read_text('utf8'))['speaker_gain_db'],sort_keys=True).encode())
 for package in ['faster-whisper','ctranslate2','tokenizers']:config[package]=importlib.metadata.version(package)
 from huggingface_hub import snapshot_download
 model=Path(snapshot_download('Systran/faster-whisper-base',local_files_only=True))
 config['model_files']={p.name:filehash(p) for p in [model/'model.bin',model/'config.json',model/'tokenizer.json']}
 for path in sorted((ROOT/'public-tiger/tts zip').glob('*.zip')):
  with zipfile.ZipFile(path) as z:
   data=json.loads(z.read(next(n for n in z.namelist() if n.endswith('_INDEX.json'))));ch=data['chapter'];key=str(ch);vol=1 if ch<=10 else 2 if ch<=20 else 3;folder=SITE/f'volume-{vol}/audio/ch{ch:02}';items={}
   for s in sorted(data['segments'],key=lambda x:x['order']):
    name=s['filename'];assert Path(name).name==name and name.endswith('.mp3')
    items[name]={'audio':digest(z.read(name)),'text':digest(s['text'].encode()),'speaker':s['speaker'],'order':s['order']}
   signature={'items':items,'config':config};new[key]=signature;previous=old.get(key)
   if previous==signature:events.append({'chapter':ch,'action':'reuse','reason':'audio/transcript/speaker/order/settings/dependencies unchanged'});continue
   changed=set(items) if previous is None else {n for n in set(items)|set(previous['items']) if items.get(n)!=previous['items'].get(n)}
   audio_changed={n for n in changed if previous is None or items.get(n,{}).get('audio')!=previous['items'].get(n,{}).get('audio')}
   gain_changed=previous is None or previous['config'].get('gains')!=config['gains'] or previous['config'].get('normalize_clips.py')!=config['normalize_clips.py']
   for name in items:
    raw=folder/name
    if raw.exists() and filehash(raw)!=items[name]['audio']:archive(raw);audio_changed.add(name)
   for name in set(changed)|(set(items) if gain_changed else set()):archive(folder/'clips'/name)
   # DTW batches depend on neighboring utterances, so recompute the affected chapter.
   archive(WORK/f'aligned-ch{ch:02}.json')
   levels=WORK/'clip-levels.json'
   if levels.exists():
    values=json.loads(levels.read_text('utf8'));affected=set(audio_changed)
    if previous is None or previous['config'].get('measure_new_clips.py')!=config['measure_new_clips.py'] or previous['config'].get('render_audiobook.py')!=config['render_audiobook.py']:affected|=set(items)
    values={n:v for n,v in values.items() if n not in affected};levels.write_text(json.dumps(values),encoding='utf8')
   events.append({'chapter':ch,'action':'invalidate','changed_files':sorted(changed),'reason':'first registry or dependency/input changed; affected chapter alignment recomputed'})
 registry.write_text(json.dumps(new,indent=2),encoding='utf8');(WORK/'cache-guard-report.json').write_text(json.dumps({'events':events,'backup_root':str(backup) if backup.exists() else None},indent=2),encoding='utf8');print(json.dumps(events))
if __name__=='__main__':main()
