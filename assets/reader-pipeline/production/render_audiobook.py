"""Conservative speaker leveling, silence-only joins, continuous chapter master."""
from pathlib import Path
import json,subprocess,re,wave,math,collections,argparse
import numpy as np
import av,imageio_ffmpeg
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'production/audiobook';SITE=ROOT/'story-reader';FF=imageio_ffmpeg.get_ffmpeg_exe();SR=24000
def decode(p):
 out=[]
 with av.open(str(p)) as c:
  res=av.AudioResampler(format='fltp',layout='mono',rate=SR)
  for frame in c.decode(audio=0):
   for f in res.resample(frame):out.append(f.to_ndarray().ravel())
  for f in res.resample(None):out.append(f.to_ndarray().ravel())
 return np.concatenate(out)
def bounds(x):
 # Require both a quiet 10ms frame and no significant transient before trimming.
 n=240;count=len(x)//n
 if count<1:return 0,len(x)
 frames=x[:count*n].reshape(-1,n);r=np.sqrt(np.mean(frames**2,axis=1));pk=np.max(np.abs(frames),axis=1)
 threshold=max(.001,min(.004,float(np.quantile(r,.8))*.045))
 active=np.where((r>threshold)|(pk>.012))[0]
 if not len(active):return 0,len(x)
 return max(0,int(active[0]*n)-1440),min(len(x),int((active[-1]+1)*n)+2400)
def run(args):return subprocess.run([FF,'-hide_banner','-nostdin',*args],capture_output=True,text=True,encoding='utf8',errors='replace',check=True)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--chapter',type=int,default=0);args=ap.parse_args()
 statspath=WORK/'clip-levels.json';stats=json.loads(statspath.read_text('utf8')) if statspath.exists() else {};speakers=collections.defaultdict(list)
 for p in sorted(WORK.glob('ch??.json')):
  d=json.loads(p.read_text('utf8'));folder=SITE/f"volume-{d['volume']}"/'audio'/f"ch{d['chapter']:02}"
  for s in d['segments']:
   if s['filename'] not in stats:
    x=decode(folder/s['filename']);a,b=bounds(x);speech=x[a:b];level=20*math.log10(max(1e-8,float(np.sqrt(np.mean(speech**2)))))
    stats[s['filename']]={'rms_db':level,'samples':len(x),'trim_start':a,'trim_end':b}
   st=stats[s['filename']]
   if st['trim_end']-st['trim_start']>SR*.8:speakers[s['speaker']].append(st['rms_db'])
  statspath.write_text(json.dumps(stats),encoding='utf8');print(f'measured chapter {d["chapter"]}: {len(stats)} clips',flush=True)
 medians={s:float(np.median(vals)) for s,vals in speakers.items()};target=float(np.median(list(medians.values())))
 (WORK/'loudness-analysis.json').write_text(json.dumps({'speaker_rms_baseline':medians,'target_rms':target,'clips':stats},indent=2),encoding='utf8')
 for p in sorted(WORK.glob('ch??.json')):
  d=json.loads(p.read_text('utf8'));ch=d['chapter']
  if args.chapter and ch!=args.chapter:continue
  folder=SITE/f"volume-{d['volume']}"/'audio'/f'ch{ch:02}';dest=folder/'chapter.mp3';edlpath=WORK/f'edit-ch{ch:02}.json'
  if dest.exists() and edlpath.exists():print(f'cached {ch}',flush=True);continue
  parts=[];edits=[];pos=0;segments=d['segments']
  para=lambda ref:ref[0].split('-s')[0] if ref else None
  for i,s in enumerate(segments):
   x=decode(folder/s['filename']);st=stats[s['filename']];a=0;b=len(x)
   prev_same=i>0 and para(segments[i-1]['word_map'][-1])==para(s['word_map'][0])
   next_same=i+1<len(segments) and para(s['word_map'][-1])==para(segments[i+1]['word_map'][0])
   if prev_same:a=st['trim_start']
   if next_same:b=st['trim_end']
   baseline=medians.get(s['speaker'],target);speaker_gain=max(-8,min(8,target-baseline))
   residual=st['rms_db']-baseline;correction=max(-3,min(3,-math.copysign(max(0,abs(residual)-4),residual)))
   gain=speaker_gain+correction;y=(x[a:b]*10**(gain/20)).copy()
   # Tiny fades affect only already retained quiet edges, not overlapping words.
   fade=min(96,len(y)//2)
   if prev_same:y[:fade]*=np.linspace(0,1,fade)
   if next_same:y[-fade:]*=np.linspace(1,0,fade)
   edits.append({'filename':s['filename'],'input_samples':len(x),'start_sample':a,'end_sample':b,'output_start_sample':pos,'gain_db':round(gain,3),'same_paragraph_before':prev_same,'same_paragraph_after':next_same})
   parts.append(y);pos+=len(y)
   # Retain 60ms before +100ms after each cut; no extra artificial gap.
  master=np.concatenate(parts);pre_scale=min(1.0,.95/max(.95,float(np.max(np.abs(master)))));master*=pre_scale;wav=WORK/f'ch{ch:02}-master.wav'
  with wave.open(str(wav),'wb') as w:w.setnchannels(1);w.setsampwidth(4);w.setframerate(SR);w.writeframes(np.clip(master*2147483647,-2147483648,2147483647).astype('<i4').tobytes())
  first=run(['-i',str(wav),'-af','loudnorm=I=-18:TP=-1.5:LRA=20:print_format=json','-f','null','-'])
  measurement=json.loads(re.findall(r'\{[^{}]+\}',first.stderr)[-1]);filt='loudnorm=I=-18:TP=-1.5:LRA=20:linear=true:'+':'.join(f'{key}={measurement[src]}' for key,src in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
  run(['-y','-i',str(wav),'-af',filt,'-ar',str(SR),'-ac','1','-c:a','libmp3lame','-b:a','96k',str(dest)])
  final=run(['-i',str(dest),'-af','loudnorm=I=-18:TP=-1.5:LRA=20:print_format=json','-f','null','-']);final_measure=json.loads(re.findall(r'\{[^{}]+\}',final.stderr)[-1])
  decoded=decode(dest);assert abs(len(decoded)-len(master))<=SR*.05
  report={'chapter':ch,'sample_rate':SR,'duration':len(decoded)/SR,'timeline_samples':pos,'edits':edits,'pre_scale':pre_scale,'normalization_input':measurement,'final_measurement':final_measure,'original_files_preserved':True,'listened':False}
  edlpath.write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({'chapter':ch,'duration':len(decoded)/SR,'LUFS':final_measure['input_i'],'true_peak':final_measure['input_tp'],'clips':len(edits)}),flush=True)
if __name__=='__main__':main()
