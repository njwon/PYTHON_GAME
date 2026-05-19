const CHARS = require('../chars');

const state = {
    scores:    Object.fromEntries(CHARS.map((_, i) => [i, 50])),
    respIndex: Object.fromEntries(CHARS.map((_, i) => [i, 0])),
    solved:    false,
};

function applyScore(charId, delta) {
    state.scores[charId] = Math.max(0, Math.min(100, state.scores[charId] + delta));
}

function nextResponse(charId) {
    const char  = CHARS[charId];
    const idx   = state.respIndex[charId];
    const [msg, delta] = char.responses[idx];
    state.respIndex[charId] = (idx + 1) % char.responses.length;
    applyScore(charId, delta);
    return { msg, delta, score: state.scores[charId] };
}

function reset() {
    CHARS.forEach((_, i) => {
        state.scores[i]    = 50;
        state.respIndex[i] = 0;
    });
    state.solved = false;
}

module.exports = { state, nextResponse, reset };
