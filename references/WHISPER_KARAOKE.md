# Whisper 단어 타이밍과 노래방식 본문 강조

## 결과와 정확도 범위

실제 개별 MP3를 Whisper로 처리해 문장 속 단어마다 시작·끝 시간을 저장한다. 재생 중 현재 문장은 연한 배경, 현재 단어는 진한 배경으로 표시한다. 노래방식은 이 단어 단위 강조를 뜻하며 화면에 모든 단어를 균등 간격으로 칠하는 방식이 아니다. 원문 텍스트는 바꾸지 않는다.

포함 구현은 영어 토큰 `[A-Za-z0-9]+(?:['’][A-Za-z0-9]+)*`, faster-whisper base/CPU/int8 기준이다. 한국어·일본어 등에는 이 토큰 규칙을 그대로 쓰지 않는다. `find_alignment`를 사용하는 **원문을 주어진 대본으로 강제 정렬**한 결과와, 독립 ASR로 음성이 원문과 일치하는지 확인한 결과를 구별한다. 현재 짧은 음성의 recognized_words는 강제 정렬에서 나온 단어이므로 독립 음성 인식 검증으로 보고하지 않는다.

## 입력→시간→DOM 경로

1. 초기 읽기 HTML에 `.reading-sentence[data-sentence]`와 문단 ID가 있어야 한다. 단어 정리를 추가해도 textContent·문장 ID·순서를 보존한다.
2. MP3 ZIP의 색인에 chapter/order/filename/text/speaker가 있어야 한다. `prepare_audiobook.py`는 ZIP 원문과 읽기 원문의 정규화 단어를 순서대로 매핑해 `word_map=[sentence_id, word_index]`를 만든다. 누락·중복·미매핑을 보고하고 매핑되지 않은 원문을 몰래 삭제하거나 임의 연결하지 않는다.
3. `measure_new_clips.py`와 `normalize_clips.py`로 화자별 일정한 gain만 적용한 개별 MP3를 만든다. 음량 보정 단계에서는 무음을 자르거나 클립을 합치지 않는다. 시간 정렬 대상과 배포한 음원의 관계는 SHA와 캐시 검증으로 추적한다.
4. `whisper_force_align.py`가 원본 클립을 16kHz로 디코딩한다. 짧은 클립은 0.2초 간격으로 묶어 28초 이하 그룹에서 cross-attention DTW를 수행한다. 그룹 시간을 각 클립 시간으로 되돌리고, SequenceMatcher의 일치 토큰 중 확률≥0.05·끝>시작인 단어만 유지한다. 임계값은 정확도 보증이 아니다.
5. 29.5초를 넘는 예외 클립은 전체 길이의 `transcribe(word_timestamps=True)` 결과로 매핑하며 review_required를 남긴다. 30초에서 잘라 뒤쪽을 누락하지 않는다.
6. `publish_audiobook.py`는 `aligned-chNN.json`과 `word_map`을 결합해 해당 권의 timing.json을 만든다. 단어의 start/end는 **원본 개별 클립 기준**이고 offset은 **브라우저 재생용 장 타임라인 기준**이다.
7. `audiobook.js`는 기존 문장 안의 텍스트 노드만 `.audio-word`로 감싼다. 어휘 button/a를 지우지 않는다. 현재 시간의 구간·단어를 찾아 `.audio-word-active`, `.audio-sentence-active`를 갱신한다. 단어 카드 클릭이 오디오 탐색으로 전파되지 않도록 한다.
8. 같은 기존 플레이어에서 `tiger-active-sentence`를 발행해 가로모드 그림·오른쪽 본문을 연결한다. 재생 모드마다 별도 본문·별도 오디오 객체를 만들지 않는다.

## 실행 순서

새 작업공간에서 의존성 잠금 파일을 설치하고 Whisper base 모델을 사전에 준비한다. 정렬기는 local_files_only=True이므로 모델이 없는 환경은 실패를 보고해야 한다. 운영 중 자동으로 다른 모델이나 API로 바꾸지 않는다.

```shell
python production/build_reading_html.py --input book.json --output story-reader
# 공급 ZIP은 START_HERE.md의 public-tiger/tts zip 입력 규약 사용
python production/run_pipeline.py
```

문제 진단 때만 단계를 나누어 실행한다. cache_guard.py가 입력/배역/gain/설정 변경을 검사하도록 유지한다.

```shell
python production/prepare_audiobook.py
python production/measure_new_clips.py
python production/bootstrap_speaker_levels.py
python production/normalize_clips.py
python production/whisper_force_align.py --chapter 1
python production/publish_audiobook.py
python production/install_offline_v2.py
python production/install_landscape_reader.py story-reader
python production/validate_reader_audio.py
python production/validate_audio_assets.py
```

중간 명령만 실행한 결과는 전체 파이프라인 통과로 보고하지 않는다. --limit는 진단용 일부 처리이며 전 장 완료가 아니다. 새 음원이 있으면 해당 장·캐시 의존 관계를 검사하고, 기존 타이밍을 파일명만 같다는 이유로 재사용하지 않는다.

## 시간 계산: 반드시 같은 기준 사용

구간 offset=12.0, trim_start=0.15, 단어 start=0.45/end=0.80이라면 단어가 강조되는 장 시간은 **12.30~12.65초**다.

```javascript
const segmentLocal = chapterCurrentTime - segment.offset;
const originalClipTime = segmentLocal + segment.trim_start;
const word = segment.words.find(w =>
  w.start !== null && originalClipTime >= w.start && originalClipTime < w.end);
```

같은 문단 안에서만 시작/끝 무음 경계를 브라우저 플레이어가 건너뛰도록 trim을 적용한다. 다른 문단 사이의 쉼은 유지한다. 단어 start/end 자체를 trim만큼 다시 이동해 저장하면 위 계산과 중복 보정되므로 금지한다. currentTime은 선택된 재생기의 장 타임라인 getter를 사용하고 HTMLAudioElement 클립 시간과 혼용하지 않는다. 속도 변경은 재생기 시간이 이미 반영하므로 시간에 playbackRate를 다시 곱하지 않는다.

timing.json의 핵심 구조:

```json
{"chapter":1,"duration":13.0,"segments":[{"src":"audio/ch01/clips/EXAMPLE.mp3","offset":12.0,"duration":1.0,"original_duration":1.2,"trim_start":0.15,"trim_end":1.15,"sentences":["p0001-s1"],"words":[{"sentence":"p0001-s1","word":0,"start":0.45,"end":0.80}],"timing_coverage":1.0}]}
```

위는 단일 구간 설명용 예시이며 전체 장 시작 offset은 0이어야 한다. 단어가 확인되지 않으면 start/end=null로 남긴다. 무음·빈 응답·낮은 신뢰 구간을 균등 분배로 채우지 않는다. 단어가 없는 순간에는 해당 구간의 문장 강조만 제공한다. 범위 밖 word_index나 존재하지 않는 sentence_id는 배포 실패다.

## 검증과 보고

포함된 재생 코드의 시간·강조 회귀 시험:

```shell
python scripts/verify_karaoke.py --browser-path CHROME_EXECUTABLE --report KARAOKE_REPORT.json
```

실제 audiobook.js를 사용하되 재생 시계만 제어해 trim 보정·단어 경계·null fallback·어휘 버튼 안 단어·속도 변경을 검사한다. 실제 Whisper 실행 기록은 `verification/WHISPER_PIPELINE_SMOKE_20261123.json`, DOM 강조 검사는 `verification/KARAOKE_BROWSER_REPORT.json`을 구별해서 본다.

- 본문·색인·word_map·배포 음원의 일치와 SHA, 누락·중복, 구간 offset 연속성, 양의 duration, 원음 범위 안의 단어 시간을 검사한다.
- 모든 장 첫/중간/마지막 구간, 단어 start 직전/정중앙/end 이후, null 타이밍, seek/이전·다음/속도 변경/가로·전체화면/백그라운드 복귀에서 강조를 확인한다.
- 문장 안 어휘 버튼이 여러 텍스트 노드로 나뉘어 있어도 단어 인덱스가 틀어지지 않아야 한다. 새 어휘 작업 후 DOM textContent 일치를 재검사한다.
- `python production/smoke_template.py`는 새 소스 ZIP에서 실제 Whisper를 실행하지만 기본 음원은 합성 톤이다. 모델 호출·파일 연결·null fallback의 증거이지 실제 발화 정확도의 증거가 아니다.
- 정확도는 실제 음성 샘플을 듣고 단어 경계를 사람 기준과 비교한다. 강제 정렬 통과만으로 누락 발화·오인 화자·다른 대사를 검증했다고 하지 않는다.
- 최종 보고는 자동 스키마/브라우저/실제 Whisper 실행/독립 ASR/사람 청취/실기기 각각의 실시 여부를 구분한다.
