const { CHARS, BASE_PROMPT, GAME_CONTEXT } = require('../chars');

const SUMMARY_TRIGGER = 16; // 히스토리가 이 개수 초과 시 요약

const state = {
    scores:    Object.fromEntries(CHARS.map((_, i) => [i, 50])),
    histories: Object.fromEntries(CHARS.map((_, i) => [i, []])),
    culpritId: Math.floor(Math.random() * CHARS.length),
    solved:    false,
};

// ── 단서 키워드 ─────────────────────────────────────────────────────────────
const CLUE_KEYWORDS   = ["17:12", "17:05", "17:45", "17:38", "링크", "ip", "218",
                          "서버실", "계정", "이직", "로그", "유출", "삭제", "도용",
                          "경쟁", "알리바이", "cctv", "네트워크", "db", "보안"];
const ACCUSE_KEYWORDS = ["왜", "어디", "언제", "했어", "맞죠", "아닌가요", "수상",
                          "이상", "거짓", "숨기", "범인", "증거", "확인", "아닌가"];

function calcBaseScore(userMsg) {
    const msg      = userMsg.toLowerCase();
    const hasClue  = CLUE_KEYWORDS.some(k => msg.includes(k));
    const hasAccuse = ACCUSE_KEYWORDS.some(k => msg.includes(k));

    if (hasClue && hasAccuse) return +7;
    if (hasClue)              return +3;
    return -3;
}

// Haiku로 맥락 검증 — 키워드는 있지만 실제 수사 질문이 아닌 경우를 걸러냄
async function checkContext(userMsg, client) {
    try {
        const res = await client.messages.create({
            model:      'claude-haiku-4-5-20251001',
            max_tokens: 5,
            system:     '아래 질문이 "IT 학교 서버 데이터 유출 사건 수사"와 직접 관련된 질문이면 yes, 아니면 no만 출력해. 다른 말은 하지 마.',
            messages:   [{ role: 'user', content: userMsg }],
        });
        return res.content[0].text.trim().toLowerCase().startsWith('y');
    } catch {
        return true; // 판단 실패 시 키워드 결과 그대로
    }
}

async function calcDelta(userMsg, client) {
    const base     = calcBaseScore(userMsg);
    const hasClue  = CLUE_KEYWORDS.some(k => userMsg.toLowerCase().includes(k));

    // 키워드가 없으면 AI 호출 없이 바로 반환
    if (!hasClue) return base;

    // 키워드 있을 때만 Haiku로 맥락 확인
    const relevant = await checkContext(userMsg, client);
    return relevant ? base : Math.max(-3, Math.floor(base * 0.15)); // 맥락 안 맞으면 크게 깎음
}

console.log(`[게임] 범인: ${CHARS[state.culpritId].name} (id: ${state.culpritId})`);

function buildSystemPrompt(charId) {
    const char       = CHARS[charId];
    const rolePrompt = charId === state.culpritId ? char.culpritPrompt : char.witnessPrompt;
    return `${GAME_CONTEXT}\n\n${BASE_PROMPT}\n\n${char.profile}\n\n${rolePrompt}`;
}

function applyScore(charId, delta) {
    state.scores[charId] = Math.max(0, Math.min(100, state.scores[charId] + delta));
}

async function _summarize(charId, client) {
    const history = state.histories[charId];
    if (history.length <= SUMMARY_TRIGGER) return;

    const toSummarize = history.slice(0, -4);
    const recent      = history.slice(-4);

    const res = await client.messages.create({
        model:      'claude-haiku-4-5-20251001',
        max_tokens: 300,
        messages:   [
            ...toSummarize,
            { role: 'user', content: '지금까지 대화를 3줄 이내로 요약해. 핵심 주장과 단서만 포함.' },
        ],
    });

    const summary = res.content[0].text;
    state.histories[charId] = [
        { role: 'user',      content: `[이전 대화 요약] ${summary}` },
        { role: 'assistant', content: '알겠습니다.' },
        ...recent,
    ];
}

async function getAIResponse(charId, userMsg, client) {
    const history = state.histories[charId];

    history.push({ role: 'user', content: userMsg });

    // AI 응답 + delta 계산 병렬 처리
    const [res, delta] = await Promise.all([
        client.messages.create({
            model:      'claude-sonnet-4-6',
            max_tokens: 120,
            system:     buildSystemPrompt(charId),
            messages:   history,
        }),
        calcDelta(userMsg, client),
    ]);

    const reply = res.content[0].text;
    history.push({ role: 'assistant', content: reply });

    applyScore(charId, delta);
    await _summarize(charId, client);

    return { reply, score: state.scores[charId], score_delta: delta };
}

function reset() {
    CHARS.forEach((_, i) => {
        state.scores[i]    = 50;
        state.histories[i] = [];
    });
    state.culpritId = Math.floor(Math.random() * CHARS.length);
    state.solved    = false;
    console.log(`[게임] 리셋 — 새 범인: ${CHARS[state.culpritId].name} (id: ${state.culpritId})`);
}

module.exports = { state, getAIResponse, applyScore, reset };
