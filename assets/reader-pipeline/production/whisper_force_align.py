"""Align verified MP3-index text using Whisper cross-attention + dynamic time warping.
This is forced alignment, not ASR transcript verification. No uniform timing fallback.
"""
from pathlib import Path
from difflib import SequenceMatcher
import json,time,math,argparse,re
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT/'production/audiobook';SITE=ROOT/'story-reader'
TOKEN=re.compile(r"[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*")
def norm(t):return [x.group().lower().replace('’',"'") for x in TOKEN.finditer(t)]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--limit',type=int,default=0);parser.add_argument('--chapter',type=int,default=0);args=parser.parse_args()
 import numpy as np
 from faster_whisper import WhisperModel
 from faster_whisper.audio import decode_audio,pad_or_trim
 from faster_whisper.tokenizer import Tokenizer
 model=WhisperModel('base',device='cpu',compute_type='int8',cpu_threads=4,local_files_only=True)
 tokenizer=Tokenizer(model.hf_tokenizer,model.model.is_multilingual,task='transcribe',language='en')
 start=time.time();done=0
 for p in sorted(WORK.glob('ch??.json')):
  data=json.loads(p.read_text('utf8'));ch=data['chapter']
  if args.chapter and ch!=args.chapter:continue
  folder=SITE/f"volume-{data['volume']}"/'audio'/f'ch{ch:02}'
  cache=WORK/f'aligned-ch{ch:02}.json';results=json.loads(cache.read_text('utf8')) if cache.exists() else {}
  pending=[s for s in data['segments'] if s['filename'] not in results]
  batch=[];duration=0
  def process(group):
   nonlocal done
   pcm=np.concatenate([np.concatenate([sound,np.zeros(3200,dtype=np.float32)]) for s,sound in group]);features=model.feature_extractor(pcm)
   enc=model.encode(pad_or_trim(features));text=' '.join(s['text'] for s,sound in group)
   raw=model.find_alignment(tokenizer,[tokenizer.encode(' '+text)],enc,num_frames=min(3000,features.shape[-1]))[0]
   offset=0
   for s,sound in group:
    seconds=len(sound)/16000;expected=norm(s['text']);recognized=[];times=[];probs=[]
    for w in raw:
     if offset<=((float(w['start'])+float(w['end']))/2)<offset+seconds:
      for token in norm(w['word']):recognized.append(token);times.append([round(max(0,float(w['start'])-offset),3),round(min(seconds,float(w['end'])-offset),3)]);probs.append(float(w['probability']))
    aligned=[None]*len(expected);prob=[None]*len(expected)
    for a,b,n in SequenceMatcher(None,expected,recognized,autojunk=False).get_matching_blocks():
     for k in range(n):
      t=times[b+k]
      if t[1]>t[0] and probs[b+k]>=.05:aligned[a+k]=t;prob[a+k]=round(probs[b+k],4)
    results[s['filename']]={'sha256':s['sha256'],'duration':round(seconds,4),'word_times':aligned,'probabilities':prob,'matched':sum(t is not None for t in aligned),'expected':len(expected),'engine':'faster-whisper/base/int8','method':'Whisper cross-attention DTW forced alignment; verified supplied transcript','recognized_words':recognized}
    offset+=seconds+.2
   done+=len(group);cache.write_text(json.dumps(results,ensure_ascii=False),encoding='utf8')
   print(json.dumps({'chapter':ch,'finished':len(results),'total':len(data['segments']),'elapsed_seconds':round(time.time()-start),'matched_words':sum(x['matched'] for x in results.values()),'expected_words':sum(x['expected'] for x in results.values())}),flush=True)
  for s in pending:
   if args.limit and done+len(batch)>=args.limit:break
   sound=decode_audio(str(folder/s['filename']),sampling_rate=16000);secs=len(sound)/16000+.2
   if secs>29.5:
    if batch:process(batch);batch=[];duration=0
    # Long source clips require ASR over all windows, not truncation to 30 seconds.
    raw,_=model.transcribe(sound,language='en',word_timestamps=True,beam_size=1,condition_on_previous_text=False,vad_filter=False)
    recognized=[];times=[]
    for segment in raw:
     for w in segment.words or []:
      for token in norm(w.word):recognized.append(token);times.append([round(w.start,3),round(w.end,3)])
    expected=norm(s['text']);aligned=[None]*len(expected)
    for a,b,n in SequenceMatcher(None,expected,recognized,autojunk=False).get_matching_blocks():
     for k in range(n):
      if times[b+k][1]>times[b+k][0]:aligned[a+k]=times[b+k]
    results[s['filename']]={'sha256':s['sha256'],'duration':len(sound)/16000,'word_times':aligned,'matched':sum(t is not None for t in aligned),'expected':len(expected),'engine':'faster-whisper/base/int8','method':'Whisper ASR word_timestamps, full long source clip','recognized_words':recognized,'review_required':'Unexpected source length for supplied transcript; kept intact.'}
    done+=1;cache.write_text(json.dumps(results,ensure_ascii=False),encoding='utf8');continue
   if duration+secs>28 and batch:process(batch);batch=[];duration=0
   batch.append((s,sound));duration+=secs
  if batch:process(batch)
  if args.limit and done>=args.limit:return
if __name__=='__main__':main()
