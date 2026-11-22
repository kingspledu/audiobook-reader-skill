"""Keep clips separate; use one constant gain per speaker, never edit silence."""
from pathlib import Path
import json,math,collections
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import av
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'production/audiobook';SITE=ROOT/'story-reader'
def process(task):
 source,dest,gain=task
 if dest.exists():return dest.stat().st_size
 temp=dest.with_suffix('.tmp.mp3')
 with av.open(str(source)) as c:
  rate=c.streams.audio[0].codec_context.sample_rate
  with av.open(str(temp),'w',format='mp3') as out:
   stream=out.add_stream('libmp3lame',rate=rate);stream.bit_rate=192000;stream.layout='mono'
   res=av.AudioResampler(format='fltp',layout='mono',rate=rate);position=0
   def encode(frame):
    nonlocal position
    x=frame.to_ndarray().astype(np.float32)*10**(gain/20)
    # All gains are <=0; reserve extra peak headroom, no compression or per-clip AGC.
    assert np.max(np.abs(x))<=1.001
    f=av.AudioFrame.from_ndarray(x,format='fltp',layout='mono');f.sample_rate=rate;f.pts=position;position+=f.samples
    for packet in stream.encode(f):out.mux(packet)
   for frame in c.decode(audio=0):
    for f in res.resample(frame):encode(f)
   for f in res.resample(None):encode(f)
   for packet in stream.encode(None):out.mux(packet)
 temp.replace(dest);return dest.stat().st_size
def main():
 analysis=json.loads((WORK/'loudness-analysis.json').read_text('utf8'));baselines=analysis['speaker_rms_baseline']
 # Conservative attenuation-only leveling avoids amplification and clipping.
 target=min(-20.0,min(baselines.values())-.1);gains={speaker:round(target-level,5) for speaker,level in baselines.items()}
 previous=WORK/'normalization-report.json'
 if previous.exists():gains.update(json.loads(previous.read_text('utf8'))['speaker_gain_db'])
 report=[]
 with ThreadPoolExecutor(max_workers=4) as pool:
  for p in sorted(WORK.glob('ch??.json')):
   d=json.loads(p.read_text('utf8'));folder=SITE/f"volume-{d['volume']}"/'audio'/f"ch{d['chapter']:02}";dest=folder/'clips';dest.mkdir(exist_ok=True)
   tasks=[(folder/s['filename'],dest/s['filename'],gains.get(s['speaker'],0)) for s in d['segments']]
   sizes=list(pool.map(process,tasks));row={'chapter':d['chapter'],'clips':len(tasks),'bytes':sum(sizes)};report.append(row);print(json.dumps(row),flush=True)
 (WORK/'normalization-report.json').write_text(json.dumps({'method':'constant speaker gain, attenuation only; no trimming, mixing, compression, or chapter merge','target_speech_rms_db':target,'speaker_gain_db':gains,'sample_rate':'source rate preserved','bitrate':192000,'chapters':report},indent=2),encoding='utf8')
if __name__=='__main__':main()
