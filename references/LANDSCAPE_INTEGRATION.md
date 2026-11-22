# 본문 전체 가로모드

별도 landscape-test가 존재하는 것만으로 전체 적용 완료로 보고하지 않는다. 각 volume-N/index.html이 공통 landscape-reader.css와 landscape-reader.js를 로드하고 실제 가로 화면에서 작동해야 한다.

새 작업공간의 `run_pipeline.py`는 오디오·오프라인 생성 후 `install_landscape_reader.py`를 실행한다. 기존 사이트에 별도로 적용하려면 작업공간에서 다음 명령을 실행한다.

```shell
python production/install_landscape_reader.py story-reader
```

이 설치기는 기존 3권의 HTML·audiobook.js·service worker·오프라인 목록을 갱신한다. MP3와 타이밍을 다시 만들지 않는다. 원문 문장·ID를 확인하고 삽화 원본·어휘 노드를 복제하지 않는다. 별도 프로젝트에서 3권 이외의 구성을 쓰려면 설치기의 권 순회와 기존 사이트의 DOM ID를 먼저 맞춘다.

휴대폰·태블릿 터치 기기의 가로 화면(너비≤1600px, 높이 제한 없음)에서는 같은 본문을 오른쪽 독립 스크롤 영역에 배치하고 해당 문장의 기존 삽화를 왼쪽에 고정한다. 재생기의 `tiger-active-sentence` 이벤트가 현재 문장·자동 따라가기 상태를 전달한다. 그림이 바뀔 때만 세로 슬라이드하며 reduced-motion에서는 즉시 전환한다. 수동 스크롤 중에는 사용자 읽기 위치를 우선한다. 별도 플레이어나 중복 본문을 만들지 않는다.

상단은 32px 접이식 목차·설정, 하단은 36px 재생 바다. **가로모드**와 **전체모드** 버튼은 기본 읽기에서도 항상 표시한다. 가로모드는 화면 크기와 관계없이 좌우 배치를 켜고 끄며 선택은 회전·새로고침·다른 권 이동 후에도 유지한다. 전체모드는 Fullscreen API 진입·종료 버튼이며 미지원 환경에서는 기존 설치 안내를 연다. 기존 오프라인 저장·삭제·호환 재생·테마·권 이동은 설정 안에 유지한다. 가로모드 글자 크기는 14~102pt로 별도 저장하며 세로모드 14~50pt와 분리한다.

오프라인 manifest의 `./`와 `index.html`은 모두 새 HTML 해시로 갱신해야 한다. 새 모듈의 해시·파일 목록·예상 바이트도 갱신한다. 새 service worker는 오프라인 재접속 때 최신 core 화면을 이전 saved 화면보다 우선하지만 기존 saved MP3 캐시는 지우지 않는다.

검증 기준: 1~29장 선택·강조, 740×360/844×390/932×430 가로와 390×844 세로 회전, 102pt·어휘 카드, 그림 고정·탐색 후 전환, 재생기 1개, 원문·어휘·그림 연결 보존, 실제 오프라인 재접속과 이전 캐시 유지. `verification/LANDSCAPE_*`에 공개 사이트 기반 검사 결과가 있다. Chrome 모바일 에뮬레이션 통과와 실제 Android/iPhone 잠금 재생·청취는 구별한다.

## 1. TTS 생성 화면과 오디오북 읽기 화면 구분

Gemini Canvas HTML은 음성을 생성하고 MP3 ZIP을 받는 도구다. 이 HTML에 읽기 가로모드를 붙이지 않는다. 가로모드는 생성·다운로드·음량 보정·문장 매핑을 마친 **읽기 사이트**에 설치한다. 코드 복사 사이트 역시 읽기 사이트와 별도다. 가로모드를 요청받으면 대상 읽기 URL과 생성 소스를 먼저 확인한다.

## 2. 포함된 실행 소스와 순서

| 파일 | 책임 |
|---|---|
| production/build_reading_html.py | 전체 원문·문장 ID가 있는 초기 읽기 HTML 생성 |
| production/clip-player.js | 개별 MP3 유지, 문단 내부 무음 경계를 브라우저에서 연결 |
| production/media-player.js | 호환 재생 경로 |
| production/audiobook.js | 시간→구간→단어/문장 강조, 재생 위치·미디어 세션 |
| production/landscape-reader.js | 기존 DOM을 사용한 좌우 화면, 삽화와 활성 문장 연결 |
| production/landscape-reader.css | 가로모드 배치·접힘 설정·얇은 바 |
| production/install_landscape_reader.py | 모든 권 설치, 오디오 이벤트 연결, 오프라인 해시 갱신 |
| production/run_pipeline.py | 오디오 연결→오프라인 생성→가로모드 설치→자료 검증 |

스킬 루트에서 별도 빈 작업공간을 만들고 그 작업공간에서 실행한다.

```shell
python scripts/init_workspace.py --out PROJECT
# 이후 PROJECT에서 실행
python production/build_reading_html.py --input book.json --output story-reader
# 오디오 입력·배역·음량·Whisper 준비는 START_HERE.md를 따른다.
python production/run_pipeline.py
# 화면 코드만 갱신할 때는 MP3 재생성 없이 다음 설치기를 사용한다.
python production/install_landscape_reader.py story-reader
python production/validate_reader_audio.py
python production/validate_audio_assets.py
node --check production/landscape-reader.js
```

명령은 로컬 파일을 만든다. 공개 업로드는 사용자에게 승인된 저장소·범위에서 별도로 수행한다. 새 작품에 기존 책의 원문·이미지·배포 계정을 재사용하지 않는다.

## 3. 이식할 때 지켜야 할 DOM 계약

기존 템플릿과 다른 사이트에 설치하면 다음 대응표부터 만든다. 선택자가 없다고 본문을 새로 복제해서 해결하지 않는다.

| 선택자/속성 | 요구사항 |
|---|---|
| article | 전체 본문 컨테이너 1개 |
| section.chapter#chapter-NNN | 장 식별자, 기존 오디오 chapter와 대응 |
| .reading-sentence[data-sentence] | 변경하지 않는 문장 ID·원문·순서 |
| .story-text[id] | 문단과 읽기 위치 식별자 |
| figure img[src] | 문장 사이에 배치된 기존 삽화 |
| #floating-reader, #chapter-menu | 기존 목차와 상단 도구 |
| #font-size, #font-value | 기존 글자 범위 입력과 출력, 필수 |
| #smaller, #larger | 선택적인 확대·축소 버튼, 없어도 동작 |
| #theme, #install-app, #install-help | 테마·설치·전체화면 미지원 안내 |
| .audiobook, .audio-progress input | 기존 오디오 패널과 탐색 입력 |
| .offline-tools | 기존 다운로드·캐시 삭제 도구 |
| #reader-layout-toggle | 가로모드 켜기·끄기, aria-pressed로 분할 상태 표시 |
| #landscape-fullscreen | 전체모드 진입·종료, Fullscreen API 상태 표시 |

스크립트는 기존 article을 #landscape-text-pane 안으로 이동시킨다. #landscape-art-stage에는 현재 그림만 표시한다. 숨긴 원래 figure는 본문 데이터로 남아 있으며 그림 파일을 재생성하지 않는다. 설정으로 옮기는 노드는 원래 자리에 주석 마커를 두고 세로 모드 복귀 시 복원한다. 어휘 버튼·이벤트·기존 재생기는 그대로 사용한다. 가로모드가 꺼져도 추가 컨테이너로 인해 기존 CSS 선택자가 깨지지 않는지 확인한다.

## 4. 개별 MP3·타이밍·활성 문장 계약

각 권의 audio/catalog.json은 사용 가능한 장을, audio/chNN/timing.json은 구간별 src·offset·duration·trim_start·trim_end·sentences·words를 제공한다. src는 해당 권 URL 기준이다. words의 start/end는 원본 클립 기준이며, 구간 내 시간에 trim_start를 더해 비교한다. Whisper 근거가 없는 단어에는 타이밍을 만들지 않고 문장 강조로 대체한다. 화면 모드 때문에 오디오를 병합하거나 다시 노멀라이즈하지 않는다.

기존 audiobook.js의 mark()에서 현재 문장을 계산한 뒤 다음 계약의 이벤트를 전달한다. 상세 구현은 설치기가 실제 삽입하는 코드를 기준으로 한다.

```javascript
dispatchEvent(new CustomEvent('tiger-active-sentence', {
  detail: {
    sentence: current, // 현재 실제 DOM 요소; 복제본 아님
    follow: follow.checked,
    chapter: track.chapter,
    index,
    time: absolute // 장 전체 재생 시간(초)
  }
}));
```

가로모드에서는 기존 window용 scrollIntoView 자동 따라가기를 끄고 오른쪽 pane을 스크롤한다. 같은 이벤트를 내는 재생기 1개만 둔다. 가로모드 전환으로 pause/play, currentTime, playbackRate, 트랙 선택을 초기화하지 않는다. 정밀·호환 재생 모두 같은 문장 이벤트를 내야 한다.

## 5. 삽화 선택·전환 규칙

1. 각 장 DOM을 순서대로 읽어 가장 최근에 등장한 img를 다음 문장들에 연결한다. 장 밖의 이전 그림을 가져오지 않는다.
2. 첫 그림 이전 문장에는 그 장의 첫 그림을 사용한다. 그림 없는 장은 빈 삽화 영역을 허용하며 다른 장의 그림으로 잘못 채우지 않는다.
3. 활성 문장 이벤트로 연결된 그림을 표시한다. src가 같으면 다시 전환하지 않는다. 이미지 decode 완료 후 교체하고, 요청 순번으로 오래 걸린 이전 그림이 최신 그림을 덮지 못하게 한다.
4. 새 그림은 아래에서 들어오고 이전 그림은 위로 나간다(600ms). reduced-motion은 애니메이션 없이 전환한다. 로딩 실패는 이전 그림을 해당 장면인 것처럼 유지하지 않는다.
5. 재생 탐색·이전/다음 구간·문장 클릭·다음 장 이동도 같은 매핑을 사용한다. 사용자의 휠·터치·포인터 조작 뒤 4.5초 동안 자동 따라가기를 유예한다. 수동 스크롤은 읽는 문장에 맞춰 그림을 갱신한다.
6. 이미지가 먼저 나오도록 구성한 기존 본문과, 이미지가 뒤에 오는 다른 원본은 의미가 다를 수 있다. 다른 사이트 이식 시 실제 장면 시작 문장 3곳 이상을 대조하고 필요하면 명시적인 sentence→scene 매핑으로 교체한다.

## 6. 자동·수동 화면 상태와 저장

| 상태 | 동작 |
|---|---|
| 저장값 없음(auto) | orientation:landscape + max-width:1600px + any-pointer:coarse면 분할 |
| split | 가로모드 강제 켜기, 화면 방향·크기 제한 없음 |
| full | 기본 전체 본문 배치, 자동 조건보다 우선 |

`tiger-reader-layout`에 split/full을 저장한다. 이 키의 full은 **본문 배치 상태**이고 브라우저 fullscreen 상태가 아니다. 버튼 표시는 가로모드의 aria-pressed로 현재 분할 여부를 나타낸다. 전체모드는 독립적인 Fullscreen API 버튼이다. 저장된 수동 선택은 새로고침·화면 회전·권 이동 후에도 유지한다. 자동 동작을 시험할 때는 이 키만 지워야 하며 오디오 캐시 전체를 삭제하면 안 된다.

가로 글자 크기는 `tiger-landscape-font`에 14~102pt로 저장한다. 전환 전 기존 글자 크기·slider 상한을 보관하고 기본 배치로 돌아올 때 복원한다. 다른 책·같은 출처 여러 앱에 적용할 때는 layout/font 키를 책 식별자로 분리해 설정이 섞이지 않게 한다. 기존 구현의 공용 키를 바꾸면 저장값 마이그레이션도 정한다.

## 7. 배치 수치·접근성·전체화면

- 삽화 약 44%, 본문 약 56%. 그림은 object-fit:contain으로 잘리지 않게 표시한다.
- 상단 32px, 하단 36px. 본문과 그림은 양쪽 바 사이에 두고 safe-area-inset과 100dvh를 반영한다.
- 목차·설정은 기본 접힘. 설정 안에는 글자·테마·오프라인 저장/삭제·재생 호환 모드·권 이동을 유지한다. 단어 카드는 오른쪽 원문 문장 바로 아래에서 열린다.
- 기본 배치에서도 가로모드/전체모드 버튼은 보여야 한다. 작은 세로 화면에서 버튼이 가로 넘침을 만드는지 확인한다.
- 전체화면 요청은 직접 사용자 클릭에서 실행한다. document.fullscreenElement와 fullscreenchange로 진입/종료 표시를 갱신한다. 미지원/거부 시 기존 설치 안내를 연다. iOS 전체화면 가능성을 에뮬레이션 결과만으로 보장하지 않는다.
- 키보드 Escape·바깥 클릭으로 설정 닫기, 메뉴 항목 선택 후 닫기, 숨겨진 도구의 포커스, 대비·reduced-motion을 확인한다.

## 8. 오프라인·릴리스 절차

설치기는 HTML, audiobook.js 이벤트, 공통 JS/CSS, sw.js, offline-manifest.json을 갱신한다. 모든 권 HTML이 공통 모듈을 로드하는지 확인한다. 스크립트 URL 버전과 CORE 버전은 함께 올린다. manifest의 `./`와 index.html은 같은 HTML을 가리키므로 둘의 해시를 모두 갱신하고 바이트 합계도 각각 반영한다. 기존 오디오 항목의 SHA는 그대로여야 한다.

네트워크가 끊겼을 때 새 CORE 앱 화면을 이전 SAVED 화면보다 먼저 선택한다. 이미 다운로드한 MP3·그림 캐시는 유지한다. 테스트에서는 의도적으로 오래된 SAVED HTML을 넣고 재접속해 새 모드가 유지되는지 확인한다. 오프라인 첫 진입은 온라인 저장이 먼저 필요하다.

공개 배포는 HTML/공통 JS/CSS/SW/manifest만 변경 목록에 명시한다. 로컬의 미배포 음성·기타 작업을 일괄 git add하지 않는다. 기대 커밋이 Pages에서 built인지 확인하고 공개 파일 해시와 실제 화면을 다시 검사한다. 다음 생성에서 기능이 사라지지 않도록 소스 ZIP과 펼친 reader-pipeline의 파일이 같아야 한다.

## 9. 완료 전 검증 행렬과 실패 판정

| 시험 | 통과 기준 |
|---|---|
| 문장 보존 | 원문·ID·순서·개수 전부 동일, 어휘 노드·삽화 경로 보존 |
| 모든 권·장 | 각 장 선택 후 본문·타이밍·강조가 맞고 오디오 패널 1개 |
| 휴대폰 | 740×360, 844×390, 932×430에서 가로 넘침 0, 상단≤35px/하단≤40px |
| 태블릿 | 1024×768, 1180×820, 1366×1024에서 자동 분할; 높이 600px 제한 재도입 금지 |
| 수동 모드 | 세로·1920×1080에서도 버튼 강제 전환, 새로고침 후 선택 유지 |
| 회전 | 활성 문장·재생 시간·속도 유지, 기본 배치 글자값 복원 |
| 장면 | 동일 그림 반복 애니메이션 없음, 다음 장면 탐색 시 그림 교체, 스크롤 중 그림 위치 고정 |
| 어휘 | 각 권의 실제 버튼에서 뜻·닫기 작동; 원본에 없으면 미실시로 기록 |
| 전체모드 | 진입·종료·버튼 상태, 미지원 모의 환경에서 설치 안내 |
| 오프라인 | 저장 후 네트워크 차단·재접속, 새 CORE 우선, 기존 MP3 보존 |
| 실기기 | Android Chrome/iPad Safari에서 회전·설치·잠금/복귀·이어폰 조작 별도 확인 |

오디오북 재생이 포함된 검증에서는 의미 없는 합성 음성과 실제 음성 청취를 구별한다. 합성 톤+실제 Whisper 실행은 파이프라인 연결 시험이며 단어 정렬 정확도나 듣기 품질의 증거가 아니다. `LANDSCAPE_REPORT.json`, `LANDSCAPE_OFFLINE_SCENE_REPORT.json`, `LANDSCAPE_TABLET_REPORT.json`, `LANDSCAPE_GENERATED_BROWSER.json`, `LANDSCAPE_PIPELINE_SMOKE.json`은 각각 화면·오프라인·태블릿·신규 생성 화면·전체 생성 경로의 검사 범위를 기록한다.

## 10. 자주 생기는 실패와 진단 순서

- 태블릿만 안 됨: 기존 max-height:600px 조건·터치 판정·저장된 full 설정 확인. 수동 버튼으로 조건을 우회할 수 있어야 한다.
- 별도 시험만 동작: 실제 각 권 index.html의 link/script와 공통 모듈 응답을 확인한다.
- 모듈이 바로 종료: article/#floating-reader 존재 확인. slider/value 누락·선택 버튼 존재 여부를 구분한다.
- 본문은 바뀌는데 그림 정지: 문장 이벤트, 실제 DOM sentence, 이미지 매핑, decode 실패를 순서대로 확인한다.
- 두 음성이 겹침: 추가 생성한 재생기 제거, 기존 재생기 이벤트만 구독한다.
- 재생 때 화면 전체가 점프: 기존 window용 따라가기와 pane 따라가기가 동시에 실행되는지 확인한다.
- 새로고침하면 예전 화면: 공개 SHA, HTML 자원 버전, SW CORE, SAVED 우선순위, 두 HTML 해시를 확인한다.
- 다른 작품에 설정이 섞임: 출처 공용 localStorage 키를 작품별로 분리한다.
