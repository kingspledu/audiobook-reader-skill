# TTS HTML 제작의 최종 결과: 코드 복사 웹사이트

읽기 사이트의 HTML과 Gemini Canvas에 붙여 넣는 TTS HTML은 용도가 다르다. 이 문서는 TTS HTML을 전달하는 **코드 복사 사이트**의 필수 제작 절차다. 기존 읽기 사이트는 유지하고 별도 경로에 연결한다.

## 하나의 알고리즘

`assets/gemini-canvas-tts/scripts/copy_site.py`의 `render_episode(episode, stem, title)`만 Canvas HTML을 렌더링한다. `build.py`와 기존 대본의 사이트 이관은 모두 이 함수를 사용한다. 템플릿은 `assets/gemini-canvas-tts/assets/canvas-template.html` 하나다. 복사 페이지도 `assets/code-copy-template.html` 한 개에서 생성한다.

```shell
python scripts/init_workspace.py --out PROJECT_ROOT
# PROJECT_ROOT에서 실행
python tts/scripts/build.py book.json --out output
node tts/scripts/verify.cjs output
```

결과:

```text
output/
  PREFIX_C01_V01_GEMINI_CANVAS_TTS.html
  PREFIX_C01_V01_SCRIPT.json
  PREFIX_AUDIO_INDEX_V01.json
  PREFIX_AUDIO_INDEX_V01.csv
  code-copy/
    index.html
    manifest.json
    chapters/
      PREFIX_C01_V01_GEMINI_CANVAS_TTS.html
      ...
```

`output/code-copy/` 전체를 GitHub Pages의 지정 경로에 배포한다. index.html만 올리면 안 된다. 생성된 HTML을 읽어 다른 HTML로 감싸거나, 경로 문자열을 복사하거나, 29장 원문을 index.html에 통째로 내장하지 않는다. 페이지는 선택한 장만 요청하고 파일 크기와 SHA-256 검증 후 HTML 원문을 복사한다. 장 선택 후 **선택한 장 코드 복사**를 누르면 Gemini Canvas에 붙여 넣을 코드가 복사된다. 클립보드가 차단되면 코드 전체를 선택해 수동 복사할 수 있고, 동일 파일 다운로드도 제공한다. 로컬 점검은 file:// 대신 `python -m http.server`를 쓴다. 배포는 HTTPS가 필요하다.

## 기존 장별 HTML을 이관할 때

기존 HTML의 `originalEpisode`를 `extract_episode()`로 추출한다. 대본·화자·voice·persona·파일명·검토 증거·문장별 연기 설계 등 모든 필드를 그대로 유지한다. 각 HTML을 `render_episode()`로 재생성한 뒤:

```shell
python tts/scripts/copy_site.py --chapters output --out output/code-copy --title "작품명 · TTS HTML 코드 복사"
```

이 명령은 공통 렌더러의 결과와 입력 HTML이 다르면 실패한다. 오래된 템플릿을 그대로 복사해 놓고 일치한다고 보고하지 않는다. 배포 대상 디렉터리는 별도로 준비하고, 불필요한 이전 파일 삭제는 사용자 승인 범위에서만 한다.

## 검토와 연기 지침

각 segment에 `review`를 입력한다. `attribution`, `classification`, `performance`가 모두 `confirmed`이고 `evidence`가 비어 있지 않아야 생성할 수 있다. 이것은 실제 문맥 검토 결과여야 하며 생성기가 자동으로 확정 표시를 만들지 않는다. TXT 입력은 본문 보존용 **검토 전 초안**이다. 화자와 연기 검토를 마친 book.json으로 다시 생성하기 전에는 음성 생성이 차단된다.

```json
"review": {
  "attribution": "confirmed",
  "classification": "confirmed",
  "performance": "confirmed",
  "evidence": "앞뒤 문맥에 근거한 구체적인 화자·분류·연기 확인 사유"
}
```

`performance.design`에는 `addressee_intention`, `outer_inner`, `pivot`, `prosody`, `nonverbal`, `continuation`을 문장별로 작성한다. 화면의 연기 지침과 실제 `makePrompt()` 양쪽에 같은 값이 들어간다. 본문과 지시를 분리하고 기존 고정 배역을 유지한다. 독백에만 짧은 에코를 후처리한다.

## 필수 검증

```shell
python tts/scripts/self_test.py
pip install playwright
python -m playwright install chromium
python tts/scripts/verify_copy_site.py output/code-copy --report copy-browser-report.json
```

설치된 Chrome을 쓰려면 `--browser-path "Chrome 실행파일 경로"`를 지정한다. 검증기는 모든 장의 템플릿 재렌더링 바이트·파일 크기·SHA, 실제 브라우저 클립보드 내용, HTTP 오류·해시 불일치 거부, 빠른 장 전환, 클립보드 거부 시 수동 선택을 검사한다. Windows 클립보드의 CRLF 변환만 정규화해서 비교하며 HTML 내용은 바뀌면 안 된다. 다운로드 파일 바이트는 정규화 없이 비교한다.

배포 후 공개 manifest와 모든 장 HTML을 다시 내려받아 해시를 대조한다. 정적 검사·모의 생성·브라우저 복사 통과는 Gemini Canvas의 실제 음성 생성이나 사람 청취 검증을 의미하지 않는다. 모델 지원 여부와 실제 생성·다운로드는 Canvas에서 별도로 확인한다.
