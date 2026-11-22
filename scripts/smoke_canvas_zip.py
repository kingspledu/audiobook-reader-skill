"""Fresh public-package reproduction, format parity and real-browser ZIP smoke.
Only the model response is mocked. Browser PCM/WAV/DSP/MP3/ZIP are real.
"""
import base64,copy,functools,hashlib,html,http.server,io,json,math,re,struct,subprocess,sys,threading,zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--out',type=Path,required=True,help='New empty test directory outside the skill')
parser.add_argument('--public-site',type=Path,required=True,help='Downloaded code-copy site with manifest.json and chapters/')
parser.add_argument('--encoder',type=Path,required=True,help='Local lamejs 1.2.1 lame.min.js')
parser.add_argument('--browser-path',required=True,help='Installed Chrome or Chromium executable')
args=parser.parse_args()
SKILL=Path(__file__).resolve().parents[1]
BASE=args.out.resolve();WORK=BASE/'fresh-workspace';CHROME=args.browser_path
if BASE==SKILL or SKILL in BASE.parents:raise SystemExit('Choose output outside the skill')
if BASE.exists() and any(BASE.iterdir()):raise SystemExit('Output must be empty')
BASE.mkdir(parents=True,exist_ok=True)
PUBLIC=args.public_site.resolve();ENCODER=args.encoder.resolve()

def command(*args,cwd=None):
 p=subprocess.run(list(map(str,args)),cwd=cwd,text=True,encoding='utf8',capture_output=True)
 print(p.stdout,flush=True)
 assert p.returncode==0,p.stderr

def main():
 command(sys.executable,'-X','utf8',SKILL/'scripts/validate_package.py')
 command(sys.executable,'-X','utf8',SKILL/'scripts/init_workspace.py','--out',WORK)
 sys.path.insert(0,str(WORK/'tts/scripts'))
 from build import generate
 from copy_site import extract_episode,render_episode
 from verify_copy_site import verify
 report={'source':'installed skill, supplied public-site snapshot, fresh workspace','actual_canvas_generation_tested':False,'actual_audio_listened':False}
 report['public_copy_browser']=verify(PUBLIC,CHROME)
 template=(WORK/'tts/assets/canvas-template.html').read_bytes()
 manifest=json.loads((PUBLIC/'manifest.json').read_text('utf8'))
 assert hashlib.sha256(template).hexdigest()==manifest['template_sha256']
 for entry in manifest['chapters']:
  data=(PUBLIC/entry['file']).read_bytes();page=data.decode('utf8');episode=extract_episode(page)
  title=html.unescape(re.search(r'<title>(.*?)</title>',page,re.S)[1])
  stem=Path(entry['file']).name.removesuffix('_GEMINI_CANVAS_TTS.html')
  assert render_episode(episode,stem,title).encode('utf8')==data
 report['public_html_exact_rerender']=True
 report['public_chapters']=len(manifest['chapters'])
 book=json.loads((WORK/'tts/assets/example-book.json').read_text('utf8'))
 book['prefix']='SMOKE';book['title']='Fresh smoke <UTF-8 한글> & test'
 book['chapters'].append(copy.deepcopy(book['chapters'][0]));book['chapters'][1]['number']=2
 book['chapters'][1]['segments'][0]['text']='Escaping stays intact: </script> 한글 & __FILE_STEM__.'
 generate(book,WORK/'generated')
 command('node',WORK/'tts/scripts/verify.cjs',WORK/'generated')
 command(sys.executable,'-X','utf8',WORK/'tts/scripts/self_test.py')
 command('node',WORK/'tts/scripts/verify_site_episodes.cjs',PUBLIC)
 report['fresh_generated_copy_browser']=verify(WORK/'generated/code-copy',CHROME)
 report['fresh_workspace_2_chapters_6_segments']=True
 class Handler(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(WORK/'generated')))
 threading.Thread(target=server.serve_forever,daemon=True).start()
 url=f'http://127.0.0.1:{server.server_port}/SMOKE_C01_V01_GEMINI_CANVAS_TTS.html'
 pcm=struct.pack('<'+'h'*4800,*[int(8000*math.sin(i*2*math.pi*440/24000)) for i in range(4800)])
 response={'candidates':[{'content':{'parts':[{'inlineData':{'mimeType':'audio/L16;codec=pcm;rate=24000','data':base64.b64encode(pcm).decode()}}]}}]}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,executable_path=CHROME)
   scenarios=[]
   for scenario in ['retry_then_complete','permanent_failure_partial']:
    context=browser.new_context(accept_downloads=True)
    page=context.new_page();errors=[];calls=[];downloads=[];attempts={}
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('download',lambda d:downloads.append(d))
    def route_request(route):
     address=route.request.url
     if 'generativelanguage.googleapis.com' in address:
      payload=route.request.post_data_json;prompt=payload['contents'][0]['parts'][0]['text']
      matched=[(i,s) for i,s in enumerate(book['chapters'][0]['segments']) if prompt.endswith(s['text'])]
      assert len(matched)==1
      i,segment=matched[0];calls.append(i);attempts[i]=attempts.get(i,0)+1
      for value in segment['performance']['design'].values():assert value in prompt
      voice=payload['generationConfig']['speechConfig']['voiceConfig']['prebuiltVoiceConfig']['voiceName']
      assert voice==book['cast'][segment['cast_id']]['voice']
      assert 'key=' in address and not address.split('key=',1)[1]
      failed=(i==1 and (scenario=='permanent_failure_partial' or attempts[i]==1))
      route.fulfill(status=200,content_type='application/json',body=json.dumps({'candidates':[]} if failed else response))
     elif 'lame.min.js' in address:
      route.fulfill(status=200,content_type='text/javascript',body=ENCODER.read_bytes())
     elif address.startswith('http://127.0.0.1:'):route.continue_()
     else:route.fulfill(status=200,content_type='text/javascript' if 'tailwind' in address else 'text/css',body='')
    page.route('**/*',route_request)
    page.goto(url);page.wait_for_function("document.querySelectorAll('.acting-guide').length===3")
    assert page.get_by_role('button',name='전체 생성 후 MP3 ZIP 다운로드',exact=True).is_visible()
    page.locator('.acting-guide').first.click()
    assert page.locator('.acting-guide').first.get_attribute('open') is not None
    with page.expect_download(timeout=90000) as download_info:
     page.locator('#generatePackMp3Zip').click()
    download=download_info.value
    save=BASE/(scenario+'_'+download.suggested_filename);download.save_as(save)
    page.wait_for_function("!document.getElementById('generatePackMp3Zip').disabled")
    with zipfile.ZipFile(save) as z:
     assert z.testzip() is None
     index=json.loads(z.read('SMOKE_C01_V01_MP3_INDEX.json'))
     expected_count=3 if scenario=='retry_then_complete' else 2
     assert len(index['segments'])==expected_count
     assert index['complete']==(expected_count==3)
     assert len(index['missing'])==3-expected_count
     for segment in index['segments']:
      data=z.read(segment['filename']);assert len(data)>100
      # Real lamejs MP3 frame and valid textual manifest, not fake MP3 payloads.
      assert data[0]==255 and data[1]&224==224
      assert segment['text_sha256']==hashlib.sha256(segment['text'].encode('utf8')).hexdigest()
    assert attempts[1]==(2 if scenario=='retry_then_complete' else 3),attempts
    if scenario=='retry_then_complete':
     before=len(calls)
     with page.expect_download(timeout=30000):page.locator('#generatePackMp3Zip').click()
     page.wait_for_function("!document.getElementById('generatePackMp3Zip').disabled")
     assert len(calls)==before,'Cached segments regenerated'
    assert not errors,errors
    scenarios.append(dict(scenario=scenario,status='PASS',api_attempts=attempts,mp3_files=expected_count,
                          actual_browser_pcm_wav_dsp_mp3_zip=True,download_event_received=True,
                          button_reenabled=True,all_design_fields_in_request=True))
    context.close()
   browser.close();report['zip_smoke']=scenarios
 finally:server.shutdown();server.server_close()
 report['status']='PASS'
 (BASE/'SMOKE_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
