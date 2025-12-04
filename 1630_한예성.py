import sys
import subprocess

def ensure_packages(packages):
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            print(f"[INFO] '{pkg}' 모듈이 없어 설치를 시도합니다")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

ensure_packages(["pygame", "requests"])

import pygame
import math
import random
import requests
from io import BytesIO

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("The Artists : Composer's Adventure (Music Roguelike)")
clock = pygame.time.Clock()

HELP_TEXTS = [
    "클릭하여 다음 도움말을 확인하세요",
    "게임에 필요한 이미지를 Github에서 불러오고 있습니다",
    "이미지는 제가 다 직접 그렸습니다!",
    "이 게임은 wasd, 그리고 마우스 좌클릭으로 조작합니다",
    "게임 캐릭터는 마우스 포인터 방향을 항상 바라봅니다",
    "방은 몬스터방, 보물방, 보스방이 있습니다",
    "보스를 처치하면 게임을 클리어 합니다",
    "거리조절이 핵심 입니다!",
    "보스방은 각 네 모서리 방 중에 하나입니다",
    "성수쌤 사랑합니다"
]
def show_loading_screen(current=0, total=0, help_idx=0):
    screen.fill((0, 0, 0))
    font = pygame.font.SysFont('Noto sans KR', 36)
    text = font.render("이미지 불러오는 중...", True, (255, 255, 255))
    screen.blit(font.render("이미지 불러오는 중...", True, (255, 255, 255)), (WIDTH//2 - text.get_width()//2, HEIGHT//2 - 50))
    if total > 0:
        prog_msg = f"{current}/{total}"
        prog_text = font.render(prog_msg, True, (255, 255, 255))
        screen.blit(prog_text, (WIDTH//2 - prog_text.get_width()//2, HEIGHT//2))
    help_font = pygame.font.SysFont('Noto sans KR', 24)
    help_lines = HELP_TEXTS[help_idx % len(HELP_TEXTS)].split('\n')
    for i, line in enumerate(help_lines):
        help_text = help_font.render(line, True, (150, 150, 150))
        screen.blit(help_text, (WIDTH//2 - help_text.get_width()//2, HEIGHT//2 + 60 + i*32))
    pygame.display.flip()

def load_images_with_ui(image_files):
    images = {}
    total = len(image_files)
    help_idx = 0
    for idx, key_name in enumerate(image_files):
        show_loading_screen(idx+1, total, help_idx)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                help_idx += 1
        key, name = key_name
        images[key] = load_image(name)
    return images

def load_image(filename):
    url = f"https://raw.githubusercontent.com/Ayeseong/programming_game_lib/main/Img/{filename}"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        img = pygame.image.load(BytesIO(resp.content)).convert_alpha()
        return img
    except Exception as e:
        print(f"[WARN] GitHub 이미지 로드 실패: {url} ({e})")
        return None

IMAGE_FILES = [
    ('player', 'player.png'),
    ('axe', 'axe.png'),
    ('sword', 'sword.png'),
    ('spear', 'spear.png'),
    ('knife', 'knife.png'),
    ('wand', 'wand.png'),
    ('bow', 'bow.png'),
    ('spear_effect', 'spear_effect.png'),
    ('sword_effect', 'sword_effect.png'),
    ('wand_effect', 'wand_effect.png'),
    ('sword_motion', 'sword_motion.png'),
    ('spear_motion', 'spear_motion.png'),
    ('axe_motion', 'axe_motion.png'),
    ('wand_projectile', 'wand_projectile.png'),
    ('bow_projectile', 'bow_projectile.png'),
    ('treasure_closed', 'treasure_closed.png'),
    ('treasure_opened', 'treasure_opened.png'),
]
try:
    font = pygame.font.SysFont('Noto sans KR', 25)
except pygame.error:
    font = pygame.font.Font(None, 30)

IMAGES = load_images_with_ui(IMAGE_FILES)

class Weapon:
    def __init__(self, name, attack_damage, type="근접", attack_range=70, attack_angle=90, projectile_speed=10, cooldown=20, shape="rect"):
        self.name = name
        self.attack_damage = attack_damage
        self.type = type
        self.attack_range = attack_range
        self.attack_angle = attack_angle
        self.projectile_speed = projectile_speed
        self.cooldown = cooldown
        self.shape = shape

WEAPON_PREFABS = [
    Weapon("어쿠스틱 기타", 10, type="근접", attack_range=100, attack_angle=90, cooldown=20, shape="sword"),
    Weapon("피아노 조율용 망치", 14, type="근접", attack_range=80, attack_angle=70, cooldown=28, shape="axe"),
    Weapon("드럼 스틱", 8, type="근접", attack_range=130, attack_angle=40, cooldown=18, shape="spear"),
    Weapon("바이올린", 9, type="원거리", attack_range=350, projectile_speed=12, cooldown=50, shape="bow"),
    Weapon("보컬 마이크", 8, type="원거리", attack_range=400, projectile_speed=15, cooldown=12, shape="wand"),
    Weapon("단검", 11, type="원거리", attack_range=420, projectile_speed=18, cooldown=5, shape="knife"),
]

class Player:
    def __init__(self, x=None, y=None):
        self.size = 40
        self.x = WIDTH // 2 - self.size // 2 if x is None else x
        self.y = HEIGHT // 2 - self.size // 2 if y is None else y
        self.speed = 5
        self.hp = 100
        self.max_hp = 100
        self.attack_damage = 10
        self.knockback = 20
        self.attack_cooldown = 0
        self.attack_range = 70
        self.last_effect_time = 0
        self.last_effect_text = ""
        self.weapon = Weapon("어쿠스틱 기타", 10, type="근접", attack_range=100, attack_angle=90, cooldown=20, shape="sword")
        self.facing_angle = 0.0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]: self.y -= self.speed
        if keys[pygame.K_s]: self.y += self.speed
        if keys[pygame.K_a]: self.x -= self.speed
        if keys[pygame.K_d]: self.x += self.speed

    def equip_weapon(self, new_weapon):
        self.weapon = new_weapon
        self.last_effect_text = f"{new_weapon.name} 장착!"
        self.last_effect_time = pygame.time.get_ticks()

    def attack(self, enemies, projectiles, effects):
        if self.attack_cooldown > 0:
            return
        w = self.weapon
        cx = self.x + self.size / 2
        cy = self.y + self.size / 2
        if w.type == "근접":
            motion_name = None
            if w.shape == "sword": motion_name = "sword_motion"
            elif w.shape == "spear": motion_name = "spear_motion"
            elif w.shape == "axe": motion_name = "axe_motion"
            if motion_name:
                mx = cx + math.cos(self.facing_angle) * (self.size * 0.75)
                my = cy + math.sin(self.facing_angle) * (self.size * 0.75)
                effects.append(Effect(mx, my, IMAGES.get(motion_name), lifetime=220, angle=self.facing_angle))
        if w.type == "근접":
            for enemy in enemies:
                if not enemy.alive: continue
                ex = enemy.x + enemy.size / 2
                ey = enemy.y + enemy.size / 2
                dx = ex - cx
                dy = ey - cy
                dist = math.hypot(dx, dy)
                if dist <= w.attack_range:
                    angle_to_enemy = math.degrees(math.atan2(dy, dx))
                    facing_deg = math.degrees(self.facing_angle)
                    diff = (angle_to_enemy - facing_deg + 180) % 360 - 180
                    if abs(diff) <= w.attack_angle / 2:
                        enemy.take_damage(w.attack_damage)
                        eff_name = None
                        if w.shape == "spear": eff_name = "spear_effect"
                        elif w.shape == "sword": eff_name = "sword_effect"
                        elif w.shape == "wand": eff_name = "wand_effect"
                        if eff_name:
                            effects.append(Effect(ex, ey, IMAGES.get(eff_name), angle=self.facing_angle))
                        if dist != 0:
                            kb = self.knockback
                            enemy.x += (dx / dist) * kb
                            enemy.y += (dy / dist) * kb
        else:
            dir_x, dir_y = math.cos(self.facing_angle), math.sin(self.facing_angle)
            px = cx + dir_x * (self.size / 2 + 5)
            py = cy + dir_y * (self.size / 2 + 5)
            proj = Projectile(px, py, dir_x, dir_y, w.projectile_speed, w.attack_damage, shape=w.shape)
            projectiles.append(proj)
        self.attack_cooldown = w.cooldown

    def update(self):
        mx, my = pygame.mouse.get_pos()
        cx = self.x + self.size / 2
        cy = self.y + self.size / 2
        self.facing_angle = math.atan2(my - cy, mx - cx)
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        self.x = max(0, min(WIDTH - self.size, self.x))
        self.y = max(0, min(HEIGHT - self.size, self.y))

    def apply_item(self, t):
        if t == "atk_up":
            self.attack_damage += 1
            msg = "공격력 +1!"
        elif t == "spd_up":
            self.speed += 0.5
            msg = "이동속도 +0.5!"
        elif t == "heal":
            self.hp = min(self.max_hp, self.hp + 20)
            msg = "체력회복 +20!"
        else:
            msg = ""
        self.last_effect_text = msg
        self.last_effect_time = pygame.time.get_ticks()

    def draw(self, surface):
        cx = self.x + self.size / 2
        cy = self.y + self.size / 2
        p_img = IMAGES.get('player')

        target_size = (self.size, self.size)
        img = pygame.transform.smoothscale(p_img, target_size)
        deg = -math.degrees(self.facing_angle) + 90
        rotated = pygame.transform.rotate(img, deg)
        rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, rect.topleft)

        draw_weapon_visual(surface, (cx, cy), self.facing_angle, self.weapon, self.size)
        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        bar_width = 60
        bar_height = 8
        x = self.x + (self.size / 2) - (bar_width / 2)
        y = self.y - 15
        pygame.draw.rect(surface, (200, 50, 50), (x, y, bar_width, bar_height))
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, (50, 200, 50), (x, y, bar_width * hp_ratio, bar_height))

def draw_weapon_visual(surface, center, facing_angle, weapon, player_size):
    cx, cy = center
    desired = int(player_size * 1.2)
    img = IMAGES.get(weapon.shape)

    iw, ih = img.get_size()
    scale = desired / max(iw, ih)
    new_w, new_h = max(1, int(iw * scale)), max(1, int(ih * scale))
    img_s = pygame.transform.smoothscale(img, (new_w, new_h))
    deg = -math.degrees(facing_angle)
    rotated = pygame.transform.rotate(img_s, deg)
    rect = rotated.get_rect(center=(cx + math.cos(facing_angle)*(player_size*0.45), cy + math.sin(facing_angle)*(player_size*0.45)))
    surface.blit(rotated, rect.topleft)
    return

class Enemy:
    def __init__(self, x, y, is_boss=False):
        self.x, self.y = x, y
        self.is_boss = is_boss
        self.size = 60 if is_boss else 40
        self.color = (255, 150, 50) if is_boss else (200, 50, 50)
        self.hp = 300 if is_boss else 50
        self.max_hp = self.hp
        self.speed = 4 if is_boss else 2
        self.attack_damage = 20 if is_boss else 5
        self.attack_cooldown = 0
        self.attack_range = 50
        self.alive = True

    def update(self, player):
        if not self.alive: return
        dx, dy = player.x - self.x, player.y - self.y
        distance = math.hypot(dx, dy)
        if distance > 0:
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        elif distance < self.attack_range:
            player.hp -= self.attack_damage
            self.attack_cooldown = 60

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive: return
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.size, self.size))
        self.draw_health_bar(surface)

    def draw_health_bar(self, surface):
        bar_width = 40
        bar_height = 6
        x = self.x + (self.size / 2) - (bar_width / 2)
        y = self.y - 10
        pygame.draw.rect(surface, (200, 50, 50), (x, y, bar_width, bar_height))
        hp_ratio = self.hp / self.max_hp
        pygame.draw.rect(surface, (50, 200, 50), (x, y, bar_width * hp_ratio, bar_height))

class Treasure:
    def __init__(self, x, y, current_weapon_name=None):
        self.x, self.y = x, y
        self.size = 30
        self.color = (240, 200, 50)
        self.type = random.choice(["atk_up", "spd_up", "heal"])
        self.collected = False
        self.opened = False
        self.rewarded = False
        weapon_choices = [w for w in WEAPON_PREFABS if w.name != current_weapon_name]
        if random.random() < 0.5 and weapon_choices:
            prefab = random.choice(weapon_choices)
            self.weapon = Weapon(prefab.name, prefab.attack_damage, prefab.type, prefab.attack_range, prefab.attack_angle, prefab.projectile_speed, prefab.cooldown, shape=prefab.shape)
        else:
            self.weapon = None

    def draw(self, surface):
        key = 'treasure_opened' if self.opened else 'treasure_closed'
        img = IMAGES.get(key)

        iw, ih = img.get_size()
        target = 48
        scale = target / max(iw, ih)
        img_s = pygame.transform.smoothscale(img, (max(1,int(iw*scale)), max(1,int(ih*scale))))
        surface.blit(img_s, (self.x - img_s.get_width()//2, self.y - img_s.get_height()//2))

class Room:
    def __init__(self, room_type="monster", is_boss=False, coord=(0,0), dungeon_size=5, current_weapon_name=None):
        self.room_type = room_type
        self.is_boss = is_boss
        self.coord = coord
        self.dungeon_size = dungeon_size
        self.visited = False
        self.enemies = []
        self.treasure = None
        if self.is_boss:
            self.enemies = [Enemy(WIDTH // 2 - 30, HEIGHT // 2 - 30, True)]
        elif self.room_type == "monster":
            self.enemies = [Enemy(random.randint(100, 700), random.randint(100, 500)) for _ in range(random.randint(2, 4))]
        elif self.room_type == "treasure":
            margin = 60
            corners = [
                (WIDTH - margin, margin),
                (margin, HEIGHT - margin),
                (WIDTH - margin, HEIGHT - margin),
            ]
            tx, ty = random.choice(corners)
            self.treasure = Treasure(tx, ty, current_weapon_name)
        x_idx, y_idx = coord
        self.doors = {}
        if y_idx > 0: self.doors["up"] = pygame.Rect(WIDTH//2 - 40, 0, 80, 20)
        if y_idx < dungeon_size - 1: self.doors["down"] = pygame.Rect(WIDTH//2 - 40, HEIGHT - 20, 80, 20)
        if x_idx > 0: self.doors["left"] = pygame.Rect(0, HEIGHT//2 - 40, 20, 80)
        if x_idx < dungeon_size - 1: self.doors["right"] = pygame.Rect(WIDTH - 20, HEIGHT//2 - 40, 20, 80)

    def update(self, player):
        for enemy in self.enemies:
            enemy.update(player)
    def draw(self, surface):
        pygame.draw.rect(surface, (30, 30, 30), (0, 0, WIDTH, HEIGHT))
        for rect in self.doors.values(): pygame.draw.rect(surface, (240, 200, 50), rect)
        if self.room_type == "monster" or self.is_boss:
            for enemy in self.enemies: enemy.draw(surface)
        elif self.room_type == "treasure" and self.treasure:
            self.treasure.draw(surface)

class Dungeon:
    def __init__(self, difficulty, current_weapon_name):
        self.rooms = {}
        self.size = {"EASY": 5, "NORMAL": 7, "HARD": 11}[difficulty]
        self.room_coords = [(x, y) for x in range(self.size) for y in range(self.size)]
        self.current_room = (self.size // 2, self.size // 2)
        self.visited = set()
        self.generate_rooms(current_weapon_name)

    def generate_rooms(self, current_weapon_name):
        coords = self.room_coords
        start_room = self.current_room
        boss_pos = coords[-1]
        treasure_count = max(1, int(round(len(coords) * 0.2)))
        selectable_rooms = [c for c in coords if c not in (boss_pos, start_room)]
        treasure_coords = random.sample(selectable_rooms, treasure_count)
        for coord in coords:
            if coord == boss_pos:
                self.rooms[coord] = Room("monster", is_boss=True, coord=coord, dungeon_size=self.size)
            elif coord == start_room:
                self.rooms[coord] = Room("empty", coord=coord, dungeon_size=self.size)
            elif coord in treasure_coords:
                self.rooms[coord] = Room("treasure", coord=coord, dungeon_size=self.size, current_weapon_name=current_weapon_name)
            else:
                self.rooms[coord] = Room("monster", coord=coord, dungeon_size=self.size)

    def get_room(self, coord): return self.rooms[coord]
    def move_room(self, direction):
        x, y = self.current_room
        if direction == "up": y -= 1
        elif direction == "down": y += 1
        elif direction == "left": x -= 1
        elif direction == "right": x += 1
        if 0 <= x < self.size and 0 <= y < self.size:
            self.current_room = (x, y)
            self.visited.add(self.current_room)

def draw_minimap(surface, dungeon):
    map_surface = pygame.Surface((150, 150))
    map_surface.fill((20, 20, 20))
    size = 12
    offset = 10
    for (x, y), room in dungeon.rooms.items():
        if (x, y) in dungeon.visited:
            color = (255, 150, 50) if room.is_boss else ((240, 200, 50) if room.room_type == "treasure" else (50, 200, 50))
        else:
            color = (150, 150, 150)
        rect = pygame.Rect(offset + x * size, offset + y * size, 10, 10)
        pygame.draw.rect(map_surface, color, rect)
        if (x, y) == dungeon.current_room:
            pygame.draw.rect(map_surface, (255, 255, 255), rect, 2)
    surface.blit(map_surface, (20, 20))

def draw_stats(surface, player):
    stats = f"HP: {int(player.hp)}/{player.max_hp} | ATK: {player.weapon.attack_damage} ({player.weapon.name}) | TYPE: {player.weapon.type} | SPD: {round(player.speed,1)}"
    text = font.render(stats, True, (255, 255, 255))
    surface.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT - 60))

class Projectile:
    def __init__(self, x, y, dir_x, dir_y, speed, damage, radius=6, shape=None):
        self.x, self.y = x, y
        length = math.hypot(dir_x, dir_y)
        self.dx, self.dy = (dir_x / length, dir_y / length) if length != 0 else (1, 0)
        self.speed = speed
        self.damage = damage
        self.radius = radius
        self.alive = True
        self.shape = shape

    def update(self, enemies, effects, room=None):
        if not self.alive: return
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed
        if self.x < -50 or self.x > WIDTH + 50 or self.y < -50 or self.y > HEIGHT + 50:
            self.alive = False
            return
        for enemy in enemies:
            if not enemy.alive: continue
            ecx = enemy.x + enemy.size / 2
            ecy = enemy.y + enemy.size / 2
            dist = math.hypot(self.x - ecx, self.y - ecy)
            if dist <= self.radius + enemy.size * 0.25:
                enemy.take_damage(self.damage)
                eff_name = None
                if self.shape == "wand": eff_name = "wand_effect"
                elif self.shape == "spear": eff_name = "spear_effect"
                elif self.shape == "sword": eff_name = "sword_effect"
                if eff_name:
                    effects.append(Effect(ecx, ecy, IMAGES.get(eff_name), angle=int(math.atan2(self.dy, self.dx))))
                if self.shape != "bow":
                    self.alive = False
                    break
        if self.alive and room is not None and self.shape == "bow":
            if self.y <= 20:
                door_up = room.doors.get("up")
                if not (door_up and door_up.collidepoint(self.x, self.y)):
                    self.alive = False; return
            if self.y >= HEIGHT - 20:
                door_down = room.doors.get("down")
                if not (door_down and door_down.collidepoint(self.x, self.y)):
                    self.alive = False; return
            if self.x <= 20:
                door_left = room.doors.get("left")
                if not (door_left and door_left.collidepoint(self.x, self.y)):
                    self.alive = False; return
            if self.x >= WIDTH - 20:
                door_right = room.doors.get("right")
                if not (door_right and door_right.collidepoint(self.x, self.y)):
                    self.alive = False; return

    def draw(self, surface):
        if not self.alive: return
        proj_img = IMAGES.get(f"{self.shape}_projectile") or IMAGES.get(self.shape) if self.shape else None

        iw, ih = proj_img.get_size()
        scale = max(1, int(self.radius*2))
        img_s = pygame.transform.smoothscale(proj_img, (scale, scale))
        deg = -math.degrees(math.atan2(self.dy, self.dx))
        rotated = pygame.transform.rotate(img_s, deg)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)
        return

class Effect:
    def __init__(self, x, y, image=None, lifetime=400, angle=0):
        self.x = x
        self.y = y
        self.image = image
        self.lifetime = lifetime
        self.start = pygame.time.get_ticks()
        self.angle = angle

    def update(self):
        return pygame.time.get_ticks() - self.start >= self.lifetime

    def draw(self, surface):

        iw, ih = self.image.get_size()
        target = 48
        scale = target / max(iw, ih)
        img_s = pygame.transform.smoothscale(self.image, (max(1,int(iw*scale)), max(1,int(ih*scale))))
        deg = -math.degrees(self.angle)
        rotated = pygame.transform.rotate(img_s, deg)
        surface.blit(rotated, (self.x - rotated.get_width()//2, self.y - rotated.get_height()//2))

def select_difficulty():
    btn_w, btn_h = 220, 60
    spacing = 20
    labels = ["EASY", "NORMAL", "HARD"]
    total_h = btn_h * len(labels) + spacing * (len(labels) - 1)
    start_y = HEIGHT // 2 - total_h // 2
    while True:
        screen.fill((0, 0, 0))
        title = font.render("난이도를 설정하세요", True, (240, 200, 50))
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//4 - title.get_height()//2))

        mx, my = pygame.mouse.get_pos()
        clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True

        for i, label in enumerate(labels):
            x = WIDTH // 2 - btn_w // 2
            y = start_y + i * (btn_h + spacing)
            rect = pygame.Rect(x, y, btn_w, btn_h)
            color = (150, 150, 150) if rect.collidepoint(mx, my) else (100, 100, 100)
            pygame.draw.rect(screen, color, rect, border_radius=8)
            txt = font.render(label, True, (255, 255, 255))
            screen.blit(txt, (x + btn_w//2 - txt.get_width()//2, y + btn_h//2 - txt.get_height()//2))
            if clicked and rect.collidepoint(mx, my):
                return label

        pygame.display.flip()
        clock.tick(60)

def main():
    difficulty = select_difficulty()
    if difficulty not in ["EASY", "NORMAL", "HARD"]:
        difficulty = "EASY"

    player = Player()
    dungeon = Dungeon(difficulty, player.weapon.name)
    dungeon.visited.add(dungeon.current_room)

    treasure_modal = None
    projectiles = []
    effects = []

    running = True
    while running:
        screen.fill((0, 0, 0))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if treasure_modal:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_y:
                        player.equip_weapon(treasure_modal['weapon'])
                        treasure_modal['room'].treasure.rewarded = True
                        treasure_modal['room'].treasure.opened = True
                        treasure_modal = None
                    elif event.key == pygame.K_n:
                        treasure_modal['room'].treasure.rewarded = True
                        treasure_modal['room'].treasure.opened = True
                        player.last_effect_text = "기존 무기 유지"
                        player.last_effect_time = pygame.time.get_ticks()
                        treasure_modal = None
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                room = dungeon.get_room(dungeon.current_room)
                player.attack(room.enemies, projectiles, effects)

        room = dungeon.get_room(dungeon.current_room)

        if not treasure_modal:
            player.handle_input()
            player.update()
            room.update(player)
            for p in projectiles:
                p.update(room.enemies, effects, room)
            projectiles = [p for p in projectiles if p.alive]

        if player.hp <= 0:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            go_text = font.render("GAME OVER", True, (200, 50, 50))
            screen.blit(go_text, (WIDTH//2 - go_text.get_width()//2, HEIGHT//2 - go_text.get_height()//2))
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            sys.exit()

        if room.room_type == "treasure" and room.treasure and not room.treasure.collected:
            player_rect = pygame.Rect(player.x, player.y, player.size, player.size)
            half = room.treasure.size // 2
            treasure_rect = pygame.Rect(room.treasure.x - half, room.treasure.y - half, room.treasure.size, room.treasure.size)
            if player_rect.colliderect(treasure_rect):
                if not room.treasure.opened:
                    room.treasure.opened = True
                    if room.treasure.weapon:
                        treasure_modal = {'weapon': room.treasure.weapon, 'room': room}
                    else:
                        player.apply_item(room.treasure.type)
                        room.treasure.rewarded = True
                else:
                    if getattr(room.treasure, 'rewarded', False):
                        pass

        for direction, rect in room.doors.items():
            if pygame.Rect(player.x, player.y, player.size, player.size).colliderect(rect):
                if any(e.alive for e in room.enemies):
                    player.last_effect_text = "방을 정리해야 이동할 수 있습니다."
                    player.last_effect_time = pygame.time.get_ticks()
                    break
                dungeon.move_room(direction)
                player.x, player.y = WIDTH//2, HEIGHT//2
                projectiles.clear()
                break

        room.draw(screen)
        player.draw(screen)
        for p in projectiles: p.draw(screen)
        new_effects = []
        for e in effects:
            if not e.update():
                e.draw(screen)
                new_effects.append(e)
        effects = new_effects
        draw_minimap(screen, dungeon)
        draw_stats(screen, player)

        if treasure_modal:
            w = treasure_modal['weapon']
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            title = font.render("무기 발견!", True, (240, 200, 50))
            new_line = font.render(f"새 무기: {w.name}  ATK {w.attack_damage}  TYPE {w.type}", True, (255, 255, 255))
            cur_line = font.render(f"현재 무기: {player.weapon.name}  ATK {player.weapon.attack_damage}  TYPE {player.weapon.type}", True, (255, 255, 255))
            hint = font.render("Y: 장착   N: 유지", True, (150, 150, 150))
            screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//2 - 80))
            screen.blit(new_line, (WIDTH//2 - new_line.get_width()//2, HEIGHT//2 - 40))
            screen.blit(cur_line, (WIDTH//2 - cur_line.get_width()//2, HEIGHT//2))
            screen.blit(hint, (WIDTH//2 - hint.get_width()//2, HEIGHT//2 + 60))

        if pygame.time.get_ticks() - player.last_effect_time < 2000:
            text = font.render(player.last_effect_text, True, (255, 255, 255))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, 50))
        if room.is_boss and all(not e.alive for e in room.enemies):
            text = font.render("던전 클리어!", True, (240, 200, 50))
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
            pygame.display.flip()
            pygame.time.delay(3000)
            pygame.quit()
            sys.exit()
        pygame.display.flip()
        clock.tick(60)

main()