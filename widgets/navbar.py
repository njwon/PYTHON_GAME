from PyQt6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QSizePolicy
from PyQt6.QtCore    import Qt, pyqtSignal
from config import C, LAYOUT
from utils  import F


class NavBar(QWidget):
    tab_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = "home"
        self.setFixedHeight(LAYOUT["nav"])
        self.setStyleSheet(
            f"background:{C['nav_bg']}; border-top:1px solid {C['nav_border']};"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._btns = {}
        for tid, label in [("home", "홈"), ("chat", "채팅")]:
            btn = QPushButton(label)
            btn.setFont(F("nav", bold=True))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setFlat(True)
            btn.clicked.connect(lambda _, t=tid: self._click(t))
            self._btns[tid] = btn
            layout.addWidget(btn)

        self._refresh()

    def set_active(self, tid: str):
        self.active = tid
        self._refresh()

    def _click(self, tid: str):
        self.active = tid
        self._refresh()
        self.tab_changed.emit(tid)

    def _refresh(self):
        for tid, btn in self._btns.items():
            if tid == self.active:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color:{C['text_dark']}; background:transparent; border:none;
                        border-bottom:3px solid {C['accent']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        color:{C['text_light']}; background:transparent; border:none;
                    }}
                    QPushButton:hover {{ background:#EEEEEE; }}
                """)
