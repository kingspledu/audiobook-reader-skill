# 책별 리소스와 독서 기능 입력

생성기는 원문·단어·이미지·배역을 저절로 확보하지 않는다. 실제 책 콘텐츠는 사용자 제공 자료로 별도 프로젝트에 보관하고 재사용 스킬에 넣지 않는다.

`book.json`은 book_id/title/language/chapters/vocabulary/characters를 사용한다. vocabulary는 `term`, `meaning`, 선택적인 `sentenceMeaning`을 가진다. 문맥별 뜻이 다르면 매칭 규칙을 장·문장 ID로 확장하고 실제 문맥을 검토한다. 현재 기본 생성기는 문장당 첫 일치 어휘 하나를 버튼으로 만든다. 전 장의 버튼 수·어휘 0개 장·설명 없는 긴 문단을 검사하고 필요한 항목을 추가한다. 자동 사전 매칭을 문맥 검토 완료로 보고하지 않는다.

캐릭터 입력 예:

```json
"characters": [{
  "name": "인물 이름",
  "description": "원문에서 확인한 외형·나이·관계와 근거",
  "visual_notes": "제작 과정에서 승인한 머리·옷·색상·외형 기준",
  "sheets": ["assets/character-approved.png"]
}]
```

`build_reading_html.py`가 characters/index.html과 각 권의 링크를 만든다. 이미지는 입력 파일 기준 상대 경로 또는 --assets 경로 안에 있어야 한다. 미생성 시트를 승인된 시트처럼 채우지 않는다. 단독 재생성은 `python production/build_character_sheets.py --input book.json --output story-reader/characters`를 쓴다. 현재 권별 오프라인 다운로드는 **읽기 본문·삽화·오디오** 대상이며 별도 characters 페이지의 오프라인 배포는 추가 SW scope 설계가 필요하다. 링크 생성만으로 오프라인 제공 완료라고 하지 않는다.

슬라이드형 어휘 카드는 원래 문장 바로 뒤에서 펼쳐지고 뜻·선택적 문장 해석·닫기 버튼을 제공한다. 새 카드가 열리면 이전 카드는 제거되며 Escape로 닫고 원래 버튼에 포커스를 돌린다. reduced-motion에서는 펼침 효과를 생략한다. 현재 닫기는 즉시 제거이며 공개 사이트의 닫힘 애니메이션까지 동일하다는 의미는 아니다.

독서 진행선은 기본 화면에서는 문서 스크롤, 분할 화면에서는 오른쪽 본문 스크롤 비율이다. 문단 위치는 reader-position:storyId에 저장하고 이어 읽기 링크로 복원한다. 오디오 재생 시간 저장과 별도다. 본문 ID가 바뀌면 예전 위치는 유효한 문단인지 검사한다.

언어·권수 확장: 현재 생성기는 1~29장/3권, 오디오 파이프라인은 영어 tokenizer·권 매핑을 사용한다. 이를 범용이라고 보고하지 않는다. 다른 책은 build_reading_html/prepare_audiobook/publish_audiobook/install_offline_v2/install_landscape_reader/build_landscape_test의 장·권 순회, UI 링크와 언어 토큰 규칙을 함께 바꾼다. 먼저 작은 fixture로 본문 보존·매핑·Whisper·강조·오프라인·모드 전환을 검증한다. 음성 언어만 바꾸는 것으로 다국어 단어 강조를 지원했다고 하지 않는다.

실기기 확인 항목: Android Chrome과 iOS Safari에서 재생 시작, 가로/세로, 전체화면 또는 홈 화면 설치, 잠금 후 재생 지속, 잠금 화면 미디어 위젯, 이어폰 조작, 오프라인 재접속, 캐시 삭제 범위, 저장 공간 부족, 복귀 후 강조 동기화를 확인한다. 기기가 없으면 미실시로 남긴다.

반복 가능한 신규 기능 시험:

```shell
python scripts/verify_reader_features.py --browser-path CHROME_EXECUTABLE --report READER_FEATURES_REPORT.json
```
