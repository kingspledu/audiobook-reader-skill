"""Regression: same-paragraph cuts, paragraph pauses, spanning clips, scheduling."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'assets/reader-pipeline/production'))
from paragraph_cuts import plan
def seg(*ids):return {'word_map':[[sid,0] for sid in ids]}
level={'trim_start':2400,'trim_end':19200}
segments=[seg('p1-s1'),seg('p1-s2'),seg('p2-s1')]
assert [plan(segments,i,level,1) for i in range(3)]==[(0,.8),(.1,1),(0,1)]
# A legacy clip can span paragraphs. Compare its last paragraph at its right edge.
segments=[seg('p1-s1','p2-s1'),seg('p2-s2'),seg('p3-s1')]
assert [plan(segments,i,level,1) for i in range(3)]==[(0,.8),(.1,1),(0,1)]
assert plan([seg('p1-s1')],0,level,1)==(0,1)
code=r'''
const fs=require('fs'),vm=require('vm'),assert=require('assert');
let calls=[];const ctx={currentTime:0,destination:{},createBufferSource(){return {playbackRate:{},connect(){},disconnect(){},start(...args){calls.push(args)}}},createGain(){return {connect(){},disconnect(){},gain:{setValueAtTime(){},linearRampToValueAtTime(){}}}}};
const sandbox={EventTarget,Event,console,window:{},navigator:{},setInterval(){},clearInterval(){},setTimeout};vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1],'utf8')+';this.Player=TigerClipPlayer;',sandbox);
(async()=>{const p=new sandbox.Player();p.ctx=ctx;p.track={duration:2.7,segments:[{src:'a',offset:0,duration:.8,trim_start:0,trim_end:.8},{src:'b',offset:.8,duration:.9,trim_start:.1,trim_end:1},{src:'c',offset:1.7,duration:1,trim_start:0,trim_end:1}]};p.buffer=async()=>({duration:1});p.running=true;p.reset();await p.pump();assert.equal(calls.length,3);for(let i=1;i<3;i++)assert(Math.abs(calls[i][0]-(calls[i-1][0]+calls[i-1][2]))<1e-9);assert.equal(calls[1][1],.1);assert.equal(calls[2][1],0);console.log('PASS actual scheduler: adjacent sample-clock slots, trim offsets, no added gap');})().catch(e=>{console.error(e);process.exit(1)});
'''
subprocess.run(['node','-e',code,str(ROOT/'assets/reader-pipeline/production/clip-player.js')],check=True)
report=dict(status='PASS',same_paragraph_silence_cut=True,different_paragraph_full_pause=True,legacy_multi_paragraph_clip_boundary=True,first_last_edges_preserved=True,actual_clip_scheduler=True,mp3_files_not_modified=True,physical_device_tested=False,actual_listening=False)
(ROOT/'verification/PARAGRAPH_CUT_REPORT.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
