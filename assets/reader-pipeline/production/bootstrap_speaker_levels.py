"""First-project RMS baseline bootstrap. Preserve an existing baseline."""
from pathlib import Path
from collections import defaultdict
import json
import numpy as np
work=Path(__file__).resolve().parent/'audiobook'
destination=work/'loudness-analysis.json'
if destination.exists():
 print('Existing baseline retained; do not change existing speaker gains implicitly.')
else:
 levels=json.loads((work/'clip-levels.json').read_text('utf8'));voices=defaultdict(list)
 for chapter in sorted(work.glob('ch??.json')):
  data=json.loads(chapter.read_text('utf8'))
  for segment in data['segments']:
   level=levels[segment['filename']]
   if level['trim_end']-level['trim_start']>24000*.8:voices[segment['speaker']].append(level['rms_db'])
 baselines={name:float(np.median(values)) for name,values in voices.items()};assert baselines
 destination.write_text(json.dumps({'speaker_rms_baseline':baselines},indent=2),encoding='utf8')
 print('Baseline created for',len(baselines),'speakers')
