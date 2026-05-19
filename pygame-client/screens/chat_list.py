from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame,
)
from PyQt6.QtCore import pyqtSignal
from config  import C, LAYOUT, CHARS
from utils   import F
from widgets import CharItem


class ChatListScreen(QWidget):
    enter_chat = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: white;")
        main = QVBoxLayout(self)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        list_w = QWidget()
        list_w.setStyleSheet(f"background:{C['bg_home']};")
        self._list_layout = QVBoxLayout(list_w)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(0)

        self._items: list[CharItem] = []
        for i, char in enumerate(CHARS):
            item = CharItem(char, i)
            item.clicked.connect(self.enter_chat.emit)
            self._items.append(item)
            self._list_layout.addWidget(item)
            if i < len(CHARS) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet(f"color:{C['divider']}; margin:0 12px;")
                self._list_layout.addWidget(line)

        self._list_layout.addStretch()
        scroll.setWidget(list_w)
        main.addWidget(scroll, stretch=1)

    def update_preview(self, idx: int, text: str):
        self._items[idx].set_preview(text)
