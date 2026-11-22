# 삽화·오디오북 읽기 웹사이트 제작 템플릿과 재현 매뉴얼

작성일: 2026-11-22 · 템플릿 규격 1.2 · 입력 변경 감지·단일 실행·새 가상환경 검증판

### 1.2 실행 진입점

최초 읽기 HTML 생성은 `python production/build_reading_html.py --input book.json --output story-reader`로 수행한다. 장별 TTS ZIP 준비 후 오디오 제작은 **`python production/run_pipeline.py` 한 명령**으로 실행한다. 입력과 모델이 바뀌지 않은 경우 검증한 정렬 캐시를 그대로 재사용한다.

새 가상환경에서는 `docs/requirements-audiobook-full-lock.txt`를 사용한다. 현재 Windows/Python 3.12 환경에서 기본 의존성의 전이 관계까지 27개 패키지를 고정한 파일이다. 운영체제와 모델 다운로드까지 포함하는 컨테이너 이미지나 wheel 해시 잠금은 아니며, 모델은 따로 준비한다.

> **제작 순서 정정:** 읽기 HTML 생성이 가장 먼저다. 이전 1.0은 기존 읽기 HTML을 전제로 해 신규 제작 단계가 빠져 있었다. 이 판에는 기본 HTML·CSS·JS 전체 소스, 원문 JSON 예제, `build_reading_html.py`, 빈 폴더 검증 스크립트를 추가했다. 기존 오디오 파일을 연결하는 도구만으로 최초 읽기 HTML까지 생성되는 것으로 설명하지 않는다.

### 처음부터 실행하는 올바른 순서

```text
원문·문장 분할 JSON 준비
→ 기본 읽기 HTML 생성 (build_reading_html.py)
→ 본문·문단·문장 ID·삽화 위치 검증
→ 장별 TTS MP3와 대본 색인 준비
→ 원문-음성 매핑
→ 음량 기준 생성·보정
→ Whisper 타이밍
→ 오디오 포함 HTML 갱신
→ 가로모드 HTML 생성
→ 최종 파일 해시·오프라인 목록 생성
→ 브라우저·실기기 검증
→ 배포
```

`install_offline_v2.py`의 현재 manifest는 권별 읽기 자료를 대상으로 하며 별도 `landscape-test/`를 포함하지 않는다. 가로 테스트 페이지까지 완전 오프라인 대상으로 삼으려면 해당 HTML·chapters.json·CSS·JS·manifest와 공유 오디오 경로를 추가해야 한다.

이 문서는 When You Trap a Tiger 읽기 사이트에서 사용한 제작 절차와 가로모드 테스트 방식을 다른 책에 재현하기 위한 매뉴얼이다. **가로모드의 UI 규격을 템플릿으로 확정**한다. 기존 3권 읽기 사이트를 전부 가로모드로 전환했다는 뜻은 아니다. 현재 별도 `landscape-test/` 페이지에서 동작한다.

실행 소스는 이 문서 옆 `audiobook-template-source.zip`에 보관한다. ZIP의 `production/`을 프로젝트 루트 아래에 풀어 사용한다. 이 ZIP에는 책 원문, 삽화, MP3, API 키가 포함되지 않는다. 책 데이터는 별도로 준비해야 한다. 아래의 스크립트는 현재 프로젝트 구조에 맞춘 구현으로, 다른 책에서는 경로·권 구분·언어·장 수를 먼저 변경한다. 범용 패키지처럼 책 이름만 입력하면 완성되는 도구는 아니다.

## 1. 최종 결과와 고정 원칙

| 항목 | 템플릿 규격 |
|---|---|
| 본문 | 원문 전체 보존, 문장 ID와 원본 문단 ID 유지 |
| 음성 | 구간별 MP3 유지. 서버에서 장별 MP3로 합쳐 올리지 않음 |
| 음량 | 작품 전체에서 같은 화자에게 같은 기본 보정값 적용 |
| 단어 강조 | Whisper로 얻은 시간과 실제 오디오 재생 위치를 연결 |
| 문단 안 | 불필요한 경계 무음만 브라우저에서 건너뜀 |
| 문단 사이 | 기존 앞뒤 쉼 유지 |
| 삽화 | 현재 문장에 해당하는 장면 표시. 임의 시간마다 교체하지 않음 |
| 가로모드 | 왼쪽 삽화 고정, 오른쪽 본문 독립 스크롤 |
| 장면 전환 | 다음 삽화의 본문에 도달하면 위아래 슬라이드 |
| 설정 | 상단 얇은 바에서 목차·글자 설정을 눌러 펼침 |
| 재생바 | 하단 한 줄 플로팅, 화면 안전 영역 반영 |
| 오프라인 | 사용자가 선택해 다운로드, 파일별 SHA-256 검증 |
| 삭제 | 해당 책의 저장 자료만 삭제. 다른 사이트 캐시 보존 |
| 공개 배포 | 실제 배포 SHA와 공개 파일 응답 확인 후 완료 보고 |

## 2. 검증된 범위와 한계

- 현재 자료: 제공된 1~29장, 개별 MP3 4,763개. **29장은 원문 제공 범위상 중간까지**다. 소설 전체가 완결됐다고 표기하지 않는다.
- 전체 대본 단어 38,739개 중 36,364개에 시간 연결이 생성됐다. 약 93.87%이며, 나머지는 문장 강조로 대체한다. 이것은 전체 실제 청취 검수 통과율이 아니다.
- Whisper 기본 경로는 **대본을 이용한 강제 정렬**이다. 모든 파일의 내용을 독립적으로 전사해 원문과 재검증한 것은 아니다.
- 브라우저 자동화로 재생, 문장 강조, 화면 배치, 오프라인 재생, 부분 요청, 삭제 범위를 검사했다. 휴대폰 잠금 상태의 30분 연속 재생과 전체 사람 청취는 미완료다.
- HTML 기본 오디오 요소의 `media` 모드는 시험 선택지다. 정밀 Web Audio 모드가 현재 기본이다. 두 모드 모두 모든 기기의 잠금 상태 재생을 보장하지 않는다.
- 16장 order 273 원본은 대본 `Right,`에 비해 약 101초이며 발화가 인식되지 않았다. 확인 필요 표시를 유지한다. 음량 보정으로 원본 생성 오류가 고쳐지지는 않는다.

## 3. 디렉터리 구조

```text
PROJECT_ROOT/
  public-tiger/tts zip/                 # 입력 ZIP; 현재 구현의 고정 경로
  production/                          # 실행 소스; 공개 루트 밖
    prepare_audiobook.py
    measure_new_clips.py
    normalize_clips.py
    whisper_force_align.py
    publish_audiobook.py
    install_offline_v2.py
    build_landscape_test.py
    clip-player.js                     # 정밀 Web Audio 엔진
    media-player.js                    # 기본 audio 요소 엔진
    audiobook.js / audiobook.css        # 기존 읽기 페이지 UI
    offline-v2.js                      # 저장·삭제 UI
    landscape-test/
      index.html / test.css / test.js   # 확정한 가로 UI 원본
    audiobook/                         # 비공개 작업·검증 산출물
      ch01.json
      aligned-ch01.json
      clip-levels.json
      loudness-analysis.json
      normalization-report.json
  story-reader/                        # GitHub Pages 공개 저장소
    volume-1/                          # 현재 1~10장
    volume-2/                          # 현재 11~20장
    volume-3/                          # 현재 21~29장
      index.html / app.js / style.css
      audio/catalog.json
      audio/ch29/timing.json
      audio/ch29/clips/*.mp3            # 공개할 보정 MP3
      assets/*                         # 삽화·아이콘
      sw.js / offline.js
      offline-manifest.json
    landscape-test/
      index.html / test.css / test.js
      chapters.json
      manifest.webmanifest
  docs/AUDIOBOOK_READER_TEMPLATE_KO.md
```

주의: `audio/ch29/원본.mp3`와 `audio/ch29/clips/보정본.mp3`는 역할이 다르다. 원본은 검증과 복구용이다. 배포 목록에는 `clips/` 아래의 보정본만 포함한다. `git add -A`로 입력·임시 파일을 통째로 올리지 않는다.

## 4. 원문과 TTS 입력 규격

### 4.1 읽기 HTML의 문장·문단 ID

```html
<section class="chapter" id="chapter-001">
  <header class="chapter-head"><h3>Chapter 1</h3></header>
  <div class="story-text" id="p0001" data-paragraph="true">
    <span class="reading-sentence" data-sentence="p0001-s1">First sentence. </span>
    <span class="reading-sentence" data-sentence="p0001-s2">Second sentence.</span>
  </div>
</section>
```

ID는 책 안에서 유일해야 한다. 구두점과 띄어쓰기는 원문 그대로 유지한다. 여러 문장으로 나눴다고 원문 문단을 새 문단으로 취급하지 않는다. 삽화 때문에 문단 DOM을 나누면 `p0001--p0001-s2`처럼 원본 ID를 추적할 수 있게 한다. 기존 단어 뜻 버튼은 문장 내부에 있어도 된다. 단어를 감싸는 처리는 텍스트 노드에만 적용하고 버튼 이벤트는 보존한다.

### 4.2 장별 TTS ZIP

```text
WYTT_C01_V05_MP3.zip
  WYTT_C01_V05_0000_C01_P001_LILY.mp3
  WYTT_C01_V05_0001_C01_P002_SAM.mp3
  WYTT_C01_V05_MP3_INDEX.json
  WYTT_C01_V05_MP3_INDEX.csv
```

최소 JSON 예시:

```json
{
  "schema": "mp3-zip-index-1",
  "chapter": 1,
  "complete": true,
  "missing": [],
  "segments": [
    {
      "order": 0,
      "filename": "WYTT_C01_V05_0000_C01_P001_LILY.mp3",
      "speaker": "Lily / first-person narrator",
      "voice": "Leda",
      "kind": "narration",
      "text": "The exact spoken source sentence."
    }
  ]
}
```

`order`는 장 안에서 중복 없이 연속 순서를 나타낸다. 파일명에 화자가 있어도 순서·원문은 반드시 색인으로 확인한다. 파일 하나가 문장 하나일 필요는 없다. 대사와 나레이션이 나뉘어 한 문장에 여러 MP3가 연결될 수도 있다.

새 TTS를 제작하는 경우에도 이 색인이 필요하다. 이 매뉴얼의 오디오 파이프라인은 이미 생성된 MP3를 입력으로 받는다. Gemini Canvas HTML은 별도 `gemini-canvas-tts` 제작 절차에서 생성하며, 이 파이프라인이 API 키 없이 TTS를 새로 만드는 것은 아니다. 여기서 말하는 HTML 생성은 **오디오를 듣는 읽기 사이트 HTML**이다.

## 5. 환경 준비

기준 실행 환경: Windows PowerShell, Python 3.12, Node.js, Git, GitHub CLI. 오디오 처리는 Python의 PyAV와 faster-whisper를 사용한다. 재생은 정적 HTTPS 웹사이트에서 동작한다.

소스 ZIP을 PROJECT_ROOT에 풀면 `production/`과 `docs/`가 생긴다. 공개 사이트 폴더 `story-reader/`와 입력 ZIP 폴더는 별도로 준비한다. 첨부한 `docs/requirements-audiobook-lock.txt`는 현재 환경의 주요 직접 의존성 및 Whisper 엔진 버전을 기록한 스냅샷이다. 전체 전이 의존성과 운영체제를 동결한 파일은 아니므로, 재현용 환경을 만든 다음 아래 `pip freeze` 결과도 추가 보관한다.

```powershell
Set-Location 'C:\PATH\TO\PROJECT_ROOT'
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install beautifulsoup4 numpy av faster-whisper imageio-ffmpeg huggingface-hub
python -m pip freeze > requirements-lock.txt
```

기존 자료를 같은 결과로 재현할 때는 해당 작업의 `requirements-lock.txt`를 보관해 `pip install -r`로 설치한다. 최신 라이브러리로 교체하는 것은 별도의 회귀 시험이 필요하다. 특히 `whisper_force_align.py`는 faster-whisper 내부 정렬 메서드를 사용하므로 버전 변경에 민감하다.

현재 스크립트는 캐시된 `Systran/faster-whisper-base` 모델을 `local_files_only=True`로 로드한다. 첫 실행 전 네트워크가 되는 곳에서 모델을 준비한다.

```powershell
python -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-base')"
```

모델 다운로드 후 음성 처리는 로컬에서 수행된다. API 키는 필요 없다. 원본 음성을 외부 전사 서버로 보내지 않는다.

## 6. 첫 제작: 원문과 MP3 연결

### 6.0. 읽기 HTML을 먼저 생성

기본 템플릿 전체는 소스 ZIP의 아래 네 파일에 들어 있다.

```text
production/reader-template/index.html       # HTML 원본: 문자열 템플릿
production/reader-template/style.css        # 기본 읽기 스타일
production/reader-template/app.js           # 글자·테마·목차·단어 뜻
production/reader-template/book.sample.json # 입력 규격 예제
production/build_reading_html.py            # 실제 HTML 생성기
```

원문은 `book.json`의 `chapters[].paragraphs[].sentences[]`에 문장별로 넣는다. 문장 분할은 편집 단계에서 확정한다. 생성기가 마침표로 원문을 임의 분할하거나 요약하지 않는다. 공백이 필요한 문장 끝에는 원문의 공백을 그대로 포함한다. 문단 ID는 책 전체에서 p0001부터 생성되고 문장 ID는 p0001-s1처럼 부여된다.

```powershell
Copy-Item -LiteralPath production/reader-template/book.sample.json -Destination book.json
# book.json을 실제 원문으로 편집한 다음 실행
python production/build_reading_html.py --input book.json --output story-reader
```

이미지를 넣는 문단 예시:

```json
{
  "sentences": ["First sentence. ", "Second sentence."],
  "image": "images/scene-001.webp",
  "alt": "원문과 일치하는 장면 설명"
}
```

기본 image 경로는 book.json의 폴더 기준이다. `--assets PATH`로 바꿀 수 있다. 생성기는 지정한 폴더 밖으로 벗어나는 경로를 거부하고 그림을 `assets/`에 복사한다. 그림은 해당 문단보다 먼저 삽입한다.

현재 생성기는 기존 배포 도구와 호환되는 **1~29장·3권 프로필**을 사용한다. 장 1~10은 1권, 11~20은 2권, 21~29는 3권이다. 비어 있는 권도 필요한 파일 구조를 만든다. 다른 권수·30장 이상·다른 언어는 전체 도구의 고정 프로필을 함께 수정해야 한다. 생성기는 이미 읽기 HTML이 있는 출력 폴더에 덮어쓰지 않는다. 기존 사이트에 오디오만 추가할 때는 이 최초 생성 단계를 재실행하지 않는다.

이 단계에서 생성되는 파일:

```text
story-reader/index.html, .nojekyll
story-reader/volume-N/index.html, style.css, app.js, pwa.js
story-reader/volume-N/manifest.webmanifest, sw.js
story-reader/volume-N/assets/app-icon-192.png, app-icon-512.png
```

처음 생성되는 sw.js는 초기 설치용 최소 파일이다. 완성된 오프라인 기능은 이후 `install_offline_v2.py`가 생성한다. 이 시점부터 오디오 없이도 본문·목차·글자 크기·테마·단어 뜻을 사용할 수 있다.

`validate_reader_audio.py`는 기존 HTML 보존 여부를 Git HEAD와 비교한다. 신규 프로젝트는 최초 생성 결과를 먼저 기준 커밋으로 남긴다.

```powershell
Set-Location story-reader
git init
git add -- index.html .nojekyll volume-1 volume-2 volume-3
git commit -m "Create source reading HTML before audiobook integration"
Set-Location ..
```

먼저 읽기 사이트의 모든 장 HTML과 `assets/`를 준비한다. 이 템플릿은 기존 본문 HTML에 오디오를 붙인다. 다른 책이라면 다음 고정값을 수정한다.

- `prepare_audiobook.py`: ZIP 입력 경로, 공개 루트, 장→권 매핑, 영문 토큰 규칙.
- `publish_audiobook.py`, `install_offline_v2.py`, `build_landscape_test.py`: 권 수와 폴더명.
- HTML의 장 ID, 원문 문단·문장 ID, 사이트 제목과 아이콘.
- 캐시 prefix와 PWA scope: **새 책마다 고유하게** 설정.
- 테스트 코드의 기본 장과 실행 경로.

```powershell
python production/prepare_audiobook.py
```

이 스크립트는 ZIP 색인을 읽고 `order`로 정렬한다. 원문과 대본을 영문 단어 토큰으로 비교해 각 TTS 단어를 `[sentence_id, word_index]`에 연결한다. 파일 번호만으로 매칭하지 않는다. 원본 바이트의 SHA-256도 기록한다.

합격 조건:

- 모든 `complete`가 true이고 `missing`이 빈 배열.
- `unmapped_words`와 `unmapped_segments`가 0.
- 같은 단어나 문장이 반복되는 부분은 앞뒤 문맥과 장 안 순서까지 점검.
- 대본 단어가 모두 연결됐다는 사실과 본문 전체가 오디오로 덮였다는 사실은 구분한다. `web_word_count`, `spoken_word_count`와 미사용 본문 단어도 따로 대조한다.

개별 `prepare_audiobook.py`만 실행하면 같은 이름의 원본을 덮어쓰지 않는다. 따라서 정규 실행은 `run_pipeline.py`를 사용한다. 이 명령의 `cache_guard.py`가 ZIP 안 실제 MP3 바이트·대본·화자·순서·분석 코드·화자 gain·Whisper 의존성 버전·모델 파일 해시를 비교한다. 바뀐 파일과 해당 장 정렬 결과는 `production/audiobook/cache-backups/시각/`로 옮겨 보존한 뒤 재생성한다. 이웃 발화가 정렬에 영향을 주므로 대본 변경은 해당 장 전체의 정렬을 다시 수행한다. 무관한 장은 재사용한다. 최초 registry 생성 때는 기존 산출물을 검증된 것으로 추정하지 않고 백업 후 재분석하므로 여유 공간과 처리 시간이 필요하다.

## 7. 음량 분석과 화자별 보정

### 7.1 신규 프로젝트 초기화

`measure_new_clips.py`는 기존 `clip-levels.json`을 읽으므로 첫 작업에서는 빈 파일을 먼저 만든다. 아래 명령은 기존 파일을 덮어쓰지 않는다.

```powershell
python -c "from pathlib import Path; p=Path('production/audiobook/clip-levels.json'); p.parent.mkdir(parents=True,exist_ok=True); p.exists() or p.write_text('{}',encoding='utf8')"
python production/measure_new_clips.py
```

분석은 24kHz 모노로 임시 디코딩해 RMS와 앞뒤 무음 경계를 구한다. **최종 MP3의 샘플레이트를 24kHz로 낮춘다는 뜻은 아니다.** 분석 결과의 샘플 위치는 24,000으로 나누어 초로 변환한다.

첫 화자별 기준 파일은 아래 Python 코드를 `production/bootstrap_speaker_levels.py`로 저장해 한 번 실행한다.

```python
from pathlib import Path
from collections import defaultdict
import json
import numpy as np

work = Path(__file__).resolve().parent / 'audiobook'
levels = json.loads((work / 'clip-levels.json').read_text('utf8'))
voices = defaultdict(list)
for chapter in sorted(work.glob('ch??.json')):
    data = json.loads(chapter.read_text('utf8'))
    for segment in data['segments']:
        level = levels[segment['filename']]
        if level['trim_end'] - level['trim_start'] > 24000 * .8:
            voices[segment['speaker']].append(level['rms_db'])
baselines = {name: float(np.median(values)) for name, values in voices.items()}
assert baselines, 'No usable voice samples'
(work / 'loudness-analysis.json').write_text(
    json.dumps({'speaker_rms_baseline': baselines}, indent=2), encoding='utf8')
```

```powershell
python production/bootstrap_speaker_levels.py
python production/normalize_clips.py
```

현재 보정은 **LUFS 정규화가 아니라 화자별 RMS 기준의 고정 감쇠**다. 계획 단계의 `−18 LUFS`와 혼동하지 않는다. 보정 대상은 화자 간 기본 음량 차이이며 문장마다 독립적으로 음량을 같게 만들지 않는다. 고함·독백·감정 강약을 압축하지 않는다.

현재 구현은 가장 조용한 화자 기준과 −20dBFS 중 더 보수적인 값을 목표로 잡고 증폭 없이 감쇠한다. 샘플레이트 유지, 모노, MP3 192kbps로 한 번 재인코딩한다. 기존 `normalization-report.json`의 화자별 gain은 다음 장 추가 때 재사용한다. 새 화자가 들어오면 그 화자의 표본으로 기준을 추가하고 기존 화자 값을 바꾸지 않는다. 알 수 없는 화자를 0dB 처리한 채 완료하지 않는다.

`render_audiobook.py`는 `decode()`와 `bounds()`를 가져오기 위한 기존 의존성이다. **파일 자체를 실행하지 않는다.** 그 스크립트의 장별 병합 기능은 이 템플릿에서 사용하지 않는다.

## 8. Whisper 단어 타이밍

```powershell
python production/whisper_force_align.py
# 특정 장만 시험
python production/whisper_force_align.py --chapter 13 --limit 16
```

현재 경로:

1. 원본 MP3를 16kHz PCM으로 디코딩.
2. 30초 미만 분석 창에 여러 구간을 넣고 경계와 실제 샘플 수 기록.
3. 공급된 대본에 대해 Whisper cross-attention + DTW 정렬.
4. 실제 MP3 구간 안으로 시간을 환산.
5. 단어 일치·시간 유효성·최소 확률 조건을 통과한 값만 저장.
6. 결과를 `aligned-chNN.json`에 캐시해 이어서 처리.

보통 짧은 대사는 강제 정렬이며, 긴 예외 파일은 전체 창을 ASR로 처리한다. `word_times`의 null을 단어 수로 균등 분할해 채우지 않는다. 불확실한 경우 문장 강조만 한다. 단순 길이 비례 타이밍을 Whisper 결과라고 부르지 않는다.

캐시는 파일명으로 재사용되는 부분이 있으므로 원본 또는 대본이 바뀌면 SHA와 분석 버전을 확인하고 해당 캐시를 무효화한다. 보정이 고정 gain만 바꾸면 재생 길이는 유지되지만, 실제로 무음을 파일에서 잘랐다면 기존 단어 시간은 더 이상 그대로 쓸 수 없다.

## 9. 읽기 HTML과 JSON 생성

```powershell
python production/publish_audiobook.py
python production/install_offline_v2.py
```

순서가 중요하다. `publish_audiobook.py`가 오디오 정보를 갱신한 **후** `install_offline_v2.py`가 최종 HTML·스크립트의 해시를 계산해야 한다. 파일이 바뀐 뒤 manifest를 그대로 두면 검증 다운로드가 실패한다.

첫 번째 명령은 기존 본문을 유지하고 다음 리소스를 만든다.

- `audio/catalog.json`: 재생 가능한 장과 길이, 원본 이상 항목.
- `audio/chNN/timing.json`: 구간별 MP3 URL, 화자, 문장 ID, 단어 시간, trim, 가상 장 타임라인.
- `audiobook.js`, `audiobook.css`, `clip-player.js`, `media-player.js`.
- 본문 HTML의 CSS·JS 로딩 태그.

출력 데이터 개념 예시(숫자는 설명용):

```json
{
  "chapter": 1,
  "duration": 100.0,
  "segments": [{
    "src": "audio/ch01/clips/BOOK_C01_0000_LILY.mp3",
    "order": 0,
    "speaker": "Lily",
    "sentences": ["p0001-s1"],
    "original_duration": 2.0,
    "trim_start": 0.0,
    "trim_end": 1.8,
    "duration": 1.8,
    "offset": 0.0,
    "words": [{"sentence":"p0001-s1","word":0,"start":0.2,"end":0.5}]
  }]
}
```

위 `duration:100.0`은 구조 설명을 위한 예시다. 실제 데이터에서는 장 duration을 모든 segment duration의 합계와 일치시킨다. 단어 start/end는 원본 클립 기준이고, offset은 브라우저 trim 이후의 가상 장 타임라인 기준이다.

読み上げ時間から単語を選ぶ式:

```text
local_original_time = player.currentTime - segment.offset + segment.trim_start
word.start <= local_original_time < word.end
```

公開 JSON にローカル絶対パスを入れない。ファイルの不在、段落 ID 不整合、単語の順番逆転、範囲外 timestamp を生成段階でエラーにする。

## 10. 브라우저 재생과 문단 내 점프컷

### 정밀 모드

`TigerClipPlayer`는 MP3를 개별적으로 읽어 Web Audio로 디코딩하고 다음 구간들을 미리 예약한다. `AudioContext.currentTime`이 기준이다. 동일 구간이 재생 중일 때 `requestAnimationFrame`은 화면 표시만 담당한다.

같은 원본 문단의 인접 MP3라면 분석한 조용한 경계만 생략한다. 현재 경계 분석에는 약 60ms의 앞 보호 구간과 100ms의 뒤 보호 구간이 포함된다. 다른 문단이면 앞 trim은 0, 앞 파일의 end는 원본 끝이다. 음성 샘플을 겹쳐 재생하지 않는다. trim 경계의 약 4ms fade는 클릭 방지용이며 발음 크로스페이드가 아니다.

다음 파일이 늦게 로드되면 가상 시간이 조용히 진행하거나 문장이 건너뛰면 안 된다. 네트워크 대기 상태에서 재생 위치를 멈추고 재시도한다. 디코딩한 파일은 현재 주변의 짧은 창만 메모리에 남긴다.

### 호환 모드

`?audioMode=media`로 선택한다. `<audio>`의 재생 이벤트를 이용해 같은 개별 파일을 재생한다. `timeupdate` 빈도와 백그라운드 실행 제약 때문에 정밀 모드와 같은 무음 절단 정확도를 보장하지 않는다. 현재 다음 파일의 완전한 무간격 전환이나 휴대폰 잠금 호환은 미검증이며 시험 모드로 유지한다.

## 11. 가로모드 확정 UI 규격

| 요소 | 값·동작 |
|---|---|
| 좌우 비율 | 왼쪽 삽화 44%, 오른쪽 본문 56% |
| 상단 | 32px 바. 전체화면, 목차·글자 펼침 메뉴 |
| 하단 | 36px 한 줄 플로팅 재생바 |
| 글자 크기 | 14~102pt, 기본 19pt. 102pt는 기존 34pt보다 200% 증가한 값 |
| 본문 | 오른쪽 패널만 세로 스크롤. 문장·현재 단어 강조 |
| 삽화 | object-fit: contain. 해당 장면이 끝날 때까지 왼쪽 위치 유지 |
| 이미지 전환 | 650ms 세로 슬라이드. 뒤로 이동하면 반대 방향 |
| 동작 줄이기 | prefers-reduced-motion이면 슬라이드 생략 |
| 수동 스크롤 | 사용자가 본문을 만지거나 스크롤하면 자동 따라가기를 5초 유예 |
| 자동 스크롤 | 현재 문장이 패널의 안전 범위를 벗어날 때만 이동 |
| 세로 회전 | 삽화 위·본문 아래로 전환, 재생 상태 유지 |
| 안전 영역 | 노치와 홈바의 env(safe-area-inset-*) 반영 |

삽화를 음성 재생 시작 때마다 바꾸지 않는다. 같은 이미지 src가 연결된 문장들은 이미지가 그대로 유지된다. 다음 장면의 문장 ID에 도달할 때만 교체한다. 이미지는 decode가 끝난 뒤 삽입하고, 늦게 도착한 이전 요청은 화면을 덮어쓰지 못하게 한다.

### 생성 명령

```powershell
python production/build_landscape_test.py
```

이 스크립트는 권별 HTML을 읽어 `chapters.json`을 만든다. 문장별로 ID, 원문, 원본 문단, 이미지 경로를 저장하고 `production/landscape-test/`의 HTML·CSS·JS를 공개 테스트 폴더로 복사한다.

현재 구현은 **DOM에서 문장 앞에 가장 최근 나온 삽화**를 연결한다. 장 초반에 이미지가 없으면 그 장의 첫 삽화를 사용한다. 따라서 기존 HTML이 삽화→관련 본문 순서인지 검증해야 한다. 명시적 scene-manifest 매핑이 있는 책이라면 그것을 우선 사용하도록 빌더를 수정한다. 이미지가 없는 장은 이전 장의 삽화를 잘못 이어받지 않게 한다.

기존 읽기 페이지와 가로 테스트 HTML은 서로 다른 UI 구현이다. 기존 단어 뜻 기능은 원래 페이지에 남지만, 현재 가로 테스트는 텍스트만 추출하므로 **단어 뜻 펼침 기능을 이식했다고 주장하지 않는다.** 전체 적용 전에 이 차이를 해소해야 한다.

### 기본 HTML 구조

```html
<header class="topbar">
  <span id="title">책 제목</span>
  <button id="fullscreen">⛶ 전체화면</button>
  <details id="settings"><summary>목차 · 글자 ▾</summary><!-- 장·글자 설정 --></details>
</header>
<main>
  <aside id="art"><div id="art-stage"></div></aside>
  <article id="text-pane"><div id="text"></div></article>
</main>
<footer class="player"><!-- 이전·재생·다음·시크·시간·속도 --></footer>
```

CSS·JS 전체는 `production/landscape-test/` 소스를 사용한다. 위 조각만으로 완성된 플레이어가 되는 것은 아니다.

## 12. 전체화면·홈 화면 실행

클릭 이벤트 안에서 `document.documentElement.requestFullscreen()`을 호출한다. 사용자가 누르지 않았는데 자동 진입시키지 않는다. 진입·종료는 `fullscreenchange`로 버튼 표시를 갱신한다. 지원하지 않거나 요청이 거부되면 설치 안내를 띄운다.

- 아이폰: Safari 공유 → 홈 화면에 추가 → 웹 앱으로 열기 옵션이 보이면 사용.
- 안드로이드: 브라우저 메뉴 → 앱 설치/홈 화면에 추가.
- manifest의 scope는 해당 책/테스트 폴더 안으로 제한하고 `display: standalone`을 설정.
- `display_override`의 fullscreen은 지원 브라우저의 선호 설정이지 강제 보장이 아니다.
- 웹페이지가 브라우저 주소창을 CSS로 직접 지울 수는 없다.

현재 `manifest.webmanifest`는 `add_test_fullscreen.py`가 별도로 생성한다. 이 스크립트는 기존 프로젝트용 일회성 편집 도구다. 새 프로젝트에서는 manifest를 버전 관리하는 템플릿 파일로 저장하고 빌더가 복사하도록 정리하는 편이 안전하다. `expand_test_font.py`도 일회성 변경 도구여서 반복 실행 대상으로 넣지 않는다.

소스 ZIP에는 manifest 템플릿도 함께 제공한다. 새 프로젝트에서 `build_landscape_test.py` 실행 후 아래처럼 복사하고, 제목·아이콘 경로·scope가 새 책과 맞는지 확인한다. `expand_test_font.py`는 소스 묶음의 필수 실행 파일이 아니다. HTML 템플릿에 이미 `max="102"`가 반영돼 있다.

```powershell
Copy-Item -LiteralPath production/landscape-test/manifest.webmanifest -Destination story-reader/landscape-test/manifest.webmanifest
```

## 13. 오프라인 저장과 삭제

`install_offline_v2.py`는 공개 파일의 SHA-256을 계산해 `offline-manifest.json`에 기록하고 권별 service worker를 생성한다. 사용자가 전체 읽기 자료 또는 전체 오디오 저장을 선택하면 동시 작업 3개로 내려받고, 해시 일치 후 Cache API에 저장한다.

- 재시도 횟수는 제한하고 실패 파일이 있으면 완료로 표시하지 않는다.
- 같은 SHA 파일은 다시 내려받지 않는다.
- 오디오 전용 모드는 본문·타이밍·플레이어·아이콘을 포함하고 삽화는 제외한다.
- 현재 용량 안내는 오디오 전용에서도 **전체 자료 기준 최대값**이며, 남은 시간은 파일 수 처리율 기반 추정이다. 정확한 바이트 속도 ETA가 완성됐다고 표현하지 않는다.
- 다운로드 중단은 진행 중 전송을 취소하고 이미 받은 파일을 보존한다. 최신 코드의 AbortController 연결을 유지한다.
- 권마다 cache prefix가 다르며, 다른 책의 cache와 service worker를 삭제하지 않는다.
- 오디오 삭제 전에 재생을 멈추고 디코딩 버퍼와 미디어 source를 해제한다. 읽기 기록 삭제는 별도 선택이다.
- 현재 전체 삭제 버튼은 이 책의 Cache API 자료와 다운로드 완료 기록을 정리한다. 브라우저 HTTP 캐시·시스템 캐시·다른 앱 자료 삭제 기능이 아니다. service worker 등록까지 모두 해제하는 완전 초기화는 별도 구현 범위다.
- 기본 `<audio>` 요소의 오프라인 탐색을 위해 저장된 전체 MP3에 대해 `Range` 요청을 처리한다. 정상은 206, 범위가 유효하지 않으면 416을 반환한다.
- 저장 공간은 브라우저가 정리할 수 있다. 영구 저장 요청이 승인됐다고 가정하지 않는다. 다운로드 이력 표시와 실제 파일 존재는 구분해 재검증한다.

## 14. 잠금화면과 백그라운드

Media Session에 책 제목·장·로컬 아이콘을 제공하고 play/pause, ±15초, 지원되는 seek-to, 같은 권의 인접 장 제어를 연결한다. `setPositionState`의 duration과 position은 같은 가상 장 타임라인 기준이어야 한다.

지원되는 환경에서 `navigator.audioSession.type = 'playback'`을 설정한다. 그러나 이것으로 iPhone과 Android의 절전·브라우저 종료·화면 잠금 재생을 보장할 수 없다. AOD/잠금화면의 위젯 위치·크기·디자인은 OS가 결정한다.

아래는 반드시 별도 실기기 검사로 남긴다.

- iPhone Safari 및 홈 화면 웹앱, Android Chrome·삼성 인터넷 및 설치형 실행.
- 화면 잠금 30분, MP3 경계 20회 이상, 장 전환 1회 이상.
- 전화·알람·다른 미디어·블루투스 연결 해제 이후의 동작.
- 강제 종료나 시스템 회수 뒤 임의 자동 재생이 일어나지 않는지.

웹 방식이 이 검사를 통과하지 못하면 native audio를 사용하는 앱을 별도로 설계한다. 단순 WebView 포장만으로 해결됐다고 보지 않는다. 앱 개발·서명·스토어 배포는 이 웹 템플릿의 실행 범위가 아니다.

## 15. 실행 순서: 새 장 추가

**최초 제작은 이 절부터 시작하지 않는다.** 6.0절의 읽기 HTML 생성과 기준 커밋이 선행돼야 한다. 아래는 이미 읽기 HTML과 화자 기준이 있는 프로젝트의 새 오디오 추가 절차다.

권장 명령:

```powershell
python production/run_pipeline.py
```

이 명령은 입력 변경 감지, 추출·분석, 첫 화자 기준 생성, 보정, 정렬, HTML·가로모드·manifest 생성, 기본 파일 검증을 순서대로 수행하고 `production/audiobook/pipeline-report.json`을 기록한다. 공개 배포는 하지 않는다. 기존 Git HEAD와 본문·삽화 보존을 대조하는 `validate_reader_audio.py`는 기준 커밋이 준비된 프로젝트에서 추가 실행한다. 새 프로젝트를 한 번에 초기화하려면 `--initialize --book book.json`을 쓸 수 있지만, 읽기 HTML 검토와 기준 커밋은 별도로 수행해야 한다.

아래 개별 명령은 내부 단계 설명·디버깅용이며 `cache_guard.py`를 생략한 운영 절차로 사용하지 않는다.

```powershell
# PROJECT_ROOT에서 실행
python production/prepare_audiobook.py
python production/measure_new_clips.py
python production/normalize_clips.py
python production/whisper_force_align.py
python production/publish_audiobook.py
python production/install_offline_v2.py
python production/build_landscape_test.py
python production/validate_reader_audio.py
python production/validate_audio_assets.py
```

초기 loudness 기준 파일이 없는 경우 7절을 먼저 수행한다. TTS 입력 파일을 교체했거나 기본값을 변경한 경우 단순 재실행만 하지 말고 영향을 받는 캐시를 명시적으로 무효화한다.

`normalize_clips.py`도 보정본이 있으면 재사용한다. gain 정책 변경 시 과거 보정본까지 같은 규칙으로 다시 생성할지 결정하고 별도 출력 디렉터리에서 비교한다. 무작정 기존 자료를 일괄 삭제하지 않는다.

## 16. 검증과 재현 체크리스트

### 빈 프로젝트 스모크 테스트

```powershell
python production/smoke_template.py
```

이 테스트는 배포 사이트를 수정하지 않는다. 소스 ZIP을 새 임시 폴더에 풀고 그 안에서 예제 JSON → 기본 읽기 HTML → 기준 Git 커밋 → 인공 톤 MP3 ZIP → 본문 매핑 → 첫 음량 기준 → 개별 보정 → **실제 Whisper 실행** → 오디오 HTML → 오프라인 목록 → 가로 HTML → 검증을 수행한다. 결과는 `docs/SMOKE_TEST_REPORT.json`에 저장한다.

톤은 실제 발화가 아니므로 이 시험은 **파이프라인 실행과 불확실한 단어 fallback**만 확인한다. 단어 인식 품질·실제 음성 연기·휴대폰 잠금 재생을 검증한 것으로 표시하지 않는다. 음성 품질 시험에는 별도의 실제 TTS fixture와 청취가 필요하다. 실패 로그와 생성된 임시 프로젝트는 재현을 위해 남긴다.

```powershell
node --check production/clip-player.js
node --check production/media-player.js
node --check production/audiobook.js
node --check production/offline-v2.js
node --check production/landscape-test/test.js
python production/validate_reader_audio.py
python production/validate_audio_assets.py
```

브라우저 검사는 Playwright를 사용한다. 기존 시험 스크립트는 다른 작업 폴더의 `playwright-core`에 상대경로로 의존하므로 새 환경에서는 프로젝트 안에 설치하고 require 경로를 바꾼다.

```powershell
npm install --save-dev playwright
npx playwright install chromium
# 각 검증 파일의 require를 require('playwright')로,
# launch의 하드코딩된 Chrome executablePath는 제거하거나 실제 경로로 변경
```

로컬 서버는 반드시 **공개 루트**에서 실행한다.

```powershell
Set-Location story-reader
python -m http.server 8765 --bind 127.0.0.1
```

다른 터미널에서 PROJECT_ROOT로 돌아와 실행한다.

```powershell
node production/verify_audiobook.cjs
node production/verify_mobile_features.cjs
node production/verify_landscape.cjs
node production/verify_offline_all.cjs
```

검증 파일별 서버 포트는 소스를 확인한다. 전체화면 시험은 현재 8766 포트를 사용한다. 새 책의 장 번호에 맞게 테스트 장도 바꿔야 한다.

합격 기준:

1. 본문 문자열·문장 순서·단어장 연결·기존 삽화가 제작 전과 동일하다.
2. MP3 누락·중복, 원본 SHA 변경, 대본 미연결 단어를 설명 없이 통과시키지 않는다.
3. word index와 time 범위가 유효하고 잘못된 추정 시간을 만들지 않는다.
4. 같은 문단만 trim되고 문단 경계는 원본 쉼이 유지된다.
5. 844×390 등 가로 화면에서 왼쪽 이미지 위치가 유지되고 상·하단 바는 각각 32px·36px이다.
6. 한 장면의 여러 문장 동안 이미지가 유지되고 다음 장면에서만 전환한다.
7. 글자 14·19·102pt와 세로 회전에서 가로 넘침이 없고 본문을 스크롤할 수 있다. 최대 글자에서는 한 문장이 여러 화면에 걸칠 수 있으므로 자동 스크롤도 확인한다.
8. 오프라인 전체 저장 후 실제 네트워크 차단·재열기·재생·Range 요청을 검사한다.
9. 삭제 시험은 별도 브라우저 프로필에서 수행해 다른 사이트 fixture가 보존되는지 확인한다.
10. 자동화·실제 청취·휴대폰 잠금 검증을 서로 다른 항목으로 보고한다.

## 17. 공개 배포

기존 GitHub Pages 저장소를 사용할 때는 올바른 원격과 공개 폴더인지 확인한다. 새 책이면 별도 저장소와 고유 캐시·앱 ID를 사용한다.

```powershell
python production/prepare_audio_release.py
Set-Location story-reader
git remote -v
git add --pathspec-from-file=../production/audiobook/stage-paths.txt
# 가로 테스트 파일은 release 목록에 기본 포함되지 않으므로 명시적으로 추가
git add -- landscape-test/index.html landscape-test/test.css landscape-test/test.js landscape-test/chapters.json landscape-test/manifest.webmanifest
git diff --cached --stat
git commit -m "Update audiobook reader and landscape template"
git push origin main
gh api repos/OWNER/REPOSITORY/pages/builds/latest
```

manifest가 없는 새 프로젝트라면 먼저 생성한다. 문서의 OWNER/REPOSITORY를 실제 저장소로 바꾼다. Pages build의 commit이 방금 push한 SHA와 같고 status가 built인지 확인한다. 공개 HTML·JS·JSON·최종 MP3 응답까지 확인한 뒤 완료로 보고한다. 이전 배포의 built를 새 배포의 성공으로 착각하지 않는다.

기존 실제 주소:

- 읽기: https://kingspledu.github.io/when-you-trap-a-tiger-story-reader/volume-1/
- 가로 UI: https://kingspledu.github.io/when-you-trap-a-tiger-story-reader/landscape-test/

## 18. 문제 해결

| 증상 | 확인·대응 |
|---|---|
| 새 장이 목록에 없음 | catalog, timing, 실제 MP3, 공개 배포 SHA 확인. 온라인 metadata는 갱신하고 오프라인 자료 업데이트 |
| 파일명은 같은데 수정 음성이 안 나옴 | 추출·보정·정렬 캐시가 파일명을 재사용하는지 확인. 해시 비교 후 해당 항목만 재생성 |
| 보정 명령이 기준 JSON 없다고 실패 | 첫 프로젝트 bootstrap 절차 실행 |
| Whisper 모델 없다고 실패 | 모델을 먼저 다운로드. local_files_only는 오프라인 분석용 설정 |
| 다운로드 해시 불일치 | manifest 생성 뒤 파일을 바꿨거나 배포 중인 상태. 최종 파일로 manifest 재생성 후 같은 버전 배포 |
| 가로 삽화가 내용보다 먼저/늦게 바뀜 | HTML 삽화 위치와 문장→scene 연결 점검. 음성 분할 번호를 장면 번호로 쓰지 않음 |
| 이미지가 너무 빨리 사라짐 | 오른쪽만 스크롤하는지, 이미지 src가 문장마다 잘못 갱신되는지 확인 |
| 단어 강조가 없음 | null timing은 문장 fallback이 정상. 잘못된 word index·토큰 규칙 불일치는 오류 |
| 오프라인 기본 audio만 실패 | service worker 범위·Range 206·media-player.js 저장 여부 확인 |
| 전체화면 버튼이 안내만 표시 | 요청 미지원/거부. 홈 화면 웹앱 실행을 사용하고 강제 전체화면이라고 표기하지 않음 |
| 화면 잠금 후 끊김 | 실기기와 OS/브라우저 조합 기록. Web Audio와 media 모드를 각각 비교하고 미검증을 보장으로 바꾸지 않음 |

## 19. 제작 완료 보고 예시

> 새 N장, MP3 M개를 음량 보정·Whisper 정렬해 배포했습니다. 본문·단어 연결과 두 모드의 브라우저 재생을 검사했습니다. 단어 타이밍 연결률은 X%이며 불확실한 단어는 문장 강조로 표시합니다. 오프라인 검증 여부, 실제 청취 여부, 휴대폰 잠금 검사 여부를 각각 적습니다. 원본이 중간에서 끝나면 그 범위를 명시합니다.

이 문서를 기준으로 다음 책을 제작할 때도 입력 규격 → 원문 매핑 → 음량 기준 고정 → 시간 정렬 → HTML 생성 → 가로 UI → 오프라인 → 검증 → 배포 순서를 유지한다.

정확한 최초 제작 순서는 **입력 규격 → 기본 읽기 HTML 생성·검증 → 원문 매핑 → 음량 기준·보정 → 시간 정렬 → 오디오 포함 HTML 갱신 → 가로 UI → 오프라인 → 검증 → 배포**다. 앞의 ‘HTML 생성’은 오디오를 붙이는 갱신 단계와 구분해야 한다.

## 20. 이번 스모크 테스트 결과와 납품 소스 점검

2026-11-22 실행 결과:

| 검사 | 결과 |
|---|---|
| 이전 1.0 ZIP에 기본 HTML 생성기가 있는가 | FAIL: 생성기·기본 HTML/CSS/JS 누락 확인 |
| 보완 ZIP을 새 임시 프로젝트에 풀어 최초 생성 | PASS |
| 1·11·21장에 원문 5문장 생성과 원문 보존 | PASS |
| 인공 톤 MP3 ZIP → 색인 매핑 → 음량 초기화·개별 보정 | PASS |
| 실제 로컬 Whisper 실행 | PASS: 인공 음원이라 인식 정확도 검증 아님 |
| 오디오 포함 HTML·timing·catalog 생성 | PASS |
| 가로 HTML·chapters.json 생성 | PASS |
| 오프라인 목록의 모든 SHA-256 재계산 대조 | PASS |
| 브라우저에서 글자 크기·테마·단어 뜻 | PASS |
| 브라우저에서 오디오 문장 강조·원문 보존 | PASS |
| 가로 화면·삽화 로딩·102pt 상한·가로 넘침 | PASS |
| 브라우저 JavaScript 예외 | 0개 |
| 사람 청취·실제 발화 단어 정확도·휴대폰 잠금 | 이 스모크 테스트 범위 아님 |

실행 로그: `docs/SMOKE_TEST_REPORT.json`, 브라우저 결과: `docs/SMOKE_BROWSER_REPORT.json`. 이 결과는 웹사이트 전체 내용을 새로 제작한 테스트가 아니라 작은 fixture로 빈 프로젝트의 실행 의존성과 파일 생성을 확인한 것이다.

새 소스 묶음 필수 파일 점검:

```text
[포함] 기본 읽기 HTML/CSS/JS 전체 원본
[포함] 원문 JSON 입력 예제와 실제 읽기 HTML 생성기
[포함] 초기 PWA·아이콘 생성 코드
[포함] ZIP 원문 매핑·화자 기준 초기화·개별 음량 보정
[포함] Whisper 강제 정렬·타이밍 JSON 생성
[포함] 정밀/호환 재생 엔진과 문장·단어 강조
[포함] 오프라인 저장·삭제·Range 응답 생성
[포함] 가로 UI HTML/CSS/JS 전체 원본과 manifest
[포함] CLI 스모크 테스트와 브라우저 스모크 테스트 소스
[포함] 버전 목록·각 소스 SHA-256·상세 매뉴얼
[제외] 실제 책 원문·삽화·MP3·비밀키 (사용자 입력 자료)
```

`verify_template_smoke.cjs`는 `SMOKE_TEST_REPORT.json`에 기록된 임시 출력 프로젝트를 검증한다. 현재 환경의 Playwright 경로를 사용하므로 다른 컴퓨터에서는 16절에 따라 설치·require·브라우저 실행 경로를 변경한 뒤 실행한다.

## 21. 보완판 검증과 남은 합격 조건

보완 소스:

- `cache_guard.py`: 내용·설정·모델 버전 기반 변경 감지와 해당 파일 백업.
- `run_pipeline.py`: 단일 제작 진입점. 실패하면 비정상 종료하고 실패 단계를 기록.
- `lock_dependencies.py`: 현재 플랫폼에서 실행 의존성의 전이 관계 버전 잠금.
- `verify_cache_pipeline.py`: 변경 없는 재실행, 대본만 변경, 같은 이름의 음성 변경, 무관한 장 재사용 검증.

검증된 변경 감지 결과는 `docs/CACHE_PIPELINE_REPORT.json`을 본다. 이 검사는 별도 스모크 프로젝트에서 진행했으며 기존 공개 책의 분석 캐시를 초기화하지 않았다.

실제 TTS 파일 표본을 사용할 때:

```powershell
python production/smoke_template.py --real-speech
```

이 옵션은 기존 프로젝트의 `production/audiobook/ch01.json`과 원본 MP3에서 5개 구간을 읽어 별도 임시 프로젝트를 만든다. 소스 ZIP 자체에는 실제 책 음성이 포함되지 않는다. 이 표본으로 대본·파일 연결과 실제 Whisper 실행은 검증할 수 있지만, 사람이 표시한 기준 타임스탬프가 없으므로 단어 경계 오차나 인식 정확도를 입증하지 않는다. 일반 배포 ZIP의 기본 스모크는 인공 톤을 사용한다.

남은 실기기·청취 항목은 앞의 14·16절을 따른다. 이번 보완만으로 Android/iPhone 잠금 재생, Bluetooth 중단 복구, 사람 청취, 최대 102pt에서의 모든 장 자동 스크롤, 단어 뜻의 가로모드 이식이 완료됐다고 표기하지 않는다. 가로모드의 명시적 scene ID 우선 매핑과 전체 오프라인 포함도 후속 UI 통합 작업이다.
