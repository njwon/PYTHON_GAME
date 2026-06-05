# ws_client.py ── WebSocket 클라이언트 (서버와 실시간 통신) ─────────────────────
import json                              # 딕셔너리 ↔ JSON 문자열 변환
import threading                         # 백그라운드 스레드로 WebSocket 실행
import websocket                         # websocket-client 라이브러리
from PyQt6.QtCore import QObject, pyqtSignal   # Qt 시그널 기반 클래스

WS_URL = "ws://localhost:3000"   # 연결할 WebSocket 서버 주소


class WSClient(QObject):
    # 서버에서 메시지가 오면 이 시그널이 발생 → PhoneWindow._on_ws가 받아 처리
    message_received = pyqtSignal(dict)   # 페이로드: 파싱된 dict

    def __init__(self):
        super().__init__()

        # WebSocket 앱 객체 생성 — 각 이벤트마다 람다로 콜백 등록
        self._ws = websocket.WebSocketApp(
            WS_URL,
            on_message = lambda ws, m: self.message_received.emit(json.loads(m)),
            # 메시지 수신 → JSON 파싱 후 Qt 시그널로 방출 (UI 스레드로 전달됨)
            on_error   = lambda ws, e: print("[WS] 에러:", e),    # 에러 발생 시 콘솔 출력
            on_open    = lambda ws:    print("[WS] 연결됨"),       # 연결 성공 시 출력
            on_close   = lambda ws, c, m: print("[WS] 종료"),      # 연결 끊김 시 출력
        )

        # WebSocket 루프를 별도 스레드에서 실행 (메인 UI 스레드 블로킹 방지)
        t = threading.Thread(
            target=self._ws.run_forever,
            kwargs={"reconnect": 5},   # 연결 끊기면 5초 후 자동 재연결
        )
        t.daemon = True   # 메인 프로그램 종료 시 이 스레드도 같이 종료
        t.start()          # 스레드 시작

    def send(self, data: dict):
        # 딕셔너리를 JSON 문자열로 변환해 서버로 전송
        try:
            self._ws.send(json.dumps(data))
        except Exception as e:
            print("[WS] 전송 실패:", e)   # 전송 실패 시 콘솔에 오류 출력
