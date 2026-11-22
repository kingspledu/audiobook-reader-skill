# 재현성 검증 결과

Same Windows/Python/Node/dependency/model environment; two separately unpacked clean project directories; 3 sample chapters and 5 artificial-tone clips per run

| 지표 | 결과 |
|---|---|
| 빈 프로젝트 실행 | 2/2 |
| CLI 단계 | 44/44 (100.00%) |
| 브라우저 검사 | 2/2 |
| 배포 소스 해시 | 36/36 |
| 두 실행의 출력 바이트 일치 | 70/72 (97.22%) |

출력 차이 파일: volume-1/audio/ch01/timing.json, volume-1/offline-manifest.json

위 수치는 같은 환경의 시험 데이터에 대한 관측값이며, 임의의 컴퓨터·책·휴대폰에서 100% 재현된다는 의미가 아닙니다. 실제 음성 타이밍 정확도·청취·휴대폰 잠금 재생·깨끗한 환경의 의존성 설치는 이 시험에서 검증하지 않았습니다.

읽기 HTML 생성이 최초 단계이며, 그 뒤에 MP3 매핑과 오디오 HTML 갱신을 수행했습니다.

차이 분석: Whisper 단어 시간 경계 2개가 달랐습니다. 최대 차이 0.02초입니다. 타이밍 변경이 offline-manifest.json 해시 변경으로 이어졌습니다. 동일한 정렬 결과를 고정하려면 검증한 aligned-chNN.json과 분석 버전·원본 해시를 함께 보관하고 그대로 재사용해야 합니다. 이 결과를 음성 인식 정확도로 해석하지 않습니다.
