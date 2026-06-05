const Anthropic                       = require('@anthropic-ai/sdk');
const { CHARS }                       = require('../chars');
const { state, getAIResponse, reset } = require('../game/state');
const fs   = require('fs');
const path = require('path');

const client    = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const RANK_FILE = path.join(__dirname, '..', 'rankings.json');
const MAC_FILE  = path.join(__dirname, '..', 'played_macs.json');

function loadRankings() {
    try { return JSON.parse(fs.readFileSync(RANK_FILE, 'utf-8')); } catch { return []; }
}

function saveRanking(name, time) {
    const ranks = loadRankings();
    ranks.push({ name, time, date: new Date().toISOString().slice(0, 10) });
    ranks.sort((a, b) => a.time - b.time);
    fs.writeFileSync(RANK_FILE, JSON.stringify(ranks.slice(0, 10), null, 2), 'utf-8');
}

function loadMacs() {
    try { return JSON.parse(fs.readFileSync(MAC_FILE, 'utf-8')); } catch { return []; }
}


async function handleChat(ws, msg) {
    const charId  = msg.char_id;
    const userMsg = (msg.msg || '').trim();

    if (charId === undefined || !CHARS[charId]) {
        return send(ws, { type: 'error', msg: '유효하지 않은 char_id' });
    }
    if (!userMsg) {
        return send(ws, { type: 'error', msg: '메시지가 비어있습니다.' });
    }

    try {
        const { reply, score, score_delta } = await getAIResponse(charId, userMsg, client);
        send(ws, { type: 'reply', char_id: charId, msg: reply, score, score_delta });
    } catch (err) {
        console.error('[AI] 오류:', err.message);
        send(ws, { type: 'error', msg: 'AI 응답 오류가 발생했습니다.' });
    }
}

function handleAccusation(ws, msg) {
    if (state.solved) {
        return send(ws, { type: 'result', correct: false, msg: '이미 종료된 게임입니다.' });
    }
    const correct  = msg.char_id === state.culpritId;
    state.solved   = correct;
    send(ws, { type: 'result', correct, char_id: msg.char_id, culprit_id: state.culpritId });
}

function handleReset(ws) {
    reset();
    send(ws, { type: 'reset_ok' });
}

function handlePing(ws) {
    send(ws, { type: 'pong' });
}

function handleRankingSave(ws, msg) {
    const { name, time, mac } = msg;
    if (!name || typeof time !== 'number' || !mac) return;
    const macs = loadMacs();
    if (macs.includes(mac)) return send(ws, { type: 'ranking_saved', accepted: false });
    macs.push(mac);
    fs.writeFileSync(MAC_FILE, JSON.stringify(macs, null, 2));
    saveRanking(name.slice(0, 20), Math.floor(time));
    send(ws, { type: 'ranking_saved', accepted: true });
}

function handleRankingGet(ws) {
    send(ws, { type: 'ranking_data', rankings: loadRankings() });
}

// ── 라우터 ──────────────────────────────────────────────────────────────────
const handlers = {
    chat:         handleChat,
    accusation:   handleAccusation,
    reset:        handleReset,
    ping:         handlePing,
    ranking_save: handleRankingSave,
    ranking_get:  handleRankingGet,
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
