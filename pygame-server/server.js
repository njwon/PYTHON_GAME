const { WebSocketServer } = require('ws');
const { dispatch }        = require('./handlers');

const PORT = process.env.PORT || 3000;
const wss  = new WebSocketServer({ port: PORT });

wss.on('connection', (ws) => {
    console.log(`[+] 연결됨  (총 ${wss.clients.size}명)`);

    ws.on('message', (data) => dispatch(ws, data));

    ws.on('close', () => {
        console.log(`[-] 연결 종료  (총 ${wss.clients.size}명)`);
    });

    ws.on('error', (err) => {
        console.error('[!] 에러:', err.message);
    });
});

console.log(`WebSocket 서버 시작: ws://localhost:${PORT}`);
