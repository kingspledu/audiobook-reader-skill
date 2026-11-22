"""Refresh public skill file hashes after deliberate source edits."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
files={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
       for p in sorted(ROOT.rglob('*')) if p.is_file() and '.git' not in p.parts
       and '__pycache__' not in p.parts and p.suffix!='.pyc' and p.name!='CONTENT_MANIFEST.json'}
(ROOT/'CONTENT_MANIFEST.json').write_text(json.dumps({'files':files},ensure_ascii=False,indent=2)+'\n','utf8')
print(f'Manifest: {len(files)} files')
