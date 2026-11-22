from pathlib import Path
import json,hashlib,zipfile,re
ROOT=Path(__file__).resolve().parents[1]
def main():
 manifest=json.loads((ROOT/'CONTENT_MANIFEST.json').read_text('utf8'))['files'];assert manifest
 for name,digest in manifest.items():
  p=ROOT/name;assert p.is_file(),name;assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
 for name in ['SKILL.md','references/START_HERE.md','scripts/init_workspace.py','assets/gemini-canvas-tts/scripts/build.py','assets/gemini-canvas-tts/assets/canvas-template.html']:assert (ROOT/name).exists(),name
 with zipfile.ZipFile(ROOT/'assets/audiobook-template-source.zip') as z:
  assert z.testzip() is None
  inner=json.loads(z.read('SOURCE_MANIFEST.json'))['sha256']
  for name,digest in inner.items():
   assert hashlib.sha256(z.read(name)).hexdigest()==digest,name
   assert (ROOT/'assets/reader-pipeline'/name).read_bytes()==z.read(name),name
  for name in ['production/build_reading_html.py','production/reader-template/index.html','production/reader-template/style.css','production/reader-template/app.js','production/run_pipeline.py','production/whisper_force_align.py','production/landscape-test/test.js']:assert name in z.namelist(),name
 for p in ROOT.rglob('*'):
  if not p.is_file() or '.git' in p.parts or '__pycache__' in p.parts:continue
  assert p.suffix not in ['.mp3','.wav','.pyc'],p
  if p.suffix in ['.md','.json','.py','.html','.js','.csv','.txt']:
   text=p.read_text('utf8');assert not re.search(r'AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{20,}',text),p
 print(json.dumps({'status':'PASS','manifest_files':len(manifest),'reader_source_files':len(inner),'no_real_audio_or_credentials':True}))
if __name__=='__main__':main()
