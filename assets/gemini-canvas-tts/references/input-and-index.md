# 입력과 파일명

`assets/example-book.json`을 복사해 작품 정보를 바꾼다. JSON은 UTF-8이다. 파이썬·PowerShell 출력 파이프로 한글을 재인코딩하지 말고 파일 API로 UTF-8을 명시한다. 물음표로 저장되지 않았는지 실제 파일을 읽어 확인한다.

## 필드

| 위치 | 필드 | 의미 |
|---|---|---|
| 작품 | title, prefix | 표시 제목과 파일용 고유 접두사 |
| 작품 | revision | V01 같은 명시적 음성 버전. 내용·배역이 크게 바뀌면 새 버전 |
| 작품 | model, language | 모델 ID, ko-KR 등 낭독 언어 |
| cast | 배역 ID | name, voice, persona. 여러 장에서 동일 ID/voice/persona 사용 |
| chapters | number, title | 양의 장 번호와 제목 |
| segments | text | 실제 낭독할 본문. 메타정보와 연기 지시를 삽입하지 않음 |
| segments | cast_id | cast의 배역 ID. 누락·오타는 실패 |
| segments | kind | narration / dialogue / monologue |
| segments | scene_id | 장면 앵커 또는 안정된 장면 ID |
| segments | performance | emotion, intensity(0–1), pace, delivery, pause_after_ms, character_state, acting_notes, mic_direction, nonverbal 등 선택 보정 |

prefix/revision/cast_id/scene_id는 1–64자의 영문·숫자·밑줄·하이픈으로 만든다. 한국어 표시는 title/name/text에 둔다. 파일 경로나 슬래시를 ID에 넣지 않는다.

`character_persona`는 cast에서 가져오고 `audio_effect`는 kind에서 결정하므로 개별 구간이 이를 덮어쓰지 못한다. 같은 화자의 대사와 독백은 같은 voice를 쓴다.

## 파일 패턴

```text
MYBOOK_C01_V01_GEMINI_CANVAS_TTS.html
MYBOOK_C01_V01_SCRIPT.json
MYBOOK_AUDIO_INDEX_V01.json
MYBOOK_AUDIO_INDEX_V01.csv
MYBOOK_C01_V01_0000_scene01_NARRATOR.wav
MYBOOK_C01_V01_0001_scene01_HERO.wav
MYBOOK_C01_V01_FULL.mp3
MYBOOK_C01_V01_RETRY.json
```

구간 순번은 장마다 0000부터 시작한다. 파일명은 생성기에서 한 번 만들고 개별 생성·전체 생성·검사·재시도·합치기에 동일하게 사용한다. 색인에는 chapter/order/scene_id/segment_id/speaker/kind/cast_id/filename/voice/model/cast_revision/text_sha256/text가 들어간다. CSV는 Excel 호환 UTF-8 BOM이다.

`*_SCRIPT.json`은 HTML 안 `originalEpisode`와 완전히 같아야 한다. 장문은 발화 단위로 적절히 나누되, 문단을 버리거나 중간을 요약하지 않는다. TXT 간편 모드는 모든 글을 나레이션으로 보존한다. 대사 화자를 자동 추측하지 않는다. 너무 긴 단일 문단은 JSON으로 분할하고 원래 문자들을 이어 붙였을 때 동일한지 검증한다.


## 문장별 음성 제작 필수 규칙

한 문장 = 한 생성 요청 = 한 개별 WAV/MP3다. 문단 전체나 배우가 이어 읽을 여러 문장을 한 요청으로 묶지 않는다. 배포 ZIP은 개별 문장 MP3를 유지한다. 합본은 선택적 청취 파생물이며 문장 파일을 대체하지 않는다.

각 segment는 sentence_id, paragraph_id, context_before/context_after(문장 ID 배열), 문장별 performance.sentence_persona, performance.design을 가진다. 기본 배역 페르소나는 유지하되 해당 문장의 상대·목적·현재 감정을 별도로 적용한다. 같은 문단의 분위기·호흡을 이어 주며 분리 생성한다.

앞뒤의 ‘울부짖었다·웃었다·울었다’ 같은 묘사를 읽고 누구의 어느 발화에 적용되는지 찾는다. performance.cue_links에 source_sentence_id, target_sentence_id, cue_text, instruction을 기록한다. 해당 단서가 없으면 빈 배열로 명시한다. 단서가 다른 인물/시점이면 억지로 적용하지 않는다. 웃음·울음의 강도·위치는 근거에 맞추며 기계적으로 덧붙이지 않는다.

검토는 speaker_pass, cue_pass, continuity_pass의 세 항목으로 각각 기록한다. review.evidence와 review.sentence_boundary_evidence에는 실제 문맥·분할 근거를 적는다. 생성기나 정규식이 검토를 confirmed로 자동 변경해서는 안 된다. 화자가 애매하면 review.attribution=user_review_required로 두고 질문 대상 문장·앞뒤 문맥·후보·판단 근거를 사용자에게 제시한다. 승인 전 그 문장은 생성 차단한다. 나레이터로 임의 대체하지 않는다.

문장 분할 시 인용부호·약어·소수·말줄임표·감탄사에 주의한다. 문장 경계의 자동 탐지는 보조 검사일 뿐 의미 검토가 아니다. 기존 문단의 문자 범위와 문장 순서를 유지하며 누락·중복을 대조한다. 이전 문단형 대본은 신규 문장 검토 전까지 생성 불가 초안이다.
