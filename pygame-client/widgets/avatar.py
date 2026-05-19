from PyQt6.QtWidgets import QLabel
from PyQt6.QtCore    import Qt
from config import C
from utils  import F


class Avatar(QLabel):
    def __init__(self, char: dict, size: int = 36, parent=None):
        super().__init__(char["avatar_ch"], parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(F("body", bold=True))
        self.setStyleSheet(f"""
            background: {char["avatar_color"]};
            color: {char["avatar_text"]};
            border-radius: {size // 2}px;
        """)
