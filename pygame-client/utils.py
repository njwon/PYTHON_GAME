import time as _time
from PyQt6.QtGui import QFont
from config import FS


def _break_words(text: str, n: int = 13) -> str:
    """공백 없는 긴 단어에 제로폭 공백을 삽입해 Qt 줄바꿈이 작동하게 함."""
    parts = []
    for word in text.split(' '):
        if len(word) > n:
            word = '​'.join(word[i:i+n] for i in range(0, len(word), n))
        parts.append(word)
    return ' '.join(parts)


def F(size_key: str, bold: bool = False) -> QFont:
    f = QFont("맑은 고딕", FS[size_key])
    f.setBold(bold)
    return f


def now() -> str:
    t = _time.localtime()
    ap = "오전" if t.tm_hour < 12 else "오후"
    return f"{ap} {t.tm_hour % 12 or 12}:{t.tm_min:02d}"
