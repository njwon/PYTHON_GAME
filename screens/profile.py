from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal
from config  import C, LAYOUT, CHARS
from utils   import F
from widgets import Avatar


class ProfileScreen(QWidget):
    view_profile = pyqtSignal(int)
    go_novel     = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._aff_labels: list = []
        self.setStyleSheet("background: white;")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["home_top"])
        topbar.setStyleSheet(f"background:{C['topbar']};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(16, 0, 16, 0)
        title = QLabel("용의자 조사")
        title.setFont(F("big", bold=True))
        title.setStyleSheet(f"color:{C['text_white']};")
        tb.addWidget(title)
        tb.addStretch()
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        list_w = QWidget()
        list_w.setStyleSheet(f"background:{C['bg_home']};")
        ll = QVBoxLayout(list_w)
        ll.setContentsMargins(12, 12, 12, 12)
        ll.setSpacing(10)
        for i, char in enumerate(CHARS):
            ll.addWidget(self._make_card(char, i))
        ll.addStretch()
        scroll.setWidget(list_w)
        main.addWidget(scroll, stretch=1)

    def _make_card(self, char: dict, idx: int) -> QWidget:
        card = QWidget()
        card.setStyleSheet("background:white; border-radius:14px;")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.mousePressEvent = lambda _: self.view_profile.emit(idx)
        card.enterEvent = lambda _: card.setStyleSheet("background:#F0F0F0; border-radius:14px;")
        card.leaveEvent = lambda _: card.setStyleSheet("background:white; border-radius:14px;")

        row = QHBoxLayout(card)
        row.setContentsMargins(14, 12, 14, 12)
        row.setSpacing(14)
        row.addWidget(Avatar(char, size=52), alignment=Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout()
        info.setSpacing(4)

        name_lbl = QLabel(char["name"])
        name_lbl.setFont(F("body", bold=True))
        name_lbl.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        info.addWidget(name_lbl)

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

        hint_lbl = QLabel(char["hint"])
        hint_lbl.setFont(F("small"))
        hint_lbl.setWordWrap(True)
        hint_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        info.addWidget(hint_lbl)

        row.addLayout(info, stretch=1)
        return card

    def refresh(self):
        pass  # 호감도 제거 — 갱신할 수치 없음

    def _refresh_unused(self):
        for lbl, char in self._aff_labels:
            v = int(char["affection"])
            col = "#DC4650" if v < 30 else "#F0B432" if v < 60 else "#32C878"
            lbl.setText(f"호감도  {v}%")
            lbl.setStyleSheet(f"color:{col}; background:transparent;")


class ProfileDetailScreen(QWidget):
    go_back    = pyqtSignal()
    enter_chat = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._idx  = 0
        self._char = CHARS[0]
        self.setStyleSheet(f"background:{C['bg_home']};")

        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["home_top"])
        topbar.setStyleSheet(f"background:{C['topbar']};")
        tb = QHBoxLayout(topbar)
        tb.setContentsMargins(10, 0, 16, 0)
        back = QPushButton("‹")
        back.setFont(F("big", bold=True))
        back.setFixedSize(32, 40)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"color:{C['text_white']}; background:transparent; border:none;")
        back.clicked.connect(self.go_back.emit)
        tb.addWidget(back)
        self._title_lbl = QLabel()
        self._title_lbl.setFont(F("body", bold=True))
        self._title_lbl.setStyleSheet(f"color:{C['text_white']}; background:transparent;")
        tb.addWidget(self._title_lbl)
        tb.addStretch()
        main.addWidget(topbar)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        content = QWidget()
        content.setStyleSheet(f"background:{C['bg_home']};")
        cl = QVBoxLayout(content)
        cl.setContentsMargins(24, 28, 24, 24)
        cl.setSpacing(0)

        self._avatar_box = QHBoxLayout()
        self._avatar_box.addStretch()
        self._avatar_inner = QHBoxLayout()
        self._avatar_box.addLayout(self._avatar_inner)
        self._avatar_box.addStretch()
        cl.addLayout(self._avatar_box)
        cl.addSpacing(16)

        self._name_lbl = QLabel()
        self._name_lbl.setFont(F("big", bold=True))
        self._name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name_lbl.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        cl.addWidget(self._name_lbl)
        cl.addSpacing(8)

        mid_row = QHBoxLayout()
        mid_row.setSpacing(8)
        mid_row.addStretch()
        self._badge_lbl = QLabel()
        self._badge_lbl.setFont(F("label"))
        self._badge_lbl.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        mid_row.addWidget(self._badge_lbl)
        mid_row.addStretch()
        cl.addLayout(mid_row)
        cl.addSpacing(24)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C['divider']};")
        cl.addWidget(sep)
        cl.addSpacing(20)

        hint_title = QLabel("말투 / 조사 특징")
        hint_title.setFont(F("small", bold=True))
        hint_title.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        cl.addWidget(hint_title)
        cl.addSpacing(6)
        self._hint_lbl = QLabel()
        self._hint_lbl.setFont(F("body"))
        self._hint_lbl.setWordWrap(True)
        self._hint_lbl.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        cl.addWidget(self._hint_lbl)
        cl.addSpacing(20)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color:{C['divider']};")
        cl.addWidget(sep2)
        cl.addSpacing(20)

        greet_title = QLabel("첫 진술")
        greet_title.setFont(F("small", bold=True))
        greet_title.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        cl.addWidget(greet_title)
        cl.addSpacing(8)
        self._greet_lbl = QLabel()
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
        self._char = char
        self._idx  = idx

        while self._avatar_inner.count():
            item = self._avatar_inner.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._avatar_inner.addWidget(Avatar(char, size=80))

        self._title_lbl.setText(char["name"])
        self._name_lbl.setText(char["name"])
        self._badge_lbl.setText(char["type"])
        self._badge_lbl.setStyleSheet(
            f"background:{char['bubble_color']}; color:white;"
            f"border-radius:9px; padding:2px 10px;"
        )
        self._hint_lbl.setText(char["hint"])
        self._greet_lbl.setText(f'"{char["greeting"]}"')
