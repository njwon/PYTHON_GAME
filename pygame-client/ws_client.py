import json
import threading
import websocket
from PyQt6.QtCore import QObject, pyqtSignal

WS_URL = "ws://localhost:3000"

class WSClient(QObject):
    message_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._ws = websocket.WebSocketApp(
            WS_URL,
            on_message = lambda ws, m: self.message_received.emit(json.loads(m)),
            on_error   = lambda ws, e: print("[WS] 에러:", e),
            on_open    = lambda ws:    print("[WS] 연결됨"),
            on_close   = lambda ws, c, m: print("[WS] 종료"),
        )
        t = threading.Thread(
            target=self._ws.run_forever,
            kwargs={"reconnect": 5},
        )
        t.daemon = True
        t.start()

    def send(self, data: dict):
        try:
            self._ws.send(json.dumps(data))
        except Exception as e:
            print("[WS] 전송 실패:", e)
