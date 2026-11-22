"""Verify exact render parity and real browser clipboard, failure and race handling.

Requires Playwright Python and installed Chromium (or --browser-path).
No paid calls, no speech synthesis, no actual listening.
"""
import argparse, functools, hashlib, http.server, json, threading
from pathlib import Path
from copy_site import extract_episode, render_episode
import html, re

def verify(root, browser_path=None):
    root=Path(root).resolve(); manifest=json.loads((root/'manifest.json').read_text('utf8'))
    expected={}
    for entry in manifest['chapters']:
        data=(root/entry['file']).read_bytes();page=data.decode('utf8')
        assert len(data)==entry['bytes'] and hashlib.sha256(data).hexdigest()==entry['sha256']
        title=html.unescape(re.search(r'<title>(.*?)</title>',page,re.S)[1])
        stem=Path(entry['file']).name.removesuffix('_GEMINI_CANVAS_TTS.html')
        assert render_episode(extract_episode(page),stem,title).encode('utf8')==data
        expected[entry['chapter']]=page
    class Handler(http.server.SimpleHTTPRequestHandler):
        def log_message(self,*args): pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(root)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,**({'executable_path':browser_path} if browser_path else {}))
            context=browser.new_context(permissions=['clipboard-read','clipboard-write'])
            page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            url=f'http://127.0.0.1:{server.server_port}/';page.goto(url)
            page.wait_for_function("document.querySelectorAll('#chapters button').length>0")
            for entry in manifest['chapters']:
                page.get_by_role('button',name=str(entry['chapter'])+'장 코드',exact=True).click()
                page.wait_for_function("!document.getElementById('copy').disabled")
                page.locator('#copy').click()
                page.wait_for_function("document.getElementById('status').textContent.includes('복사 완료')")
                copied=page.evaluate('navigator.clipboard.readText()')
                # Windows clipboard text uses CRLF; it is not a change to HTML content.
                assert copied.replace('\r\n','\n')==expected[entry['chapter']],(entry['chapter'],len(copied),len(expected[entry['chapter']]))
            # Deliberately unavailable HTML: never copy error page or previous chapter.
            page.route('**/chapters/**',lambda route:route.fulfill(status=404,body='missing'))
            page.locator('#chapters button').first.click();page.wait_for_function("document.getElementById('status').textContent.includes('HTTP 404')")
            assert page.locator('#copy').is_disabled() and page.locator('#code').input_value()==''
            page.unroute('**/chapters/**')
            # Correct status/size but wrong bytes: hash must reject.
            first=manifest['chapters'][0]; original=expected[first['chapter']].encode('utf8');corrupt=b'X'+original[1:]
            page.route('**/chapters/**',lambda route:route.fulfill(status=200,body=corrupt))
            page.locator('#chapters button').first.click();page.wait_for_function("document.getElementById('status').textContent.includes('무결성 검사 실패')")
            assert page.locator('#copy').is_disabled()
            page.unroute('**/chapters/**')
            # Rapid switching: only last selection can become copyable.
            if len(manifest['chapters'])>1:
                page.evaluate("document.querySelectorAll('#chapters button')[0].click();document.querySelectorAll('#chapters button')[1].click()")
                page.wait_for_function("!document.getElementById('copy').disabled")
                assert page.locator('#code').input_value()==expected[manifest['chapters'][1]['chapter']]
            # Clipboard denied: manual selection still contains exact HTML.
            page.evaluate("Object.defineProperty(navigator,'clipboard',{value:{writeText:async()=>{throw Error('denied')}}});document.execCommand=()=>false")
            page.locator('#copy').click();page.wait_for_function("document.getElementById('status').textContent.includes('코드 전체가 선택')")
            assert page.evaluate("document.getElementById('code').selectionEnd-document.getElementById('code').selectionStart")==page.evaluate("document.getElementById('code').value.length")
            assert not errors,errors
            browser.close()
    finally: server.shutdown();server.server_close()
    return dict(status='PASS',chapters=len(expected),render_bytes_exact=True,clipboard_content_exact_after_os_newline_normalization=True,http_404_rejected=True,hash_mismatch_rejected=True,
                rapid_selection_tested=True,clipboard_denied_fallback=True,actual_canvas_generation_tested=False,actual_audio_listened=False)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('site',type=Path);a.add_argument('--browser-path');a.add_argument('--report',type=Path);o=a.parse_args()
    report=verify(o.site,o.browser_path)
    if o.report:o.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps(report))
