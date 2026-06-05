# screens.py ── Qt 화면 모음 (프로필 목록 / 프로필 상세 / 채팅 목록 / 채팅) ────
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from config  import C, LAYOUT, RADIUS, BTN, FS, SEND_TEXT, W, H, CHARS
from utils   import F, now
from widgets import Avatar, ChatBubble, ChatInput, CharItem


# ════════════════════════════════════════════════════════════════════════════════
# ProfileScreen — 용의자 프로필 목록 화면 (홈 탭)
# ════════════════════════════════════════════════════════════════════════════════
class ProfileScreen(QWidget):
    view_profile = pyqtSignal(int)   # 카드 클릭 시 발생 — 페이로드: 캐릭터 인덱스
    go_novel     = pyqtSignal()      # 나가기 버튼 클릭 시 발생 → PhoneWindow.close()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aff_labels: list = []   # 호감도 라벨 목록 (나중에 갱신 가능하도록 보관)
        self.setStyleSheet("background: white;")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── 상단 바 ───────────────────────────────────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["home_top"])
        topbar.setStyleSheet(f"background:{C['topbar']};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)

        title = QLabel("용의자 조사")
        title.setFont(F("big", bold=True))
        title.setStyleSheet(f"color:{C['text_white']};")
        tb.addWidget(title)
        tb.addStretch()   # 제목과 나가기 버튼 사이를 벌림

        # 나가기 버튼 — 클릭 시 go_novel 시그널 발생 → PhoneWindow가 창 닫음
        quit_btn = QPushButton("나가기")
        quit_btn.setFont(F("label"))
        quit_btn.setFixedSize(54, 30)
        quit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        quit_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {C['text_light']};
                border: 1px solid {C['text_light']};
                border-radius: 6px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,30); color: white; }}
        """)
        quit_btn.clicked.connect(self.go_novel.emit)
        tb.addWidget(quit_btn)
        main.addWidget(topbar)

        # ── 캐릭터 카드 목록 (스크롤 가능) ──────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        list_w = QWidget()
        list_w.setStyleSheet(f"background:{C['bg_home']};")
        ll = QVBoxLayout(list_w)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(10)
        for i, char in enumerate(CHARS):
            ll.addWidget(self._make_card(char, i))   # 캐릭터마다 카드 생성
        ll.addStretch()   # 카드들을 위로 모으고 아래 빈 공간 채움
        scroll.setWidget(list_w)
        main.addWidget(scroll, stretch=1)

    def _make_card(self, char: dict, idx: int) -> QWidget:
        # 캐릭터 한 명의 프로필 카드 위젯 생성
        card = QWidget()
        card.setStyleSheet("background:white; border-radius:14px;")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.mousePressEvent = lambda _: self.view_profile.emit(idx)   # 클릭 → 상세 화면으로
        card.enterEvent = lambda _: card.setStyleSheet("background:#F0F0F0; border-radius:14px;")
        card.leaveEvent = lambda _: card.setStyleSheet("background:white; border-radius:14px;")

        row = QHBoxLayout(card)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(14)
        row.addWidget(Avatar(char, size=52), alignment=Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(4)

        # 이름
        name_lbl = QLabel(char["name"])
        name_lbl.setFont(F("body", bold=True))
        name_lbl.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        info.addWidget(name_lbl)

        # 담당 과목 배지
        mid = QHBoxLayout()
        mid.setSpacing(6)
        badge = QLabel(char["type"])
        badge.setFont(F("small"))
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        badge.setStyleSheet(
            f"background:{char['bubble_color']}; color:white; border-radius:7px; padding:1px 6px;"
        )
        mid.addWidget(badge)
        mid.addStretch()
        info.addLayout(mid)

        # 성격 힌트 텍스트
        hint_lbl = QLabel(char["hint"])
        hint_lbl.setFont(F("small"))
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        info.addWidget(hint_lbl)

        row.addLayout(info, stretch=1)
        return card

    def refresh(self):
        pass   # 나중에 호감도 등 동적 정보 갱신 시 사용 예정


# ════════════════════════════════════════════════════════════════════════════════
# ProfileDetailScreen — 캐릭터 상세 프로필 화면
# ════════════════════════════════════════════════════════════════════════════════
class ProfileDetailScreen(QWidget):
    go_back    = pyqtSignal()    # ‹ 버튼 클릭 시 발생 → 홈 화면으로
    enter_chat = pyqtSignal(int) # (현재 미사용) 채팅 시작 시그널

    def __init__(self, parent=None):
        super().__init__(parent)
        self._idx  = 0           # 현재 표시 중인 캐릭터 인덱스
        self._char = CHARS[0]    # 현재 표시 중인 캐릭터 데이터
        self.setStyleSheet(f"background:{C['bg_home']};")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── 상단 바 ───────────────────────────────────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["home_top"])
        topbar.setStyleSheet(f"background:{C['topbar']};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(10, 0, 16, 0)

        back = QPushButton("‹")   # 뒤로가기 화살표
        back.setFont(F("big", bold=True))
        back.setFixedSize(32, 40)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"color:{C['text_white']}; background:transparent; border:none;")
        back.clicked.connect(self.go_back.emit)
        tb.addWidget(back)

        self._title_lbl = QLabel()   # 상단 바에 표시할 이름 (show_char에서 채워짐)
        self._title_lbl.setFont(F("body", bold=True))
        self._title_lbl.setStyleSheet(f"color:{C['text_white']}; background:transparent;")
        tb.addWidget(self._title_lbl)
        tb.addStretch()
        main.addWidget(topbar)

        # ── 스크롤 가능한 상세 내용 영역 ─────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        content = QWidget()
        content.setStyleSheet(f"background:{C['bg_home']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 28, 24, 24)
        cl.setSpacing(0)

        # 아바타 (가운데 정렬) — show_char()에서 기존 위젯을 지우고 새로 추가
        self._avatar_box   = QHBoxLayout()
        self._avatar_inner = QHBoxLayout()
        self._avatar_box.addStretch()
        self._avatar_box.addLayout(self._avatar_inner)
        self._avatar_box.addStretch()
        cl.addLayout(self._avatar_box)
        cl.addSpacing(16)

        # 캐릭터 이름 (크게, 가운데)
        self._name_lbl = QLabel()
        self._name_lbl.setFont(F("big", bold=True))
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        cl.addWidget(self._name_lbl)
        cl.addSpacing(8)

        # 담당 과목 배지 (가운데 정렬)
        mid_row = QHBoxLayout()
        mid_row.addStretch()
        self._badge_lbl = QLabel()
        self._badge_lbl.setFont(F("label"))
        self._badge_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        mid_row.addWidget(self._badge_lbl)
        mid_row.addStretch()
        cl.addLayout(mid_row)
        cl.addSpacing(24)

        # 구분선 + 말투/조사특징 + 구분선 + 첫 진술 두 섹션 생성
        for sep_var in ("_sep1", "_sep2"):
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet(f"color:{C['divider']};")
            if sep_var == "_sep1":
                cl.addWidget(sep); cl.addSpacing(20)
                hint_title = QLabel("말투 / 조사 특징")
                hint_title.setFont(F("small", bold=True))
                hint_title.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
                cl.addWidget(hint_title); cl.addSpacing(6)
                self._hint_lbl = QLabel()    # show_char()에서 캐릭터 힌트 텍스트 채워짐
                self._hint_lbl.setFont(F("body"))
                self._hint_lbl.setWordWrap(True)
                self._hint_lbl.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
                cl.addWidget(self._hint_lbl); cl.addSpacing(20)
            else:
                cl.addWidget(sep); cl.addSpacing(20)
                greet_title = QLabel("첫 진술")
                greet_title.setFont(F("small", bold=True))
                greet_title.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
                cl.addWidget(greet_title); cl.addSpacing(8)
                self._greet_lbl = QLabel()   # show_char()에서 캐릭터 인삿말 채워짐
                self._greet_lbl.setFont(F("body"))
                self._greet_lbl.setWordWrap(True)
                self._greet_lbl.setStyleSheet(f"""
                    background:{C['bubble_her']}; border-radius:12px;
                    padding:12px 16px; color:{C['text_dark']};
                """)
                cl.addWidget(self._greet_lbl)
                cl.addStretch()

        scroll.setWidget(content)
        main.addWidget(scroll, stretch=1)

    def show_char(self, char: dict, idx: int):
        # 표시할 캐릭터 데이터로 화면 내용 갱신
        self._char = char
        self._idx  = idx

        # 기존 아바타 위젯 제거 후 새 아바타 추가
        while self._avatar_inner.count():
            item = self._avatar_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._avatar_inner.addWidget(Avatar(char, size=80))

        # 각 라벨 텍스트 갱신
        self._title_lbl.setText(char["name"])
        self._name_lbl.setText(char["name"])
        self._badge_lbl.setText(char["type"])
        self._badge_lbl.setStyleSheet(
            f"background:{char['bubble_color']}; color:white;"
            f"border-radius:9px; padding:2px 10px;"
        )
        self._hint_lbl.setText(char["hint"])
        self._greet_lbl.setText(f'"{char["greeting"]}"')


# ════════════════════════════════════════════════════════════════════════════════
# ChatListScreen — 채팅 목록 화면 (채팅 탭)
# ════════════════════════════════════════════════════════════════════════════════
class ChatListScreen(QWidget):
    enter_chat = pyqtSignal(int)   # 항목 클릭 시 발생 — 페이로드: 캐릭터 인덱스

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: white;")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── 상단 바 ───────────────────────────────────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["home_top"])
        topbar.setStyleSheet(f"background:{C['topbar']};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        title = QLabel("선생님 조사")
        title.setFont(F("big", bold=True))
        title.setStyleSheet(f"color:{C['text_white']};")
        tb.addWidget(title)
        main.addWidget(topbar)

        # ── 캐릭터 목록 (스크롤 가능) ────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        list_w = QWidget()
        list_w.setStyleSheet(f"background:{C['bg_home']};")
        self._list_layout = QVBoxLayout(list_w)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(0)

        self._items: list[CharItem] = []   # CharItem 참조 보관 (미리보기 갱신용)
        for i, char in enumerate(CHARS):
            item = CharItem(char, i)
            item.clicked.connect(self.enter_chat.emit)   # 클릭 → enter_chat 시그널
            self._items.append(item)
            self._list_layout.addWidget(item)
            if i < len(CHARS) - 1:
                # 마지막 항목 제외 하단에 구분선 추가
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet(f"color:{C['divider']}; margin:0 12px;")
                self._list_layout.addWidget(line)

        self._list_layout.addStretch()
        scroll.setWidget(list_w)
        main.addWidget(scroll, stretch=1)

    def update_preview(self, idx: int, text: str):
        # 새 메시지가 오면 해당 캐릭터 항목의 미리보기 텍스트 갱신
        self._items[idx].set_preview(text)


# ════════════════════════════════════════════════════════════════════════════════
# ChatScreen — 개별 채팅 화면 (선생님 한 명과의 대화)
# ════════════════════════════════════════════════════════════════════════════════
class ChatScreen(QWidget):
    go_home         = pyqtSignal()         # ‹ 버튼 클릭 시 발생 → 채팅 목록으로
    preview_updated = pyqtSignal(int, str) # 메시지 추가 시 발생 — (캐릭터 인덱스, 텍스트)

    def __init__(self, char: dict, idx: int, ws_client, parent=None):
        super().__init__(parent)
        self.char           = char        # 이 화면의 캐릭터 데이터
        self.idx            = idx         # 캐릭터 인덱스
        self._ws            = ws_client   # WSClient 인스턴스 (메시지 전송용)
        self._waiting_reply = False       # True면 답장 대기 중 (중복 전송 방지)
        self._build_ui()                  # UI 위젯 생성
        self._add_msg(char["greeting"], is_mine=False)   # 초기 인삿말 추가

    def _build_ui(self):
        self.setStyleSheet(f"background:{C['bg_chat']};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        # ── 상단 바 (뒤로가기 + 아바타 + 이름) ──────────────────────────────
        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["topbar"])
        topbar.setStyleSheet(f"background:{C['topbar']};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(10, 0, 14, 0)
        tb.setSpacing(10)

        back = QPushButton("‹")
        back.setFont(F("big", bold=True))
        back.setFixedSize(32, 40)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"color:{C['text_white']}; background:transparent; border:none;")
        back.clicked.connect(self.go_home.emit)
        tb.addWidget(back)

        tb.addWidget(Avatar(self.char, size=36))

        info = QVBoxLayout()
        info.setSpacing(1)
        name = QLabel(self.char["name"])
        name.setFont(F("body", bold=True))
        name.setStyleSheet(f"color:{C['text_white']}; background:transparent;")
        sub = QLabel(f"{self.char['type']} 담당")   # 담당 과목 서브타이틀
        sub.setFont(F("small"))
        sub.setStyleSheet("color:#AAAABD; background:transparent;")
        info.addWidget(name); info.addWidget(sub)
        tb.addLayout(info)
        tb.addStretch()
        main.addWidget(topbar)

        # ── 메시지 스크롤 영역 ───────────────────────────────────────────────
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{ background:{C['bg_chat']}; border:none; }}
            QScrollBar:vertical {{ width:6px; background:transparent; margin:4px 2px; }}
            QScrollBar::handle:vertical {{
                background:rgba(0,0,0,30); border-radius:3px; min-height:32px;
            }}
            QScrollBar::handle:vertical:hover   {{ background:rgba(0,0,0,55); }}
            QScrollBar::handle:vertical:pressed  {{ background:rgba(0,0,0,80); }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:none; }}
        """)
        chat_wrap = QWidget()
        chat_wrap.setStyleSheet(f"background:{C['bg_chat']};")
        self.msg_layout = QVBoxLayout(chat_wrap)
        self.msg_layout.setContentsMargins(0, 8, 0, 8)
        self.msg_layout.setSpacing(2)
        self.msg_layout.addStretch()   # 메시지가 적을 때 위로 밀리도록 아래 여백
        self.scroll.setWidget(chat_wrap)
        main.addWidget(self.scroll, stretch=1)

        # ── 타이핑 인디케이터 (···) ─────────────────────────────────────────
        self.typing_row = QWidget()
        self.typing_row.setStyleSheet(f"background:{C['bg_chat']};")
        self.typing_row.setVisible(False)   # 평소엔 숨겨져 있음
        tr = QHBoxLayout(self.typing_row)
        tr.setContentsMargins(8, 4, 8, 4)
        tr.setSpacing(6)
        tr.addWidget(Avatar(self.char, size=28), alignment=Qt.AlignmentFlag.AlignTop)
        self.typing_lbl = QLabel("···")
        self.typing_lbl.setFont(F("body"))
        self.typing_lbl.setStyleSheet(f"""
            background:{C['bubble_her']}; border-radius:12px;
            padding:6px 14px; color:{C['text_mid']};
        """)
        tr.addWidget(self.typing_lbl)
        tr.addStretch()
        main.addWidget(self.typing_row)

        # ── 입력 영역 (입력창 + 전송 버튼) ──────────────────────────────────
        input_area = QWidget()
        input_area.setStyleSheet(
            f"background:{C['input_bg']}; border-top:1px solid {C['nav_border']};"
        )
        ia = QHBoxLayout(input_area)
        ia.setContentsMargins(8, 8, 8, 8)
        ia.setSpacing(6)

        self.input = ChatInput()   # Enter 전송 / 자동 높이 조절 입력창
        self.input.setFont(F("body"))
        self.input.setStyleSheet(f"""
            ChatInput {{
                background:white; border:1px solid #C3C3C3;
                border-radius:{RADIUS['input']}px;
                padding:4px 14px; color:{C['text_dark']};
            }}
            ChatInput:focus {{ border:1px solid #AAAACC; }}
        """)
        self.input.send_requested.connect(self._send)
        ia.addWidget(self.input, stretch=1)

        send_btn = QPushButton(SEND_TEXT)   # "전송" 버튼
        send_btn.setFont(F("label", bold=True))
        send_btn.setFixedSize(BTN["w"], BTN["h"])
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{ background:{C['accent']}; color:{C['text_dark']};
                           border-radius:{RADIUS['button']}px; }}
            QPushButton:hover {{ background:#EED400; }}
        """)
        send_btn.clicked.connect(self._send)
        ia.addWidget(send_btn)
        main.addWidget(input_area)

        # ── 타이핑 애니메이션 타이머 ─────────────────────────────────────────
        self._typing_timer  = QTimer(self)
        self._typing_timer.timeout.connect(self._anim_typing)   # 400ms마다 ·/··/··· 전환
        self._typing_frame  = 0                                  # 현재 애니메이션 프레임

        # ── 단서/교란 팝업 (화면 중앙에 잠깐 표시) ──────────────────────────
        self._popup = QLabel("", self)
        self._popup.setFont(F("big", bold=True))
        self._popup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._popup.setFixedWidth(W)                   # 창 너비 꽉 채움
        self._popup.move(0, H // 2 - 100)              # 화면 세로 중앙보다 살짝 위
        self._popup.setVisible(False)                  # 평소엔 숨김
        self._opacity_fx = QGraphicsOpacityEffect()    # 투명도 애니메이션용
        self._popup.setGraphicsEffect(self._opacity_fx)
        self._popup_timer = QTimer(self)
        self._popup_timer.timeout.connect(self._fade_popup)   # 30ms마다 페이드 아웃
        self._popup_alpha = 0.0                               # 현재 불투명도 (0.0~1.0)

    def _add_msg(self, text: str, is_mine: bool, score: int = 0):
        # 새 말풍선을 메시지 영역에 추가하고 스크롤을 맨 아래로 내림
        self.msg_layout.addWidget(ChatBubble(text, is_mine, self.char, score, now()))
        QTimer.singleShot(30, self._scroll_bottom)    # 30ms 후 스크롤 (위젯 그려진 뒤)
        self.preview_updated.emit(self.idx, text)     # 채팅 목록 미리보기 갱신

    def _scroll_bottom(self):
        # 스크롤바를 맨 아래로 이동
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _send(self):
        # 전송 버튼 또는 Enter 키 → 메시지 전송 처리
        txt = self.input.toPlainText().strip()
        if not txt or self._waiting_reply:
            return   # 빈 텍스트거나 답장 대기 중이면 무시

        self.input.clear()
        self.input.setFixedHeight(38)        # 입력창 초기 높이로 리셋
        self._add_msg(txt, is_mine=True)     # 내 메시지를 바로 화면에 표시
        self.char["unread"] = 0              # 이 창 열려있으니 안 읽은 수 초기화
        self._waiting_reply = True           # 답장 올 때까지 재전송 차단
        self.typing_row.setVisible(True)     # 타이핑 인디케이터 표시
        self._typing_timer.start(400)        # 400ms 간격으로 애니메이션 시작
        self._ws.send({"type": "chat", "char_id": self.idx, "msg": txt})   # 서버로 전송

    def _anim_typing(self):
        # 타이핑 인디케이터 문자 순환: ·  → ··  → ··· → 반복
        self.typing_lbl.setText(["·  ", "·· ", "···"][self._typing_frame % 3])
        self._typing_frame += 1

    def receive_reply(self, data: dict):
        # 서버에서 AI 답장이 왔을 때 호출 (PhoneWindow._on_ws → 여기로)
        self._waiting_reply = False
        self.typing_row.setVisible(False)   # 타이핑 인디케이터 숨김
        self._typing_timer.stop()
        self._add_msg(data["msg"], is_mine=False, score=data.get("score", 0))

        # 점수 변동 팝업 표시
        delta     = data.get("score_delta", 0)
        popup_txt = "단서 획득" if delta > 0 else "교란 주의"
        col       = C["score_up"] if delta > 0 else C["score_down"]
        self._popup.setText(popup_txt)
        self._popup.setStyleSheet(
            f"color:{col}; background:transparent; font-size:{FS['body']}pt; font-weight:bold;"
        )
        self._popup.setVisible(True)
        self._popup_alpha = 1.0              # 불투명도 1.0(완전 불투명)으로 시작
        self._opacity_fx.setOpacity(1.0)
        self._popup_timer.start(30)          # 30ms마다 페이드 아웃 시작

    def _fade_popup(self):
        # 팝업을 서서히 투명하게 만들어 사라지게 함
        self._popup_alpha -= 0.04            # 매 30ms마다 0.04씩 감소
        if self._popup_alpha <= 0:
            self._popup.setVisible(False)    # 완전히 투명해지면 숨김
            self._popup_timer.stop()
        else:
            self._opacity_fx.setOpacity(self._popup_alpha)   # 투명도 적용
