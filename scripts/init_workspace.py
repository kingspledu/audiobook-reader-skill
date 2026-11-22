from pathlib import Path
import argparse,zipfile,shutil
SKILL=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args();out=Path(a.out).resolve()
 if out.exists() and any(out.iterdir()):raise SystemExit('Refusing to overwrite a nonempty workspace')
 if out==SKILL or SKILL in out.parents:raise SystemExit('Choose a workspace outside this skill')
 out.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(SKILL/'assets/audiobook-template-source.zip') as z:
  for name in z.namelist():
   target=(out/name).resolve()
   if not target.is_relative_to(out):raise SystemExit('Unsafe archive member')
  z.extractall(out)
 shutil.copytree(SKILL/'assets/gemini-canvas-tts',out/'tts')
 (out/'docs').mkdir(exist_ok=True);shutil.copyfile(SKILL/'assets/audiobook-template-source.zip',out/'docs/audiobook-template-source.zip')
 print(out)
if __name__=='__main__':main()
