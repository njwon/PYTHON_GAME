from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore    import Qt, pyqtSignal


class ChatInput(QTextEdit):
    send_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("질문을 입력하세요...")
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setFixedHeight(38)
        self.document().contentsChanged.connect(self._adjust_height)

    def _adjust_height(self):
        doc_h = int(self.document().size().height())
        new_h = max(38, min(doc_h + 4, 100))
        if self.height() != new_h:
            self.setFixedHeight(new_h)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if e.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(e)
            else:
                self.send_requested.emit()
        else:
            super().keyPressEvent(e)
