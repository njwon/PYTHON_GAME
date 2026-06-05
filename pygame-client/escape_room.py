import os
import math
import pygame
from config import VN_W, VN_H


# 이미지 파일 경로 만들기
this_folder   = os.path.dirname(os.path.abspath(__file__))
client_folder = os.path.dirname(this_folder)
root_folder   = os.path.dirname(client_folder)
asset_folder  = os.path.join(root_folder, "노정원꺼")
IMG_DIR  = os.path.join(asset_folder, "이미지")
CHAR_DIR = os.path.join(asset_folder, "캐릭터")
CLUE_DIR = os.path.join(asset_folder, "단서")

def _i(filename): return os.path.join(IMG_DIR,  filename)
def _d(filename): return os.path.join(CLUE_DIR, filename)


# 게임 기본 설정값
SPEED   = 3.5   # 플레이어 속도
WALL_T  = 45    # 벽 두께
INTER_R = 85    # 상호작용 가능 거리
PL_R    = 16    # 플레이어 크기(반지름)

# 방 경계선 좌표
RX1 = WALL_T
RX2 = VN_W - WALL_T
RY1 = WALL_T + 3
RY2 = VN_H - WALL_T

# 색상 모음
C = {
    "hud"    : ( 30,  13,   0),
    "yellow" : (255, 224, 102),
    "green"  : (136, 221,  68),
    "white"  : (255, 255, 255),
    "black"  : (  0,   0,   0),
    "gray"   : (136, 136, 136),
    "dgray"  : ( 60,  60,  60),
    "bubble" : (255, 252, 218),
    "bub_b"  : (100,  72,  18),
    "bub_t"  : ( 35,  18,   2),
    "p_dark" : ( 34,  85, 170),
    "p_light": (123, 188, 245),
    "p_rim"  : ( 26,  64, 128),
    "safe_bg": ( 20,  20,  30),
    "safe_bd": (200, 180,  60),
}

# 모스부호 패턴 (켜짐여부, 지속프레임)
MORSE_SEQ = [
    (True,  10), (False,  7),
    (True,  26), (False,  7),
    (True,  10), (False,  7),
    (True,  10), (False, 35),
]
MORSE_REPEATS = 3


# 방 안에 있는 오브젝트 하나하나를 나타내는 클래스
class RoomObj:
    def __init__(self, name, x, y, w, h, label, img_path=None, blocking=True):
        self.name     = name
        self.rect     = pygame.Rect(x, y, w, h)
        self.label    = label       # 이미지 없을 때 대신 보여줄 이름
        self.img_path = img_path
        self.blocking = blocking    # True면 플레이어가 통과 못 함
        self.image    = None        # 이미지는 처음 접근할 때 한 번만 로드

    def get_center_x(self):
        return self.rect.centerx

    def get_center_y(self):
        return self.rect.centery

    def get_distance(self, player_x, player_y):
        # 플레이어까지 직선 거리 계산
        dx = player_x - self.rect.centerx
        dy = player_y - self.rect.centery
        return math.sqrt(dx * dx + dy * dy)

    def get_image(self):
        # 이미지를 처음 불렀을 때만 파일에서 읽고, 그 다음부터는 저장된 거 씀
        if self.image is None and self.img_path and os.path.exists(self.img_path):
            try:
                raw = pygame.image.load(self.img_path).convert_alpha()
                self.image = pygame.transform.scale(raw, (self.rect.w, self.rect.h))
            except:
                pass  # 이미지 로드 실패하면 그냥 None으로 둠
        return self.image


# 게임 전체 상태를 관리하는 클래스
class EscapeRoomGame:
    SAFE_CODE = "0780"  # 금고 정답

    def __init__(self):
        self.objs = [
            # 가구들 (blocking=True → 못 지나감)
            RoomObj("door",       248, RY1,     100, 175, "문",   _i("문.png"),   blocking=True),
            RoomObj("bookshelf",  560, RY1+5,    75, 165, "책장", _i("책장.png"), blocking=True),
            RoomObj("desk",        65, 288,     175, 107, "책상", _i("책상.png"), blocking=True),
            RoomObj("chair",       92, 358,      55,  65, "의자", _i("의자.png"), blocking=True),
            RoomObj("safe",       355, 333,      72,  72, "금고", _i("금고.png"), blocking=True),
            # 소품들 (blocking=False → 지나갈 수 있음)
            RoomObj("chocolate",  120, 280,      55,  46, "초콜릿", _i("초콜릿.png"), blocking=False),
            RoomObj("drawer",     243, 288,      62,  85, "서랍",   _i("서랍.png"),   blocking=False),
            RoomObj("switch",     365, 142,      30,  44, "스위치", _i("스위치.png"), blocking=False),
            RoomObj("key",        298, 368,      45,  45, "열쇠",   _i("열쇠.png"),   blocking=False),
            RoomObj("book",       238, 384,      50,  48, "책",     _i("책.png"),     blocking=False),
            RoomObj("wall_prob",  440, RY1+25,   70,  60, "문제",   _d("금고비번문제.png"), blocking=False),
        ]
        self.reset()

    def reset(self):
        # 플레이어 시작 위치
        self.px = 390.0
        self.py = 290.0

        # 단서 수집 여부 (6개 다 True면 클리어)
        self.saw_chocolate = False
        self.read_drawer   = False
        self.found_key     = False
        self.switch_used   = False
        self.read_book     = False
        self.safe_open     = False

        # 금고 비밀번호 입력 관련
        self.safe_mode  = False   # True면 입력창 표시
        self.safe_input = ""      # 지금까지 입력한 숫자

        # 모스부호 전등 깜박임 관련
        self.morse_active = False
        self.morse_step   = 0
        self.morse_timer  = 0
        self.morse_repeat = 0
        self.lights_on    = True

        # 팝업 이미지 관련
        self.popup_img    = ""
        self.popup_active = False

        # 말풍선 관련
        self.bubble = ""
        self.btimer = 0
        self.won    = False

    def set_pos(self, px, py):
        self.px = px
        self.py = py

    def clear_bubble(self):
        self.bubble = ""

    def tick_bubble(self):
        # 말풍선 타이머 줄이기, 0 되면 숨김
        if self.btimer > 0:
            self.btimer -= 1
            if self.btimer == 0:
                self.bubble = ""

    def show_message(self, text, frames=240):
        # 말풍선에 메시지 띄우기
        self.bubble = text
        self.btimer = frames  # 240프레임 = 4초

    def check_cleared(self):
        # 6개 단서 다 모았는지 확인
        if self.saw_chocolate and self.read_drawer and self.found_key and \
           self.switch_used and self.read_book and self.safe_open:
            self.won = True

    def tick_morse(self):
        # 모스부호 깜박임 처리 (매 프레임 호출)
        if not self.morse_active:
            return

        self.morse_timer -= 1
        if self.morse_timer > 0:
            return  # 아직 이 단계 진행 중

        # 다음 단계로 넘어가기
        self.morse_step += 1
        if self.morse_step >= len(MORSE_SEQ):
            # 시퀀스 한 번 끝남 → 반복 횟수 체크
            self.morse_step = 0
            self.morse_repeat += 1
            if self.morse_repeat >= MORSE_REPEATS:
                # 3번 다 끝남
                self.morse_active = False
                self.lights_on    = True
                self.show_message("· - · ·\n모스부호로 'ㄱ'을 나타낸다.")
                return

        on, dur = MORSE_SEQ[self.morse_step]
        self.lights_on   = on
        self.morse_timer = dur

    def interact(self):
        # E 키 눌렀을 때 - 가장 가까운 오브젝트 찾아서 상호작용
        nearest  = None
        min_dist = float(INTER_R)

        for obj in self.objs:
            d = obj.get_distance(self.px, self.py)
            if d < min_dist:
                min_dist = d
                nearest  = obj

        if nearest is None:
            self.show_message("주변에 상호작용할 것이 없다.")
            return

        name = nearest.name

        if name == "door":
            if self.won:
                self.show_message("탈출 성공!\n선생님들을 조사하자!")
            else:
                self.show_message("문이 잠겨있다.\n단서를 더 수집해야 한다.")

        elif name == "bookshelf":
            self.show_message("책들이 빼곡히 꽂혀있다.\n특별한 것은 없어 보인다.")

        elif name == "chair":
            self.show_message("평범한 의자다.")

        elif name == "desk" or name == "chocolate":
            self.saw_chocolate = True
            self.show_message("초콜릿이 책상 위에 있다.\n오른쪽 대각선으로 놓여있다.")

        elif name == "drawer":
            if not self.saw_chocolate:
                self.show_message("먼저 주변을 살펴봐야 할 것 같다.")
            else:
                self.read_drawer = True
                self.show_message("[포스트잇]\n초콜릿의 방향을 보면\n어느 손잡이인지 알 수 있다.")
                self.check_cleared()

        elif name == "switch":
            if not self.switch_used:
                self.switch_used  = True
                self.morse_active = True
                self.morse_step   = 0
                self.morse_repeat = 0
                on, dur = MORSE_SEQ[0]
                self.lights_on   = on
                self.morse_timer = dur
                self.show_message("스위치를 눌렀다.\n전등이 이상하게 깜박인다...")
            else:
                self.show_message("· - · ·\n모스부호로 'ㄱ'을 나타낸다.")

        elif name == "key":
            self.found_key = True
            self.show_message("[메모]\n담임을 맡은 선생님이\n범인인 것 같다.")
            self.check_cleared()

        elif name == "book":
            self.read_book = True
            self.show_message("[주석]\n50kg인 나를 들 수 있는\n선생님을 알아보자!")
            self.check_cleared()

        elif name == "wall_prob":
            self.popup_img    = _d("금고비번문제.png")
            self.popup_active = True
            self.show_message("벽에 붙어있는 문제다.\n풀면 숫자가 나올 것 같다.")

        elif name == "safe":
            if self.safe_open:
                self.show_message("[메모]\n유재석 = 466\n(이름의 획수)")
            else:
                self.safe_mode  = True
                self.safe_input = ""

    def input_safe(self, key):
        # 금고 숫자 입력 처리
        if not self.safe_mode:
            return

        if key == "cancel":
            self.safe_mode  = False
            self.safe_input = ""

        elif key == "back":
            self.safe_input = self.safe_input[:-1]  # 마지막 글자 지우기

        elif key.isdigit() and len(self.safe_input) < 4:
            self.safe_input += key
            if len(self.safe_input) == 4:
                # 4자리 다 입력됨 - 정답 확인
                if self.safe_input == self.SAFE_CODE:
                    self.safe_open  = True
                    self.safe_mode  = False
                    self.show_message("[금고 열림!]\n메모: 유재석 = 466\n(이름의 획수)")
                    self.check_cleared()
                else:
                    self.show_message("틀린 비밀번호다.")
                    self.safe_input = ""


# ─── 렌더링 관련 ─────────────────────────────────────────────────────────────

# 배경 그릴 때 쓰는 좌표값
_AX = RX1 + int((RX2 - RX1) * 0.751)
_AY = RY1 + int((RY2 - RY1) * 0.574)
_BY = RY1 + int((RY2 - RY1) * 0.745)

# 하단 버튼 위치
_BTN_W = 70
_BTN_H = 26
_BTN_Y       = RY2 + (VN_H - RY2 - _BTN_H) // 2
_BTN_CONTACT = pygame.Rect(VN_W - _BTN_W - 10,   _BTN_Y, _BTN_W, _BTN_H)
_BTN_QUIT    = pygame.Rect(VN_W - _BTN_W*2 - 20, _BTN_Y, _BTN_W, _BTN_H)

# 이미지 캐시 (같은 이미지 여러 번 안 불러오려고)
img_cache = {}

def load_img(path, w, h):
    key = (path, w, h)
    if key not in img_cache:
        try:
            raw = pygame.image.load(path).convert_alpha()
            img_cache[key] = pygame.transform.scale(raw, (w, h))
        except:
            img_cache[key] = None
    return img_cache.get(key)

def check_collision(game, cx, cy):
    # 플레이어가 (cx, cy)에 있을 때 오브젝트에 막히는지 확인
    for obj in game.objs:
        if not obj.blocking:
            continue  # 통과 가능한 건 무시
        r = obj.rect
        # 플레이어 원과 사각형 오브젝트 충돌 판정
        nearest_x = max(r.left, min(cx, r.right))
        nearest_y = max(r.top,  min(cy, r.bottom))
        dist = math.sqrt((cx - nearest_x)**2 + (cy - nearest_y)**2)
        if dist < PL_R:
            return True  # 충돌함
    return False  # 충돌 안 함


def load_font(size, bold=False):
    # 한글 폰트 찾아서 로드
    win_font = rf"C:\Windows\Fonts\malgun{'bd' if bold else ''}.ttf"
    if os.path.exists(win_font):
        return pygame.font.Font(win_font, size)
    nanum_file = "NanumGothicBold.ttf" if bold else "NanumGothic.ttf"
    nanum_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts", nanum_file)
    if os.path.exists(nanum_path):
        return pygame.font.Font(nanum_path, size)
    return pygame.font.Font(None, size)  # 폰트 없으면 기본 폰트


# 화면 그리는 기능을 모아놓은 클래스
class Renderer:
    def __init__(self, screen, game):
        self.screen = screen
        self.game   = game
        self.facing_back = False  # 플레이어 방향 (True = 뒷모습)

        # 폰트 준비
        self.fonts = {
            "title" : load_font(16, bold=True),
            "label" : load_font(11, bold=True),
            "bub"   : load_font(11),
            "small" : load_font( 9),
            "hint"  : load_font( 9, bold=True),
            "safe"  : load_font(22, bold=True),
            "safe_s": load_font(12),
        }

        # 캐릭터 이미지 준비
        self.sprites = {
            "front": load_img(os.path.join(CHAR_DIR, "정면.png"), 34, 80),
            "back" : load_img(os.path.join(CHAR_DIR, "후면.png"), 30, 80),
        }

    def draw_centered(self, surf, y):
        # 텍스트를 화면 가로 중앙에 그리기
        x = (VN_W - surf.get_width()) // 2
        self.screen.blit(surf, (x, y))

    def draw_overlay(self, alpha):
        # 화면 전체를 반투명 검정으로 덮음
        overlay = pygame.Surface((VN_W, VN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

    def draw_bg(self):
        # 방 배경 그리기
        self.screen.fill((30, 13, 0))
        # 왼쪽 벽
        pygame.draw.polygon(self.screen, (255, 255, 255), [(RX1, _AY), (RX1, RY1), (_AX, RY1), (_AX, _AY)])
        # 오른쪽 벽
        pygame.draw.polygon(self.screen, (242, 242, 242), [(_AX, RY1), (RX2, RY1), (RX2, _BY), (_AX, _AY)])
        # 바닥
        pygame.draw.polygon(self.screen, (235, 232, 225), [(RX1, _AY), (_AX, _AY), (RX2, _BY), (RX2, RY2), (RX1, RY2)])
        # 경계선들
        pygame.draw.line(self.screen, (10, 10, 10), (_AX, RY1), (_AX, _AY), 1)
        pygame.draw.line(self.screen, (10, 10, 10), (RX1, _AY), (_AX, _AY), 1)
        pygame.draw.line(self.screen, (10, 10, 10), (_AX, _AY), (RX2, _BY), 1)
        # 방 테두리
        pygame.draw.rect(self.screen, (50, 35, 15), (RX1, RY1, RX2-RX1, RY2-RY1), 2)

    def draw_objects(self):
        # 오브젝트들 그리기
        for obj in self.game.objs:
            dist     = obj.get_distance(self.game.px, self.game.py)
            in_range = dist < INTER_R

            img = obj.get_image()
            if img:
                self.screen.blit(img, obj.rect.topleft)
            else:
                # 이미지 없으면 갈색 사각형으로 대체
                pygame.draw.rect(self.screen, (120, 80, 40), obj.rect, border_radius=4)
                text = self.fonts["label"].render(obj.label, True, C["white"])
                tx = obj.rect.centerx - text.get_width() // 2
                ty = obj.rect.centery - text.get_height() // 2
                self.screen.blit(text, (tx, ty))

            if in_range:
                # 가까이 있으면 노란 테두리 + E 뱃지 표시
                pygame.draw.rect(self.screen, C["yellow"], obj.rect, 2, border_radius=4)
                badge_x = obj.rect.centerx - 11
                badge_y = obj.rect.top - 20
                pygame.draw.rect(self.screen, C["yellow"], (badge_x, badge_y, 22, 15), border_radius=3)
                e_text = self.fonts["hint"].render("E", True, (50, 30, 0))
                ex = badge_x + (22 - e_text.get_width()) // 2
                ey = badge_y + (15 - e_text.get_height()) // 2
                self.screen.blit(e_text, (ex, ey))

    def draw_player(self):
        # 플레이어 그리기
        px = int(self.game.px)
        py = int(self.game.py)

        if self.facing_back:
            sprite = self.sprites["back"]
        else:
            sprite = self.sprites["front"]

        if sprite:
            sx = px - sprite.get_width() // 2
            sy = py - sprite.get_height() + PL_R
            self.screen.blit(sprite, (sx, sy))
        else:
            # 스프라이트 없으면 원으로 대체
            pygame.draw.circle(self.screen, C["p_dark"],  (px, py), PL_R)
            pygame.draw.circle(self.screen, C["p_light"], (px-4, py-4), PL_R-4)
            pygame.draw.circle(self.screen, C["p_rim"],   (px, py), PL_R, 1)

    def draw_dark(self):
        # 불 꺼진 상태 - 어둡게 덮기
        self.draw_overlay(200)

    def draw_bubble(self):
        # 말풍선 그리기
        game        = self.game
        font        = self.fonts["bub"]
        line_height = font.get_height()
        padding     = 10
        max_width   = int(VN_W * 0.35)

        # 텍스트 줄 나누기
        lines = []
        for line in game.bubble.split("\n"):
            if font.size(line)[0] <= max_width - padding * 2:
                lines.append(line)
            else:
                # 너무 길면 글자 단위로 자르기
                cur_line = ""
                for ch in line:
                    if font.size(cur_line + ch)[0] > max_width - padding * 2:
                        lines.append(cur_line)
                        cur_line = ch
                    else:
                        cur_line += ch
                if cur_line:
                    lines.append(cur_line)

        if not lines:
            return

        # 말풍선 크기 계산
        max_line_width = 0
        for line in lines:
            w = font.size(line)[0]
            if w > max_line_width:
                max_line_width = w

        bw = max_line_width + padding * 2 + 4
        bh = len(lines) * line_height + padding * 2

        px = int(game.px)
        bx = max(4, min(VN_W - bw - 4, px - bw // 2))

        # 페이드 아웃 (사라지기 직전에 투명해짐)
        if game.btimer > 45:
            alpha = 255
        else:
            alpha = max(0, int(255 * game.btimer / 45))

        tip_x      = max(9, min(bw - 9, px - bx))
        head_y     = int(game.py) - PL_R - 3
        show_below = (head_y - bh - 14) < RY1  # 위에 공간이 없으면 아래에 표시

        bs = pygame.Surface((bw, bh + 16), pygame.SRCALPHA)

        bubble_color = (C["bubble"][0], C["bubble"][1], C["bubble"][2], alpha)
        border_color = (C["bub_b"][0],  C["bub_b"][1],  C["bub_b"][2],  alpha)

        if show_below:
            # 꼬리가 위에 달린 말풍선
            pygame.draw.polygon(bs, bubble_color, [(tip_x-8, 14), (tip_x+8, 14), (tip_x, 1)])
            pygame.draw.rect(bs, bubble_color, (0, 14, bw, bh), border_radius=10)
            pygame.draw.rect(bs, border_color, (0, 14, bw, bh), 2, border_radius=10)
            by = int(game.py) + PL_R + 3
        else:
            # 꼬리가 아래에 달린 말풍선
            pygame.draw.rect(bs, bubble_color, (0, 0, bw, bh), border_radius=10)
            pygame.draw.rect(bs, border_color, (0, 0, bw, bh), 2, border_radius=10)
            pygame.draw.polygon(bs, bubble_color, [(tip_x-8, bh-1), (tip_x+8, bh-1), (tip_x, bh+13)])
            by = max(4, head_y - bh - 14)

        self.screen.blit(bs, (bx, by))

        text_start_y = (14 + padding) if show_below else padding
        for i, line in enumerate(lines):
            text_surf = font.render(line, True, C["bub_t"])
            if alpha < 255:
                text_surf.set_alpha(alpha)
            self.screen.blit(text_surf, (bx + padding, by + text_start_y + i * line_height))

    def draw_hud(self, mouse_pos):
        # 상단 HUD 그리기
        pygame.draw.rect(self.screen, C["hud"], (0, 0, VN_W, RY1-1))
        title = self.fonts["title"].render("서버실 탈출  ─  선생님이 범인!", True, C["yellow"])
        self.screen.blit(title, (12, (RY1 - 1 - title.get_height()) // 2))

        # 단서 수집 현황 아이콘
        icons = [
            ("초콜릿", self.game.saw_chocolate),
            ("서 랍",  self.game.read_drawer),
            ("스위치", self.game.switch_used),
            ("열 쇠",  self.game.found_key),
            ("책",     self.game.read_book),
            ("금 고",  self.game.safe_open),
        ]
        iw, ih, gap = 42, 18, 3
        sx = VN_W - len(icons) * (iw + gap) - 10
        iy = (RY1 - 1 - ih) // 2

        for j, (label, collected) in enumerate(icons):
            ix = sx + j * (iw + gap)
            if collected:
                icon_color = C["yellow"]
                text_color = (20, 10, 0)
            else:
                icon_color = (60, 60, 60)
                text_color = C["gray"]
            pygame.draw.rect(self.screen, icon_color, (ix, iy, iw, ih), border_radius=4)
            text = self.fonts["small"].render(label, True, text_color)
            tx = ix + (iw - text.get_width()) // 2
            ty = iy + (ih - text.get_height()) // 2
            self.screen.blit(text, (tx, ty))

        # 하단 HUD 그리기
        pygame.draw.rect(self.screen, C["hud"], (0, RY2+1, VN_W, VN_H-RY2))
        guide = self.fonts["small"].render("WASD : 이동     E : 상호작용", True, C["gray"])
        gx = (VN_W - guide.get_width()) // 2
        gy = RY2 + (VN_H - RY2 - guide.get_height()) // 2
        self.screen.blit(guide, (gx, gy))

        # 연락 버튼
        if _BTN_CONTACT.collidepoint(mouse_pos):
            contact_color = (255, 208, 0)
        else:
            contact_color = (255, 224, 102)
        pygame.draw.rect(self.screen, contact_color, _BTN_CONTACT, border_radius=8)
        contact_text = self.fonts["label"].render("연락", True, (26, 10, 0))
        self.screen.blit(contact_text, (
            _BTN_CONTACT.centerx - contact_text.get_width() // 2,
            _BTN_CONTACT.centery - contact_text.get_height() // 2
        ))

        # 나가기 버튼
        if _BTN_QUIT.collidepoint(mouse_pos):
            quit_color = (200, 60, 60)
        else:
            quit_color = (160, 50, 50)
        pygame.draw.rect(self.screen, quit_color, _BTN_QUIT, border_radius=8)
        quit_text = self.fonts["label"].render("나가기", True, (255, 220, 220))
        self.screen.blit(quit_text, (
            _BTN_QUIT.centerx - quit_text.get_width() // 2,
            _BTN_QUIT.centery - quit_text.get_height() // 2
        ))

    def draw_win(self):
        # 클리어 화면
        self.draw_overlay(175)
        cy = VN_H // 2

        t1 = self.fonts["title"].render("서버실 탈출!", True, C["yellow"])
        t2 = self.fonts["label"].render("이제 선생님들을 조사하라!", True, C["white"])
        t3 = self.fonts["small"].render("[ E ] 를 눌러 스마트폰으로 이동", True, C["gray"])

        self.draw_centered(t1, cy - 38)
        self.draw_centered(t2, cy + 10)
        self.draw_centered(t3, cy + 44)

    def draw_safe_overlay(self):
        # 금고 비밀번호 입력창
        self.draw_overlay(160)
        bw, bh = 300, 160
        bx = (VN_W - bw) // 2
        by = (VN_H - bh) // 2

        pygame.draw.rect(self.screen, C["safe_bg"], (bx, by, bw, bh), border_radius=14)
        pygame.draw.rect(self.screen, C["safe_bd"], (bx, by, bw, bh), 2, border_radius=14)

        # 안내 문구
        t1 = self.fonts["safe_s"].render("금고 비밀번호 (숫자 4자리)", True, C["yellow"])
        self.screen.blit(t1, (bx + (bw - t1.get_width()) // 2, by + 18))

        # 입력 숫자 표시 (빈 자리는 _)
        display_text = "  ".join(self.game.safe_input.ljust(4, "_"))
        t2 = self.fonts["safe"].render(display_text, True, C["white"])
        self.screen.blit(t2, (bx + (bw - t2.get_width()) // 2, by + 58))

        # 조작법 안내
        t3 = self.fonts["small"].render("0~9 입력  |  Backspace 지우기  |  ESC 취소", True, C["gray"])
        self.screen.blit(t3, (bx + (bw - t3.get_width()) // 2, by + 120))

    def draw_popup(self):
        # 팝업 이미지 표시 (벽에 붙은 문제 등)
        self.draw_overlay(200)
        pw = VN_W - 60
        ph = min(int(pw * 844 / 1863), VN_H - 80)
        img = load_img(self.game.popup_img, pw, ph)
        if img:
            ix = (VN_W - pw) // 2
            iy = (VN_H - ph) // 2
            pygame.draw.rect(self.screen, (255, 255, 255), (ix-3, iy-3, pw+6, ph+6), border_radius=8)
            self.screen.blit(img, (ix, iy))
        hint = self.fonts["small"].render("아무 키나 눌러 닫기", True, C["gray"])
        self.draw_centered(hint, VN_H - 28)

    def draw_all(self, mouse_pos):
        # 매 프레임 호출 - 순서대로 모든 걸 그림
        self.draw_bg()       # 배경
        self.draw_objects()  # 오브젝트
        self.draw_player()   # 플레이어

        if not self.game.lights_on:
            self.draw_dark()   # 불 꺼짐

        if self.game.bubble:
            self.draw_bubble() # 말풍선

        self.draw_hud(mouse_pos)  # HUD

        if self.game.won:
            self.draw_win()    # 클리어 화면

        if self.game.safe_mode:
            self.draw_safe_overlay()  # 금고 입력창

        if self.game.popup_active and self.game.popup_img:
            self.draw_popup()  # 팝업 이미지


# 게임 실행 함수
def run_escape_room(on_phone=None):
    pygame.init()
    pygame.display.set_caption("서버실 탈출  ─  선생님이 범인!")
    screen = pygame.display.set_mode((VN_W, VN_H))
    clock  = pygame.time.Clock()

    game         = EscapeRoomGame()
    renderer     = Renderer(screen, game)
    go_phone     = False   # 폰 창 열기 예약 플래그
    phone_opened = False   # 이미 열었는지 여부 (중복 방지)

    while True:
        mouse_pos = pygame.mouse.get_pos()

        # 이벤트 처리
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if _BTN_CONTACT.collidepoint(event.pos):
                    go_phone = True  # 연락 버튼 클릭
                elif _BTN_QUIT.collidepoint(event.pos):
                    pygame.quit()
                    return  # 나가기 버튼 클릭

            if event.type == pygame.KEYDOWN:
                k = event.key

                if game.popup_active:
                    game.popup_active = False  # 아무 키나 누르면 팝업 닫기
                    continue

                if game.safe_mode:
                    # 금고 입력 중
                    if k == pygame.K_ESCAPE:
                        game.input_safe("cancel")
                    elif k == pygame.K_BACKSPACE:
                        game.input_safe("back")
                    elif pygame.K_0 <= k <= pygame.K_9:
                        game.input_safe(chr(k))
                    elif pygame.K_KP0 <= k <= pygame.K_KP9:
                        game.input_safe(str(k - pygame.K_KP0))
                    continue

                if k == pygame.K_e:
                    if game.won:
                        go_phone = True
                    else:
                        game.interact()

        # 플레이어 이동 (클리어/팝업/금고입력 중에는 이동 안 됨)
        if not game.won and not game.safe_mode and not game.popup_active:
            keys = pygame.key.get_pressed()
            dx = 0.0
            dy = 0.0

            if keys[pygame.K_a] or keys[pygame.K_LEFT]:  dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            if keys[pygame.K_w] or keys[pygame.K_UP]:    dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]:  dy += 1

            # 대각선 이동할 때 속도 보정
            if dx != 0 and dy != 0:
                dx *= 0.7071
                dy *= 0.7071

            if dx != 0 or dy != 0:
                if dy < 0:
                    renderer.facing_back = True   # 위로 이동 = 뒷모습
                if dy > 0:
                    renderer.facing_back = False  # 아래로 이동 = 정면

                # 다음 위치 계산
                next_x = game.px + dx * SPEED
                next_y = game.py + dy * SPEED

                # 방 경계 안에 가두기
                next_x = max(float(RX1 + PL_R), min(float(RX2 - PL_R), next_x))
                next_y = max(float(RY1 + PL_R), min(float(RY2 - PL_R), next_y))

                # 충돌 체크 후 이동
                new_px = game.px
                new_py = game.py
                if not check_collision(game, next_x, game.py):
                    new_px = next_x
                if not check_collision(game, new_px, next_y):
                    new_py = next_y

                game.set_pos(new_px, new_py)

                if game.bubble:
                    game.clear_bubble()  # 움직이면 말풍선 닫기

        # 업데이트
        game.tick_morse()
        game.tick_bubble()

        # 화면 그리기
        renderer.draw_all(mouse_pos)
        pygame.display.flip()

        # 폰 창 열기
        if go_phone:
            go_phone = False
            if on_phone and not phone_opened:
                phone_opened = True
                on_phone()

        clock.tick(60)  # 60fps 제한
