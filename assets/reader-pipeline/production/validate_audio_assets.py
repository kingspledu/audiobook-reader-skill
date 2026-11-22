from pathlib import Path
from collections import defaultdict
import json,hashlib
import numpy as np
import av
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'production/audiobook';SITE=ROOT/'story-reader'
report=json.loads((WORK/'normalization-report.json').read_text('utf8'));gains=report['speaker_gain_db'];samples={};count=0
for p in WORK.glob('ch??.json'):
 d=json.loads(p.read_text('utf8'));folder=SITE/f"volume-{d['volume']}"/'audio'/f"ch{d['chapter']:02}"
 for s in d['segments']:
  source=folder/s['filename'];target=folder/'clips'/s['filename'];assert target.exists() and target.stat().st_size>100
  assert hashlib.sha256(source.read_bytes()).hexdigest()==s['sha256'];count+=1
  if s['speaker'] not in samples:samples[s['speaker']]=(source,target,s['speaker'])
def pcm(path):
 with av.open(str(path)) as c:
  rate=c.streams.audio[0].sample_rate;frames=[f.to_ndarray().ravel() for f in c.decode(audio=0)]
 return np.concatenate(frames),rate
checks=[]
for source,target,speaker in samples.values():
 a,ra=pcm(source);b,rb=pcm(target);assert ra==rb and len(a)==len(b)
 db=20*np.log10(np.sqrt(np.mean(b*b))/np.sqrt(np.mean(a*a)));print(json.dumps({'speaker':speaker,'expected':gains[speaker],'measured':float(db)}),flush=True);assert abs(db-gains[speaker])<.5
 checks.append({'speaker':speaker,'expected_gain_db':gains[speaker],'measured_rms_change_db':round(float(db),4),'peak':round(float(np.max(np.abs(b))),4),'duration_and_sample_rate':'PASS'})
residuals=[x['measured_rms_change_db']-x['expected_gain_db'] for x in checks];assert max(residuals)-min(residuals)<.05
result={'clips_checked':count,'original_hashes':'PASS','separate_mp3_files':'PASS','speaker_sample_checks':checks,'encoder_common_attenuation_db':float(np.mean(residuals)),'speaker_relative_gain_error_spread_db':max(residuals)-min(residuals),'gain_policy':'constant per speaker; attenuation only; no per-clip leveling, compression, silence editing, or merge','human_listening':False}
(WORK/'asset-validation.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
