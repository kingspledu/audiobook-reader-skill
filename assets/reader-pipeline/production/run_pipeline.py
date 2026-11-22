"""Single documented entry point; no publication side effect."""
from pathlib import Path
import argparse,subprocess,sys,json,time
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--book',default='book.json');parser.add_argument('--initialize',action='store_true');args=parser.parse_args();steps=[];start=time.time()
 def run(name,*extra):
  p=subprocess.run([sys.executable,str(ROOT/'production'/name),*extra],cwd=ROOT);steps.append({'stage':name,'exit_code':p.returncode});
  if p.returncode:raise RuntimeError(name+' failed')
 try:
  if args.initialize:run('build_reading_html.py','--input',args.book,'--output','story-reader')
  assert (ROOT/'story-reader/volume-1/index.html').exists(),'Create reading HTML first with --initialize'
  work=ROOT/'production/audiobook';work.mkdir(parents=True,exist_ok=True);levels=work/'clip-levels.json'
  if not levels.exists():levels.write_text('{}',encoding='utf8')
  run('cache_guard.py');run('prepare_audiobook.py');run('measure_new_clips.py');run('bootstrap_speaker_levels.py');run('normalize_clips.py')
  # Capture the newly bootstrapped gain baseline before alignment is committed.
  run('cache_guard.py');run('measure_new_clips.py');run('normalize_clips.py');run('whisper_force_align.py');run('publish_audiobook.py');run('build_landscape_test.py')
  import shutil
  shutil.copyfile(ROOT/'production/landscape-test/manifest.webmanifest',ROOT/'story-reader/landscape-test/manifest.webmanifest')
  run('install_offline_v2.py');run('validate_audio_assets.py')
  status='PASS'
 except Exception as error:status='FAIL';print(error,file=sys.stderr)
 (ROOT/'production/audiobook/pipeline-report.json').write_text(json.dumps({'status':status,'seconds':round(time.time()-start,2),'steps':steps},indent=2),encoding='utf8')
 if status!='PASS':sys.exit(1)
if __name__=='__main__':main()
