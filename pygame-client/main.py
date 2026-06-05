"""
선생님, 맞죠?  ─  pygame(탈출방) + Qt(폰 채팅) 통합 창
  python main.py   → 타이틀 → 탈출방 + 폰 나란히
"""
import os, sys, math, threading, time as _time, json

import pygame, websocket
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QLabel, QPushButton, QScrollArea, QFrame,
    QSizePolicy, QTextEdit, QGraphicsOpacityEffect, QDialog, QLineEdit,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve, QPoint
from PyQt6.QtGui  import QFont, QImage, QPixmap


# ── 설정값 ────────────────────────────────────────────────────────────────────

W, H       = 380, 700
VN_W, VN_H = 780, 468

C = {
    "bg_home"    : "#FFFFFF",
    "bg_chat"    : "#B2C7DA",
    "topbar"     : "#3A3A44",
    "nav_bg"     : "#FFFFFF",
    "nav_border" : "#D2D2D2",
    "bubble_me"  : "#FEE500",
    "bubble_her" : "#FFFFFF",
    "text_dark"  : "#191919",
    "text_mid"   : "#5A5A5A",
    "text_light" : "#A0A0A0",
    "text_white" : "#FFFFFF",
    "accent"     : "#FEE500",
    "unread_badge": "#FE4646",
    "score_up"   : "#2ECC71",
    "score_down" : "#E74C3C",
    "input_bg"   : "#F5F5F5",
    "divider"    : "#DCDCDC",
}

FS = {"big": 16, "nav": 13, "body": 12, "label": 10, "small": 8}

LAYOUT = {"topbar": 56, "nav": 58, "home_top": 54}
BTN    = {"w": 50, "h": 38}
RADIUS = {"bubble": 14, "input": 18, "button": 19}

CHARS = [
    {
        "name": "고경균 선생님", "type": "프로그래밍", "difficulty": "★★★★",
        "hint": "ENFJ  ·  프로그래밍 담당  ·  오른손잡이\n성격: 논리적이고 설득력 강함. 친절해 보이지만 속으로는 계산적",
        "preview": "그건 오해이죠. 논리적으로 생각해봐까요?", "time_label": "", "unread": 0, "affection": 50,
        "avatar_color": "#E8C8D8", "avatar_text": "#6A2848", "avatar_ch": "고", "bubble_color": "#7A4A6A",
        "greeting": "그건 오해이죠. 서버실에 있었던 건 맞지만 개인 프로젝트 작업이었어까요. 왜 그렇게 생각하시는 거죠?",
    },
    {
        "name": "박예진 선생님", "type": "네트워크", "difficulty": "★★★",
        "hint": "ENFP  ·  네트워크 담당  ·  왼손잡이\n성격: 극 F. 감정 이입이 빠르고 공감 능력 뛰어남. 분위기 금방 바꿈",
        "preview": "진짜요~? 저 바로 로그 확인해볼게요!", "time_label": "", "unread": 0, "affection": 50,
        "avatar_color": "#C8D8F0", "avatar_text": "#1A4080", "avatar_ch": "박", "bubble_color": "#3C6A9C",
        "greeting": "진짜~? 이런 일이 생겼어요? 어머 진짜로요? 저 네트워크 로그 바로 확인해볼게요~!",
    },
    {
        "name": "나혜연 선생님", "type": "데이터베이스", "difficulty": "★★★★",
        "hint": "ENFJ  ·  데이터베이스 담당  ·  오른손잡이\n성격: 직설적이고 경쾌함. 의리 있고 솔직함. 숨기려 하지 않음",
        "preview": "야, 그게 무슨 말이야? 뭐래는거얌~", "time_label": "", "unread": 0, "affection": 50,
        "avatar_color": "#D8E8C8", "avatar_text": "#2A5A1A", "avatar_ch": "나", "bubble_color": "#3A7A2A",
        "greeting": "야, 이게 무슨 상황이야? DB 로그 내가 확인했는데 이거 진짜 심각한 거 맞지 않아?",
    },
    {
        "name": "김태곤 선생님", "type": "보안", "difficulty": "★★★",
        "hint": "ESTP  ·  보안 담당  ·  왼손잡이\n성격: 사실에만 집중함. 감정 표현 거의 없음. 데이터와 로그로만 말함. 반박을 즐김",
        "preview": "엄... 그건 좀 다릅니다.", "time_label": "", "unread": 0, "affection": 50,
        "avatar_color": "#E8D8C8", "avatar_text": "#6A3A18", "avatar_ch": "김", "bubble_color": "#8A5A30",
        "greeting": "엄... 보안 로그 확인했습니다. 드릴 말씀이 있습니다.",
    },
]


# ── 유틸리티 ──────────────────────────────────────────────────────────────────

def _break_words(text, n=13):
    return ' '.join(
        '​'.join(w[i:i+n] for i in range(0, len(w), n)) if len(w) > n else w
        for w in text.split(' ')
    )

def F(size_key, bold=False):
    f = QFont("맑은 고딕", FS[size_key]); f.setBold(bold); return f

def now():
    t = _time.localtime()
    return f"{'오전' if t.tm_hour < 12 else '오후'} {t.tm_hour % 12 or 12}:{t.tm_min:02d}"


# ── 탈출방 (pygame) ───────────────────────────────────────────────────────────

_BASE     = os.path.dirname(os.path.abspath(__file__))
IMG_DIR   = os.path.join(_BASE, "assets", "images")
CHAR_DIR  = os.path.join(_BASE, "assets", "characters")
CLUE_DIR  = os.path.join(_BASE, "assets", "clues")
_i = lambda f: os.path.join(IMG_DIR,  f)
_d = lambda f: os.path.join(CLUE_DIR, f)

SPEED, INTER_R, PL_R = 3.5, 85, 16
RX1, RX2 = 0, VN_W
RY1, RY2 = 0, VN_H

RC = {
    "hud": (30,13,0), "yellow": (255,224,102), "blue": (144, 144, 236), "white": (255,255,255),
    "gray": (136,136,136), "bubble": (255,255,255), "bub_b": (0,0,0),
    "bub_t": (20,20,20), "p_dark": (34,85,170), "p_light": (123,188,245),
    "p_rim": (26,64,128), "safe_bg": (20,20,30), "safe_bd": (200,180,60),
}

MORSE_SEQ = [(False,12),(True,12),(False,36),(True,12),(False,12),(True,12),(False,12),(True,48)]


class RoomObj:
    def __init__(self, name, x, y, w, h, label, img_path=None, blocking=True):
        self.name = name; self.rect = pygame.Rect(x, y, w, h)
        self.label = label; self.img_path = img_path
        self.blocking = blocking; self.image = None; self.outline = None; self.mask = None

    def get_distance(self, px, py):
        return math.hypot(px - self.rect.centerx, py - self.rect.centery)

    def get_image(self):
        if self.image is None and self.img_path and os.path.exists(self.img_path):
            try:
                raw = pygame.image.load(self.img_path).convert_alpha()
                self.image = pygame.transform.scale(raw, (self.rect.w, self.rect.h))
                self.mask    = pygame.mask.from_surface(self.image)
                self.outline = self.mask.outline(2)
            except: pass
        return self.image


class EscapeRoomGame:
    SAFE_CODE = "78"
    DOOR_CODE = "355"

    def __init__(self):
        self.objs = [
            RoomObj("door",      245, 127,    80,144,"문",   _i("door.png"),      False),
            RoomObj("bookshelf", 630, 136,   99,209,"책장", _i("bookshelf.png"), True),
            RoomObj("drawer",    185, 215,   58,  77,"서랍", _i("drawer.png"),    True),
            RoomObj("desk",       55, 210,  130,  81,"책상", _i("desk.png"),      True),
            RoomObj("chair",      58, 233,   61,  81,"의자", _i("chair.png"),     True),
            RoomObj("safe",      545, 230,   70,  70,"금고", _i("safe.png"),      True),
            RoomObj("chocolate", 122, 207,   38,  32,"초콜릿",_i("chocolate.png"),False),
            RoomObj("switch",    327, 193,   24,  32,"스위치",_i("switch.png"),   False),
            RoomObj("key",       500, 372,   23,  23,"열쇠", _i("key.png"),       False),
            RoomObj("book",      238, 386,   47,  44,"책",   _i("book.png"),      False),
            RoomObj("wall_prob", 360, 140,  180,  90,"문제", _d("safe_puzzle.png"),False),
        ]
        self.reset()

    def reset(self):
        self.px, self.py = 390.0, 290.0
        self.saw_chocolate = self.safe_open = False
        self.safe_mode = False; self.safe_input = ""
        self.door_mode = False; self.door_input = ""
        self.morse_active = False; self.morse_step = self.morse_timer = 0
        self.lights_on = True; self.popup_img = ""; self.popup_active = False
        self.bubble = ""; self.btimer = 0; self.note_mode = False; self.won = False
        self.shake_obj = None; self.shake_timer = 0
        self.face_dx, self.face_dy = 0.0, 1.0

    def set_pos(self, px, py): self.px = px; self.py = py
    def clear_bubble(self): self.bubble = ""; self.note_mode = False

    def tick_bubble(self):
        if self.btimer > 0 and not self.note_mode:
            self.btimer -= 1
            if self.btimer == 0: self.bubble = ""

    def show_message(self, text, frames=240):
        self.bubble = text; self.btimer = frames; self.note_mode = False

    def show_note(self, text):
        self.bubble = text; self.btimer = 9999; self.note_mode = True

    def start_shake(self, obj_name, frames=45):
        self.shake_obj = obj_name; self.shake_timer = frames

    def tick_shake(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
            if self.shake_timer == 0:
                self.shake_obj = None

    def tick_morse(self):
        if not self.morse_active: return
        self.morse_timer -= 1
        if self.morse_timer > 0: return
        self.morse_step += 1
        if self.morse_step >= len(MORSE_SEQ):
            self.morse_active = False; self.lights_on = True
            return
        self.lights_on, self.morse_timer = MORSE_SEQ[self.morse_step]

    def interact(self):
        nearest, min_dist = None, float(INTER_R)
        for obj in self.objs:
            d = obj.get_distance(self.px, self.py)
            if d >= min_dist: continue
            odx = obj.rect.centerx - self.px
            ody = obj.rect.centery - self.py
            if self.face_dx * odx + self.face_dy * ody < 0:
                continue  # 등 뒤는 무시
            min_dist, nearest = d, obj
        if nearest is None:
            self.show_message("주변에 상호작용할 것이 없다."); return
        n = nearest.name

        if n == "door":
            self.door_mode = True; self.door_input = ""
        elif n == "bookshelf": self.show_message("누군가 꽂아둔 책들...\n정리 언제 한거지?")
        elif n == "chair":     self.show_message("평범한 의자처럼 보인다.")
        elif n in ("desk", "chocolate"):
            self.saw_chocolate = True
            self.show_message("책상 위에 초콜릿 하나가 놓여있다.\n놓인 각도가 의미심장하다.")
        elif n == "drawer":
            if not self.saw_chocolate:
                self.show_message("뭔가 있을 것 같은데...\n아직 확인할 게 남은 것 같다.")
            else:
                self.show_note("'물건은 잡는 손을 기억한다.'\n방향을 잘 봐라.")
        elif n == "switch":
            self.morse_active = True
            self.morse_step = 0
            self.lights_on, self.morse_timer = MORSE_SEQ[0]
            self.show_message("딸깍.\n규칙적으로 깜빡인다.\n전등이 뭔가를 말하려는 것 같다.")
        elif n == "key":
            self.show_message("열쇠에 희미하게 새겨진 글자.\n'X반 열쇠'\n출석부에 달려 있어야할 열쇠가 왜 여기 있지?\n조사를 통해 알아보자.")
        elif n == "book":
            self.show_note("누가 무거운 나를 들었을까?")
        elif n == "wall_prob":
            self.popup_img = _d("금고비번문제.png"); self.popup_active = True
            self.show_message("벽에 붙은 종이.\n수식인지 암호인지 모르겠다.")
        elif n == "safe":
            if self.safe_open:
                self.show_note("탈출을 위한 숫자\n유재석 = 455")
            else:
                self.safe_mode = True; self.safe_input = ""

    def input_door(self, key):
        if not self.door_mode: return
        if key == "cancel":
            self.door_mode = False; self.door_input = ""
        elif key == "back":
            self.door_input = self.door_input[:-1]
        elif key.isdigit() and len(self.door_input) < 3:
            self.door_input += key
            if len(self.door_input) == 3:
                if self.door_input == self.DOOR_CODE:
                    self.door_mode = False
                    self.won = True
                    self.show_message("탈출 성공!\n선생님들을 조사하자!")
                else:
                    self.start_shake("door"); self.door_input = ""

    def input_safe(self, key):
        if not self.safe_mode: return
        if key == "cancel":
            self.safe_mode = False; self.safe_input = ""
        elif key == "back":
            self.safe_input = self.safe_input[:-1]
        elif key.isdigit() and len(self.safe_input) < 2:
            self.safe_input += key
            if len(self.safe_input) == 2:
                if self.safe_input == self.SAFE_CODE:
                    self.safe_open = True; self.safe_mode = False
                    self.show_message("[금고 열림!]\n메모: 유재석 = 466\n(이름의 획수)")
                else:
                    self.start_shake("safe"); self.safe_input = ""


_AX = RX1 + int((RX2-RX1)*0.751)
_AY = RY1 + int((RY2-RY1)*0.574)
_BY = RY1 + int((RY2-RY1)*0.745)

def _wall_floor_y(x):
    """x 좌표에서 벽-바닥 경계선의 y값 반환 (이 값보다 위는 벽)"""
    if x <= _AX:
        return float(_AY)
    return _AY + (_BY - _AY) * (x - _AX) / (RX2 - _AX)
_BTN_W, _BTN_H = 70, 26
_BTN_CONTACT = pygame.Rect(RX2-_BTN_W-8, RY2-_BTN_H-8, _BTN_W, _BTN_H)

_img_cache = {}
def load_img(path, w, h):
    k = (path, w, h)
    if k not in _img_cache:
        try:
            _img_cache[k] = pygame.transform.scale(
                pygame.image.load(path).convert_alpha(), (w, h))
        except: _img_cache[k] = None
    return _img_cache.get(k)

_RECT_COLLISION = {"desk", "chair"}

def check_collision(game, cx, cy):
    fy = cy + PL_R  # 발 위치
    r_check = PL_R - 13
    for obj in game.objs:
        if not obj.blocking: continue
        r = obj.rect
        nx = max(r.left, min(cx, r.right))
        ny = max(r.top,  min(fy, r.bottom))
        if math.hypot(cx-nx, fy-ny) >= r_check: continue
        # 책상·의자는 rect 충돌 유지
        if obj.name in _RECT_COLLISION or not obj.mask:
            return True
        # 나머지는 원 둘레 16포인트로 부드러운 마스크 충돌
        for i in range(16):
            angle = math.tau * i / 16
            px = cx + math.cos(angle) * r_check
            py = fy + math.sin(angle) * r_check
            mx, my = int(px) - r.left, int(py) - r.top
            if 0 <= mx < r.w and 0 <= my < r.h and obj.mask.get_at((mx, my)):
                return True
    return False

def load_font(size, bold=False):
    wf = rf"C:\Windows\Fonts\malgun{'bd' if bold else ''}.ttf"
    if os.path.exists(wf): return pygame.font.Font(wf, size)
    nf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts",
                      f"NanumGothic{'Bold' if bold else ''}.ttf")
    return pygame.font.Font(nf if os.path.exists(nf) else None, size)

def load_gif_frames(path, target_h):
    """GIF 파일에서 프레임을 추출해 pygame Surface 리스트로 반환"""
    frames = []
    if not os.path.exists(path):
        return frames
    try:
        from PIL import Image
        gif = Image.open(path)
        for i in range(gif.n_frames):
            gif.seek(i)
            frame = gif.convert("RGBA")
            ow, oh = frame.size
            w = max(1, int(ow * target_h / oh))
            frame = frame.resize((w, target_h), Image.LANCZOS)
            surf = pygame.image.fromstring(frame.tobytes(), frame.size, "RGBA")
            frames.append(surf)
    except Exception as e:
        print(f"[GIF] 로드 실패: {e}")
    return frames

def load_walk_frames(folder, target_h):
    """walk/ 폴더의 frame_01.png... 를 원본 비율 유지한 채 target_h 높이로 로드"""
    frames = []
    i = 1
    while True:
        path = os.path.join(folder, f"frame_{i:02d}.png")
        if not os.path.exists(path): break
        try:
            raw = pygame.image.load(path).convert_alpha()
            ow, oh = raw.get_size()
            w = max(1, int(ow * target_h / oh))
            frames.append(pygame.transform.scale(raw, (w, target_h)))
        except: break
        i += 1
    return frames


class Renderer:
    WALK_TICK = 12  # 60fps ÷ 12 = 5fps (원본 GIF fps와 일치)

    def __init__(self, screen, game):
        self.screen = screen; self.game = game; self.last_dir = "front"
        self.fonts = {
            "title": load_font(16,True), "label": load_font(11,True),
            "bub": load_font(11), "small": load_font(9),
            "hint": load_font(9,True), "safe": load_font(22,True), "safe_s": load_font(12),
        }
        self.sprites = {
            "front": load_img(os.path.join(CHAR_DIR,"front.png"), 45, 120),
            "back":  load_img(os.path.join(CHAR_DIR,"back.png"),  38, 120),
            "side":  load_img(os.path.join(CHAR_DIR,"side.png"),  38, 120),
        }
        self.walk_frames      = load_gif_frames(os.path.join(CHAR_DIR,"walk_side.gif"), 116)
        self.back_walk_frames = load_gif_frames(os.path.join(CHAR_DIR,"walk_back.gif"), 120)
        self.anim_frame      = 0
        self.anim_tick       = 0
        self.back_anim_frame = 0
        self.back_anim_tick  = 0
        self.is_moving   = False
        self.facing_left = False

    def _centered(self, surf, y):
        self.screen.blit(surf, ((VN_W - surf.get_width()) // 2, y))

    def _overlay(self, alpha):
        s = pygame.Surface((VN_W, VN_H), pygame.SRCALPHA)
        s.fill((0, 0, 0, alpha)); self.screen.blit(s, (0, 0))

    def draw_bg(self):
        self.screen.fill((30,13,0))
        pygame.draw.polygon(self.screen,(255,255,255),[(RX1,_AY),(RX1,RY1),(_AX,RY1),(_AX,_AY)])
        pygame.draw.polygon(self.screen,(242,242,242),[(_AX,RY1),(RX2,RY1),(RX2,_BY),(_AX,_AY)])
        pygame.draw.polygon(self.screen,(235,232,225),[(RX1,_AY),(_AX,_AY),(RX2,_BY),(RX2,RY2),(RX1,RY2)])
        for p in [((_AX,RY1),(_AX,_AY)),((RX1,_AY),(_AX,_AY)),((_AX,_AY),(RX2,_BY))]:
            pygame.draw.line(self.screen,(10,10,10),*p,1)

    def draw_objects(self):
        g = self.game

        # 가장 가까운 오브젝트 하나만 찾기
        nearest, min_d = None, float(INTER_R)
        for obj in g.objs:
            d = obj.get_distance(g.px, g.py)
            odx = obj.rect.centerx - g.px
            ody = obj.rect.centery - g.py
            if d < min_d and g.face_dx * odx + g.face_dy * ody >= 0:
                min_d, nearest = d, obj

        for obj in g.objs:
            img = obj.get_image()
            if img:
                self.screen.blit(img, obj.rect.topleft)
            else:
                pygame.draw.rect(self.screen,(120,80,40),obj.rect,border_radius=4)
                t = self.fonts["label"].render(obj.label,True,RC["white"])
                self.screen.blit(t,(obj.rect.centerx-t.get_width()//2, obj.rect.centery-t.get_height()//2))

            if obj is nearest:
                ox, oy = obj.rect.topleft
                if obj.outline and len(obj.outline) > 1:
                    pts = [(ox + p[0], oy + p[1]) for p in obj.outline]
                    pygame.draw.lines(self.screen, RC["blue"], True, pts, 2)
                else:
                    pygame.draw.rect(self.screen, RC["blue"], obj.rect, 2, border_radius=4)
                bx,by = obj.rect.centerx-11, obj.rect.top-20
                pygame.draw.rect(self.screen,RC["blue"],(bx,by,22,15),border_radius=3)
                e = self.fonts["hint"].render("E",True,(50,30,0))
                self.screen.blit(e,(bx+(22-e.get_width())//2, by+(15-e.get_height())//2))

    def draw_player(self):
        px, py = int(self.game.px), int(self.game.py)

        if self.last_dir == "back":
            if self.is_moving and self.back_walk_frames:
                # 위로 이동 중: 후면 걷기 GIF 애니메이션
                self.back_anim_tick += 1
                if self.back_anim_tick >= self.WALK_TICK:
                    self.back_anim_tick = 0
                    self.back_anim_frame = (self.back_anim_frame + 1) % len(self.back_walk_frames)
                sp = self.back_walk_frames[self.back_anim_frame]
            else:
                # 정지: 후면 서기
                self.back_anim_frame = 0; self.back_anim_tick = 0
                sp = self.sprites["back"]
        elif self.is_moving and self.walk_frames:
            # 앞/옆 이동 중: 걷기 애니메이션
            self.anim_tick += 1
            if self.anim_tick >= self.WALK_TICK:
                self.anim_tick = 0
                self.anim_frame = (self.anim_frame + 1) % len(self.walk_frames)
            sp = self.walk_frames[self.anim_frame]
        else:
            # 정지: 마지막 방향에 맞는 스프라이트
            self.anim_frame = 0; self.anim_tick = 0
            if self.last_dir == "side" and self.sprites["side"]:
                sp = self.sprites["side"]
            else:
                sp = self.sprites["front"]

        if sp:
            if self.facing_left:
                sp = pygame.transform.flip(sp, True, False)
            self.screen.blit(sp,(px-sp.get_width()//2, py-sp.get_height()+PL_R))
        else:
            pygame.draw.circle(self.screen,RC["p_dark"], (px,py),PL_R)
            pygame.draw.circle(self.screen,RC["p_light"],(px-4,py-4),PL_R-4)
            pygame.draw.circle(self.screen,RC["p_rim"],  (px,py),PL_R,1)

    def draw_bubble(self):
        g = self.game; font = self.fonts["bub"]
        lh, pad, mw = font.get_height(), 10, int(VN_W*0.35)
        lines = []
        for line in g.bubble.split("\n"):
            if font.size(line)[0] <= mw-pad*2:
                lines.append(line)
            else:
                cur = ""
                for ch in line:
                    if font.size(cur+ch)[0] > mw-pad*2: lines.append(cur); cur = ch
                    else: cur += ch
                if cur: lines.append(cur)
        if not lines: return

        alpha = 255 if g.btimer > 45 else max(0, int(255*g.btimer/45))
        bw = max(font.size(l)[0] for l in lines) + pad*2 + 4
        bh = len(lines)*lh + pad*2
        px = int(g.px)
        bx = max(4, min(VN_W-bw-4, px-bw//2))
        head_y = int(g.py)-PL_R-43

        if g.note_mode:
            # ── 포스트잇 스타일 (화면 중앙 고정, 정사각형) ───
            FOLD = 14
            note_bg   = (255, 242, 100)
            note_fold = (220, 200, 60)
            note_shad = (180, 160, 40)
            note_text = (40,  30,  0)
            side = max(bw + FOLD, bh + FOLD, 160)  # 항상 정사각형
            bx = (VN_W - side) // 2
            by = (VN_H - side) // 2

            # 반투명 어두운 배경
            self._overlay(120)

            bs = pygame.Surface((side, side), pygame.SRCALPHA)

            # 포스트잇 본체
            body_col = (*note_bg, alpha)
            pts_body = [(0,0),(side-FOLD,0),(side,FOLD),(side,side),(0,side)]
            pygame.draw.polygon(bs, body_col, pts_body)
            pygame.draw.polygon(bs, (*note_shad, alpha), pts_body, 1)
            # 접힌 코너
            pygame.draw.polygon(bs, (*note_fold, alpha), [(side-FOLD,0),(side,FOLD),(side-FOLD,FOLD)])
            pygame.draw.line(bs, (*note_shad, alpha), (side-FOLD,0),(side,FOLD), 1)

            self.screen.blit(bs, (bx, by))
            # 텍스트 세로 중앙 정렬
            total_h = len(lines) * lh
            ty = by + (side - total_h) // 2
            for i, line in enumerate(lines):
                ts = font.render(line, True, note_text)
                if alpha < 255: ts.set_alpha(alpha)
                self.screen.blit(ts, (bx + (side - ts.get_width()) // 2, ty + i*lh))
        else:
            # ── 일반 말풍선 ───────────────────────────────────
            tip_x = max(9, min(bw-9, px-bx))
            below  = (head_y-bh-14) < RY1
            bs = pygame.Surface((bw, bh+16), pygame.SRCALPHA)
            bc = (*RC["bubble"], alpha); bd = (*RC["bub_b"], alpha)
            if below:
                pygame.draw.polygon(bs,bc,[(tip_x-8,14),(tip_x+8,14),(tip_x,1)])
                pygame.draw.polygon(bs,bd,[(tip_x-8,14),(tip_x+8,14),(tip_x,1)],1)
                pygame.draw.rect(bs,bc,(0,14,bw,bh),border_radius=10)
                pygame.draw.rect(bs,bd,(0,14,bw,bh),1,border_radius=10)
                by = int(g.py)+PL_R+3
            else:
                pygame.draw.rect(bs,bc,(0,0,bw,bh),border_radius=10)
                pygame.draw.rect(bs,bd,(0,0,bw,bh),1,border_radius=10)
                pygame.draw.polygon(bs,bc,[(tip_x-8,bh-5),(tip_x+8,bh-5),(tip_x,bh+13)])
                pygame.draw.line(bs,bd,(tip_x-8,bh-1),(tip_x,bh+13),1)
                pygame.draw.line(bs,bd,(tip_x+8,bh-1),(tip_x,bh+13),1)
                by = max(4, head_y-bh-58)
            self.screen.blit(bs,(bx,by))
            ty0 = (14+pad) if below else pad
            for i,line in enumerate(lines):
                ts = font.render(line,True,RC["bub_t"])
                if alpha < 255: ts.set_alpha(alpha)
                self.screen.blit(ts,(bx+pad, by+ty0+i*lh))

    def draw_hud(self, mouse_pos):
        sc = self.screen
        cc = (40,180,65) if _BTN_CONTACT.collidepoint(mouse_pos) else (50,200,80)
        pygame.draw.rect(sc,cc,_BTN_CONTACT,border_radius=8)
        ct = self.fonts["label"].render("연락",True,(255,255,255))
        sc.blit(ct,(_BTN_CONTACT.centerx-ct.get_width()//2, _BTN_CONTACT.centery-ct.get_height()//2))

    def draw_win(self):
        self._overlay(175); cy = VN_H//2
        self._centered(self.fonts["title"].render("서버실 탈출!",True,RC["blue"]),cy-38)
        self._centered(self.fonts["label"].render("이제 선생님들을 조사하라!",True,RC["white"]),cy+10)
        self._centered(self.fonts["small"].render("[ E ] 를 눌러 스마트폰으로 이동",True,RC["gray"]),cy+44)

    def draw_door_overlay(self):
        self._overlay(160)
        g = self.game
        shaking = (g.shake_obj == "door" and g.shake_timer > 0)
        sdx = int(math.sin(g.shake_timer * 1.2) * 6) if shaking else 0
        bd_col = (220, 50, 50) if shaking else (80, 120, 200)
        bw,bh = 300,160; bx=(VN_W-bw)//2 + sdx; by=(VN_H-bh)//2
        pygame.draw.rect(self.screen,(10,20,40),(bx,by,bw,bh),border_radius=14)
        pygame.draw.rect(self.screen,bd_col,(bx,by,bw,bh),2,border_radius=14)
        t1 = self.fonts["safe_s"].render("문 비밀번호 (숫자 3자리)",True,(180,200,255))
        self.screen.blit(t1,(bx+(bw-t1.get_width())//2, by+18))
        t2 = self.fonts["safe"].render("  ".join(g.door_input.ljust(3,"_")),True,RC["white"])
        self.screen.blit(t2,(bx+(bw-t2.get_width())//2, by+58))
        t3 = self.fonts["small"].render("0~9 입력  |  Backspace 지우기  |  ESC 취소",True,RC["gray"])
        self.screen.blit(t3,(bx+(bw-t3.get_width())//2, by+120))

    def draw_safe_overlay(self):
        self._overlay(160)
        g = self.game
        shaking = (g.shake_obj == "safe" and g.shake_timer > 0)
        sdx = int(math.sin(g.shake_timer * 1.2) * 6) if shaking else 0
        bd_col = (220, 50, 50) if shaking else RC["safe_bd"]
        bw,bh = 300,160; bx=(VN_W-bw)//2 + sdx; by=(VN_H-bh)//2
        pygame.draw.rect(self.screen,RC["safe_bg"],(bx,by,bw,bh),border_radius=14)
        pygame.draw.rect(self.screen,bd_col,(bx,by,bw,bh),2,border_radius=14)
        t1 = self.fonts["safe_s"].render("금고 비밀번호",True,RC["yellow"])
        self.screen.blit(t1,(bx+(bw-t1.get_width())//2, by+18))
        t2 = self.fonts["safe"].render("  ".join(g.safe_input.ljust(2,"_")),True,RC["white"])
        self.screen.blit(t2,(bx+(bw-t2.get_width())//2, by+58))
        t3 = self.fonts["small"].render("0~9 입력  |  Backspace 지우기  |  ESC 취소",True,RC["gray"])
        self.screen.blit(t3,(bx+(bw-t3.get_width())//2, by+120))

    def draw_popup(self):
        self._overlay(200)
        pw = VN_W-60; ph = min(int(pw*844/1863), VN_H-80)
        img = load_img(self.game.popup_img, pw, ph)
        if img:
            ix,iy = (VN_W-pw)//2, (VN_H-ph)//2
            pygame.draw.rect(self.screen,(255,255,255),(ix-3,iy-3,pw+6,ph+6),border_radius=8)
            self.screen.blit(img,(ix,iy))
        self._centered(self.fonts["small"].render("아무 키나 눌러 닫기",True,RC["gray"]), VN_H-28)

    def draw_all(self, mouse_pos):
        self.draw_bg(); self.draw_objects(); self.draw_player()
        if not self.game.lights_on: self._overlay(200)
        if self.game.bubble:        self.draw_bubble()
        self.draw_hud(mouse_pos)
        if self.game.won:                                  self.draw_win()
        if self.game.door_mode:                            self.draw_door_overlay()
        if self.game.safe_mode:                            self.draw_safe_overlay()
        if self.game.popup_active and self.game.popup_img: self.draw_popup()


def get_mac():
    import uuid
    n = uuid.getnode()
    return ':'.join(f'{(n >> (8*i)) & 0xff:02x}' for i in range(5, -1, -1))

def _fmt_time(sec):
    return f"{int(sec)//60}분 {int(sec)%60:02d}초"

def _ws_request(payload, timeout=3.0):
    """서버에 단일 요청 보내고 응답 반환 (동기)"""
    import websocket as _ws_mod
    result = [None]
    def on_msg(ws, msg):
        result[0] = json.loads(msg); ws.close()
    try:
        ws = _ws_mod.WebSocketApp("ws://localhost:3000",
            on_message=on_msg, on_error=lambda ws,e: ws.close())
        t = threading.Thread(target=ws.run_forever); t.daemon = True; t.start()
        ws.send(json.dumps(payload))
        t.join(timeout)
    except: pass
    return result[0]

def fetch_rankings():
    res = _ws_request({"type": "ranking_get"})
    if res and res.get("type") == "ranking_data":
        return res["rankings"]
    return []

def submit_ranking(name, elapsed):
    _ws_request({"type": "ranking_save", "name": name, "time": int(elapsed), "mac": get_mac()})

class RankingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("랭킹")
        self.setModal(True)
        self.resize(420, 520)
        self.setStyleSheet("background:#0f0a19; color:white;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)

        title = QLabel("랭킹")
        title.setFont(QFont("맑은 고딕", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color:#ffdc50;")
        lay.addWidget(title)

        ranks = fetch_rankings()
        if not ranks:
            lbl = QLabel("기록 없음")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color:#aaa;")
            lay.addWidget(lbl)
        else:
            MEDAL = ["#ffd700", "#c0c0c0", "#cd7f32"]
            for i, r in enumerate(ranks[:8]):
                color = MEDAL[i] if i < 3 else "#c8c8c8"
                row = QLabel(f"{i+1:2}.  {r['name']:<12}  {_fmt_time(r['time'])}  {r['date']}")
                row.setFont(QFont("맑은 고딕", 11))
                row.setStyleSheet(f"color:{color}; padding:4px;")
                lay.addWidget(row)

        lay.addStretch()
        btn = QPushButton("닫기")
        btn.setFixedHeight(40)
        btn.setStyleSheet("""
            QPushButton { background:#3c3220; color:#ffdc50; border:2px solid #ffdc50;
                          border-radius:8px; font-size:13px; }
            QPushButton:hover { background:#ffdc50; color:#0f0a19; }
        """)
        btn.clicked.connect(self.accept)
        lay.addWidget(btn)


class NameInputDialog(QDialog):
    def __init__(self, elapsed, parent=None):
        super().__init__(parent)
        self.setWindowTitle("탈출 성공!")
        self.setModal(True)
        self.resize(360, 300)
        self.setStyleSheet("background:#0f0a19;")
        self._elapsed = elapsed

        lay = QVBoxLayout(self)
        lay.setContentsMargins(30, 30, 30, 30)
        lay.setSpacing(12)

        for text, size, bold, color in [
            ("탈출 성공!", 20, True, "#ffdc50"),
            (f"클리어 시간: {_fmt_time(elapsed)}", 13, False, "#c8c8c8"),
            ("이름을 입력하세요", 12, False, "#b4b4b4"),
        ]:
            lbl = QLabel(text)
            lbl.setFont(QFont("맑은 고딕", size, QFont.Weight.Bold if bold else QFont.Weight.Normal))
            lbl.setStyleSheet(f"color:{color};")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(lbl)

        self._edit = QLineEdit()
        self._edit.setMaxLength(10)
        self._edit.setFixedHeight(44)
        self._edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._edit.setStyleSheet("""
            QLineEdit { background:#28233a; color:white; border:2px solid #ffdc50;
                        border-radius:8px; font-size:14px; }
        """)
        self._edit.returnPressed.connect(self._submit)
        lay.addWidget(self._edit)

        btn = QPushButton("저장  (Enter)")
        btn.setFixedHeight(40)
        btn.setStyleSheet("""
            QPushButton { background:#3c3220; color:#ffdc50; border:2px solid #ffdc50;
                          border-radius:8px; font-size:13px; }
            QPushButton:hover { background:#ffdc50; color:#0f0a19; }
        """)
        btn.clicked.connect(self._submit)
        lay.addWidget(btn)

    def _submit(self):
        name = self._edit.text().strip()
        if name:
            submit_ranking(name, self._elapsed)
            self.accept()


_QT_KEY_MAP = {
    Qt.Key.Key_W: pygame.K_w,     Qt.Key.Key_A: pygame.K_a,
    Qt.Key.Key_S: pygame.K_s,     Qt.Key.Key_D: pygame.K_d,
    Qt.Key.Key_Up: pygame.K_UP,   Qt.Key.Key_Down: pygame.K_DOWN,
    Qt.Key.Key_Left: pygame.K_LEFT, Qt.Key.Key_Right: pygame.K_RIGHT,
}


class EscapeRoomWidget(QWidget):
    phone_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._virt     = pygame.Surface((VN_W, VN_H))
        self._game     = EscapeRoomGame()
        self._renderer = Renderer(self._virt, self._game)
        self._start    = _time.time()
        self._saved    = False
        self._pressed  = set()

        self._lbl = QLabel(self)
        self._lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._lbl.setStyleSheet("background:black;")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMinimumSize(VN_W // 2, VN_H // 2)

    def _surf_to_pixmap(self, surf):
        raw = pygame.image.tobytes(surf, "RGB")
        w, h = surf.get_size()
        img = QImage(raw, w, h, w * 3, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(img)

    def _mouse_virt(self):
        lpos = self._lbl.mapFromGlobal(self.cursor().pos())
        lw = max(self._lbl.width(), 1); lh = max(self._lbl.height(), 1)
        scale = min(lw / VN_W, lh / VN_H)
        nw, nh = int(VN_W * scale), int(VN_H * scale)
        ox, oy = (lw - nw) // 2, (lh - nh) // 2
        vx = int((lpos.x() - ox) * VN_W / max(nw, 1))
        vy = int((lpos.y() - oy) * VN_H / max(nh, 1))
        return (vx, vy)

    def _tick(self):
        game = self._game; renderer = self._renderer
        renderer.is_moving = False

        if not game.won and not game.door_mode and not game.safe_mode and not game.popup_active:
            dx = int(pygame.K_d in self._pressed or pygame.K_RIGHT in self._pressed) - \
                 int(pygame.K_a in self._pressed or pygame.K_LEFT  in self._pressed)
            dy = int(pygame.K_s in self._pressed or pygame.K_DOWN  in self._pressed) - \
                 int(pygame.K_w in self._pressed or pygame.K_UP    in self._pressed)
            if dx and dy: dx *= 0.7071; dy *= 0.7071
            if dx or dy:
                renderer.is_moving = True
                if dx: renderer.facing_left = dx < 0
                if dy < 0:   renderer.last_dir = "back"
                elif dy > 0: renderer.last_dir = "front"
                elif dx:     renderer.last_dir = "side"
                game.face_dx, game.face_dy = dx, dy
                nx = max(float(RX1+PL_R), min(float(RX2-PL_R), game.px+dx*SPEED))
                ny = max(_wall_floor_y(nx)-PL_R+10, min(float(RY2-PL_R), game.py+dy*SPEED))
                npx = nx if not check_collision(game, nx, game.py) else game.px
                npy = max(_wall_floor_y(npx)-PL_R+10, ny if not check_collision(game, npx, ny) else game.py)
                game.set_pos(npx, npy)

        game.tick_morse(); game.tick_bubble(); game.tick_shake()
        renderer.draw_all(self._mouse_virt())

        lw = max(self._lbl.width(), 1); lh = max(self._lbl.height(), 1)
        scale = min(lw / VN_W, lh / VN_H)
        nw, nh = int(VN_W * scale), int(VN_H * scale)
        scaled = pygame.transform.scale(self._virt, (nw, nh))
        self._lbl.setPixmap(self._surf_to_pixmap(scaled))

        if game.won and not self._saved:
            self._saved = True
            self._timer.stop()
            dlg = NameInputDialog(_time.time() - self._start, self)
            dlg.exec()
            self._timer.start(16)

    def keyPressEvent(self, e):
        key = e.key()
        if key in _QT_KEY_MAP:
            self._pressed.add(_QT_KEY_MAP[key])
        game = self._game
        if game.note_mode:
            game.clear_bubble(); return
        if game.popup_active:
            game.popup_active = False; return
        if game.door_mode:
            if   key == Qt.Key.Key_Escape:             game.input_door("cancel")
            elif key == Qt.Key.Key_Backspace:           game.input_door("back")
            elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:  game.input_door(chr(key))
            return
        if game.safe_mode:
            if   key == Qt.Key.Key_Escape:             game.input_safe("cancel")
            elif key == Qt.Key.Key_Backspace:           game.input_safe("back")
            elif Qt.Key.Key_0 <= key <= Qt.Key.Key_9:  game.input_safe(chr(key))
            return
        if key == Qt.Key.Key_E and not game.won:
            game.interact()

    def keyReleaseEvent(self, e):
        key = e.key()
        if key in _QT_KEY_MAP:
            self._pressed.discard(_QT_KEY_MAP[key])

    def mousePressEvent(self, e):
        self.setFocus()
        if e.button() == Qt.MouseButton.LeftButton:
            game = self._game
            if game.note_mode:
                game.clear_bubble(); return
            vp = self._mouse_virt()
            if _BTN_CONTACT.collidepoint(vp):
                self.phone_requested.emit()


# ── Qt 위젯 ───────────────────────────────────────────────────────────────────

class Avatar(QLabel):
    def __init__(self, char, size=36, parent=None):
        super().__init__(char["avatar_ch"], parent)
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFont(F("body", bold=True))
        self.setStyleSheet(
            f"background:{char['avatar_color']}; color:{char['avatar_text']}; border-radius:{size//2}px;")


class ChatBubble(QWidget):
    def __init__(self, text, is_mine, char, score=0, ts="", parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        row = QHBoxLayout(self)
        row.setContentsMargins(8,3,8,3); row.setSpacing(6)

        bubble = QLabel(_break_words(text))
        bubble.setWordWrap(True); bubble.setFont(F("body"))
        bubble.setMaximumWidth(260); bubble.setContentsMargins(12,8,12,8)
        sp = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sp.setHeightForWidth(True); bubble.setSizePolicy(sp)

        ts_lbl = QLabel(ts)
        ts_lbl.setFont(F("small"))
        ts_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        ts_lbl.setAlignment(Qt.AlignmentFlag.AlignBottom)

        if is_mine:
            bubble.setStyleSheet(
                f"background:{C['bubble_me']}; border-radius:{RADIUS['bubble']}px; color:{C['text_dark']};")
            row.addStretch()
            if score:
                sc = QLabel(f"{'+' if score>0 else ''}{score}")
                sc.setFont(F("small"))
                sc.setStyleSheet(f"color:{C['score_up'] if score>0 else C['score_down']}; background:transparent;")
                sc.setAlignment(Qt.AlignmentFlag.AlignBottom)
                row.addWidget(sc)
            row.addWidget(ts_lbl); row.addWidget(bubble)
        else:
            bubble.setStyleSheet(
                f"background:{C['bubble_her']}; border-radius:{RADIUS['bubble']}px; color:{C['text_dark']};")
            col = QVBoxLayout(); col.setSpacing(2)
            col.addWidget(Avatar(char, size=32), alignment=Qt.AlignmentFlag.AlignTop)
            row.addLayout(col); row.addWidget(bubble); row.addWidget(ts_lbl); row.addStretch()


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
        h = max(38, min(int(self.document().size().height())+4, 100))
        if self.height() != h: self.setFixedHeight(h)

    def keyPressEvent(self, e):
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            super().keyPressEvent(e) if e.modifiers() & Qt.KeyboardModifier.ShiftModifier \
            else self.send_requested.emit()
        else:
            super().keyPressEvent(e)


class CharItem(QWidget):
    clicked = pyqtSignal(int)

    def __init__(self, char, idx, parent=None):
        super().__init__(parent)
        self.idx = idx
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(74)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("background:transparent;")

        row = QHBoxLayout(self)
        row.setContentsMargins(12,8,12,8); row.setSpacing(12)
        row.addWidget(Avatar(char, size=48), alignment=Qt.AlignmentFlag.AlignVCenter)

        info = QVBoxLayout(); info.setSpacing(2)
        top = QHBoxLayout()
        nm = QLabel(char["name"]); nm.setFont(F("body",True))
        nm.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        top.addWidget(nm); top.addStretch()
        self.time_lbl = QLabel(char["time_label"]); self.time_lbl.setFont(F("small"))
        self.time_lbl.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        top.addWidget(self.time_lbl)
        info.addLayout(top)

        self.preview = QLabel(char["preview"]); self.preview.setFont(F("label"))
        self.preview.setStyleSheet(f"color:{C['text_mid']}; background:transparent;")
        info.addWidget(self.preview)

        row.addLayout(info, stretch=1)

        self._unread_badge = QLabel(); self._unread_badge.setFont(F("small",True))
        self._unread_badge.setAlignment(Qt.AlignmentFlag.AlignCenter); self._unread_badge.setFixedSize(20,20)
        self._unread_badge.setStyleSheet(f"background:{C['unread_badge']}; color:white; border-radius:10px;")
        self._unread_badge.setVisible(False)
        row.addWidget(self._unread_badge, alignment=Qt.AlignmentFlag.AlignTop)

    def set_preview(self, text):
        self.preview.setText(text[:22]+"..." if len(text)>22 else text)
        self.time_lbl.setText(now())

    def set_unread(self, count):
        if count > 0:
            self._unread_badge.setText(str(count))
            self._unread_badge.setVisible(True)
        else:
            self._unread_badge.setVisible(False)

    def mousePressEvent(self, e): self.clicked.emit(self.idx)
    def enterEvent(self, e):      self.setStyleSheet(f"background:{C['divider']};")
    def leaveEvent(self, e):      self.setStyleSheet("background:transparent;")


class NavBar(QWidget):
    tab_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active = "home"
        self.setFixedHeight(LAYOUT["nav"])
        self.setStyleSheet(f"background:{C['nav_bg']}; border-top:1px solid {C['nav_border']};")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0); layout.setSpacing(0)
        self._btns = {}
        for tid, lbl in [("home","홈"),("chat","채팅")]:
            btn = QPushButton(lbl); btn.setFont(F("nav",True))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setFlat(True)
            btn.clicked.connect(lambda _,t=tid: self._click(t))
            self._btns[tid] = btn; layout.addWidget(btn)
        self._refresh()

    def set_active(self, tid): self.active = tid; self._refresh()

    def _click(self, tid):
        self.active = tid; self._refresh(); self.tab_changed.emit(tid)

    def _refresh(self):
        for tid, btn in self._btns.items():
            if tid == self.active:
                btn.setStyleSheet(f"QPushButton {{color:{C['text_dark']}; background:transparent; border:none;"
                                  f"border-bottom:3px solid {C['accent']};}}")
            else:
                btn.setStyleSheet(f"QPushButton {{color:{C['text_light']}; background:transparent; border:none;}}"
                                  f"QPushButton:hover {{background:#EEEEEE;}}")


# ── Qt 화면 ───────────────────────────────────────────────────────────────────

def _topbar(height):
    w = QWidget(); w.setFixedHeight(height)
    w.setStyleSheet(f"background:{C['topbar']};")
    return w

class ProfileScreen(QWidget):
    view_profile = pyqtSignal(int)
    go_novel     = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:white;")
        main = QVBoxLayout(self); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        tb_w = _topbar(LAYOUT["home_top"])
        tb = QHBoxLayout(tb_w); tb.setContentsMargins(16,0,16,0)
        t = QLabel("용의자 조사"); t.setFont(F("big",True))
        t.setStyleSheet(f"color:{C['text_white']};"); tb.addWidget(t); tb.addStretch()
        q = QPushButton("나가기"); q.setFont(F("label")); q.setFixedSize(54,30)
        q.setCursor(Qt.CursorShape.PointingHandCursor)
        q.setStyleSheet(f"QPushButton {{background:transparent; color:{C['text_light']};"
                        f"border:1px solid {C['text_light']}; border-radius:6px;}}"
                        f"QPushButton:hover {{background:rgba(255,255,255,30); color:white;}}")
        q.clicked.connect(self.go_novel.emit); tb.addWidget(q)
        main.addWidget(tb_w)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        lw = QWidget(); lw.setStyleSheet(f"background:{C['bg_home']};")
        ll = QVBoxLayout(lw); ll.setContentsMargins(12,12,12,12); ll.setSpacing(10)
        for i,char in enumerate(CHARS): ll.addWidget(self._make_card(char,i))
        ll.addStretch(); scroll.setWidget(lw); main.addWidget(scroll, stretch=1)

    def _make_card(self, char, idx):
        card = QWidget()
        card.setStyleSheet("background:white; border-radius:14px;")
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.mousePressEvent = lambda _: self.view_profile.emit(idx)
        card.enterEvent = lambda _: card.setStyleSheet("background:#F0F0F0; border-radius:14px;")
        card.leaveEvent = lambda _: card.setStyleSheet("background:white; border-radius:14px;")

        row = QHBoxLayout(card); row.setContentsMargins(14,12,14,12); row.setSpacing(14)
        row.addWidget(Avatar(char,size=52), alignment=Qt.AlignmentFlag.AlignVCenter)
        info = QVBoxLayout(); info.setSpacing(4)
        nm = QLabel(char["name"]); nm.setFont(F("body",True))
        nm.setStyleSheet(f"color:{C['text_dark']}; background:transparent;"); info.addWidget(nm)
        mid = QHBoxLayout(); mid.setSpacing(6)
        badge = QLabel(char["type"]); badge.setFont(F("small"))
        badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        badge.setStyleSheet(f"background:{char['bubble_color']}; color:white; border-radius:7px; padding:1px 6px;")
        mid.addWidget(badge); mid.addStretch(); info.addLayout(mid)
        hint = QLabel(char["hint"]); hint.setFont(F("small")); hint.setWordWrap(True)
        hint.setStyleSheet(f"color:{C['text_light']}; background:transparent;"); info.addWidget(hint)
        row.addLayout(info, stretch=1)
        return card

    def refresh(self): pass


class ProfileDetailScreen(QWidget):
    go_back = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{C['bg_home']};")
        main = QVBoxLayout(self); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        tb_w = _topbar(LAYOUT["home_top"])
        tb = QHBoxLayout(tb_w); tb.setContentsMargins(10,0,16,0)
        back = QPushButton("‹"); back.setFont(F("big",True)); back.setFixedSize(32,40)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"color:{C['text_white']}; background:transparent; border:none;")
        back.clicked.connect(self.go_back.emit); tb.addWidget(back)
        self._title = QLabel(); self._title.setFont(F("body",True))
        self._title.setStyleSheet(f"color:{C['text_white']}; background:transparent;")
        tb.addWidget(self._title); tb.addStretch()
        main.addWidget(tb_w)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        content = QWidget(); content.setStyleSheet(f"background:{C['bg_home']};")
        cl = QVBoxLayout(content); cl.setContentsMargins(24,28,24,24); cl.setSpacing(0)

        av_box = QHBoxLayout(); self._av_inner = QHBoxLayout()
        av_box.addStretch(); av_box.addLayout(self._av_inner); av_box.addStretch()
        cl.addLayout(av_box); cl.addSpacing(16)

        self._name = QLabel(); self._name.setFont(F("big",True))
        self._name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._name.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        cl.addWidget(self._name); cl.addSpacing(8)

        mid = QHBoxLayout(); mid.addStretch()
        self._badge = QLabel(); self._badge.setFont(F("label"))
        self._badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        mid.addWidget(self._badge); mid.addStretch()
        cl.addLayout(mid); cl.addSpacing(24)

        def _sep(): s=QFrame(); s.setFrameShape(QFrame.Shape.HLine); s.setStyleSheet(f"color:{C['divider']};"); return s

        cl.addWidget(_sep()); cl.addSpacing(20)
        ht = QLabel("말투 / 조사 특징"); ht.setFont(F("small",True))
        ht.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        cl.addWidget(ht); cl.addSpacing(6)
        self._hint = QLabel(); self._hint.setFont(F("body")); self._hint.setWordWrap(True)
        self._hint.setStyleSheet(f"color:{C['text_dark']}; background:transparent;")
        cl.addWidget(self._hint); cl.addSpacing(20)

        cl.addWidget(_sep()); cl.addSpacing(20)
        gt = QLabel("첫 진술"); gt.setFont(F("small",True))
        gt.setStyleSheet(f"color:{C['text_light']}; background:transparent;")
        cl.addWidget(gt); cl.addSpacing(8)
        self._greet = QLabel(); self._greet.setFont(F("body")); self._greet.setWordWrap(True)
        self._greet.setStyleSheet(f"background:{C['bubble_her']}; border-radius:12px;"
                                  f"padding:12px 16px; color:{C['text_dark']};")
        cl.addWidget(self._greet); cl.addStretch()

        scroll.setWidget(content); main.addWidget(scroll, stretch=1)

    def show_char(self, char):
        while self._av_inner.count():
            item = self._av_inner.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self._av_inner.addWidget(Avatar(char, size=80))
        self._title.setText(char["name"]); self._name.setText(char["name"])
        self._badge.setText(char["type"])
        self._badge.setStyleSheet(f"background:{char['bubble_color']}; color:white;"
                                  f"border-radius:9px; padding:2px 10px;")
        self._hint.setText(char["hint"])
        self._greet.setText(f'"{char["greeting"]}"')


class ChatListScreen(QWidget):
    enter_chat = pyqtSignal(int)
    go_back    = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:white;")
        main = QVBoxLayout(self); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        tb_w = _topbar(LAYOUT["home_top"])
        tb = QHBoxLayout(tb_w); tb.setContentsMargins(16,0,16,0)
        t = QLabel("대화방"); t.setFont(F("big",True))
        t.setStyleSheet(f"color:{C['text_white']};"); tb.addWidget(t); tb.addStretch()
        q = QPushButton("나가기"); q.setFont(F("label")); q.setFixedSize(54,30)
        q.setCursor(Qt.CursorShape.PointingHandCursor)
        q.setStyleSheet(f"QPushButton {{background:transparent; color:{C['text_light']};"
                        f"border:1px solid {C['text_light']}; border-radius:6px;}}"
                        f"QPushButton:hover {{background:rgba(255,255,255,30); color:white;}}")
        q.clicked.connect(self.go_back.emit); tb.addWidget(q)
        main.addWidget(tb_w)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background:transparent;")
        lw = QWidget(); lw.setStyleSheet(f"background:{C['bg_home']};")
        ll = QVBoxLayout(lw); ll.setContentsMargins(0,0,0,0); ll.setSpacing(0)
        self._items = []
        for i,char in enumerate(CHARS):
            item = CharItem(char,i); item.clicked.connect(self.enter_chat.emit)
            self._items.append(item); ll.addWidget(item)
            if i < len(CHARS)-1:
                sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
                sep.setStyleSheet(f"color:{C['divider']}; margin:0 12px;"); ll.addWidget(sep)
        ll.addStretch(); scroll.setWidget(lw); main.addWidget(scroll, stretch=1)

    def update_preview(self, idx, text): self._items[idx].set_preview(text)
    def update_unread(self, idx, count): self._items[idx].set_unread(count)


class ChatScreen(QWidget):
    go_home         = pyqtSignal()
    preview_updated = pyqtSignal(int, str)

    def __init__(self, char, idx, ws_client, parent=None):
        super().__init__(parent)
        self.char = char; self.idx = idx
        self._ws = ws_client; self._waiting_reply = False
        self._build_ui()
        self._add_msg(char["greeting"], is_mine=False)

    def _build_ui(self):
        self.setStyleSheet(f"background:{C['bg_chat']};")
        main = QVBoxLayout(self); main.setContentsMargins(0,0,0,0); main.setSpacing(0)

        tb_w = _topbar(LAYOUT["topbar"])
        tb = QHBoxLayout(tb_w); tb.setContentsMargins(10,0,14,0); tb.setSpacing(10)
        back = QPushButton("‹"); back.setFont(F("big",True)); back.setFixedSize(32,40)
        back.setCursor(Qt.CursorShape.PointingHandCursor)
        back.setStyleSheet(f"color:{C['text_white']}; background:transparent; border:none;")
        back.clicked.connect(self.go_home.emit); tb.addWidget(back)
        tb.addWidget(Avatar(self.char, size=36))
        info = QVBoxLayout(); info.setSpacing(1)
        nm = QLabel(self.char["name"]); nm.setFont(F("body",True))
        nm.setStyleSheet(f"color:{C['text_white']}; background:transparent;")
        sub = QLabel(f"{self.char['type']} 담당"); sub.setFont(F("small"))
        sub.setStyleSheet("color:#AAAABD; background:transparent;")
        info.addWidget(nm); info.addWidget(sub); tb.addLayout(info); tb.addStretch()
        main.addWidget(tb_w)

        self.scroll = QScrollArea(); self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"""
            QScrollArea {{background:{C['bg_chat']}; border:none;}}
            QScrollBar:vertical {{width:6px; background:transparent; margin:4px 2px;}}
            QScrollBar::handle:vertical {{background:rgba(0,0,0,30); border-radius:3px; min-height:32px;}}
            QScrollBar::handle:vertical:hover {{background:rgba(0,0,0,55);}}
            QScrollBar::handle:vertical:pressed {{background:rgba(0,0,0,80);}}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{height:0;}}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{background:none;}}
        """)
        wrap = QWidget(); wrap.setStyleSheet(f"background:{C['bg_chat']};")
        self.msg_layout = QVBoxLayout(wrap)
        self.msg_layout.setContentsMargins(0,8,0,8); self.msg_layout.setSpacing(2)
        self.msg_layout.addStretch(); self.scroll.setWidget(wrap)
        main.addWidget(self.scroll, stretch=1)

        self.typing_row = QWidget()
        self.typing_row.setStyleSheet(f"background:{C['bg_chat']};")
        self.typing_row.setVisible(False)
        tr = QHBoxLayout(self.typing_row); tr.setContentsMargins(8,4,8,4); tr.setSpacing(6)
        tr.addWidget(Avatar(self.char,size=28), alignment=Qt.AlignmentFlag.AlignTop)
        self.typing_lbl = QLabel("···"); self.typing_lbl.setFont(F("body"))
        self.typing_lbl.setStyleSheet(
            f"background:{C['bubble_her']}; border-radius:12px; padding:6px 14px; color:{C['text_mid']};")
        tr.addWidget(self.typing_lbl); tr.addStretch()
        main.addWidget(self.typing_row)

        ia_w = QWidget()
        ia_w.setStyleSheet(f"background:{C['input_bg']}; border-top:1px solid {C['nav_border']};")
        ia = QHBoxLayout(ia_w); ia.setContentsMargins(8,8,8,8); ia.setSpacing(6)
        self.input = ChatInput(); self.input.setFont(F("body"))
        self.input.setStyleSheet(
            f"ChatInput {{background:white; border:1px solid #C3C3C3;"
            f"border-radius:{RADIUS['input']}px; padding:4px 14px; color:{C['text_dark']};}}"
            f"ChatInput:focus {{border:1px solid #AAAACC;}}")
        self.input.send_requested.connect(self._send); ia.addWidget(self.input, stretch=1)
        send_btn = QPushButton("전송"); send_btn.setFont(F("label",True))
        send_btn.setFixedSize(BTN["w"],BTN["h"]); send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet(
            f"QPushButton {{background:{C['accent']}; color:{C['text_dark']}; border-radius:{RADIUS['button']}px;}}"
            f"QPushButton:hover {{background:#EED400;}}")
        send_btn.clicked.connect(self._send); ia.addWidget(send_btn)
        main.addWidget(ia_w)

        self._typing_timer = QTimer(self); self._typing_timer.timeout.connect(self._anim_typing)
        self._typing_frame = 0

        self._popup = QLabel("",self); self._popup.setFont(F("big",True))
        self._popup.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._popup.setFixedWidth(W); self._popup.move(0, H//2-100)
        self._popup.setVisible(False)
        self._opacity_fx = QGraphicsOpacityEffect(); self._popup.setGraphicsEffect(self._opacity_fx)
        self._popup_timer = QTimer(self); self._popup_timer.timeout.connect(self._fade_popup)
        self._popup_alpha = 0.0

    def _add_msg(self, text, is_mine, score=0):
        self.msg_layout.addWidget(ChatBubble(text, is_mine, self.char, score, now()))
        QTimer.singleShot(30, self._scroll_bottom)
        self.preview_updated.emit(self.idx, text)

    def _scroll_bottom(self):
        sb = self.scroll.verticalScrollBar(); sb.setValue(sb.maximum())

    def _send(self):
        txt = self.input.toPlainText().strip()
        if not txt or self._waiting_reply: return
        self.input.clear(); self.input.setFixedHeight(38)
        self._add_msg(txt, is_mine=True); self.char["unread"] = 0
        self._waiting_reply = True; self.typing_row.setVisible(True)
        self._typing_timer.start(400)
        self._ws.send({"type":"chat","char_id":self.idx,"msg":txt})

    def _anim_typing(self):
        self.typing_lbl.setText(["·  ","·· ","···"][self._typing_frame%3])
        self._typing_frame += 1

    def receive_reply(self, data):
        self._waiting_reply = False; self.typing_row.setVisible(False); self._typing_timer.stop()
        self._add_msg(data["msg"], is_mine=False, score=data.get("score",0))
        delta = data.get("score_delta",0)
        col = C["score_up"] if delta > 0 else C["score_down"]
        self._popup.setText("단서 획득" if delta > 0 else "교란 주의")
        self._popup.setStyleSheet(f"color:{col}; background:transparent; font-size:{FS['body']}pt; font-weight:bold;")
        self._popup.setVisible(True); self._popup_alpha = 1.0
        self._opacity_fx.setOpacity(1.0); self._popup_timer.start(30)

    def _fade_popup(self):
        self._popup_alpha -= 0.04
        if self._popup_alpha <= 0:
            self._popup.setVisible(False); self._popup_timer.stop()
        else:
            self._opacity_fx.setOpacity(self._popup_alpha)


# ── WebSocket ─────────────────────────────────────────────────────────────────

class WSClient(QObject):
    message_received = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self._ws = websocket.WebSocketApp(
            "ws://localhost:3000",
            on_message = lambda ws,m: self.message_received.emit(json.loads(m)),
            on_error   = lambda ws,e: print("[WS] 에러:", e),
            on_open    = lambda ws:   print("[WS] 연결됨"),
            on_close   = lambda ws,*_: print("[WS] 종료"),
        )
        t = threading.Thread(target=self._ws.run_forever, kwargs={"reconnect":5})
        t.daemon = True; t.start()

    def send(self, data):
        try: self._ws.send(json.dumps(data))
        except Exception as e: print("[WS] 전송 실패:", e)


# ── 통합 창 ─────────────────────────────────────────────────────────────────

class PhoneContainer(QWidget):
    go_game = pyqtSignal()

    _FULL_W = W + 32

    def __init__(self, ws_client, parent=None):
        super().__init__(parent)
        self.setObjectName("phonePanel")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("#phonePanel { background:#1a1a2e; }")
        self._anim = None
        self._visible = False
        self.setFixedWidth(self._FULL_W)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(8)

        notch = QFrame()
        notch.setObjectName("notch")
        notch.setFixedSize(80, 10)
        notch.setStyleSheet("#notch { background:#444; border-radius:5px; }")
        nr = QHBoxLayout(); nr.addStretch(); nr.addWidget(notch); nr.addStretch()
        outer.addLayout(nr)

        screen_frame = QFrame()
        screen_frame.setObjectName("phoneScreen")
        screen_frame.setFixedSize(W, H)
        screen_frame.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        screen_frame.setStyleSheet("#phoneScreen { background:white; border-radius:8px; }")

        sl = QVBoxLayout(screen_frame)
        sl.setContentsMargins(0, 0, 0, 0); sl.setSpacing(0)

        self.stack = QStackedWidget()
        self.chat_list = ChatListScreen()
        self.stack.addWidget(self.chat_list)

        self._chats = []
        for i, char in enumerate(CHARS):
            cs = ChatScreen(char, i, ws_client)
            cs.go_home.connect(self._go_chat_list)
            cs.preview_updated.connect(self.chat_list.update_preview)
            self._chats.append(cs)
            self.stack.addWidget(cs)

        self.chat_list.enter_chat.connect(self._enter_chat)
        self.chat_list.go_back.connect(self.slide_out)

        sl.addWidget(self.stack, stretch=1)
        self.stack.setCurrentWidget(self.chat_list)
        outer.addWidget(screen_frame, alignment=Qt.AlignmentFlag.AlignHCenter)

        home_btn = QFrame()
        home_btn.setObjectName("homeBtn")
        home_btn.setFixedSize(50, 50)
        home_btn.setStyleSheet("#homeBtn { background:#444; border-radius:25px; }")
        hbr = QHBoxLayout(); hbr.addStretch(); hbr.addWidget(home_btn); hbr.addStretch()
        outer.addLayout(hbr)

    # ── 슬라이드 애니메이션 ──────────────────────────────────────────────────────

    def slide_in(self):
        self.stack.setCurrentWidget(self.chat_list)
        self._visible = True
        self.raise_()
        self._animate(QPoint(self.parent().width() - self._FULL_W, 0), QEasingCurve.Type.OutCubic)

    def slide_out(self):
        self._visible = False
        self._animate(QPoint(self.parent().width(), 0), QEasingCurve.Type.InCubic, on_finish=self._after_slide_out)

    def _after_slide_out(self):
        self.go_game.emit()

    def _animate(self, end_pos, curve, on_finish=None):
        if self._anim:
            self._anim.stop()
        a = QPropertyAnimation(self, b"pos", self)
        a.setDuration(280)
        a.setStartValue(self.pos())
        a.setEndValue(end_pos)
        a.setEasingCurve(curve)
        if on_finish:
            a.finished.connect(on_finish)
        self._anim = a
        a.start()

    # ── 채팅 UI 헬퍼 ─────────────────────────────────────────────────────────────

    def _go_chat_list(self):
        self.stack.setCurrentWidget(self.chat_list)

    def _enter_chat(self, idx):
        CHARS[idx]["unread"] = 0
        self.chat_list.update_unread(idx, 0)
        self.stack.setCurrentWidget(self._chats[idx])
        self._chats[idx].input.setFocus()

    def on_ws(self, data):
        if data.get("type") == "reply":
            idx = data.get("char_id")
            if idx is not None and 0 <= idx < len(self._chats):
                self._chats[idx].receive_reply(data)
                if self.stack.currentWidget() is not self._chats[idx]:
                    CHARS[idx]["unread"] += 1
                    self.chat_list.update_unread(idx, CHARS[idx]["unread"])


class _TitleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("선생님, 맞죠?")
        self.setModal(True)
        self.resize(VN_W, VN_H)
        self.setStyleSheet("background:#0f0a19;")

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(16)

        title = QLabel("선생님, 맞죠?")
        title.setFont(QFont("맑은 고딕", 30, QFont.Weight.Bold))
        title.setStyleSheet("color:#ffdc50;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        sub = QLabel("서버실에서 탈출하고 범인을 찾아라")
        sub.setFont(QFont("맑은 고딕", 11))
        sub.setStyleSheet("color:#8c839e;")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub)

        lay.addSpacing(30)

        BTN_STYLE = """
            QPushButton {
                background:#3c3220; color:#ffdc50; border:2px solid #ffdc50;
                border-radius:12px; font-size:15px; font-weight:bold;
                min-width:220px; min-height:54px;
            }
            QPushButton:hover { background:#ffdc50; color:#0f0a19; }
        """
        btn_start = QPushButton("게임 시작")
        btn_start.setStyleSheet(BTN_STYLE)
        btn_start.clicked.connect(self.accept)
        lay.addWidget(btn_start, alignment=Qt.AlignmentFlag.AlignHCenter)

        btn_rank = QPushButton("랭킹 확인")
        btn_rank.setStyleSheet(BTN_STYLE)
        btn_rank.clicked.connect(lambda: RankingDialog(self).exec())
        lay.addWidget(btn_rank, alignment=Qt.AlignmentFlag.AlignHCenter)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("선생님, 맞죠?")
        self.setStyleSheet("background:#0f0a19;")
        self.resize(1440, 860)

        ws = WSClient()

        central = QWidget()
        self.setCentralWidget(central)

        self._game_w = EscapeRoomWidget(central)
        self._phone  = PhoneContainer(ws, central)

        ws.message_received.connect(self._phone.on_ws)
        self._game_w.phone_requested.connect(self._phone.slide_in)
        self._phone.go_game.connect(self._game_w.setFocus)

        self._game_w.setFocus()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        r = self.centralWidget().rect()
        self._game_w.setGeometry(r)
        self._phone.setFixedHeight(r.height())
        if self._phone._visible:
            self._phone.move(r.width() - PhoneContainer._FULL_W, 0)
        else:
            self._phone.move(r.width(), 0)


# ── 진입점 ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("맑은 고딕", FS["body"]))

    pygame.init()
    pygame.display.set_mode((1, 1), pygame.NOFRAME | pygame.HIDDEN)

    dlg = _TitleDialog()
    if dlg.exec() != QDialog.DialogCode.Accepted:
        pygame.quit()
        sys.exit(0)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

