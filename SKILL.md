---
name: audiobook-reader
description: 원문에서 Gemini Canvas용 드라마 TTS HTML을 제작하고 완성한 개별 MP3를 읽기 HTML·Whisper 하이라이트·가로모드·오프라인 사이트에 연결한다. TTS와 오디오북 읽기 사이트를 이어서 재현할 때 사용한다.
---

# 오디오북 읽기 사이트 제작

먼저 [제작 시작과 입출력 연결](references/START_HERE.md)을 읽는다. **기본 읽기 HTML을 먼저 만들고 문단·문장 ID를 검증한 뒤 오디오를 연결**한다. 기존 읽기 페이지는 새로 덮어쓰지 않는다.

## 실행 경로

1. `python scripts/init_workspace.py --out PROJECT_ROOT`로 별도 작업공간에 소스와 템플릿을 푼다. 스킬 폴더에서 책 파일을 만들지 않는다.
2. 원문을 book.json의 chapters/paragraphs/sentences에 넣고 `python production/build_reading_html.py --input book.json --output story-reader`로 기본 HTML을 생성한다. 요약하거나 문단을 임의 변경하지 않는다.
3. TTS를 새로 만들면 [포함된 TTS 스킬](assets/gemini-canvas-tts/SKILL.md)과 연결된 references를 읽는다. 고정 배역·성우·문장별 연기 JSON으로 `python tts/scripts/build.py ... --out output`을 실행해 Canvas용 HTML·대본·JSON/CSV 색인을 만든다. 키 입력 없는 Canvas 호스트만 사용하며 실제 지원 여부를 확인한다.
4. 이미 MP3가 있으면 생성 단계를 건너뛴다. 색인 변환·WAV→MP3는 [입출력 연결](references/START_HERE.md)을 따른다.
5. [전체 재현 매뉴얼](references/AUDIOBOOK_READER_TEMPLATE_KO.md)의 모델·초기 음량 준비 후 `python production/run_pipeline.py`를 실행한다.
6. [검증 범위](references/IMPROVEMENT_EXECUTION_REPORT_KO.md)에 따라 자동 검사와 실제 청취·휴대폰 잠금 검증을 구분한다.

## 제품 규격

- 개별 MP3 유지, 화자별 기본 음량 보정. 문단 안 경계 무음은 브라우저에서 건너뛰고 문단 사이 쉼 보존.
- Whisper 근거가 있는 단어만 시간 연결. 강제 정렬과 독립 ASR 검증을 구분하고 불확실한 단어는 문장 강조로 대체.
- 가로 화면은 왼쪽 삽화 고정·오른쪽 본문 스크롤. 다음 장면의 문장에 도달할 때 세로 슬라이드. 상단 설정은 접힘 메뉴, 하단 재생은 얇은 한 줄 바.
- 실험 배너·장면 번호·시험 문구를 독서 화면에 넣지 않는다. 필요한 실패 안내는 유지.
- 오프라인은 파일 검증 후 완료 표시. 삭제는 해당 책 자료에만 적용.
- 공개 배포는 요청된 범위에만 수행. 실제 책 원문·음성·개인 경로·키는 공개 스킬에 넣지 않는다.

## 현재 프로필 제한

읽기 파이프라인은 영어 토큰과 1~29장·3권을 기준으로 한다. 다른 언어·권수는 문서의 고정값을 모두 수정하고 시험한다. TTS 생성기가 한국어를 지원해도 읽기 도구의 한국어 정렬까지 검증된 것은 아니다. `--real-speech` 스모크는 과거 책의 로컬 fixture를 요구하므로 공개 기본 시험에는 사용하지 않는다.

`python scripts/validate_package.py`로 포함 파일과 해시를 검사한다. 작업공간에서 `python production/smoke_template.py` 및 브라우저 시험을 수행한다. Canvas 생성·사람 청취·휴대폰 잠금 재생을 자동 시험 통과로 대체하지 않는다.
