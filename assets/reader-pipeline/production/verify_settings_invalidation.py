from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];report=ROOT/'docs/CACHE_PIPELINE_REPORT.json';data=json.loads(report.read_text('utf8'));fixture=Path(data['fixture']);code=fixture/'production/whisper_force_align.py';original=code.read_bytes()
try:
 code.write_bytes(original+b'\n# configuration invalidation probe\n')
 p=subprocess.run([sys.executable,'production/cache_guard.py'],cwd=fixture,capture_output=True,text=True);assert p.returncode==0,p.stderr
 rows=json.loads((fixture/'production/audiobook/cache-guard-report.json').read_text('utf8'))['events'];invalid=[r['chapter'] for r in rows if r['action']=='invalidate'];assert invalid==[1,11,21],invalid
 data['alignment_code_change_invalidates_affected_chapters']='PASS';report.write_text(json.dumps(data,indent=2),encoding='utf8');print('PASS: alignment configuration change invalidated chapters 1,11,21')
finally:code.write_bytes(original)
