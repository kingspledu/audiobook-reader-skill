"""Unpack the deliverable into a fresh project and execute real CLI stages.
Fixture audio is an artificial sine tone, NOT speech. Whisper execution is real;
this smoke test proves wiring/fallback, never ASR accuracy or human listening.
"""
from pathlib import Path
from tempfile import mkdtemp
import argparse,zipfile,json,subprocess,sys,shutil,math,hashlib
import numpy as np
import av

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--skip-whisper',action='store_true');parser.add_argument('--real-speech',action='store_true');args=parser.parse_args()
 original=Path(__file__).resolve().parents[1];bundle=original/'docs/audiobook-template-source.zip';root=Path(mkdtemp(prefix='audio-template-smoke-',dir=original/'production'));steps=[]
 with zipfile.ZipFile(bundle) as z:z.extractall(root)
 def run(command,cwd=None):
  p=subprocess.run(command,cwd=cwd or root,capture_output=True,text=True,encoding='utf8',errors='replace');steps.append({'command':command,'exit_code':p.returncode,'stdout_tail':p.stdout[-1800:],'stderr_tail':p.stderr[-1200:]})
  if p.returncode:raise RuntimeError(f'Failed {command}: {p.stderr[-1500:]}')
 def py(name,*extra):run([sys.executable,'production/'+name,*extra])
 try:
  book=json.loads((root/'production/reader-template/book.sample.json').read_text('utf8'));(root/'assets').mkdir();(root/'assets/scene.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><rect width="200" height="200" fill="#729d7f"/></svg>',encoding='utf8')
  speech=[]
  if args.real_speech:
   original_data=json.loads((original/'production/audiobook/ch01.json').read_text('utf8'));segments=original_data['segments'];selected=[0,16,17,18,19]
   speech=[(segments[i],original/'story-reader/volume-1/audio/ch01'/segments[i]['filename']) for i in selected];texts=iter(s['text'] for s,p in speech)
   for chapter in book['chapters']:
    for paragraph in chapter['paragraphs']:paragraph['sentences']=[next(texts) for _ in paragraph['sentences']]
  for ch in book['chapters']:ch['paragraphs'][0].update(image='assets/scene.svg',alt='Synthetic smoke fixture')
  (root/'book.json').write_text(json.dumps(book,ensure_ascii=False),encoding='utf8')
  py('build_reading_html.py','--input','book.json','--output','story-reader')
  from bs4 import BeautifulSoup
  expected=[s for c in book['chapters'] for p in c['paragraphs'] for s in p['sentences']];actual=[]
  for v in (1,2,3):actual.extend(s.get_text() for s in BeautifulSoup((root/f'story-reader/volume-{v}/index.html').read_text('utf8'),'html.parser').select('.reading-sentence'))
  assert actual==expected,'Initial HTML source mismatch'
  site=root/'story-reader';run(['git','init','--quiet'],site);run(['git','add','--','.'],site);run(['git','-c','user.name=Smoke','-c','user.email=smoke@example.invalid','commit','--quiet','-m','Initial source reader fixture'],site)
  tone=root/'tone.mp3'
  with av.open(str(tone),'w',format='mp3') as out:
   stream=out.add_stream('libmp3lame',rate=44100);stream.bit_rate=192000;stream.layout='mono';t=np.arange(44100*2)/44100;signal=(.12*np.sin(2*np.pi*440*t)).astype('float32');signal[:4410]=0;signal[-4410:]=0
   frame=av.AudioFrame.from_ndarray(signal.reshape(1,-1),format='fltp',layout='mono');frame.sample_rate=44100
   for p in stream.encode(frame):out.mux(p)
   for p in stream.encode(None):out.mux(p)
  inbox=root/'public-tiger/tts zip';inbox.mkdir(parents=True)
  fixture_index=0
  for chapter in book['chapters']:
   ch=chapter['number'];segments=[];i=0
   for pi,paragraph in enumerate(chapter['paragraphs'],1):
    for sentence in paragraph['sentences']:
     name=f'SMOKE_C{ch:02}_V01_{i:04}_C{ch:02}_P{pi:03}_TEST.mp3';segments.append({'filename':name,'order':i,'text':sentence,'speaker':speech[fixture_index][0]['speaker'] if speech else 'Test Narrator','kind':'narration','fixture_source':str(speech[fixture_index][1]) if speech else str(tone)});i+=1;fixture_index+=1
   with zipfile.ZipFile(inbox/f'SMOKE_C{ch:02}.zip','w') as z:
    for s in segments:z.write(Path(s.pop('fixture_source')),s['filename'])
    z.writestr(f'SMOKE_C{ch:02}_INDEX.json',json.dumps({'chapter':ch,'complete':True,'missing':[],'segments':segments}))
  py('prepare_audiobook.py');work=root/'production/audiobook';(work/'clip-levels.json').write_text('{}',encoding='utf8')
  py('measure_new_clips.py');py('bootstrap_speaker_levels.py');py('normalize_clips.py')
  if args.skip_whisper:raise RuntimeError('Full reproducibility gate requires Whisper; --skip-whisper is diagnostic only')
  py('whisper_force_align.py')
  py('publish_audiobook.py');py('install_offline_v2.py');py('build_landscape_test.py');shutil.copyfile(root/'production/landscape-test/manifest.webmanifest',site/'landscape-test/manifest.webmanifest')
  py('validate_reader_audio.py');py('validate_audio_assets.py');py('prepare_audio_release.py')
  py('run_pipeline.py')
  for js in ['clip-player.js','media-player.js','audiobook.js','offline-v2.js','landscape-test/test.js','reader-template/app.js']:run(['node','--check','production/'+js])
  for v in (1,2,3):
   folder=site/f'volume-{v}';manifest=json.loads((folder/'offline-manifest.json').read_text('utf8'))
   for name,digest in manifest['sha256'].items():assert hashlib.sha256((folder/('index.html' if name=='./' else name.split('?')[0])).read_bytes()).hexdigest()==digest
  run([sys.executable,'-c',"from pathlib import Path; import hashlib,json; p=Path('story-reader'); print('READY',len(list(p.glob('volume-*/audio/ch*/clips/*.mp3'))))"])
  result={'status':'PASS','fresh_unpacked_project':str(root),'initial_reader_html':'PASS','source_sentence_preservation':'PASS','fixture_chapters':[1,11,21],'fixture_segments':5,'real_whisper_executed':True,'fixture_audio':'five supplied TTS clips, local only' if args.real_speech else 'synthetic sine wave, no speech','claims_not_covered':['human-annotated speech timing accuracy','human listening','physical phone lock playback','full book processing'],'offline_hashes':'PASS','steps':steps}
 except Exception as error:
  result={'status':'FAIL','fresh_unpacked_project':str(root),'error':str(error),'steps':steps}
 (original/'docs/SMOKE_TEST_REPORT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='steps'},ensure_ascii=True,indent=2))
 if result['status']!='PASS':sys.exit(1)
if __name__=='__main__':main()
