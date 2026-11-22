"""Canvas audio-index-1 plus individual WAV/MP3 -> reader MP3 ZIP."""
from pathlib import Path
import argparse,json,zipfile,hashlib,tempfile,subprocess
def main():
 p=argparse.ArgumentParser();p.add_argument('--index',required=True);p.add_argument('--audio-dir',required=True);p.add_argument('--out',required=True);a=p.parse_args()
 data=json.loads(Path(a.index).read_text('utf8'));audio=Path(a.audio_dir).resolve();out=Path(a.out).resolve();groups={}
 for s in data['segments']:
  name=s['filename'];assert Path(name).name==name,'Unsafe filename';source=audio/name
  if not source.exists():source=source.with_suffix('.mp3')
  assert source.is_file(),f'Missing audio: {name}'
  assert source.suffix.lower() in ['.wav','.mp3'],'Individual WAV/MP3 required'
  if s.get('text_sha256'):assert hashlib.sha256(s['text'].encode()).hexdigest()==s['text_sha256'],'Transcript hash mismatch'
  chapter=s.get('chapter',data.get('chapter'));assert isinstance(chapter,int)
  groups.setdefault(chapter,[]).append((s,source))
 out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as temp:
  for chapter,items in groups.items():
   orders=[s['order'] for s,f in items];assert len(orders)==len(set(orders)),'Duplicate orders'
   segments=[];files=[]
   for s,source in sorted(items,key=lambda t:t[0]['order']):
    name=source.stem+'.mp3';dest=Path(temp)/name
    if source.suffix.lower()=='.mp3':dest.write_bytes(source.read_bytes())
    else:
     import imageio_ffmpeg
     subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),'-hide_banner','-loglevel','error','-y','-i',str(source),'-c:a','libmp3lame','-b:a','192k',str(dest)],check=True)
    segment={k:v for k,v in s.items() if k!='chapter'};segment['filename']=name;segments.append(segment);files.append(dest)
   assert len({s['filename'] for s in segments})==len(segments),'Duplicate filenames'
   target=out/f'READER_C{chapter:02}_MP3.zip'
   if target.exists():raise FileExistsError(f'Refusing to overwrite {target}')
   with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for f in files:z.write(f,f.name)
    z.writestr(f'READER_C{chapter:02}_MP3_INDEX.json',json.dumps({'schema':'mp3-zip-index-1','chapter':chapter,'complete':True,'missing':[],'segments':segments},ensure_ascii=False,indent=2))
   print(target)
if __name__=='__main__':main()
