"""Generate a new book and exercise vocabulary, progress, resume and characters."""
import argparse,functools,http.server,json,subprocess,sys,tempfile,threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--browser-path',required=True);p.add_argument('--report',type=Path);a=p.parse_args()
 with tempfile.TemporaryDirectory() as tmp:
  folder=Path(tmp);(folder/'sheet.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="green"/></svg>','utf8')
  book=dict(book_id='feature-smoke',title='Feature smoke',chapters=[dict(number=n,paragraphs=[dict(sentences=['A gentle tone. '*8]) for _ in range(30)]) for n in [1,11,21]],vocabulary=[dict(term='gentle',meaning='부드러운',sentenceMeaning='부드러운 소리.')],characters=[dict(name='Example',description='Original fictional character.',visual_notes='Approved green reference.',sheets=['sheet.svg'])])
  (folder/'book.json').write_text(json.dumps(book),'utf8')
  subprocess.run([sys.executable,str(ROOT/'assets/reader-pipeline/production/build_reading_html.py'),'--input',str(folder/'book.json'),'--output',str(folder/'site')],check=True)
  class Handler(http.server.SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(folder/'site')));threading.Thread(target=server.serve_forever,daemon=True).start()
  try:
   with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=a.browser_path);page=browser.new_page(viewport={'width':1000,'height':800});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    for v in [1,2,3]:
     page.goto(f'http://127.0.0.1:{server.server_port}/volume-{v}/');button=page.locator('.vocab-word').first;button.click();page.wait_for_selector('.vocab-slide');assert page.locator('.vocab-meaning').inner_text()=='부드러운'
     assert page.locator('.vocab-context').inner_text()=='부드러운 소리.'
     page.locator('.vocab-close').click();assert page.locator('.vocab-panel').count()==0;assert button.get_attribute('aria-expanded')=='false'
     button.click();page.keyboard.press('Escape');assert page.locator('.vocab-panel').count()==0
     page.locator('.story-text').nth(15).scroll_into_view_if_needed();page.wait_for_function("parseFloat(document.getElementById('reading-progress').style.width)>0")
     stored=page.evaluate("localStorage.getItem('reader-position:'+document.documentElement.dataset.storyId)");assert stored
     page.reload();page.locator('#resume-reading').click();assert page.evaluate("scrollY>0")
     assert page.locator('a[href="../characters/"]').count()==1
    page.goto(f'http://127.0.0.1:{server.server_port}/characters/');assert page.locator('section img').count()==1;assert 'Approved green reference.' in page.inner_text('body')
    assert not errors,errors;browser.close()
  finally:server.shutdown();server.server_close()
 report=dict(status='PASS',fresh_generated_volumes=3,vocab_slide_close_escape=True,context_meaning=True,progress=True,paragraph_position_resume=True,character_page_and_links=True,actual_book_assets_included=False)
 if a.report:a.report.write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
