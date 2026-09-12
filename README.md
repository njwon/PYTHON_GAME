# PYTHON_GAME

Python과 pygame으로 만든 **WebSocket 기반 멀티플레이 게임**입니다.
클라이언트와 서버로 분리되어 실시간 통신으로 동작합니다.

## 구성
- `pygame-client/` — pygame 게임 클라이언트 (화면 전환·UI 위젯·방탈출 로직)
- `pygame-server/` — WebSocket 게임 서버
- `websocket-guide.html` — WebSocket 학습 정리 문서

## 실행
```bash
# 의존성 설치
./setup.sh          # Windows: setup.ps1

# 서버 실행 (Windows: run-server.ps1)
# 클라이언트 실행
python pygame-client/main.py
```

## 배운 것
- 클라이언트–서버 실시간 통신 (WebSocket)
- pygame 화면 전환·이벤트 처리·UI 위젯 구현


---
Made by [노정원 (njwon)](https://njw.kro.kr)
