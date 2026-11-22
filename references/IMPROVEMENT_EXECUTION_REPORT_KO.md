# 보완 실행·검증 결과

2026-11-22. 이 작업은 제작 템플릿과 별도 시험 프로젝트에서 실행했다. 기존 공개 책의 캐시·오디오를 초기화하거나 실험 결과를 공개 배포하지 않았다.

## 구현

1. 읽기 HTML을 최초 생성한 뒤 오디오를 처리하는 `run_pipeline.py` 단일 명령 추가.
2. `cache_guard.py`로 음성 바이트·대본·화자·순서·분석 코드·gain·Whisper 엔진/모델 해시를 비교.
3. 변경 파일과 해당 장 정렬 캐시를 백업하고, 무관한 장은 재사용.
4. 기본 의존성과 전이 의존성 27개를 현재 Windows/Python 3.12용으로 고정.
5. 실제 제공 TTS 5개를 별도 로컬 fixture로 사용하는 스모크 옵션 추가. 책 음성은 배포 ZIP에 포함하지 않음.

## 검증 근거

| 검사 | 결과 | 근거 파일 |
|---|---|---|
| 시스템 패키지 미공유 새 venv에 27개 설치 | PASS | FRESH_ENVIRONMENT_REPORT.json |
| pip check | 충돌 없음 | FRESH_ENVIRONMENT_REPORT.json |
| 새 venv 인공 톤 5개 전체 파이프라인 | PASS | SMOKE_TEST_REPORT.json |
| 새 venv 실제 TTS 5개 전체 파이프라인 | PASS | REAL_SPEECH_SMOKE_REPORT.json |
| 브라우저 기본 HTML·오디오 강조·가로모드 | PASS, JS 예외 0 | SMOKE_BROWSER_REPORT.json |
| 캐시를 재사용한 재실행의 출력 일치 | PASS | CACHE_PIPELINE_REPORT.json |
| 같은 이름의 수정 MP3 감지·추출 | PASS | CACHE_PIPELINE_REPORT.json |
| 대본만 변경한 장의 정렬 무효화 | PASS | CACHE_PIPELINE_REPORT.json |
| 정렬 코드/설정 변경 감지 | PASS: 시험 3개 장 무효화 | CACHE_PIPELINE_REPORT.json |

실제 TTS 표본은 원문 단어 53개 중 46개에 시간 연결이 생성됐다. 이는 연결률이며 사람이 표시한 기준 타이밍과 비교한 정확도가 아니다. 정렬 캐시 재사용은 결과를 고정하지만, Whisper 자체를 새로 분석할 때 바이트 단위 결정성을 보장하지 않는다.

새 가상환경도 같은 Windows PC와 기존 모델 다운로드 캐시를 사용했다. 다른 OS나 처음부터의 모델 다운로드는 검증 범위가 아니다. 브라우저 검사는 기존 Node/Chrome 설치를 사용했다.

## 남은 작업: 완료로 표시하지 않을 항목

- 실제 음성의 사람 기준 단어 타임스탬프 작성과 오차 측정, 실제 청취.
- Android/iPhone 실기기 화면 잠금 30분·장 전환·Bluetooth·전화 중단 시험.
- 가로모드의 명시적 scene ID 매핑과 단어 뜻 기능 이식.
- 가로모드 전체 오프라인 범위 확장, 용량 부족·브라우저 회수·중단 후 복구의 광범위 시험.
- 다른 운영체제/기기/처음 다운로드하는 모델 환경에서의 재현 시험.

위 항목은 이번 자동화 결과로 대체하지 않는다. 실제 장면 생성이나 네이티브 앱 개발을 수행한 것도 아니다.
