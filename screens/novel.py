# screens/novel.py  ── 렌더링 + 충돌 + Qt 래퍼 ────────────────────────────────
import os, math
import pygame
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton
from PyQt6.QtCore    import Qt, pyqtSignal, QTimer
from PyQt6.QtGui     import QImage, QPixmap
from config          import W, H
from .escape_room    import EscapeRoomGame, C, RX1, RX2, RY1, RY2, PL_R, INTER_R, SPEED

if not pygame.get_init():
    pygame.init()


def _font(size: int, bold: bool = False) -> pygame.font.Font:
    path = rf"C:\Windows\Fonts\malgun{'bd' if bold else ''}.ttf"
    return pygame.font.Font(path if os.path.exists(path) else None, size)


def _draw_circle_badge(surf: pygame.Surface, rx: int, ry: int, col: tuple):
    pygame.draw.circle(surf, col,        (rx, ry + 7), 7)
    pygame.draw.circle(surf, C["black"], (rx, ry + 7), 7, 1)


# Qt 키 → pygame 키 매핑
QT2PG = {
    Qt.Key.Key_W: pygame.K_w,    Qt.Key.Key_A: pygame.K_a,
    Qt.Key.Key_S: pygame.K_s,    Qt.Key.Key_D: pygame.K_d,
    Qt.Key.Key_Up: pygame.K_UP,  Qt.Key.Key_Down:  pygame.K_DOWN,
    Qt.Key.Key_Left: pygame.K_LEFT, Qt.Key.Key_Right: pygame.K_RIGHT,
}


# ── 렌더러 (충돌 감지 + 모든 draw 메서드) ─────────────────────────────────────
class EscapeRoomRenderer:
    def __init__(self):
        self._game = EscapeRoomGame()
        self._surf = pygame.Surface((W, H))

        self._ftitle = _font(16, bold=True)
        self._flabel = _font(11, bold=True)
        self._fbub   = _font(11)
        self._fsmall = _font( 9)
        self._fhint  = _font( 9, bold=True)

        self._floor_surf = self._bake_floor()
        self._tile_surf  = self._bake_tiles()

    def reset(self):
        self._game.reset()

    # ── 사전 렌더링 ─────────────────────────────────────────────────────────────
    def _bake_floor(self) -> pygame.Surface:
        fw, fh = RX2 - RX1, RY2 - RY1
        s = pygame.Surface((fw, fh))
        for y in range(fh):
            t = y / max(1, fh - 1)
            col = tuple(int(C["floor_t"][i] + (C["floor_b"][i] - C["floor_t"][i]) * t)
                        for i in range(3))
            pygame.draw.line(s, col, (0, y), (fw, y))
        return s

    def _bake_tiles(self) -> pygame.Surface:
        fw, fh = RX2 - RX1, RY2 - RY1
        s = pygame.Surface((fw, fh), pygame.SRCALPHA)
        tile_col = (160, 118, 55, 50)
        for x in range(0, fw, 52):
            pygame.draw.line(s, tile_col, (x, 0), (x, fh))
        for y in range(0, fh, 52):
            pygame.draw.line(s, tile_col, (0, y), (fw, y))
        return s

    # ── 충돌 감지 ───────────────────────────────────────────────────────────────
    def _circle_rect_collide(self, cx: float, cy: float, rect: pygame.Rect) -> bool:
        closest_x = max(rect.left, min(cx, rect.right))
        closest_y = max(rect.top,  min(cy, rect.bottom))
        return math.hypot(cx - closest_x, cy - closest_y) < PL_R

    def _any_collision(self, cx: float, cy: float) -> bool:
        return any(self._circle_rect_collide(cx, cy, obj.rect) for obj in self._game.objs)

    # ── 업데이트 ────────────────────────────────────────────────────────────────
    def update(self, keys: set, interact: bool):
        g = self._game
        if not g.won:
            dx = dy = 0.0
            if pygame.K_a in keys or pygame.K_LEFT  in keys: dx -= 1
            if pygame.K_d in keys or pygame.K_RIGHT in keys: dx += 1
            if pygame.K_w in keys or pygame.K_UP    in keys: dy -= 1
            if pygame.K_s in keys or pygame.K_DOWN  in keys: dy += 1
            if dx and dy:
                dx *= 0.7071; dy *= 0.7071
            if dx or dy:
                new_px = max(float(RX1 + PL_R), min(float(RX2 - PL_R), g.px + dx * SPEED))
                new_py = max(float(RY1 + PL_R), min(float(RY2 - PL_R), g.py + dy * SPEED))
                px, py = g.px, g.py
                if not self._any_collision(new_px, py):
                    px = new_px
                if not self._any_collision(px, new_py):
                    py = new_py
                g.set_pos(px, py)
                if g.bubble:
                    g.clear_bubble()

        if interact:
            g.interact()

        g.tick_bubble()

    # ── 렌더링 ─────────────────────────────────────────────────────────────────
    def render(self) -> pygame.Surface:
        g = self._game
        self._draw_room()
        self._draw_objects()
        self._draw_player()
        if g.bubble:
            self._draw_bubble()
        self._draw_hud()
        if g.won:
            self._draw_win()
        return self._surf

    def _draw_room(self):
        s = self._surf
        s.fill(C["outer"])
        s.blit(self._floor_surf, (RX1, RY1))
        s.blit(self._tile_surf,  (RX1, RY1))
        pygame.draw.rect(s, C["wall"], (RX1, RY1, RX2-RX1, RY2-RY1), 3)

    def _draw_objects(self):
        s = self._surf
        g = self._game
        for obj in g.objs:
            in_rng = obj.dist(g.px, g.py) < INTER_R

            sh = pygame.Surface((obj.rect.w + 6, obj.rect.h + 6), pygame.SRCALPHA)
            pygame.draw.rect(sh, (0, 0, 0, 55), sh.get_rect(), border_radius=5)
            s.blit(sh, (obj.rect.x + 4, obj.rect.y + 4))

            pygame.draw.rect(s, obj.color, obj.rect, border_radius=5)
            pygame.draw.rect(s, C["yellow"] if in_rng else C["black"],
                             obj.rect, 3 if in_rng else 1, border_radius=5)

            lines   = obj.label.split("\n")
            total_h = len(lines) * self._flabel.get_height()
            for i, line in enumerate(lines):
                ls = self._flabel.render(line, True, C["white"])
                s.blit(ls, (obj.rect.centerx - ls.get_width() // 2,
                            obj.rect.centery - total_h // 2 + i * self._flabel.get_height()))

            if in_rng:
                hx = obj.rect.centerx - 11
                hy = obj.rect.top - 22
                pygame.draw.rect(s, C["yellow"],   (hx, hy, 22, 16), border_radius=3)
                pygame.draw.rect(s, (170, 136, 0), (hx, hy, 22, 16), 1, border_radius=3)
                es = self._fhint.render("E", True, (50, 30, 0))
                s.blit(es, (hx + (22 - es.get_width()) // 2,
                            hy + (16 - es.get_height()) // 2))

        if g.has_note:
            desk = next(o for o in g.objs if o.name == "desk")
            _draw_circle_badge(s, desk.rect.right - 8, desk.rect.top + 2, C["yellow"])
        if g.has_key:
            safe = next(o for o in g.objs if o.name == "safe")
            _draw_circle_badge(s, safe.rect.right - 8, safe.rect.top + 2, C["green"])

    def _draw_player(self):
        s  = self._surf
        px = int(self._game.px)
        py = int(self._game.py)

        sh = pygame.Surface((PL_R * 4, PL_R), pygame.SRCALPHA)
        pygame.draw.ellipse(sh, (0, 0, 0, 55), sh.get_rect())
        s.blit(sh, (px - PL_R * 2, py + int(PL_R * 0.65)))

        pygame.draw.circle(s, C["p_dark"],  (px, py), PL_R)
        pygame.draw.circle(s, C["p_light"], (px - 4, py - 4), PL_R - 4)
        pygame.draw.circle(s, C["p_rim"],   (px, py), PL_R, 1)

        for ex, ey, r, col in [
            (px - 5, py - 4, 4, C["white"]),
            (px + 5, py - 4, 4, C["white"]),
            (px - 4, py - 4, 3, (26, 26, 26)),
            (px + 6, py - 4, 3, (26, 26, 26)),
        ]:
            pygame.draw.circle(s, col, (ex, ey), r)

    def _draw_bubble(self):
        s   = self._surf
        g   = self._game
        lh  = self._fbub.get_height()
        pad = 10
        maxw = int(W * 0.58)

        wrapped: list[str] = []
        for line in g.bubble.split("\n"):
            if self._fbub.size(line)[0] <= maxw - pad * 2:
                wrapped.append(line)
            else:
                cur = ""
                for ch in line:
                    if self._fbub.size(cur + ch)[0] > maxw - pad * 2:
                        wrapped.append(cur); cur = ch
                    else:
                        cur += ch
                if cur:
                    wrapped.append(cur)
        if not wrapped:
            return

        bw    = max(self._fbub.size(l)[0] for l in wrapped) + pad * 2 + 4
        bh    = len(wrapped) * lh + pad * 2
        px    = int(g.px)
        bx    = max(4, min(W - bw - 4, px - bw // 2))
        alpha = 255 if g.btimer > 45 else max(0, int(255 * g.btimer / 45))
        tip_x = max(9, min(bw - 9, px - bx))

        head_y    = int(g.py) - PL_R - 3
        show_below = (head_y - bh - 14) < RY1
        bs = pygame.Surface((bw, bh + 16), pygame.SRCALPHA)

        if show_below:
            tail_pts = [(tip_x - 8, 14), (tip_x + 8, 14), (tip_x, 1)]
            pygame.draw.polygon(bs, (*C["bubble"], alpha), tail_pts)
            pygame.draw.line(bs, (*C["bub_b"], alpha), tail_pts[0], tail_pts[2], 2)
            pygame.draw.line(bs, (*C["bub_b"], alpha), tail_pts[1], tail_pts[2], 2)
            pygame.draw.rect(bs, (*C["bubble"], alpha), (0, 14, bw, bh), border_radius=10)
            pygame.draw.rect(bs, (*C["bub_b"],  alpha), (0, 14, bw, bh), 2, border_radius=10)
            by = int(g.py) + PL_R + 3
            s.blit(bs, (bx, by))
            for i, line in enumerate(wrapped):
                ts = self._fbub.render(line, True, C["bub_t"])
                if alpha < 255:
                    ts.set_alpha(alpha)
                s.blit(ts, (bx + pad, by + 14 + pad + i * lh))
        else:
            pygame.draw.rect(bs, (*C["bubble"], alpha), (0, 0, bw, bh), border_radius=10)
            pygame.draw.rect(bs, (*C["bub_b"],  alpha), (0, 0, bw, bh), 2, border_radius=10)
            tail_pts = [(tip_x - 8, bh - 1), (tip_x + 8, bh - 1), (tip_x, bh + 13)]
            pygame.draw.polygon(bs, (*C["bubble"], alpha), tail_pts)
            pygame.draw.line(bs, (*C["bub_b"], alpha), tail_pts[0], tail_pts[2], 2)
            pygame.draw.line(bs, (*C["bub_b"], alpha), tail_pts[1], tail_pts[2], 2)
            by = max(4, head_y - bh - 14)
            s.blit(bs, (bx, by))
            for i, line in enumerate(wrapped):
                ts = self._fbub.render(line, True, C["bub_t"])
                if alpha < 255:
                    ts.set_alpha(alpha)
                s.blit(ts, (bx + pad, by + pad + i * lh))

    def _draw_hud(self):
        s = self._surf
        g = self._game

        pygame.draw.rect(s, C["hud"], (0, 0, W, RY1 - 1))
        ts = self._ftitle.render("선생님, 맞죠?  ─  서 버 실 탈 출", True, C["yellow"])
        s.blit(ts, (12, (RY1 - 1 - ts.get_height()) // 2))

        for i, (lbl, have, col) in enumerate([
            ("메 모", g.has_note, C["yellow"]),
            ("열 쇠", g.has_key,  C["green"]),
        ]):
            ix, iy = W - 115 + i * 55, 6
            pygame.draw.rect(s, col if have else C["dgray"], (ix, iy, 46, 22), border_radius=5)
            ls = self._fsmall.render(lbl, True, (20, 10, 0) if have else C["gray"])
            s.blit(ls, (ix + (46 - ls.get_width()) // 2, iy + (22 - ls.get_height()) // 2))

        pygame.draw.rect(s, C["hud"], (0, RY2 + 1, W, H - RY2))
        hs = self._fsmall.render("WASD : 이동     E : 상호작용", True, C["gray"])
        s.blit(hs, ((W - hs.get_width()) // 2, RY2 + (H - RY2 - hs.get_height()) // 2))

    def _draw_win(self):
        s  = self._surf
        ov = pygame.Surface((W, H), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 175))
        s.blit(ov, (0, 0))

        cy = H // 2
        for txt_surf, y in [
            (self._ftitle.render("서버실 탈출!",             True, C["yellow"]), cy - 55),
            (self._flabel.render("이제 선생님들을 조사하라!", True, C["white"]),  cy + 12),
            (self._fsmall.render("[ E ] 를 눌러 스마트폰으로 이동",
                                 True, C["gray"]),                               cy + 58),
        ]:
            s.blit(txt_surf, ((W - txt_surf.get_width()) // 2, y))


# ── Qt 래퍼 ───────────────────────────────────────────────────────────────────
class VisualNovelScreen(QWidget):
    open_phone = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._renderer = EscapeRoomRenderer()
        self._pg_keys : set  = set()
        self._interact: bool = False

        self._label = QLabel(self)
        self._label.setScaledContents(True)
        self._label.setGeometry(0, 0, W, H)

        btn_w, btn_h = 88, 32
        self._contact_btn = QPushButton("연락", self)
        self._contact_btn.setGeometry(W - btn_w - 10, RY2 + (H - RY2 - btn_h) // 2, btn_w, btn_h)
        self._contact_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._contact_btn.setStyleSheet("""
            QPushButton {
                background: #FFE066;
                color: #1A0A00;
                border: none;
                border-radius: 8px;
                font-family: 'Malgun Gothic';
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton:hover  { background: #FFD000; }
            QPushButton:pressed { background: #E6B800; }
        """)
        self._contact_btn.clicked.connect(self.open_phone)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(16)

    def reset(self):
        self._renderer.reset()
        self._pg_keys.clear()
        self._interact = False
        self.setFocus()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._label.setGeometry(0, 0, e.size().width(), e.size().height())

    def keyPressEvent(self, e):
        pg = QT2PG.get(e.key())
        if pg is not None:
            self._pg_keys.add(pg)
        if e.key() == Qt.Key.Key_E:
            if self._renderer._game.won:
                self.open_phone.emit()
            else:
                self._interact = True

    def keyReleaseEvent(self, e):
        pg = QT2PG.get(e.key())
        if pg is not None:
            self._pg_keys.discard(pg)

    def _tick(self):
        self._renderer.update(self._pg_keys, self._interact)
        self._interact = False

        surf = self._renderer.render()
        raw  = pygame.image.tostring(surf, "RGB")
        qimg = QImage(raw, W, H, W * 3, QImage.Format.Format_RGB888)
        self._label.setPixmap(QPixmap.fromImage(qimg))
