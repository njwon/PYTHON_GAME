from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QGraphicsOpacityEffect,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from config  import C, LAYOUT, RADIUS, BTN, FS, SEND_TEXT, REPLY_DELAY, W, H
from utils   import F, now
from widgets import Avatar, ChatBubble, ChatInput


class ChatScreen(QWidget):
    go_home         = pyqtSignal()
    preview_updated = pyqtSignal(int, str)

    def __init__(self, char: dict, idx: int, parent=None):
        super().__init__(parent)
        self.char     = char
        self.idx      = idx
        self.resp_idx = 0
        self._build_ui()
        self._add_msg(char["greeting"], is_mine=False)

    def _build_ui(self):
        self.setStyleSheet(f"background: {C['bg_chat']};")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(LAYOUT["topbar"])
        topbar.setStyleSheet(f"background: {C['topbar']};")
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
        sub  = QLabel(f"{self.char['type']} 담당")
        sub.setFont(F("small"))
        sub.setStyleSheet("color:#AAAABD; background:transparent;")
        info.addWidget(name)
        info.addWidget(sub)
        tb.addLayout(info)
        tb.addStretch()
        main.addWidget(topbar)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{
                background: {C['bg_chat']};
                border: none;
            }}
            QScrollBar:vertical {{
                width: 6px; background: transparent; margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(0,0,0,30); border-radius: 3px; min-height: 32px;
            }}
            QScrollBar::handle:vertical:hover  {{ background: rgba(0,0,0,55); }}
            QScrollBar::handle:vertical:pressed {{ background: rgba(0,0,0,80); }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0; background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        chat_wrap = QWidget()
        chat_wrap.setStyleSheet(f"background:{C['bg_chat']};")
        self.msg_layout = QVBoxLayout(chat_wrap)
        self.msg_layout.setContentsMargins(0, 8, 0, 8)
        self.msg_layout.setSpacing(2)
        self.msg_layout.addStretch()
        self.scroll.setWidget(chat_wrap)
        main.addWidget(self.scroll, stretch=1)

        self.typing_row = QWidget()
        self.typing_row.setStyleSheet(f"background:{C['bg_chat']};")
        self.typing_row.setVisible(False)
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

        input_area = QWidget()
        input_area.setStyleSheet(
            f"background:{C['input_bg']}; border-top:1px solid {C['nav_border']};"
        )
        ia = QHBoxLayout(input_area)
        ia.setContentsMargins(8, 8, 8, 8)
        ia.setSpacing(6)

        self.input = ChatInput()
        self.input.setFont(F("body"))
        self.input.setStyleSheet(f"""
            ChatInput {{
                background: white;
                border: 1px solid #C3C3C3;
                border-radius: {RADIUS["input"]}px;
                padding: 4px 14px;
                color: {C['text_dark']};
            }}
            ChatInput:focus {{ border: 1px solid #AAAACC; }}
        """)
        self.input.send_requested.connect(self._send)
        ia.addWidget(self.input, stretch=1)

        send_btn = QPushButton(SEND_TEXT)
        send_btn.setFont(F("label", bold=True))
        send_btn.setFixedSize(BTN["w"], BTN["h"])
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']};
                color: {C['text_dark']};
                border-radius: {RADIUS["button"]}px;
            }}
            QPushButton:hover {{ background: #EED400; }}
        """)
        send_btn.clicked.connect(self._send)
        ia.addWidget(send_btn)
        main.addWidget(input_area)

        self._reply_timer = QTimer(self)
        self._reply_timer.setSingleShot(True)
        self._reply_timer.timeout.connect(self._deliver_reply)

        self._typing_timer = QTimer(self)
        self._typing_timer.timeout.connect(self._anim_typing)
        self._typing_frame = 0

        self._popup = QLabel("", self)
        self._popup.setFont(F("big", bold=True))
        self._popup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._popup.setFixedWidth(W)
        self._popup.move(0, H // 2 - 100)
        self._popup.setVisible(False)
        self._opacity_fx = QGraphicsOpacityEffect()
        self._popup.setGraphicsEffect(self._opacity_fx)

        self._popup_timer = QTimer(self)
        self._popup_timer.timeout.connect(self._fade_popup)
        self._popup_alpha = 0.0

    def _add_msg(self, text: str, is_mine: bool, score: int = 0):
        bubble = ChatBubble(text, is_mine, self.char, score, now())
        self.msg_layout.addWidget(bubble)
        QTimer.singleShot(30, self._scroll_bottom)
        self.preview_updated.emit(self.idx, text)

    def _scroll_bottom(self):
        sb = self.scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _send(self):
        txt = self.input.toPlainText().strip()
        if not txt or self._reply_timer.isActive():
            return
        self.input.clear()
        self.input.setFixedHeight(38)
        self._add_msg(txt, is_mine=True)
        self.char["unread"] = 0
        self.typing_row.setVisible(True)
        self._typing_timer.start(400)
        self._reply_timer.start(REPLY_DELAY)

    def _anim_typing(self):
        self.typing_lbl.setText(["·  ", "·· ", "···"][self._typing_frame % 3])
        self._typing_frame += 1

    def _deliver_reply(self):
        self.typing_row.setVisible(False)
        self._typing_timer.stop()

        pool = self.char["responses"]
        txt, delta = pool[self.resp_idx % len(pool)]
        self.resp_idx += 1
        self._add_msg(txt, is_mine=False, score=0)

        if delta > 0:
            popup_txt = "단서 획득"
            col = C["score_up"]
        else:
            popup_txt = "교란 주의"
            col = C["score_down"]
        self._popup.setText(popup_txt)
        self._popup.setStyleSheet(
            f"color:{col}; background:transparent; font-size:{FS['body']}pt; font-weight:bold;"
        )
        self._popup.setVisible(True)
        self._popup_alpha = 1.0
        self._opacity_fx.setOpacity(1.0)
        self._popup_timer.start(30)

    def _fade_popup(self):
        self._popup_alpha -= 0.04
        if self._popup_alpha <= 0:
            self._popup.setVisible(False)
            self._popup_timer.stop()
        else:
            self._opacity_fx.setOpacity(self._popup_alpha)
