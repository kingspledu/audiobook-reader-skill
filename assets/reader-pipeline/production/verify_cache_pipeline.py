"""Exercise cached rebuild and changed transcript/audio invalidation in a smoke project."""
from pathlib import Path
import json,subprocess,sys,shutil,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[1];DOCS=ROOT/'docs';fixture=Path(json.loads((DOCS/'SMOKE_TEST_REPORT.json').read_text('utf8'))['fresh_unpacked_project'])
for name in ['cache_guard.py','run_pipeline.py']:shutil.copyfile(ROOT/'production'/name,fixture/'production'/name)
def run(name):
 p=subprocess.run([sys.executable,'production/'+name],cwd=fixture,capture_output=True,text=True,encoding='utf8',errors='replace');assert p.returncode==0,p.stderr[-2000:]
def hashes():return {p.relative_to(fixture).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (fixture/'story-reader').rglob('*') if p.is_file() and '.git' not in p.parts}
run('run_pipeline.py');before=hashes();run('run_pipeline.py');after=hashes();assert before==after,'Cached output changed'
report=json.loads((fixture/'production/audiobook/cache-guard-report.json').read_text());assert all(x['action']=='reuse' for x in report['events'])
archive=fixture/'public-tiger/tts zip/SMOKE_C01.zip'
with zipfile.ZipFile(archive) as z:entries={name:z.read(name) for name in z.namelist()}
name=next(n for n in entries if n.endswith('_INDEX.json'));data=json.loads(entries[name]);data['segments'][0]['text']='A gentle tone!';entries[name]=json.dumps(data).encode()
with zipfile.ZipFile(archive,'w') as z:
 for n,b in entries.items():z.writestr(n,b)
run('cache_guard.py');r=json.loads((fixture/'production/audiobook/cache-guard-report.json').read_text());invalid=[x['chapter'] for x in r['events'] if x['action']=='invalidate'];assert invalid==[1],invalid
assert (fixture/'production/audiobook/aligned-ch11.json').exists();assert not (fixture/'production/audiobook/aligned-ch01.json').exists()
run('run_pipeline.py');run('cache_guard.py')
# Replace the same filename with another valid MP3 (changed PCM amplitude).
import av,numpy as np
tone=fixture/'replacement.mp3'
with av.open(str(tone),'w',format='mp3') as out:
 stream=out.add_stream('libmp3lame',rate=44100);stream.layout='mono';stream.bit_rate=192000;x=(.06*np.sin(2*np.pi*440*np.arange(88200)/44100)).astype('float32');frame=av.AudioFrame.from_ndarray(x.reshape(1,-1),format='fltp',layout='mono');frame.sample_rate=44100
 for packet in stream.encode(frame):out.mux(packet)
 for packet in stream.encode(None):out.mux(packet)
with zipfile.ZipFile(archive) as z:entries={n:z.read(n) for n in z.namelist()}
clip=data['segments'][0]['filename'];entries[clip]=tone.read_bytes()
with zipfile.ZipFile(archive,'w') as z:
 for n,b in entries.items():z.writestr(n,b)
run('run_pipeline.py');d=json.loads((fixture/'production/audiobook/ch01.json').read_text());assert d['segments'][0]['sha256']==hashlib.sha256(tone.read_bytes()).hexdigest()
assert (fixture/'story-reader/volume-1/audio/ch01'/clip).read_bytes()==tone.read_bytes()
before=hashes();run('run_pipeline.py');after=hashes();assert before==after
result={'cached_rebuild_output_equality':'PASS','unchanged_chapters_reused':'PASS','changed_transcript_only_chapter1_invalidated':'PASS','same_filename_changed_audio_reextracted':'PASS','modified_audio_rebuild_equality':'PASS','originals_backed_up':any((fixture/'production/audiobook/cache-backups').rglob('*.mp3')),'fixture':str(fixture),'human_listening':False}
(DOCS/'CACHE_PIPELINE_REPORT.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
