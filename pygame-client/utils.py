# utils.py ── 여러 파일에서 공통으로 쓰는 유틸리티 함수 ────────────────────────
import time as _time          # 현재 시각 가져오기용 (내장 time 모듈, 이름 충돌 방지로 _time)
from PyQt6.QtGui import QFont  # Qt 폰트 객체
from config import FS          # 폰트 크기 딕셔너리 (config.py에서 가져옴)


def _break_words(text: str, n: int = 13) -> str:
    """
    공백 없는 긴 단어(영어 단어, URL 등)에 제로폭 공백(​)을 삽입해
    Qt의 자동 줄바꿈이 제대로 동작하게 만드는 함수.
    n글자마다 끊음 (기본 13자).
    """
    parts = []
    for word in text.split(' '):            # 공백 기준으로 단어 분리
        if len(word) > n:
            # n글자씩 잘라서 사이에 제로폭 공백 삽입
            word = '​'.join(word[i:i+n] for i in range(0, len(word), n))
        parts.append(word)
    return ' '.join(parts)                  # 다시 공백으로 합쳐서 반환


def F(size_key: str, bold: bool = False) -> QFont:
    """
    폰트 객체를 만들어 반환하는 단축 함수.
    size_key : config.FS의 키 ("big", "body", "small" 등)
    bold     : True면 굵게
    """
    f = QFont("맑은 고딕", FS[size_key])   # 맑은 고딕 + config에서 가져온 크기
    f.setBold(bold)                         # 굵기 설정
    return f


def now() -> str:
    """
    현재 시각을 카카오톡 스타일 "오전/오후 H:MM" 형식으로 반환.
    예: "오후 3:07"
    """
    t  = _time.localtime()                         # 현재 로컬 시간 구조체
    ap = "오전" if t.tm_hour < 12 else "오후"      # 오전/오후 판별
    return f"{ap} {t.tm_hour % 12 or 12}:{t.tm_min:02d}"
    # t.tm_hour % 12 → 12시간제 변환, or 12 → 0시·12시를 12로 표시
    # :02d → 분을 항상 두 자리로 (예: 07)
