"""
언쟁의 여신 - PyQt6 버전
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QStackedWidget,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui  import QFont

from config  import W, H, CHARS, FS, C
from widgets import NavBar
from screens import (
    VisualNovelScreen,
    ProfileScreen,
    ProfileDetailScreen,
    ChatListScreen,
    ChatScreen,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("선생님, 맞죠?")
        self.resize(W, H)
        self.setMinimumSize(W // 2, H // 2)

        central = QWidget()
        central.setStyleSheet("background: black;")
        self.setCentralWidget(central)

        self._content = QWidget(central)
        self._content.setGeometry(0, 0, W, H)
        self._content.setStyleSheet("background: white;")
        self._content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        root = QVBoxLayout(self._content)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.stack          = QStackedWidget()
        self.vn_screen      = VisualNovelScreen()
        self.profile        = ProfileScreen()
        self.profile_detail = ProfileDetailScreen()
        self.chat_list      = ChatListScreen()
        self.stack.addWidget(self.vn_screen)
        self.stack.addWidget(self.profile)
        self.stack.addWidget(self.profile_detail)
        self.stack.addWidget(self.chat_list)

        self._chats: list[ChatScreen] = []
        for i, char in enumerate(CHARS):
            cs = ChatScreen(char, i)
            cs.go_home.connect(self._go_chat_list)
            cs.preview_updated.connect(self.chat_list.update_preview)
            self._chats.append(cs)
            self.stack.addWidget(cs)

        self.vn_screen.open_phone.connect(self._open_phone)
        self.profile.view_profile.connect(self._view_profile)
        self.profile.go_novel.connect(self._go_vn)
        self.profile_detail.go_back.connect(self._go_home)
        self.profile_detail.enter_chat.connect(self._enter_chat)
        self.chat_list.enter_chat.connect(self._enter_chat)

        root.addWidget(self.stack, stretch=1)

        self.nav = NavBar()
        self.nav.tab_changed.connect(self._on_tab)
        root.addWidget(self.nav)

        self._last_idx: int | None = None
        self._go_vn()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        win_w = event.size().width()
        win_h = event.size().height()
        scale = min(win_w / W, win_h / H)
        cw = int(W * scale)
        ch = int(H * scale)
        cx = (win_w - cw) // 2
        cy = (win_h - ch) // 2
        self._content.setGeometry(cx, cy, cw, ch)

    def _go_vn(self):
        self.vn_screen.reset()
        self.stack.setCurrentWidget(self.vn_screen)
        self.nav.setVisible(False)

    def _open_phone(self):
        self.nav.setVisible(True)
        self.nav.set_active("home")
        self.profile.refresh()
        self.stack.setCurrentWidget(self.profile)

    def _view_profile(self, idx: int):
        self.profile_detail.show_char(CHARS[idx], idx)
        self.stack.setCurrentWidget(self.profile_detail)

    def _enter_chat(self, idx: int):
        self._last_idx = idx
        CHARS[idx]["unread"] = 0
        self.stack.setCurrentWidget(self._chats[idx])
        self.nav.set_active("chat")
        self._chats[idx].input.setFocus()

    def _go_home(self):
        self.profile.refresh()
        self.stack.setCurrentWidget(self.profile)
        self.nav.set_active("home")

    def _go_chat_list(self):
        self.stack.setCurrentWidget(self.chat_list)
        self.nav.set_active("chat")

    def _on_tab(self, tid: str):
        if tid == "home":
            self._go_home()
        elif tid == "chat":
            self.stack.setCurrentWidget(self.chat_list)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("맑은 고딕", FS["body"]))
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
