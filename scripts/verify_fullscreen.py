"""Browser regression of the bundled real fullscreen module, no model calls."""
import argparse,functools,http.server,json,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--browser-path',required=True);parser.add_argument('--report',type=Path);args=parser.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  folder=Path(tmp)
  for ext in ['js','css']:(folder/f'landscape-reader.{ext}').write_bytes((ROOT/f'assets/reader-pipeline/production/landscape-reader.{ext}').read_bytes())
  (folder/'index.html').write_text('''<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="landscape-reader.css"><div id="floating-reader"><details id="chapter-menu"><summary>목차</summary></details><div class="reading-tools"><input id="font-size" type="range" min="14" max="50" value="19"><output id="font-value"></output></div></div><button id="install-app">설치</button><dialog id="help">설치 안내</dialog><article><section class="chapter"><p class="story-text"><span class="reading-sentence" data-sentence="s1">Sample.</span></p></section></article><script>document.getElementById('install-app').onclick=()=>document.getElementById('help').showModal();</script><script src="landscape-reader.js"></script>''','utf8')
  class Handler(http.server.SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=tmp));threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=args.browser_path)
    page=browser.new_page(viewport={'width':1024,'height':768});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(f'http://127.0.0.1:{server.server_port}/');button=page.locator('#landscape-fullscreen');assert button.is_visible()
    page.locator('#reader-layout-toggle').click();assert page.evaluate("document.documentElement.classList.contains('reader-landscape')")
    button.click();page.wait_for_function("!!document.fullscreenElement&&document.getElementById('landscape-fullscreen').getAttribute('aria-pressed')==='true'")
    button.click();page.wait_for_function("!document.fullscreenElement&&document.getElementById('landscape-fullscreen').getAttribute('aria-pressed')==='false'")
    button.click();page.wait_for_function("!!document.fullscreenElement&&document.getElementById('landscape-fullscreen').getAttribute('aria-pressed')==='true'");page.evaluate('document.exitFullscreen()');page.wait_for_function("!document.fullscreenElement&&document.getElementById('landscape-fullscreen').textContent==='전체모드'")
    assert page.evaluate("document.documentElement.classList.contains('reader-landscape')")
    page.locator('#reader-layout-toggle').click();assert button.is_visible()
    page.evaluate("Object.defineProperty(document.documentElement,'requestFullscreen',{configurable:true,value:async()=>{throw Error('denied')}})")
    button.click();page.wait_for_function("document.getElementById('help').open");page.evaluate("document.getElementById('help').close()")
    page.evaluate("Object.defineProperty(document.documentElement,'requestFullscreen',{configurable:true,value:undefined})")
    button.click();page.wait_for_function("document.getElementById('help').open");assert not errors,errors
    browser.close()
  finally:server.shutdown();server.server_close()
 report=dict(status='PASS',real_bundled_module=True,enter_exit=True,browser_exit_state=True,split_state_preserved=True,default_layout_button_visible=True,denied_fallback=True,unsupported_fallback=True,physical_device_tested=False,actual_audio_listened=False)
 if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
