from PyQt6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt6.QtCore    import Qt, pyqtSignal
from config  import C
from utils   import F, now
from .avatar import Avatar


class CharItem(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, char: dict, idx: int, parent=None):
        super().__init__(parent)
        self.idx = idx
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

        top = QHBoxLayout()
        name = QLabel(char["name"])
        name.setFont(F("body", bold=True))
        name.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        top.addWidget(name)
        top.addStretch()
        self.time_lbl = QLabel(char["time_label"])
        self.time_lbl.setFont(F("small"))
        self.time_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        top.addWidget(self.time_lbl)
        info.addLayout(top)

        self.preview = QLabel(char["preview"])
        self.preview.setFont(F("label"))
        self.preview.setStyleSheet(f"color:{C['text_mid']}; background:transparent;")
        info.addWidget(self.preview)

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
        short = text[:22] + "..." if len(text) > 22 else text
        self.preview.setText(short)
        self.time_lbl.setText(now())

    def mousePressEvent(self, e):
        self.clicked.emit(self.idx)

    def enterEvent(self, e):
        self.setStyleSheet(f"background:{C['divider']};")

    def leaveEvent(self, e):
        self.setStyleSheet("background:transparent;")
