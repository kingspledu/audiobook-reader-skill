---
name: audiobook-reader
description: 원문에서 Gemini Canvas용 드라마 TTS HTML을 제작하고 완성한 개별 MP3를 읽기 HTML·Whisper 하이라이트·가로모드·오프라인 사이트에 연결한다. TTS와 오디오북 읽기 사이트를 이어서 재현할 때 사용한다.
---

# 오디오북 읽기 사이트 제작

먼저 [제작 시작과 입출력 연결](references/START_HERE.md)을 읽는다. **기본 읽기 HTML을 먼저 만들고 문단·문장 ID를 검증한 뒤 오디오를 연결**한다. 기존 읽기 페이지는 새로 덮어쓰지 않는다.

## 실행 경로

1. `python scripts/init_workspace.py --out PROJECT_ROOT`로 별도 작업공간에 소스와 템플릿을 푼다. 스킬 폴더에서 책 파일을 만들지 않는다.
2. 원문을 book.json의 chapters/paragraphs/sentences에 넣고 `python production/build_reading_html.py --input book.json --output story-reader`로 기본 HTML을 생성한다. 요약하거나 문단을 임의 변경하지 않는다.
3. TTS를 새로 만들면 [코드 복사 사이트 제작](references/TTS_CODE_COPY_SITE.md)과 [포함된 TTS 스킬](assets/gemini-canvas-tts/SKILL.md)을 읽는다. 고정 배역·성우·문장별 연기 JSON으로 `python tts/scripts/build.py ... --out output`을 실행한다. 최종 전달물은 장별 Canvas HTML·대본·JSON/CSV 색인과 **실제 HTML 코드를 복사하는 `output/code-copy/` 웹사이트**다. 이 폴더를 통째로 배포한다. 키 입력 없는 Canvas 호스트만 사용하며 실제 지원 여부를 확인한다.
4. 이미 MP3가 있으면 생성 단계를 건너뛴다. 색인 변환·WAV→MP3는 [입출력 연결](references/START_HERE.md)을 따른다.
5. [전체 재현 매뉴얼](references/AUDIOBOOK_READER_TEMPLATE_KO.md)의 모델·초기 음량 준비 후 `python production/run_pipeline.py`를 실행한다. [전체 본문 가로모드](references/LANDSCAPE_INTEGRATION.md)의 공통 모듈은 파이프라인 마지막에 설치된다. 별도 시험 페이지만으로 전체 적용 완료라고 보고하지 않는다.
6. [검증 범위](references/IMPROVEMENT_EXECUTION_REPORT_KO.md)에 따라 자동 검사와 실제 청취·휴대폰 잠금 검증을 구분한다.

## 제품 규격

동일 문단 내 문장 연결은 [컷 편집 규칙과 재생기 차이](references/PARAGRAPH_JUMP_CUTS.md)를 따른다. 원음 MP3는 유지하고 브라우저 trim으로 연결하며 다른 문단의 쉼은 보존한다. `scripts/verify_paragraph_cuts.py`로 경계·실제 예약 코드를 검사한다.

[책별 리소스·어휘·독서 위치·캐릭터 시트 입력](references/READER_RESOURCES.md)을 따른다. 기본 읽기 생성기는 슬라이드 어휘 카드·독서 진행선·문단 위치 이어 읽기를 포함하며 characters 입력이 있으면 시트 페이지와 권별 링크를 만든다. 새 책의 실제 콘텐츠는 따로 준비한다. 언어·권수 확장과 실기기 시험을 미실시 상태로 숨기지 않는다.

Whisper 노래방식 재생은 [타이밍→단어→문장 연결 규약](references/WHISPER_KARAOKE.md)을 먼저 읽는다. 원음 단어 시간·trim·장 offset을 혼동하지 말고 실제 근거가 없는 타이밍은 null로 둔다. [공개 읽기 사이트 기능 대응표](references/READER_FEATURE_PARITY.md)의 포함·간소화·미포함 항목을 확인하고 전체 기능이 동일하다고 추정하지 않는다.

오디오북 가로 재생을 제작·수정할 때는 [구현 계약·명령·검증 행렬](references/LANDSCAPE_INTEGRATION.md)을 먼저 읽는다. **기본 읽기 페이지 전체에 공통 모듈을 설치**하며, 별도 시험 페이지만 만들고 완료하지 않는다. 태블릿 높이 제한을 두지 않고 가로모드/전체모드 수동 버튼을 제공한다. 기존 단일 재생기·문장 ID·개별 MP3를 유지한다.

전체모드는 실제 브라우저 전체화면의 진입·종료이며 가로 배치와 독립적이다. 같은 문서의 전체화면 필수 절차를 따르고 `scripts/verify_fullscreen.py`로 실제 포함 모듈의 진입·종료·거부·미지원 안내를 검사한다. iOS 홈 화면 설치 안내와 API 성공을 구별한다.

- 개별 MP3 유지, 화자별 기본 음량 보정. 문단 안 경계 무음은 브라우저에서 건너뛰고 문단 사이 쉼 보존.
- Whisper 근거가 있는 단어만 시간 연결. 강제 정렬과 독립 ASR 검증을 구분하고 불확실한 단어는 문장 강조로 대체.
- 가로 화면은 왼쪽 삽화 고정·오른쪽 본문 스크롤. 다음 장면의 문장에 도달할 때 세로 슬라이드. 상단 설정은 접힘 메뉴, 하단 재생은 얇은 한 줄 바.
- 실험 배너·장면 번호·시험 문구를 독서 화면에 넣지 않는다. 필요한 실패 안내는 유지.
- 오프라인은 파일 검증 후 완료 표시. 삭제는 해당 책 자료에만 적용.
- 공개 배포는 요청된 범위에만 수행. 실제 책 원문·음성·개인 경로·키는 공개 스킬에 넣지 않는다.
- 복사 사이트와 Canvas HTML은 `copy_site.render_episode()` 및 단일 `canvas-template.html`로 생성한다. 별도 사이트용 생성기를 만들거나 HTML을 수작업 수정하지 않는다. 파일 SHA-256·원문/배역/연기 보존·브라우저 복사 검증이 모두 통과해야 배포한다. 기존 원고를 옮길 때 원문이나 검토 상태를 임의 변경하지 않는다.

## 현재 프로필 제한

읽기 파이프라인은 영어 토큰과 1~29장·3권을 기준으로 한다. 다른 언어·권수는 문서의 고정값을 모두 수정하고 시험한다. TTS 생성기가 한국어를 지원해도 읽기 도구의 한국어 정렬까지 검증된 것은 아니다. `--real-speech` 스모크는 과거 책의 로컬 fixture를 요구하므로 공개 기본 시험에는 사용하지 않는다.

`python scripts/validate_package.py`로 포함 파일과 해시를 검사한다. 작업공간에서 `python production/smoke_template.py` 및 브라우저 시험을 수행한다. Canvas 생성·사람 청취·휴대폰 잠금 재생을 자동 시험 통과로 대체하지 않는다.

## 문장별 음성 제작 필수 규칙

한 문장 = 한 생성 요청 = 한 개별 WAV/MP3다. 문단 전체나 배우가 이어 읽을 여러 문장을 한 요청으로 묶지 않는다. 배포 ZIP은 개별 문장 MP3를 유지한다. 합본은 선택적 청취 파생물이며 문장 파일을 대체하지 않는다.

각 segment는 sentence_id, paragraph_id, context_before/context_after(문장 ID 배열), 문장별 performance.sentence_persona, performance.design을 가진다. 기본 배역 페르소나는 유지하되 해당 문장의 상대·목적·현재 감정을 별도로 적용한다. 같은 문단의 분위기·호흡을 이어 주며 분리 생성한다.

앞뒤의 ‘울부짖었다·웃었다·울었다’ 같은 묘사를 읽고 누구의 어느 발화에 적용되는지 찾는다. performance.cue_links에 source_sentence_id, target_sentence_id, cue_text, instruction을 기록한다. 해당 단서가 없으면 빈 배열로 명시한다. 단서가 다른 인물/시점이면 억지로 적용하지 않는다. 웃음·울음의 강도·위치는 근거에 맞추며 기계적으로 덧붙이지 않는다.

검토는 speaker_pass, cue_pass, continuity_pass의 세 항목으로 각각 기록한다. review.evidence와 review.sentence_boundary_evidence에는 실제 문맥·분할 근거를 적는다. 생성기나 정규식이 검토를 confirmed로 자동 변경해서는 안 된다. 화자가 애매하면 review.attribution=user_review_required로 두고 질문 대상 문장·앞뒤 문맥·후보·판단 근거를 사용자에게 제시한다. 승인 전 그 문장은 생성 차단한다. 나레이터로 임의 대체하지 않는다.

문장 분할 시 인용부호·약어·소수·말줄임표·감탄사에 주의한다. 문장 경계의 자동 탐지는 보조 검사일 뿐 의미 검토가 아니다. 기존 문단의 문자 범위와 문장 순서를 유지하며 누락·중복을 대조한다. 이전 문단형 대본은 신규 문장 검토 전까지 생성 불가 초안이다.
