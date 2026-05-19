import websocket
import json

def on_open(ws):
    print("연결됨!")
    # 채팅 메시지 테스트
    ws.send(json.dumps({"type": "chat", "char_id": 0}))

def on_message(ws, raw):
    data = json.loads(raw)
    print("서버:", data)

def on_error(ws, error):
    print("에러:", error)

def on_close(ws, code, msg):
    print("종료")

websocket.WebSocketApp(
    "ws://localhost:3000",
    on_open    = on_open,
    on_message = on_message,
    on_error   = on_error,
    on_close   = on_close,
).run_forever()
