# widgets.py ── 재사용 가능한 Qt UI 위젯 모음 ────────────────────────────────
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QVBoxLayout, QSizePolicy,
    QPushButton, QTextEdit,
)
from PyQt6.QtCore import Qt, pyqtSignal
from config import C, LAYOUT, RADIUS    # 색상, 레이아웃 크기, 모서리 반지름
from utils  import F, _break_words, now  # 폰트 함수, 줄바꿈 처리, 현재 시각


# ════════════════════════════════════════════════════════════════════════════════
# Avatar — 캐릭터 이니셜을 원형 배경으로 표시하는 위젯
# ════════════════════════════════════════════════════════════════════════════════
class Avatar(QLabel):
    def __init__(self, char: dict, size: int = 36, parent=None):
        super().__init__(char["avatar_ch"], parent)   # 라벨 텍스트 = 캐릭터 이니셜 (예: "고")
        self.setFixedSize(size, size)                  # 정사각형 고정 크기
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)  # 글자 가운데 정렬
        self.setFont(F("body", bold=True))
        self.setStyleSheet(f"""
            background: {char["avatar_color"]};    /* 캐릭터별 배경색 */
            color: {char["avatar_text"]};          /* 캐릭터별 글자색 */
            border-radius: {size // 2}px;          /* size의 절반 = 완전한 원 */
        """)


# ════════════════════════════════════════════════════════════════════════════════
# ChatBubble — 채팅 메시지 한 개를 말풍선으로 표시하는 위젯
# ════════════════════════════════════════════════════════════════════════════════
class ChatBubble(QWidget):
    def __init__(self, text: str, is_mine: bool, char: dict,
                 score: int = 0, ts: str = "", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 3, 8, 3)   # 말풍선 바깥 여백 (좌우 8, 위아래 3)
        row.setSpacing(6)                      # 아바타 ↔ 말풍선 ↔ 타임스탬프 간격

        # 말풍선 본문 라벨
        bubble = QLabel(_break_words(text))   # 긴 단어 줄바꿈 처리 후 표시
        bubble.setWordWrap(True)               # Qt 자동 줄바꿈 활성화
        bubble.setFont(F("body"))
        bubble.setMaximumWidth(260)            # 너무 넓어지지 않도록 최대 너비 제한
        bubble.setContentsMargins(12, 8, 12, 8)  # 말풍선 안쪽 여백
        sp = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True)             # 너비에 따라 높이 자동 조정
        bubble.setSizePolicy(sp)

        # 타임스탬프 라벨
        time_lbl = QLabel(ts)
        time_lbl.setFont(F("small"))
        time_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)   # 말풍선 하단에 맞춤

        if is_mine:
            # ── 내 메시지: 오른쪽 정렬 ────────────────────────────────────────
            bubble.setStyleSheet(f"""
                background:{C['bubble_me']};
                border-radius:{RADIUS['bubble']}px;
                color:{C['text_dark']};
            """)
            row.addStretch()   # 왼쪽 여백 → 말풍선이 오른쪽으로 밀림
            if score != 0:
                # 점수 변동이 있으면 "+3" 또는 "-2" 형태로 표시
                sign = "+" if score > 0 else ""
                col  = C["score_up"] if score > 0 else C["score_down"]
                sc = QLabel(f"{sign}{score}")
                sc.setFont(F("small"))
                sc.setStyleSheet(f"color:{col}; background:transparent;")
                sc.setAlignment(Qt.AlignmentFlag.AlignBottom)
                row.addWidget(sc)
            row.addWidget(time_lbl)   # 타임스탬프 → 말풍선 왼쪽
            row.addWidget(bubble)     # 말풍선 가장 오른쪽
        else:
            # ── 상대방 메시지: 왼쪽 정렬 ─────────────────────────────────────
            bubble.setStyleSheet(f"""
                background:{C['bubble_her']};
                border-radius:{RADIUS['bubble']}px;
                color:{C['text_dark']};
            """)
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(Avatar(char, size=32), alignment=Qt.AlignmentFlag.AlignTop)  # 아바타 위쪽 고정
            row.addLayout(col)        # 아바타 → 말풍선 → 타임스탬프 → 여백 순서
            row.addWidget(bubble)
            row.addWidget(time_lbl)
            row.addStretch()          # 오른쪽 여백 → 말풍선이 왼쪽에 붙음


# ════════════════════════════════════════════════════════════════════════════════
# ChatInput — 채팅 입력창 (Enter 전송, Shift+Enter 줄바꿈, 자동 높이 조절)
# ════════════════════════════════════════════════════════════════════════════════
class ChatInput(QTextEdit):
    send_requested = pyqtSignal()   # Enter 키 눌리면 이 시그널 발생 → _send 연결됨

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("질문을 입력하세요...")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)    # 세로 스크롤바 숨김
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)  # 가로 스크롤바 숨김
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)   # 위젯 너비에서 자동 줄바꿈
        self.setFixedHeight(38)                                     # 초기 높이 (한 줄)
        self.document().contentsChanged.connect(self._adjust_height)  # 텍스트 변경 시 높이 재조정

    def _adjust_height(self):
        # 내용 길이에 따라 입력창 높이를 38~100px 사이로 자동 조절
        doc_h = int(self.document().size().height())
        new_h = max(38, min(doc_h + 4, 100))   # 최소 38, 최대 100
        if self.height() != new_h:
            self.setFixedHeight(new_h)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(e)   # Shift+Enter → 줄바꿈 (기본 동작)
            else:
                self.send_requested.emit() # Enter만 → 전송 시그널 발생
        else:
            super().keyPressEvent(e)       # 나머지 키 → 기본 동작


# ════════════════════════════════════════════════════════════════════════════════
# CharItem — 채팅 목록의 캐릭터 항목 하나
# ════════════════════════════════════════════════════════════════════════════════
class CharItem(QWidget):
    clicked = pyqtSignal(int)   # 클릭 시 발생 — 페이로드: 캐릭터 인덱스

    def __init__(self, char: dict, idx: int, parent=None):
        super().__init__(parent)
        self.idx = idx                                  # 이 아이템이 몇 번째 캐릭터인지
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(74)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background: transparent;")

        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 12, 8)
        row.setSpacing(12)
        row.addWidget(Avatar(char, size=48), alignment=Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(2)

        # 위쪽 줄: 이름 + 시간
        top = QHBoxLayout()
        name = QLabel(char["name"])
        name.setFont(F("body", bold=True))
        name.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        top.addWidget(name)
        top.addStretch()
        self.time_lbl = QLabel(char["time_label"])   # 마지막 메시지 시각
        self.time_lbl.setFont(F("small"))
        self.time_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        top.addWidget(self.time_lbl)
        info.addLayout(top)

        # 가운데 줄: 마지막 메시지 미리보기
        self.preview = QLabel(char["preview"])
        self.preview.setFont(F("label"))
        self.preview.setStyleSheet(f"color:{C['text_mid']}; background:transparent;")
        info.addWidget(self.preview)

        # 아래 줄: 담당 과목 배지
        badge = QLabel(char["type"])
        badge.setFont(F("small"))
        badge.setFixedHeight(16)
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        badge.setStyleSheet(f"""
            background:{char["bubble_color"]}; color:white;
            border-radius:8px; padding:0 6px;
        """)
        info.addWidget(badge)
        row.addLayout(info, stretch=1)

        # 안 읽은 메시지 수 뱃지 (0이면 표시 안 함)
        if char["unread"] > 0:
            ub = QLabel(str(char["unread"]))
            ub.setFont(F("small", bold=True))
            ub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ub.setFixedSize(20, 20)
            ub.setStyleSheet(f"""
                background:{C['unread_badge']}; color:white; border-radius:10px;
            """)
            row.addWidget(ub, alignment=Qt.AlignmentFlag.AlignTop)

    def set_preview(self, text: str):
        # 새 메시지가 오면 미리보기 텍스트와 시간을 갱신
        short = text[:22] + "..." if len(text) > 22 else text   # 22자 넘으면 말줄임표
        self.preview.setText(short)
        self.time_lbl.setText(now())   # 현재 시각으로 업데이트

    def mousePressEvent(self, e): self.clicked.emit(self.idx)        # 클릭 → 시그널 발생
    def enterEvent(self, e):      self.setStyleSheet(f"background:{C['divider']};")   # 마우스 진입 → 배경 어둡게
    def leaveEvent(self, e):      self.setStyleSheet("background:transparent;")       # 마우스 나감 → 원래대로


# ════════════════════════════════════════════════════════════════════════════════
# NavBar — 하단 내비게이션 바 (홈 / 채팅 탭 전환)
# ════════════════════════════════════════════════════════════════════════════════
class NavBar(QWidget):
    tab_changed = pyqtSignal(str)   # 탭 클릭 시 발생 — 페이로드: 탭 ID ("home" 또는 "chat")

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = "home"   # 현재 활성 탭 ID
        self.setFixedHeight(LAYOUT["nav"])
        self.setStyleSheet(
            f"background:{C['nav_bg']}; border-top:1px solid {C['nav_border']};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._btns = {}   # { 탭ID: QPushButton } 딕셔너리
        for tid, label in [("home", "홈"), ("chat", "채팅")]:
            btn = QPushButton(label)
            btn.setFont(F("nav", bold=True))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setFlat(True)
            btn.clicked.connect(lambda _, t=tid: self._click(t))   # 클릭 시 해당 탭 ID 전달
            self._btns[tid] = btn
            layout.addWidget(btn)

        self._refresh()   # 초기 스타일 적용

    def set_active(self, tid: str):
        # 외부에서 활성 탭을 변경할 때 사용 (시그널은 발생하지 않음)
        self.active = tid
        self._refresh()

    def _click(self, tid: str):
        # 사용자가 탭을 직접 클릭했을 때 — 스타일 갱신 후 시그널 발생
        self.active = tid
        self._refresh()
        self.tab_changed.emit(tid)

    def _refresh(self):
        # 활성 탭은 노란 하단 선 + 진한 색, 비활성 탭은 회색
        for tid, btn in self._btns.items():
            if tid == self.active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color:{C['text_dark']}; background:transparent; border:none;
                        border-bottom:3px solid {C['accent']};   /* 활성 탭 밑줄 */
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color:{C['text_light']}; background:transparent; border:none;
                    }}
                    QPushButton:hover {{ background:#EEEEEE; }}
                """)
