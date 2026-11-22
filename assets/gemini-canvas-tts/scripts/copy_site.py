"""One renderer for Canvas HTML and its byte-verified code-copy website."""
from sentence_contract import validate_sentence
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def extract_episode(page):
    marker = 'const originalEpisode = '
    offset = page.index(marker) + len(marker)
    episode, end = json.JSONDecoder().raw_decode(page[offset:])
    if not page[offset+end:].lstrip().startswith(';'):
        raise ValueError('Invalid episode boundary')
    return episode

def render_episode(episode, stem, title):
    if not re.fullmatch(r'[A-Za-z0-9_-]+', stem):
        raise ValueError('Unsafe filename stem')
    if episode.get('execution_mode') != 'canvas-host':
        raise ValueError('Canvas host only')
    for scene in episode['scenes']:
        for segment in scene['segments']:validate_sentence(segment)
    template = (ROOT/'assets/canvas-template.html').read_text('utf8')
    encoded = json.dumps(episode, ensure_ascii=False).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    values = {'__EPISODE_JSON__': encoded, '__FILE_STEM__': stem, '__TITLE_HTML__': html.escape(title)}
    # One substitution pass: original text containing token-like strings stays intact.
    page = re.sub('|'.join(map(re.escape, values)), lambda m: values[m[0]], template)
    assert extract_episode(page) == episode
    return page

def build_copy_site(chapters, output, title='TTS HTML 코드 복사'):
    output = Path(output); directory = output/'chapters'; directory.mkdir(parents=True, exist_ok=True)
    entries = []
    for source in sorted(map(Path, chapters)):
        data = source.read_bytes(); page = data.decode('utf-8')
        episode = extract_episode(page)
        stem = source.name.removesuffix('_GEMINI_CANVAS_TTS.html')
        match = re.search(r'<title>(.*?)</title>', page, re.S)
        if not match or render_episode(episode, stem, html.unescape(match[1])) != page:
            raise ValueError(f'{source.name}: canonical renderer mismatch; regenerate first')
        (directory/source.name).write_bytes(data)
        entries.append(dict(chapter=episode['chapter'], title=episode['title'], file='chapters/'+source.name,
                            bytes=len(data), sha256=sha(data), segments=sum(len(s['segments']) for s in episode['scenes'])))
    if not entries or len({e['chapter'] for e in entries}) != len(entries):
        raise ValueError('Missing or duplicate chapters')
    entries.sort(key=lambda e:e['chapter'])
    manifest = dict(schema='canvas-code-copy-1', title=title,
                    template_sha256=sha((ROOT/'assets/canvas-template.html').read_bytes()), chapters=entries)
    (output/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n', 'utf8')
    portal = (ROOT/'assets/code-copy-template.html').read_text('utf8')
    (output/'index.html').write_text(portal, 'utf8')
    (output/'.gitattributes').write_bytes(b'* -text\n')
    return manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--chapters', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--title', default='TTS HTML 코드 복사')
    a=p.parse_args(); result=build_copy_site(a.chapters.glob('*_GEMINI_CANVAS_TTS.html'), a.out, a.title)
    print(f"Code-copy site: {len(result['chapters'])} verified chapters")

if __name__ == '__main__': main()
