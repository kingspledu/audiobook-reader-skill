"""Resolve installed dependency closure for this platform; no unrelated environment packages."""
from pathlib import Path
import importlib.metadata as md,json,platform
from packaging.requirements import Requirement
ROOT=Path(__file__).resolve().parents[1];todo=['beautifulsoup4','numpy','av','faster-whisper','imageio-ffmpeg','huggingface-hub'];seen={}
while todo:
 name=todo.pop();distribution=md.distribution(name);key=distribution.metadata['Name'].lower().replace('_','-')
 if key in seen:continue
 seen[key]=distribution.version
 for raw in distribution.requires or []:
  r=Requirement(raw)
  if r.marker is None or r.marker.evaluate({'extra':''}):todo.append(r.name)
path=ROOT/'docs/requirements-audiobook-full-lock.txt';path.write_text('\n'.join(f'{n}=={v}' for n,v in sorted(seen.items()))+'\n',encoding='utf8')
(ROOT/'docs/DEPENDENCY_ENVIRONMENT.json').write_text(json.dumps({'python':platform.python_version(),'platform':platform.platform(),'packages':len(seen),'extra_dependencies':'default extras only','lock':path.name},indent=2),encoding='utf8');print(len(seen),'packages locked')
