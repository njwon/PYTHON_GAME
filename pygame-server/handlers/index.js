const CHARS              = require('../chars');
const { nextResponse, state, reset } = require('../game/state');

function handleChat(ws, msg) {
    const charId = msg.char_id;
    if (charId === undefined || !CHARS[charId]) {
        return send(ws, { type: 'error', msg: '유효하지 않은 char_id' });
    }
    const { msg: reply, delta, score } = nextResponse(charId);
    send(ws, { type: 'reply', char_id: charId, msg: reply, score_delta: delta, score });
}

function handleAccusation(ws, msg) {
    if (state.solved) {
        return send(ws, { type: 'result', correct: false, msg: '이미 종료된 게임입니다.' });
    }
    const correct = msg.char_id === 0; // 고경균 선생님이 범인
    state.solved  = correct;
    send(ws, { type: 'result', correct, char_id: msg.char_id });
}

function handleReset(ws) {
    reset();
    send(ws, { type: 'reset_ok' });
}

function handlePing(ws) {
    send(ws, { type: 'pong' });
}

// ── 라우터 ──────────────────────────────────────────────────
const handlers = {
    chat:       handleChat,
    accusation: handleAccusation,
    reset:      handleReset,
    ping:       handlePing,
};

function dispatch(ws, raw) {
    let msg;
    try {
        msg = JSON.parse(raw.toString());
    } catch {
        return send(ws, { type: 'error', msg: '잘못된 JSON 형식' });
    }

    const handler = handlers[msg.type];
    if (handler) {
        handler(ws, msg);
    } else {
        send(ws, { type: 'error', msg: `알 수 없는 type: ${msg.type}` });
    }
}

function send(ws, data) {
    if (ws.readyState === ws.OPEN) {
        ws.send(JSON.stringify(data));
    }
}

module.exports = { dispatch };
