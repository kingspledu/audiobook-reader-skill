# 처음부터 제작하는 순서

## 1. 독립 작업공간

스킬 루트에서 `python scripts/init_workspace.py --out 새폴더`를 실행합니다. 비어 있지 않은 폴더에는 덮어쓰지 않습니다. 작업공간에 production/, docs/, tts/가 생깁니다.

`docs/requirements-audiobook-full-lock.txt`로 Python 가상환경을 구성하고, Node.js·Git·Whisper base 모델을 준비합니다. 상세 단계는 [매뉴얼](AUDIOBOOK_READER_TEMPLATE_KO.md)에 있습니다. 상대경로가 다른 테스트 환경은 Playwright 경로를 설치 위치에 맞춥니다.

## 2. 읽기 HTML을 먼저 생성

`production/reader-template/book.sample.json`을 book.json으로 복사해 원문·장·문단·문장을 채웁니다. 그림 경로는 문단의 image와 alt에 지정합니다.

```shell
python production/build_reading_html.py --input book.json --output story-reader
```

본문 문자열과 순서, 문장 ID, 문단 ID를 검토하고 초기 Git 기준 커밋을 만듭니다. 기존 사이트가 있다면 이 단계는 검증으로 대체합니다.

## 3. TTS HTML 생성

```shell
python tts/scripts/build.py tts/assets/example-book.json --out output
node tts/scripts/verify.cjs output
python tts/scripts/self_test.py
```

실제 책의 원문과 배역별 voice/persona, 나레이션·대사·독백, 문장별 연기 지침을 예제 스키마에 맞게 작성합니다. 원문 누락·중복·미확정 화자는 해결해야 합니다. 생성 HTML을 Gemini Canvas에 올려 사용자 세션에서 실행합니다. 키 입력 UI나 외부 API로 우회하지 않습니다. 모델/호스트가 음성을 반환하지 않으면 생성 성공으로 표시하지 않습니다.

## 4. TTS 결과를 읽기 입력으로 연결

TTS HTML 출력과 읽기 입력 ZIP은 서로 다른 계약입니다. 자동으로 같은 색인이라 가정하지 않습니다. TTS 색인에 기록된 filename/text/order/speaker를 기준으로 완성된 오디오를 정리합니다. 구간 하나당 파일 하나를 유지합니다.

Canvas가 WAV를 반환하면 FFmpeg로 **파일별로** 변환합니다.

```shell
ffmpeg -i segment.wav -c:a libmp3lame -b:a 192k segment.mp3
```

MP3 색인을 읽기 파이프라인의 `mp3-zip-index-1` 규격으로 작성합니다. 장별 ZIP 안에 MP3들과 `_INDEX.json`을 넣습니다. [정확한 스키마](AUDIOBOOK_READER_TEMPLATE_KO.md)의 `chapter`, `complete`, `missing`, `segments`와 `order`, `filename`, `speaker`, `text`를 빠짐없이 채웁니다. WAV 이름을 MP3로 바꾸면서 본문 지문과 순서를 보존합니다. 합쳐진 오디오만 있으면 구간별 MP3가 확보되기 전 이 파이프라인에 투입하지 않습니다.

현재 입력 폴더는 `public-tiger/tts zip/`입니다. 새 책에 쓰려면 코드와 문서의 경로를 함께 조정하거나 이 호환 폴더를 사용합니다. 이름이 Tiger여도 다른 책의 원문을 가져오는 기능은 없습니다.

## 5. 연결·검증

포함된 연결 스크립트를 사용하면 Canvas 생성기의 `audio-index-1` 색인과 구간별 WAV/MP3를 읽기 입력 ZIP으로 변환할 수 있습니다. 이 명령은 스킬 루트에서 실행합니다. MP3를 이미 준비했다면 WAV 이름과 같은 stem의 MP3도 찾습니다. 누락 파일·대본 해시 불일치·중복 순서는 실패 처리하고 기존 출력 ZIP은 덮어쓰지 않습니다.

```shell
python scripts/package_tts_audio.py --index /project/output/BOOK_AUDIO_INDEX_V01.json --audio-dir /project/downloaded-audio --out /project/public-tiger/tts\ zip
```

위 공백 경로는 셸에 맞게 따옴표로 감싸는 것이 안전합니다. PowerShell에서는 `--out "C:\project\public-tiger\tts zip"`처럼 지정합니다. 색인에는 없는 임의 파일을 정렬해서 끼워 넣지 않습니다.

```shell
python production/run_pipeline.py
python production/validate_reader_audio.py
python production/smoke_template.py
```

run_pipeline은 음량 기준 생성, 입력 변경 감지, 정렬, HTML 갱신, 가로모드와 오프라인 manifest를 생성합니다. smoke_template은 별도 임시 프로젝트에서 실행하며 실제 책을 덮어쓰지 않습니다. 강제 정렬은 독립적인 대본 정확도 검증이 아닙니다.

## 6. 배포

최종 산출물을 검사한 후 명시된 공개 사이트만 GitHub Pages 등에 배포합니다. 문서·스킬 공개는 실제 소설 원문·삽화·음성을 자동으로 공개할 권한을 뜻하지 않습니다. 해당 책 자료의 공개 범위를 따릅니다. 모델에서 소리가 나왔는지, 직접 들었는지, 실기기에서 검사했는지는 각각 구분해서 보고합니다.
