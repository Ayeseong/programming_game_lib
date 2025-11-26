import sys
import subprocess


def setup_deps(pkgs):
    for pkg in pkgs:
        try:
            __import__(pkg)
        except ImportError:
            print(f"설치 중: {pkg}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


setup_deps(["pygame", "requests"])

import pygame
import math
import random
import requests
from io import BytesIO

pygame.init()

W, H = 800, 600
scr = pygame.display.set_mode((W, H))
pygame.display.set_caption("Music Roguelike")
clk = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (100, 100, 100)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
YELLOW = (240, 200, 50)
LGRAY = (150, 150, 150)
BLUE = (50, 100, 255)
ORANGE = (255, 150, 50)

TIPS = [
    "클릭하여 다음 도움말을 확인하세요",
    "게임에 필요한 이미지를 Github에서 불러오고 있습니다",
    "이미지 파일이 저장되지는 않으니 안심하세요",
    "이 게임은 wasd, 그리고 마우스 좌클릭으로 조작합니다",
    "게임 캐릭터는 마우스 포인터 방향을 항상 바라봅니다",
    "방은 몬스터방, 보물방, 보스방이 있습니다",
    "보스를 처치하면 게임을 클리어 합니다"
]


def draw_load(curr=0, tot=0, dots=0, tip=0):
    scr.fill(BLACK)
    fnt = pygame.font.SysFont('Noto sans KR', 36)
    msg = fnt.render("이미지 불러오는 중...", True, WHITE)
    scr.blit(msg, (W // 2 - msg.get_width() // 2, H // 2 - 95))

    dot_list = ["", ".", "..", "..."]
    dot_txt = fnt.render(dot_list[dots % 4], True, WHITE)
    scr.blit(dot_txt, (W // 2 - dot_txt.get_width() // 2, H // 2 - 40))

    if tot > 0:
        prog = fnt.render(f"{curr}/{tot}", True, WHITE)
        scr.blit(prog, (W // 2 - prog.get_width() // 2, H // 2))

    tfnt = pygame.font.SysFont('Noto sans KR', 24)
    tlines = TIPS[tip % len(TIPS)].split('\n')
    for i, tl in enumerate(tlines):
        ttxt = tfnt.render(tl, True, LGRAY)
        scr.blit(ttxt, (W // 2 - ttxt.get_width() // 2, H // 2 + 60 + i * 32))
    pygame.display.flip()


def load_imgs(flist):
    imgs = {}
    tot = len(flist)
    tip = 0
    dots = 0
    for idx, (key, fname) in enumerate(flist):
        for _ in range(12):
            draw_load(idx + 1, tot, dots, tip)
            pygame.time.delay(50)
            dots += 1
            for evt in pygame.event.get():
                if evt.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if evt.type == pygame.MOUSEBUTTONDOWN:
                    tip += 1
        imgs[key] = get_img(fname)
    return imgs


USR, REPO, BRANCH = "Ayeseong", "programming_game_lib", "main"
BASE = f"https://raw.githubusercontent.com/{USR}/{REPO}/{BRANCH}/Img"


def get_img(fname):
    url = f"{BASE}/{fname}"
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        img = pygame.image.load(BytesIO(r.content)).convert_alpha()
        return img
    except:
        return None


FILES = [
    ('plyr', 'player.png'),
    ('axe', 'axe.png'),
    ('swrd', 'sword.png'),
    ('spr', 'spear.png'),
    ('knf', 'knife.png'),
    ('wnd', 'wand.png'),
    ('bow', 'bow.png'),
    ('spr_fx', 'spear_effect.png'),
    ('swrd_fx', 'sword_effect.png'),
    ('wnd_fx', 'wand_effect.png'),
    ('swrd_mo', 'sword_motion.png'),
    ('spr_mo', 'spear_motion.png'),
    ('axe_mo', 'axe_motion.png'),
    ('wnd_pr', 'wand_projectile.png'),
    ('bow_pr', 'bow_projectile.png'),
    ('trs_cls', 'treasure_closed.png'),
    ('trs_opn', 'treasure_opened.png'),
]

try:
    fnt = pygame.font.SysFont('Noto sans KR', 25)
except:
    fnt = pygame.font.Font(None, 30)

IMGS = load_imgs(FILES)


class Gun:
    def __init__(self, nm, dmg, typ="m", rng=70, ang=90, spd=10, cd=20, shp="rect"):
        self.nm = nm
        self.dmg = dmg
        self.typ = typ
        self.rng = rng
        self.ang = ang
        self.spd = spd
        self.cd = cd
        self.shp = shp


GUNS = [
    Gun("Short Sword", 10, typ="m", rng=100, ang=90, cd=20, shp="swrd"),
    Gun("Iron Axe", 14, typ="m", rng=80, ang=70, cd=28, shp="axe"),
    Gun("Short Spear", 12, typ="m", rng=130, ang=40, cd=26, shp="spr"),
    Gun("Short Bow", 9, typ="r", rng=350, spd=12, cd=100, shp="bow"),
    Gun("Wand", 8, typ="r", rng=400, spd=15, cd=12, shp="wnd"),
    Gun("Throw Knife", 11, typ="r", rng=420, spd=18, cd=30, shp="knf"),
]


class Play:
    def __init__(self, x=None, y=None):
        self.sz = 40
        self.x = x if x else W // 2 - self.sz // 2
        self.y = y if y else H // 2 - self.sz // 2
        self.spd = 5
        self.hp = 100
        self.mx_hp = 100
        self.atk = 10
        self.kb = 20
        self.atk_cd = 0
        self.atk_rng = 70
        self.fx_t = 0
        self.fx_txt = ""
        self.gun = Gun("Short Bow", 9, typ="r", rng=350, spd=12, cd=100, shp="bow")
        self.ang = 0.0

    def input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.y -= self.spd
        if keys[pygame.K_s]: self.y += self.spd
        if keys[pygame.K_a]: self.x -= self.spd
        if keys[pygame.K_d]: self.x += self.spd

    def equip(self, ng):
        self.gun = ng
        self.fx_txt = f"{ng.nm} 장착!"
        self.fx_t = pygame.time.get_ticks()

    def hit(self, enms, prjs, fxs):
        if self.atk_cd > 0:
            return
        g = self.gun
        cx = self.x + self.sz / 2
        cy = self.y + self.sz / 2

        if g.typ == "m":
            mn = None
            if g.shp == "swrd":
                mn = "swrd_mo"
            elif g.shp == "spr":
                mn = "spr_mo"
            elif g.shp == "axe":
                mn = "axe_mo"
            if mn:
                mx = cx + math.cos(self.ang) * (self.sz * 0.75)
                my = cy + math.sin(self.ang) * (self.sz * 0.75)
                fxs.append(Fx(mx, my, IMGS.get(mn), life=220, ang=self.ang))

        if g.typ == "m":
            for em in enms:
                if not em.live: continue
                ex = em.x + em.sz / 2
                ey = em.y + em.sz / 2
                dx = ex - cx
                dy = ey - cy
                dt = math.hypot(dx, dy)
                if dt <= g.rng:
                    ea = math.degrees(math.atan2(dy, dx))
                    fa = math.degrees(self.ang)
                    df = (ea - fa + 180) % 360 - 180
                    if abs(df) <= g.ang / 2:
                        em.dmg(g.dmg)
                        fn = None
                        if g.shp == "spr":
                            fn = "spr_fx"
                        elif g.shp == "swrd":
                            fn = "swrd_fx"
                        elif g.shp == "wnd":
                            fn = "wnd_fx"
                        if fn:
                            fxs.append(Fx(ex, ey, IMGS.get(fn), ang=self.ang))
                        if dt != 0:
                            em.x += (dx / dt) * self.kb
                            em.y += (dy / dt) * self.kb
        else:
            dx, dy = math.cos(self.ang), math.sin(self.ang)
            px = cx + dx * (self.sz / 2 + 5)
            py = cy + dy * (self.sz / 2 + 5)
            prj = Proj(px, py, dx, dy, g.spd, g.dmg, shp=g.shp)
            prjs.append(prj)
        self.atk_cd = g.cd

    def upd(self):
        mx, my = pygame.mouse.get_pos()
        cx = self.x + self.sz / 2
        cy = self.y + self.sz / 2
        self.ang = math.atan2(my - cy, mx - cx)
        if self.atk_cd > 0:
            self.atk_cd -= 1
        self.x = max(0, min(W - self.sz, self.x))
        self.y = max(0, min(H - self.sz, self.y))

    def item(self, itp):
        if itp == "a":
            self.atk += 1
            tx = "공격력 +1!"
        elif itp == "s":
            self.spd += 0.5
            tx = "이동속도 +0.5!"
        elif itp == "h":
            self.hp = min(self.mx_hp, self.hp + 20)
            tx = "체력회복 +20!"
        else:
            tx = ""
        self.fx_txt = tx
        self.fx_t = pygame.time.get_ticks()

    def draw(self, s):
        cx = self.x + self.sz / 2
        cy = self.y + self.sz / 2
        pi = IMGS.get('plyr')
        if pi:
            ti = (self.sz, self.sz)
            img = pygame.transform.smoothscale(pi, ti)
            dg = -math.degrees(self.ang) + 90
            rt = pygame.transform.rotate(img, dg)
            rc = rt.get_rect(center=(cx, cy))
            s.blit(rt, rc.topleft)
        else:
            bs = pygame.Surface((self.sz, self.sz), pygame.SRCALPHA)
            pygame.draw.rect(bs, BLUE, (0, 0, self.sz, self.sz))
            dg = -math.degrees(self.ang) + 90
            rt = pygame.transform.rotate(bs, dg)
            rc = rt.get_rect(center=(int(cx), int(cy)))
            s.blit(rt, rc.topleft)
        draw_gun(s, (cx, cy), self.ang, self.gun, self.sz)
        self.draw_hb(s)

    def draw_hb(self, s):
        bw = 60
        bh = 8
        x = self.x + (self.sz / 2) - (bw / 2)
        y = self.y - 15
        pygame.draw.rect(s, RED, (x, y, bw, bh))
        rto = self.hp / self.mx_hp
        pygame.draw.rect(s, GREEN, (x, y, bw * rto, bh))


def draw_gun(s, ctr, ang, gun, psz):
    cx, cy = ctr
    dz = int(psz * 1.2)
    img = IMGS.get(gun.shp)
    if img:
        iw, ih = img.get_size()
        scl = dz / max(iw, ih)
        nw, nh = max(1, int(iw * scl)), max(1, int(ih * scl))
        is_ = pygame.transform.smoothscale(img, (nw, nh))
        dg = -math.degrees(ang)
        rt = pygame.transform.rotate(is_, dg)
        rc = rt.get_rect(center=(int(cx + math.cos(ang) * (psz * 0.45)), int(cy + math.sin(ang) * (psz * 0.45))))
        s.blit(rt, rc.topleft)
        return

    sz = int(psz * 0.9)
    ws = int(sz * 1.2)
    srf = pygame.Surface((ws, ws), pygame.SRCALPHA)
    col = LGRAY
    s_sz = ws
    if gun.shp == "swrd":
        pygame.draw.rect(srf, col, (s_sz * 0.45, s_sz * 0.25, s_sz * 0.12, s_sz * 0.5))
        pygame.draw.polygon(srf, col, [(s_sz * 0.45, s_sz * 0.25), (s_sz * 0.45 + s_sz * 0.12, s_sz * 0.25),
                                       (s_sz * 0.6, s_sz * 0.12)])
    elif gun.shp == "axe":
        pygame.draw.rect(srf, col, (s_sz * 0.42, s_sz * 0.28, s_sz * 0.08, s_sz * 0.44))
        pygame.draw.circle(srf, col, (int(s_sz * 0.55), int(s_sz * 0.3)), int(s_sz * 0.18))
    elif gun.shp == "spr":
        pygame.draw.rect(srf, col, (s_sz * 0.43, s_sz * 0.15, s_sz * 0.06, s_sz * 0.7))
        pygame.draw.polygon(srf, col, [(s_sz * 0.43, s_sz * 0.15), (s_sz * 0.43 + s_sz * 0.06, s_sz * 0.15),
                                       (s_sz * 0.5, s_sz * 0.05)])
    elif gun.shp == "bow":
        pygame.draw.arc(srf, col, (s_sz * 0.3, s_sz * 0.15, s_sz * 0.6, s_sz * 0.7), math.radians(60),
                        math.radians(300), 3)
        pygame.draw.line(srf, col, (s_sz * 0.3, s_sz * 0.5), (s_sz * 0.9, s_sz * 0.5), 1)
    elif gun.shp == "wnd":
        pygame.draw.rect(srf, col, (s_sz * 0.46, s_sz * 0.25, s_sz * 0.06, s_sz * 0.5))
        pygame.draw.circle(srf, col, (int(s_sz * 0.5), int(s_sz * 0.2)), int(s_sz * 0.06))
    elif gun.shp == "knf":
        pygame.draw.polygon(srf, col,
                            [(s_sz * 0.45, s_sz * 0.35), (s_sz * 0.6, s_sz * 0.5), (s_sz * 0.45, s_sz * 0.65)])
    else:
        pygame.draw.rect(srf, col, (s_sz * 0.45, s_sz * 0.35, s_sz * 0.12, s_sz * 0.3))
    dg = -math.degrees(ang)
    rt = pygame.transform.rotate(srf, dg)
    rc = rt.get_rect(center=(int(cx + math.cos(ang) * (psz * 0.45)), int(cy + math.sin(ang) * (psz * 0.45))))
    s.blit(rt, rc.topleft)


class Enemy:
    def __init__(self, x, y, is_boss=False):
        self.x, self.y = x, y
        self.is_boss = is_boss
        self.sz = 60 if is_boss else 40
        self.col = ORANGE if is_boss else RED
        self.hp = 300 if is_boss else 50
        self.mx_hp = self.hp
        self.spd = 1.5 if is_boss else 2
        self.atk = 15 if is_boss else 5
        self.atk_cd = 0
        self.atk_rng = 50
        self.live = True

    def upd(self, ply):
        if not self.live: return
        dx, dy = ply.x - self.x, ply.y - self.y
        dt = math.sqrt(dx ** 2 + dy ** 2)
        if dt > 0:
            self.x += (dx / dt) * self.spd
            self.y += (dy / dt) * self.spd
        if self.atk_cd > 0:
            self.atk_cd -= 1
        elif dt < self.atk_rng:
            ply.hp -= self.atk
            self.atk_cd = 60

    def dmg(self, amt):
        self.hp -= amt
        if self.hp <= 0:
            self.live = False

    def draw(self, s):
        if not self.live: return
        pygame.draw.rect(s, self.col, (self.x, self.y, self.sz, self.sz))
        self.draw_hb(s)

    def draw_hb(self, s):
        bw = 40
        bh = 6
        x = self.x + (self.sz / 2) - (bw / 2)
        y = self.y - 10
        pygame.draw.rect(s, RED, (x, y, bw, bh))
        rto = self.hp / self.mx_hp
        pygame.draw.rect(s, GREEN, (x, y, bw * rto, bh))


class Box:
    def __init__(self, x, y, cur_gun=None):
        self.x, self.y = x, y
        self.sz = 30
        self.col = YELLOW
        self.typ = random.choice(["a", "s", "h"])
        self.got = False
        self.opn = False
        self.rwd = False
        gc = [g for g in GUNS if g.nm != cur_gun]
        if random.random() < 0.5 and gc:
            pf = random.choice(gc)
            self.gun = Gun(pf.nm, pf.dmg, pf.typ, pf.rng, pf.ang, pf.spd, pf.cd, shp=pf.shp)
        else:
            self.gun = None

    def draw(self, s):
        key = 'trs_opn' if self.opn else 'trs_cls'
        img = IMGS.get(key)
        if img:
            iw, ih = img.get_size()
            tgt = 48
            scl = tgt / max(iw, ih)
            is_ = pygame.transform.smoothscale(img, (max(1, int(iw * scl)), max(1, int(ih * scl))))
            s.blit(is_, (int(self.x - is_.get_width() // 2), int(self.y - is_.get_height() // 2)))
        else:
            col = LGRAY if self.opn else self.col
            pygame.draw.circle(s, col, (self.x, self.y), self.sz // 2)


class Rom:
    def __init__(self, typ="m", is_boss=False, pos=(0, 0), dsz=5, cur_gun=None):
        self.typ = typ
        self.is_boss = is_boss
        self.pos = pos
        self.dsz = dsz
        self.vsf = False
        self.enms = []
        self.box = None
        if self.is_boss:
            self.enms = [Enemy(W // 2 - 30, H // 2 - 30, True)]
        elif self.typ == "m":
            self.enms = [Enemy(random.randint(100, 700), random.randint(100, 500)) for _ in range(random.randint(2, 4))]
        elif self.typ == "t":
            mgn = 60
            cors = [
                (W - mgn, mgn),
                (mgn, H - mgn),
                (W - mgn, H - mgn),
            ]
            tx, ty = random.choice(cors)
            self.box = Box(tx, ty, cur_gun)

        xi, yi = pos
        self.drs = {}
        if yi > 0: self.drs["u"] = pygame.Rect(W // 2 - 40, 0, 80, 20)
        if yi < dsz - 1: self.drs["d"] = pygame.Rect(W // 2 - 40, H - 20, 80, 20)
        if xi > 0: self.drs["l"] = pygame.Rect(0, H // 2 - 40, 20, 80)
        if xi < dsz - 1: self.drs["r"] = pygame.Rect(W - 20, H // 2 - 40, 20, 80)

    def upd(self, ply):
        for em in self.enms:
            em.upd(ply)

    def draw(self, s):
        pygame.draw.rect(s, (30, 30, 30), (0, 0, W, H))
        for rc in self.drs.values(): pygame.draw.rect(s, YELLOW, rc)
        if self.typ == "m" or self.is_boss:
            for em in self.enms: em.draw(s)
        elif self.typ == "t" and self.box:
            self.box.draw(s)


class Dng:
    def __init__(self, dif, cur_gun):
        self.rms = {}
        self.sz = {"EASY": 5, "NORMAL": 7, "HARD": 11}[dif]
        self.coords = [(x, y) for x in range(self.sz) for y in range(self.sz)]
        self.cur = (self.sz // 2, self.sz // 2)
        self.vsf = set()
        self.gen(cur_gun)

    def gen(self, cur_gun):
        coords = self.coords.copy()
        tot = len(coords)
        start = self.cur
        boss = coords[-1]
        tcnt = max(1, int(round(tot * 0.2)))
        selc = [c for c in coords if c != boss and c != start]
        tcoords = random.sample(selc, tcnt)
        for c in coords:
            if c == boss:
                self.rms[c] = Rom("m", is_boss=True, pos=c, dsz=self.sz)
            elif c == start:
                self.rms[c] = Rom("e", pos=c, dsz=self.sz)
            elif c in tcoords:
                self.rms[c] = Rom("t", pos=c, dsz=self.sz, cur_gun=cur_gun)
            else:
                self.rms[c] = Rom("m", pos=c, dsz=self.sz)

    def get_rom(self, pos):
        return self.rms[pos]

    def mv(self, drn):
        x, y = self.cur
        if drn == "u":
            y -= 1
        elif drn == "d":
            y += 1
        elif drn == "l":
            x -= 1
        elif drn == "r":
            x += 1
        if 0 <= x < self.sz and 0 <= y < self.sz:
            self.cur = (x, y)
            self.vsf.add(self.cur)


def draw_mm(s, dng):
    mms = pygame.Surface((150, 150))
    mms.fill((20, 20, 20))
    sz = 12
    off = 10
    for (x, y), rm in dng.rms.items():
        col = LGRAY
        if (x, y) in dng.vsf:
            if rm.is_boss:
                col = ORANGE
            elif rm.typ == "t":
                col = YELLOW
            else:
                col = GREEN
        rc = pygame.Rect(off + x * sz, off + y * sz, 10, 10)
        pygame.draw.rect(mms, col, rc)
        if (x, y) == dng.cur:
            pygame.draw.rect(mms, WHITE, rc, 2)
    s.blit(mms, (20, 20))


def draw_st(s, ply):
    st = f"HP: {int(ply.hp)}/{ply.mx_hp} | ATK: {ply.gun.dmg} ({ply.gun.nm}) | TYPE: {ply.gun.typ} | SPD: {round(ply.spd, 1)} | KB: {ply.kb}"
    txt = fnt.render(st, True, WHITE)
    s.blit(txt, (W // 2 - txt.get_width() // 2, H - 40))


class Proj:
    def __init__(self, x, y, dx, dy, spd, dmg, rad=6, shp=None):
        self.x, self.y = x, y
        ln = math.hypot(dx, dy)
        self.dx, self.dy = (dx / ln, dy / ln) if ln != 0 else (1, 0)
        self.spd = spd
        self.dmg = dmg
        self.rad = rad
        self.live = True
        self.shp = shp

    def upd(self, enms, fxs, rom=None):
        if not self.live: return
        self.x += self.dx * self.spd
        self.y += self.dy * self.spd
        if self.x < -50 or self.x > W + 50 or self.y < -50 or self.y > H + 50:
            self.live = False
            return
        for em in enms:
            if not em.live: continue
            ecx = em.x + em.sz / 2
            ecy = em.y + em.sz / 2
            dt = math.hypot(self.x - ecx, self.y - ecy)
            if dt <= self.rad + max(em.sz, em.sz) / 2 * 0.5:
                em.dmg(self.dmg)
                fn = None
                if self.shp == "wnd":
                    fn = "wnd_fx"
                elif self.shp == "spr":
                    fn = "spr_fx"
                elif self.shp == "swrd":
                    fn = "swrd_fx"
                if fn:
                    fxs.append(Fx(ecx, ecy, IMGS.get(fn), ang=math.atan2(self.dy, self.dx)))
                if self.shp != "bow":
                    self.live = False
                    break
        if self.live and rom is not None and self.shp == "bow":
            if self.y <= 20:
                du = rom.drs.get("u")
                if not (du and du.collidepoint(self.x, self.y)):
                    self.live = False
                    return
            if self.y >= H - 20:
                dd = rom.drs.get("d")
                if not (dd and dd.collidepoint(self.x, self.y)):
                    self.live = False
                    return
            if self.x <= 20:
                dl = rom.drs.get("l")
                if not (dl and dl.collidepoint(self.x, self.y)):
                    self.live = False
                    return
            if self.x >= W - 20:
                dr = rom.drs.get("r")
                if not (dr and dr.collidepoint(self.x, self.y)):
                    self.live = False
                    return

    def draw(self, s):
        if not self.live: return
        pi = IMGS.get(f"{self.shp}_pr") or IMGS.get(self.shp) if self.shp else None
        if pi:
            iw, ih = pi.get_size()
            scl = max(1, int(self.rad * 2))
            is_ = pygame.transform.smoothscale(pi, (scl, scl))
            dg = -math.degrees(math.atan2(self.dy, self.dx))
            rt = pygame.transform.rotate(is_, dg)
            rc = rt.get_rect(center=(int(self.x), int(self.y)))
            s.blit(rt, int(rc.topleft[0]), int(rc.topleft[1]))
            return
        pygame.draw.circle(s, LGRAY, (int(self.x), int(self.y)), self.rad)


class Fx:
    def __init__(self, x, y, img=None, life=400, ang=0):
        self.x = x
        self.y = y
        self.img = img
        self.life = life
        self.st = pygame.time.get_ticks()
        self.ang = ang

    def upd(self):
        return pygame.time.get_ticks() - self.st >= self.life

    def draw(self, s):
        if self.img:
            iw, ih = self.img.get_size()
            tgt = 48
            scl = tgt / max(iw, ih)
            is_ = pygame.transform.smoothscale(self.img, (max(1, int(iw * scl)), max(1, int(ih * scl))))
            dg = -math.degrees(self.ang)
            rt = pygame.transform.rotate(is_, dg)
            s.blit(rt, (int(self.x - rt.get_width() // 2), int(self.y - rt.get_height() // 2)))
        else:
            pygame.draw.circle(s, YELLOW, (int(self.x), int(self.y)), 10)


def sel_dif():
    bw, bh = 220, 60
    spc = 20
    lbls = ["EASY", "NORMAL", "HARD"]
    thgt = bh * len(lbls) + spc * (len(lbls) - 1)
    sy = H // 2 - thgt // 2
    while True:
        scr.fill(BLACK)
        ttl = fnt.render("Select Difficulty", True, YELLOW)
        scr.blit(ttl, (W // 2 - ttl.get_width() // 2, H // 4 - ttl.get_height() // 2))

        mx, my = pygame.mouse.get_pos()
        clkd = False
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                clkd = True

        for i, lbl in enumerate(lbls):
            x = W // 2 - bw // 2
            y = sy + i * (bh + spc)
            rc = pygame.Rect(x, y, bw, bh)
            col = LGRAY if rc.collidepoint(mx, my) else GRAY
            pygame.draw.rect(scr, col, rc, border_radius=8)
            txt = fnt.render(lbl, True, WHITE)
            scr.blit(txt, (x + bw // 2 - txt.get_width() // 2, y + bh // 2 - txt.get_height() // 2))
            if clkd and rc.collidepoint(mx, my):
                return lbl

        ht = fnt.render("Click a button to start", True, LGRAY)
        scr.blit(ht, (W // 2 - ht.get_width() // 2, H - 60))

        pygame.display.flip()
        clk.tick(60)


def main():
    dif = sel_dif()
    if dif not in ["EASY", "NORMAL", "HARD"]:
        dif = "EASY"

    ply = Play()
    dng = Dng(dif, ply.gun.nm)
    dng.vsf.add(dng.cur)

    mdl = None
    prjs = []
    fxs = []

    run = True
    while run:
        scr.fill(BLACK)
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if mdl:
                if evt.type == pygame.KEYDOWN:
                    if mdl and evt.key == pygame.K_y:
                        ply.equip(mdl['gun'])
                        if mdl['rom'] and mdl['rom'].box:
                            mdl['rom'].box.rwd = True
                            mdl['rom'].box.opn = True
                        mdl = None
                    elif mdl and evt.key == pygame.K_n:
                        if mdl['rom'] and mdl['rom'].box:
                            mdl['rom'].box.rwd = True
                            mdl['rom'].box.opn = True
                        ply.fx_txt = "기존 무기 유지"
                        ply.fx_t = pygame.time.get_ticks()
                        mdl = None
                continue
            if evt.type == pygame.MOUSEBUTTONDOWN and evt.button == 1:
                rm = dng.get_rom(dng.cur)
                ply.hit(rm.enms, prjs, fxs)

        rm = dng.get_rom(dng.cur)

        if not mdl:
            ply.input()
            ply.upd()
            rm.upd(ply)
            for p in prjs:
                p.upd(rm.enms, fxs, rm)
            prjs = [p for p in prjs if p.live]

        if ply.hp <= 0:
            ovl = pygame.Surface((W, H), pygame.SRCALPHA)
            ovl.fill((0, 0, 0, 180))
            scr.blit(ovl, (0, 0))
            go = fnt.render("GAME OVER", True, RED)
            scr.blit(go, (W // 2 - go.get_width() // 2, H // 2 - go.get_height() // 2))
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            sys.exit()

        if rm.typ == "t" and rm.box and not rm.box.got:
            pr = pygame.Rect(ply.x, ply.y, ply.sz, ply.sz)
            hf = rm.box.sz // 2
            br = pygame.Rect(rm.box.x - hf, rm.box.y - hf, rm.box.sz, rm.box.sz)
            if pr.colliderect(br):
                if not rm.box.opn:
                    rm.box.opn = True
                    if rm.box.gun:
                        mdl = {'gun': rm.box.gun, 'rom': rm}
                    else:
                        ply.item(rm.box.typ)
                        rm.box.rwd = True
                else:
                    if getattr(rm.box, 'rwd', False):
                        pass

        mvd = False
        for drn, rc in rm.drs.items():
            if pygame.Rect(ply.x, ply.y, ply.sz, ply.sz).colliderect(rc):
                if any(e.live for e in rm.enms):
                    ply.fx_txt = "방을 정리해야 이동할 수 있습니다."
                    ply.fx_t = pygame.time.get_ticks()
                    mvd = False
                    break
                dng.mv(drn)
                ply.x, ply.y = W // 2, H // 2
                prjs.clear()
                mvd = True
                break

        rm.draw(scr)
        ply.draw(scr)
        for p in prjs: p.draw(scr)
        nfx = []
        for e in fxs:
            if not e.upd():
                e.draw(scr)
                nfx.append(e)
        fxs = nfx
        draw_mm(scr, dng)
        draw_st(scr, ply)

        if mdl:
            g = mdl['gun']
            ovl = pygame.Surface((W, H), pygame.SRCALPHA)
            ovl.fill((0, 0, 0, 180))
            scr.blit(ovl, (0, 0))
            ttl = fnt.render("무기 발견!", True, YELLOW)
            nln = fnt.render(f"새 무기: {g.nm}  ATK {g.dmg}  TYPE {g.typ}", True, WHITE)
            cln = fnt.render(f"현재 무기: {ply.gun.nm}  ATK {ply.gun.dmg}  TYPE {ply.gun.typ}", True, WHITE)
            ht = fnt.render("Y: 장착   N: 유지", True, LGRAY)
            scr.blit(ttl, (W // 2 - ttl.get_width() // 2, H // 2 - 80))
            scr.blit(nln, (W // 2 - nln.get_width() // 2, H // 2 - 40))
            scr.blit(cln, (W // 2 - cln.get_width() // 2, H // 2))
            scr.blit(ht, (W // 2 - ht.get_width() // 2, H // 2 + 60))

        if pygame.time.get_ticks() - ply.fx_t < 2000:
            txt = fnt.render(ply.fx_txt, True, WHITE)
            scr.blit(txt, (W // 2 - txt.get_width() // 2, 50))
        if rm.is_boss and all(not e.live for e in rm.enms):
            txt = fnt.render("던전 클리어!", True, YELLOW)
            scr.blit(txt, (W // 2 - txt.get_width() // 2, H // 2))
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            sys.exit()
        pygame.display.flip()
        clk.tick(60)


if __name__ == "__main__":
    main()