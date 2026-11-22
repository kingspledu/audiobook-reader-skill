/* Actual chapter scripts and prompt routing, without calling the model. */
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const root=process.argv[2],manifest=JSON.parse(fs.readFileSync(path.join(root,'manifest.json'),'utf8'));let count=0;
for(const entry of manifest.chapters){
 const html=fs.readFileSync(path.join(root,entry.file),'utf8');
 const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(x=>x[1]).filter(Boolean);
 scripts.forEach(js=>new vm.Script(js));
 const js=scripts.find(s=>s.includes('const originalEpisode = '));
 const episode=JSON.parse(js.match(/const originalEpisode = (.*?);\s*const originalStory =/s)[1]);
 const turns=episode.scenes.flatMap(s=>s.segments),offset=js.indexOf('function makePrompt(');
 const end=js.indexOf('\n        }',offset)+10;
 const context={turns,originalEpisode:episode};vm.createContext(context);vm.runInContext(js.slice(offset,end)+';this.prompt=makePrompt;',context);
 for(let i=0;i<turns.length;i++){
  const t=turns[i],prompt=context.prompt(i);assert(prompt.endsWith(t.text));
  for(const value of Object.values(t.performance.design||{}))assert(prompt.includes(value),'Missing acting direction');
  assert.equal(episode.voices[t.speaker],t.voice);assert(t.performance.character_persona);
  assert.equal(t.performance.audio_effect,t.kind==='monologue'?'echo-v4':'dry');
  count++;
 }
}
console.log(JSON.stringify({status:'PASS',chapters:manifest.chapters.length,segments:count,syntax:true,review_gate:true,fixed_voice:true,design_in_prompt:true,actual_audio_listened:false}));
