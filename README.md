# audiobook-reader skill

원문 → 읽기 HTML → Gemini Canvas TTS HTML → 개별 MP3 → Whisper 시간 연결 → 가로·오프라인 읽기 사이트 제작 자료와 실행 소스입니다.

Codex에서 이 저장소를 스킬 폴더 `audiobook-reader`로 설치하고 `$audiobook-reader`로 호출합니다. 스킬 폴더에는 책 파일을 생성하지 않습니다.

```shell
python scripts/validate_package.py
python scripts/init_workspace.py --out /path/to/new-project
```

- [스킬 지침](SKILL.md)
- [처음부터 실행하기](references/START_HERE.md)
- [전체 재현 매뉴얼](references/AUDIOBOOK_READER_TEMPLATE_KO.md)
- [TTS HTML 생성 지침](assets/gemini-canvas-tts/SKILL.md)
- [실제 검증·미완료 범위](references/IMPROVEMENT_EXECUTION_REPORT_KO.md)

실제 책·오디오·삽화는 포함하지 않습니다. 공개된 예제는 작은 자체 예제입니다. Canvas 호스트의 실제 음성 생성 지원과 Android/iPhone 잠금 재생은 별도로 확인해야 합니다. 현재 읽기 실행 소스는 영어·3권·29장 프로필이며 완전한 범용/무인 생성 서비스가 아닙니다.

읽기 생성기·HTML/CSS/JS 원본은 [assets/reader-pipeline/production](assets/reader-pipeline/production)에 펼쳐져 있으며, 동일 내용의 ZIP도 제공합니다. TTS 생성 소스는 [assets/gemini-canvas-tts](assets/gemini-canvas-tts)에 있습니다. `CONTENT_MANIFEST.json`으로 전체 포함 파일의 해시를 검증합니다.
# TTS 코드 복사 사이트

TTS 제작은 장별 HTML뿐 아니라 `output/code-copy/` 웹사이트를 함께 만듭니다. [제작·배포·검증 절차](references/TTS_CODE_COPY_SITE.md)를 따르세요. 사이트가 복사하는 HTML과 스킬은 같은 템플릿·렌더러를 사용하며, 파일 크기·SHA-256과 실제 브라우저 클립보드를 검증합니다.

