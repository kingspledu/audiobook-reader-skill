# 동일 문단의 문장 간 컷 편집

목표는 같은 문단을 읽는 개별 문장 MP3 사이의 불필요한 무음을 줄여 자연스럽게 연결하는 것이다. 음성 파일을 합치거나 원문 발화를 잘라내는 효과가 아니다. 다른 문단 사이의 쉼과 장의 첫/마지막 바깥쪽 쉼은 유지한다.

## 구현 경로

1. `measure_new_clips.py`가 원음의 앞뒤 무음 경계를 측정한다. 경계에는 발화 손실을 줄이기 위한 여유가 있다. 화자별 일정한 gain은 normalize_clips.py에서 적용하며 원음 길이·무음은 편집하지 않는다.
2. `paragraph_cuts.py`는 word_map의 실제 경계 문단을 비교한다. 현재 클립의 첫 문단과 이전 클립의 마지막 문단이 같으면 시작 무음 경계를 사용한다. 현재 마지막 문단과 다음 첫 문단이 같으면 끝 무음 경계를 사용한다. 문단 ID는 sentence_id에서 마지막 `-s번호`를 제거한 값이다.
3. 다른 문단이면 시작=0 또는 끝=원음 길이로 두어 원래 쉼을 남긴다. 매핑이 불확실하면 잘라내지 않는다. 클립 하나가 여러 문단에 걸친 과거 자료도 양쪽 끝을 각각 판정한다. 클립 내부의 문단 간 쉼은 그대로다.
4. publish_audiobook.py가 trim_start/trim_end/duration/offset을 timing.json으로 내보낸다. MP3 바이트는 그대로이며, Whisper 단어 시간도 원음 기준으로 유지한다.
5. TigerClipPlayer가 Web Audio의 sample clock으로 다음 구간을 이전 구간 끝에 예약한다. 재생 offset은 trim_start+구간 내 시간이다. trim된 무음 끝에만 4ms 감쇠를 적용하며 발화를 겹치지 않는다. 다음 오디오 로딩 지연은 네트워크 부족으로 별도 취급한다.

예: 같은 문단 A→B, 다음 문단 C일 때 A의 뒤 무음과 B의 앞 무음만 줄인다. B의 뒤와 C의 앞은 원래 길이를 유지한다. 재생 속도 1.5배에서는 예약 시간에 속도를 반영하지만 저장 단어 시간을 다시 속도로 나누지 않는다.

## 정밀·호환 재생 차이

정밀 재생 TigerClipPlayer는 decoded buffer를 미리 예약한다. 호환 재생 TigerMediaPlayer는 같은 trim 정보를 사용하지만 HTMLAudioElement의 timeupdate/파일 전환 지연 때문에 sample 단위의 끊김 없는 전환을 보장하지 않는다. 잠금 화면 호환성과 문장 연결 정밀도는 별도 평가한다. 사용자에게 모든 모바일 환경에서 무음이 완전히 사라진다고 보고하지 않는다.

## 검증

```shell
python scripts/verify_paragraph_cuts.py
```

검사는 동일 문단 컷·다른 문단 원래 쉼·첫/마지막 경계·여러 문단에 걸친 기존 클립을 확인한다. 실제 clip-player.js의 pump()를 제어된 오디오 시계에서 실행해 구간 사이 추가 공백 없이 예약되는지, trim offset이 맞는지 확인한다. 모의 오디오 시계 검증이며 실제 청취가 아니다. 결과는 verification/PARAGRAPH_CUT_REPORT.json이다.

실제 발화 샘플에서는 연결 전후 음성을 들어 첫 자음·말끝 손실, 클릭음, 지나치게 급한 연결이 없는지 확인한다. 서로 다른 문단에 같은 컷을 적용하면 실패다. 단어 강조의 장 시간은 offset + 원음 단어 시간 − trim_start이므로 WHISPER_KARAOKE.md의 계산도 같이 검증한다.
