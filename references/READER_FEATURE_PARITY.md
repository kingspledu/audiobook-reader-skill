# 공개 읽기 사이트 대비 스킬 기능 검토

2026-11-23 기준. 비교 대상은 기존 타이거 읽기 사이트의 volume-1~3과 스킬의 펼친 reader-pipeline·동일 소스 ZIP이다. 책 자체의 원문·어휘 2,637개·삽화·음성은 재사용 스킬에 넣지 않는다. 기능 소스 포함과 같은 책 콘텐츠 포함을 구별한다.

| 기능 | 스킬 대응 | 검토 결과/제한 |
|---|---|---|
| 전체 본문·문단·문장 ID | build_reading_html.py, reader-template | 포함. 현재 3권/영어 프로필 고정값 조정 필요 |
| 삽화 먼저·뒤에 대응 본문 | book.json paragraph.image → figure → story-text | 포함. 시각적 인물 일관성은 별도 삽화 작업 |
| 클릭 어휘 뜻 | reader-template/app.js, vocabulary 입력 | 슬라이드 펼침·뜻·문장 해석·닫기/Escape·포커스 복원 포함. 닫힘 효과 등 세부 디자인은 다름 |
| 어휘 밀도·빠진 장 점검 | 입력 원고 검토와 별도 검증 | 기존 책에 추가한 실제 어휘 목록은 미포함. 새 책은 문맥 검토 후 새로 작성 |
| 테마·글자·목차·설정 저장 | reader-template/app.js/css | 포함. 글자 CSS 변수를 가로모드와 호환하도록 보완 |
| 개별 MP3·화자별 음량 | normalize_clips.py | 포함. 클립 병합하지 않음 |
| 문단 내부 점프컷·문단 사이 쉼 | publish_audiobook.py, clip-player.js | 포함. 단어 원음 시간과 trim 기준 구별 |
| Whisper 단어 시간 | whisper_force_align.py | 포함. 상세 계약은 WHISPER_KARAOKE.md |
| 노래방 단어/문장 강조 | audiobook.js/css | 포함. 근거 없는 단어는 문장 fallback |
| 장 선택·탐색·속도·재시도·복원 | audiobook.js, 두 player | 포함. 다음 권 URL 이동은 목차 링크로 수행 |
| 잠금 화면 위젯 | Media Session | 포함. OS 노출·지속 재생 실기기 보장 아님 |
| 오프라인 전 권/오디오 저장·삭제 | offline-v2.js, install_offline_v2.py | 포함. 실제 기기 용량·중단 상태 검사 필요 |
| 가로모드·태블릿·수동 버튼 | landscape-reader.js/css, installer | 포함. 공개 사이트와 같은 공통 소스 |
| 전체화면·미지원 설치 안내 | 공통 모듈+PWA 안내 | 공통 모듈 포함. 최소 생성 템플릿의 누락된 설치 안내도 보완 |
| PWA manifest·아이콘·SW | build_reading_html.py, offline installer | 포함. 설치 완료·백그라운드 청취 별도 검증 |
| 읽기 위치 재개·상단 독서 진행선 | reader-template/app.js | 문단 저장·이어 읽기 링크·문서/가로 pane 진행선 포함. 오디오 위치 저장과 별도 |
| 캐릭터 시트 공개 페이지 | characters 입력, build_character_sheets.py | 승인된 시트·원문 근거로 생성, 각 권 링크 포함. 이미지 생성 자체와 별도 페이지 오프라인 캐시는 자동 제공하지 않음 |
| 코드 복사·문장별 TTS·MP3 ZIP | gemini-canvas-tts | 포함. 읽기 화면과 별도 생성 도구 |

이 검토는 기능별 대응표이며 모든 UI가 완전히 동일하다는 선언이 아니다. 표의 미포함/간소화 항목을 요구받으면 실제 코드·입력 스키마·검증을 추가하고 소스 ZIP도 재생성한다. 운영 사이트의 책 콘텐츠를 스킬에 복사해서 동등성을 맞추지 않는다.

2026-11-23 통합 보완: 이전 보고의 독서 UI와 캐릭터 페이지 생성기를 포함했다. 상세 입력·기기 확인·언어/권수 확장 범위는 READER_RESOURCES.md를 따른다. 실제 책 리소스·사람 청취·실물 기기 시험은 계속 별도이며, 문서 추가로 완료 처리하지 않는다.
