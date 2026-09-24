# python-gcube-api-dashboard-piano

Roborisen **PingPong** 큐브 로봇을 제어하는 **Python PingPong API**와, 이를 이용한 **BLE 대시보드**·**웹 피아노**를 담은 저장소입니다.

## 원저작 및 되살린 내역 (Credits)

- **원 개발자: Yeseung Kim (@rhgkrsus1)** — Python PingPong API 원 코드베이스 (2019-12-30 ~ 2020-03-24, 82커밋). GitHub: <https://github.com/rhgkrsus1>
- 이 저장소는 위 코드베이스가 **약 6년 4개월간 갱신되지 않던 것을 되살린(maintained) 사본**이며, 원 커밋 이력을 그대로 보존했습니다.
- **되살림·추가 (2026-07-11, @fast1ine, 3커밋)**: 무선(BLE) 연결 지원, 웹 대시보드, 로봇의 실제 버저로 소리를 내는 웹 피아노.

## 하드웨어 출처

PingPong 로봇 하드웨어와 BLE 통신 프로토콜은 **Roborisen** 의 것입니다. 공식 사이트: <https://roborisen.com>
이 API는 해당 프로토콜에 맞춰 로봇을 제어합니다.

## 파생 프로젝트

이 코드베이스를 이용해 만든 휠체어·우산 시스템: <https://github.com/fast1ine/gcube-wheelchair-umbrella>

## 라이선스

**GNU GPLv3** — 원 코드베이스(Yeseung Kim)의 라이선스를 그대로 따릅니다. 자세한 내용은 [`LICENSE`](LICENSE)를 참조하세요.

- 원 Python PingPong API © Yeseung Kim (@rhgkrsus1)
- 2026년 추가분(BLE 대시보드·웹 피아노) © 2026 fast1ine
