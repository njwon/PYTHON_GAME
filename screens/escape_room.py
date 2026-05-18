# screens/escape_room.py  ── 게임 흐름 및 상호작용 ────────────────────────────
import math
import pygame
from config import W, H

# ── 레이아웃 상수 ──────────────────────────────────────────────────────────────
SPEED   = 3.0
WALL_T  = 45
INTER_R = 68
PL_R    = 16
RX1     = WALL_T
RX2     = W - WALL_T
RY1     = WALL_T + 32
RY2     = H  - WALL_T - 28

# ── 색상 팔레트 ────────────────────────────────────────────────────────────────
C = {
    "floor_t": (186, 149,  90), "floor_b": (205, 176, 112),
    "outer"  : ( 46,  26,  10), "wall"   : ( 62,  40,  18),
    "door"   : (122,  64,  32), "window" : (168, 216, 240),
    "shelf"  : ( 74,  47,  30), "desk"   : (139, 105,  20),
    "safe"   : ( 74,  74,  85),
    "p_light": (123, 188, 245), "p_dark" : ( 34,  85, 170),
    "p_rim"  : ( 26,  64, 128),
    "bubble" : (255, 252, 218), "bub_b"  : (100,  72,  18),
    "bub_t"  : ( 35,  18,   2),
    "yellow" : (255, 224, 102), "green"  : (136, 221,  68),
    "hud"    : ( 30,  13,   0), "white"  : (255, 255, 255),
    "black"  : (  0,   0,   0), "gray"   : (136, 136, 136),
    "dgray"  : ( 60,  60,  60),
}

_OBJ_COL = {
    "door": C["door"],  "window": C["window"], "bookshelf": C["shelf"],
    "desk": C["desk"],  "safe":   C["safe"],
}


# ── 방 오브젝트 데이터 ─────────────────────────────────────────────────────────
class RoomObj:
    def __init__(self, name: str, x: int, y: int, w: int, h: int, label: str):
        self.name  = name
        self.rect  = pygame.Rect(x, y, w, h)
        self.color = _OBJ_COL[name]
        self.label = label

    @property
    def cx(self): return self.rect.centerx
    @property
    def cy(self): return self.rect.centery

    def dist(self, px: float, py: float) -> float:
        return math.hypot(px - self.cx, py - self.cy)


# ── 게임 상태 및 상호작용 ──────────────────────────────────────────────────────
class EscapeRoomGame:
    def __init__(self):
        self.objs = [
            RoomObj("door",      160, RY1,      100, 65,  "출 구"),
            RoomObj("window",    286, RY1,       76, 45,  "창 문"),
            RoomObj("bookshelf", RX2-28, 160,    28, 165, "책\n장"),
            RoomObj("desk",       52, 570,      115, 58,  "책 상"),
            RoomObj("safe",      RX2-82, 610,    70, 70,  "금 고"),
        ]
        self.reset()

    def reset(self):
        self.px       = float(W // 2)
        self.py       = float((RY1 + RY2) // 2)
        self.has_note = False
        self.has_key  = False
        self.won      = False
        self.bubble   = ""
        self.btimer   = 0

    def set_pos(self, px: float, py: float):
        self.px = px
        self.py = py

    def clear_bubble(self):
        self.bubble = ""

    def tick_bubble(self):
        if self.btimer > 0:
            self.btimer -= 1
            if self.btimer == 0:
                self.bubble = ""

    def interact(self):
        nearest, md = None, float(INTER_R)
        for obj in self.objs:
            d = obj.dist(self.px, self.py)
            if d < md:
                md = d; nearest = obj

        if nearest is None:
            self._show("주변에 상호작용할\n것이 없다."); return

        n = nearest.name
        if n == "door":
            if self.has_key:
                self.won = True; self._show("열쇠로 문을 열었다!\n탈출 성공!", 500)
            else:
                self._show("문이 잠겨있다.\n열쇠를 찾아야 한다.")

        elif n == "window":
            self._show("창문은 굳게 잠겨있다.\n밖에 사람이 보인다...")

        elif n == "bookshelf":
            self._show("금고 비밀번호:\n[ 1  2  3  4 ]" if self.has_note
                       else "책들이 빼곡하다.\n특별한 건 없어 보인다.")

        elif n == "desk":
            if not self.has_note:
                self.has_note = True
                self._show("서랍에서 메모 발견!\n금고 비밀번호: 1234")
            else:
                self._show("비밀번호는 1234이다.\n금고를 열어보자.")

        elif n == "safe":
            if not self.has_note:
                self._show("금고가 잠겨있다.\n비밀번호를 모른다.")
            elif not self.has_key:
                self.has_key = True
                self._show("1234 입력... 철컥!\n금고에서 열쇠를 찾았다!")
            else:
                self._show("이미 열쇠를 가지고 있다.")

    def _show(self, text: str, frames: int = 230):
        self.bubble  = text
        self.btimer  = frames
