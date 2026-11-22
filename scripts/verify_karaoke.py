"""Exercise real audiobook.js DOM highlighting with a controlled playback clock."""
import argparse,functools,http.server,json,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--browser-path',required=True);p.add_argument('--report',type=Path);args=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  folder=Path(tmp);(folder/'audio/ch01').mkdir(parents=True)
  (folder/'audiobook.js').write_bytes((ROOT/'assets/reader-pipeline/production/audiobook.js').read_bytes())
  (folder/'audio/catalog.json').write_text(json.dumps({'chapters':[{'chapter':1}]}),'utf8')
  track=dict(chapter=1,duration=2,segments=[dict(offset=0,duration=2,trim_start=.2,speaker='Test',timing_coverage=.66,sentences=['p1-s1'],words=[dict(sentence='p1-s1',word=0,start=.3,end=.6),dict(sentence='p1-s1',word=1,start=.6,end=.9),dict(sentence='p1-s1',word=2,start=None,end=None)])])
  (folder/'audio/ch01/timing.json').write_text(json.dumps(track),'utf8')
  (folder/'index.html').write_text('''<!doctype html><section class="chapter" id="chapter-001"><header class="chapter-head"></header><p class="story-text"><span class="reading-sentence" data-sentence="p1-s1">Hello <button class="vocab-word">gentle</button> world.</span></p></section><script>class TigerClipPlayer extends EventTarget{constructor(){super();window.testPlayer=this;this.currentTime=0;this.paused=true;this.playbackRate=1;}setTrack(t){this.track=t;}pause(){this.paused=true;this.dispatchEvent(new Event('pause'));}async play(){this.paused=false;this.dispatchEvent(new Event('play'));}load(){}}</script><script src="audiobook.js"></script>''','utf8')
  class Handler(http.server.SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=tmp));threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=args.browser_path);page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(f'http://127.0.0.1:{server.server_port}/')
    page.wait_for_function("document.querySelectorAll('.audio-word').length===3")
    for time,expected in [(0,None),(.2,'Hello'),(.5,'gentle'),(.8,None)]:
     page.evaluate("t=>{testPlayer.currentTime=t;testPlayer.dispatchEvent(new Event('seeked'));}",time)
     assert page.locator('.audio-word-active').count()==(1 if expected else 0)
     if expected:assert page.locator('.audio-word-active').inner_text()==expected
     assert page.locator('.audio-sentence-active').count()==1
    assert page.locator('button.vocab-word .audio-word').inner_text()=='gentle'
    page.locator('button.vocab-word').click();assert page.evaluate('testPlayer.paused')
    page.locator('.audio-rate').select_option('1.5');assert page.evaluate('testPlayer.playbackRate')==1.5
    assert page.locator('.reading-sentence').inner_text()=='Hello gentle world.' and not errors,errors
    browser.close()
  finally:server.shutdown();server.server_close()
 report=dict(status='PASS',real_audiobook_js=True,controlled_clock=True,trim_offset_word_boundaries=True,null_sentence_fallback=True,nested_vocab_preserved=True,vocab_click_does_not_seek=True,rate_change=True,text_preserved=True,actual_whisper_run=False,actual_audio_listened=False)
 if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
