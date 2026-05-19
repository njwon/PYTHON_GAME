from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore    import Qt
from config    import C, RADIUS
from utils     import F, _break_words
from .avatar   import Avatar


class ChatBubble(QWidget):
    def __init__(self, text: str, is_mine: bool, char: dict,
                 score: int = 0, ts: str = "", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        row = QHBoxLayout(self)
        row.setContentsMargins(8, 3, 8, 3)
        row.setSpacing(6)

        bubble = QLabel(_break_words(text))
        bubble.setWordWrap(True)
        bubble.setFont(F("body"))
        bubble.setMaximumWidth(260)
        bubble.setContentsMargins(12, 8, 12, 8)
        _sp = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        _sp.setHeightForWidth(True)
        bubble.setSizePolicy(_sp)

        time_lbl = QLabel(ts)
        time_lbl.setFont(F("small"))
        time_lbl.setStyleSheet(f"color: {C['text_light']}; background: transparent;")
        time_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)

        if is_mine:
            bubble.setStyleSheet(f"""
                background: {C['bubble_me']};
                border-radius: {RADIUS["bubble"]}px;
                color: {C['text_dark']};
            """)
            row.addStretch()
            if score != 0:
                sign = "+" if score > 0 else ""
                col  = C["score_up"] if score > 0 else C["score_down"]
                sc = QLabel(f"{sign}{score}")
                sc.setFont(F("small"))
                sc.setStyleSheet(f"color: {col}; background: transparent;")
                sc.setAlignment(Qt.AlignmentFlag.AlignBottom)
                row.addWidget(sc)
            row.addWidget(time_lbl)
            row.addWidget(bubble)
        else:
            bubble.setStyleSheet(f"""
                background: {C['bubble_her']};
                border-radius: {RADIUS["bubble"]}px;
                color: {C['text_dark']};
            """)
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(Avatar(char, size=32), alignment=Qt.AlignmentFlag.AlignTop)
            row.addLayout(col)
            row.addWidget(bubble)
            row.addWidget(time_lbl)
            row.addStretch()
