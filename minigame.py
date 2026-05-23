import math
import os
import random
import pygame
from sys import exit


class Fighter:
    """Melee fighter on a tiled 7×7 battlefield.

    Movement : WASD
    Attack   : Left mouse button (melee swing in facing direction)
    Quit     : ESC

    Returns True (won) or False (lost/quit) from run().
    """

    BG_COLOR       = (20,  20,  30)
    PLAYER_COLOR   = (100, 200, 255)
    MELEE_COLOR    = (255, 220, 80, 100)
    ENEMY_COLOR    = (220, 60,  60)
    HP_FULL        = (200, 50,  50)
    HP_EMPTY       = (60,  60,  60)
    TEXT_COLOR     = (255, 255, 255)

    _DIFFICULTY_SETTINGS = {
        0: dict(enemy_speed_min=30,  enemy_speed_max=70,  spawn_ms=1200, hp=3, duration=45),
        1: dict(enemy_speed_min=20,  enemy_speed_max=42,  spawn_ms=1800, hp=5, duration=30),
    }

    PLAYER_SPEED       = 220
    ATTACK_COOLDOWN_MS = 300
    ATTACK_FLASH_MS    = 150
    ATTACK_WINDUP_SEC  = 0.5   # thời gian chờ trước khi enemy tấn công
    PLAYER_RADIUS      = 14
    ENEMY_RADIUS       = 14          # fallback when sprites not loaded
    MELEE_RADIUS       = int(PLAYER_RADIUS * 1.5)   # = 21
    KNOCKBACK_DIST     = 70

    BOARD_COLS    = 12
    BOARD_ROWS    = 12
    TILE_GRASS_ID = 38
    TILE_PATH_IDS = frozenset({1, 18, 20})

    _TILE_DIR         = os.path.join("media", "images", "minigame", "TopDownShooter", "tiles")
    _OBJ_DIR          = os.path.join("media", "images", "minigame", "TopDownShooter", "ground_objects")
    _SPRITE_DIR       = os.path.join("media", "images", "minigame", "TopDownShooter", "character_sprites")
    _ENEMY_SPRITE_DIR = os.path.join("media", "images", "minigame", "TopDownShooter", "enemy_sprites")

    _DIR_VEC  = {"W": (0.0, -1.0), "A": (-1.0, 0.0), "S": (0.0, 1.0), "D": (1.0, 0.0)}
    _ANIM_FPS = 10.0

    def __init__(self, surf: pygame.Surface, clock: pygame.time.Clock, difficulty: int = 0) -> None:
        self.surf  = surf
        self.clock = clock
        self.w     = surf.get_width()
        self.h     = surf.get_height()
        cfg = self._DIFFICULTY_SETTINGS.get(difficulty, self._DIFFICULTY_SETTINGS[0])
        self.ENEMY_SPEED_MIN   = cfg["enemy_speed_min"]
        self.ENEMY_SPEED_MAX   = cfg["enemy_speed_max"]
        self.SPAWN_INTERVAL_MS = cfg["spawn_ms"]
        self.PLAYER_MAX_HP     = cfg["hp"]
        self.GAME_DURATION_SEC = cfg["duration"]
        fs = max(14, self.w // 22)
        self.font = pygame.font.SysFont("monospace", fs, bold=True)

        self.tile_w   = self.w // self.BOARD_COLS
        self.tile_h   = self.h // self.BOARD_ROWS
        self.board_ox = (self.w - self.tile_w * self.BOARD_COLS) // 2
        self.board_oy = (self.h - self.tile_h * self.BOARD_ROWS) // 2

        self._tile_imgs:     dict[int, pygame.Surface]               = {}
        self._obj_imgs:      list[pygame.Surface]                    = []
        self._sprites:       dict[str, dict[str, list[pygame.Surface]]] = {}
        self._enemy_sprites: dict[str, dict[str, list[pygame.Surface]]] = {}
        self._enemy_hrad:    int = self.ENEMY_RADIUS
        self._face_dir     = "S"
        self._anim_state   = "Run"
        self._anim_frame   = 0
        self._anim_elapsed = 0.0
        self._load_assets()
        self._board_tiles, _ = self._generate_board()
        self._board_objects = self._place_objects()
        r = self.MELEE_RADIUS
        self._melee_flash_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)

    # ------------------------------------------------------------------ #
    # Asset loading
    # ------------------------------------------------------------------ #

    def _load_assets(self) -> None:
        if os.path.isdir(self._TILE_DIR):
            for i in range(1, 65):
                path = os.path.join(self._TILE_DIR, f"FieldsTile_{i:02d}.png")
                if os.path.isfile(path):
                    img = pygame.image.load(path).convert_alpha()
                    self._tile_imgs[i] = pygame.transform.smoothscale(
                        img, (self.tile_w, self.tile_h))

        if os.path.isdir(self._OBJ_DIR):
            obj_px = int(min(self.tile_w, self.tile_h) * 0.72)
            for folder in sorted(os.listdir(self._OBJ_DIR)):
                fp = os.path.join(self._OBJ_DIR, folder)
                if not os.path.isdir(fp):
                    continue
                for fname in sorted(os.listdir(fp)):
                    if fname.lower().endswith(".png"):
                        img = pygame.image.load(os.path.join(fp, fname)).convert_alpha()
                        self._obj_imgs.append(
                            pygame.transform.smoothscale(img, (obj_px, obj_px)))

        spr_px = max(48, int(min(self.tile_w, self.tile_h) * 2.0))
        self._sprites       = self._load_sprite_dir(self._SPRITE_DIR,       ["Run", "Attack"],          spr_px)
        self._enemy_hrad    = spr_px // 2
        self._enemy_sprites = self._load_sprite_dir(self._ENEMY_SPRITE_DIR, ["Run", "Attack", "Death"], spr_px,
                                                     file_map={"Run": "Walk"})

    def _load_sprite_dir(self, base_dir: str, anims: list, size: int, file_map: dict = None) -> dict:
        result: dict[str, dict[str, list[pygame.Surface]]] = {}
        for direction in ("W", "A", "S", "D"):
            result[direction] = {}
            for anim in anims:
                fname = file_map.get(anim, anim) if file_map else anim
                path = os.path.join(base_dir, f"{direction}_{fname}.png")
                if not os.path.isfile(path):
                    continue
                sheet   = pygame.image.load(path).convert_alpha()
                frame_w = sheet.get_height()
                result[direction][anim] = [
                    pygame.transform.smoothscale(
                        sheet.subsurface((i * frame_w, 0, frame_w, frame_w)),
                        (size, size)
                    )
                    for i in range(sheet.get_width() // frame_w)
                ]
        return result

    # ------------------------------------------------------------------ #
    # Board generation
    # ------------------------------------------------------------------ #

    def _generate_board(self):
        """Return (tile_grid, is_path_grid) satisfying adjacency and coverage rules."""
        COLS, ROWS = self.BOARD_COLS, self.BOARD_ROWS
        TOTAL      = COLS * ROWS
        mixed_ids  = [i for i in range(1, 65)
                      if i not in self.TILE_PATH_IDS and i != self.TILE_GRASS_ID]

        edges = (
            [(0, c) for c in range(COLS)] +
            [(ROWS-1, c) for c in range(COLS)] +
            [(r, 0) for r in range(ROWS)] +
            [(r, COLS-1) for r in range(ROWS)]
        )
        tile_path_ids_list = list(self.TILE_PATH_IDS)
        for _ in range(300):
            start     = random.choice(edges)
            path_zone: set[tuple[int, int]] = {start}
            frontier  = [start]
            target    = random.randint(int(TOTAL * 0.28), int(TOTAL * 0.40))

            while frontier and len(path_zone) < target:
                idx  = random.randrange(len(frontier))
                r, c = frontier[idx]
                dirs = [(-1,0),(1,0),(0,-1),(0,1)]
                random.shuffle(dirs)
                grew = False
                for dr, dc in dirs:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in path_zone:
                        path_zone.add((nr, nc))
                        frontier.append((nr, nc))
                        grew = True
                        break
                if not grew:
                    frontier.pop(idx)

            is_path = [[False]*COLS for _ in range(ROWS)]
            for pr, pc in path_zone:
                is_path[pr][pc] = True

            def _has_path_nbr(r, c):
                return any(
                    0 <= r+dr < ROWS and 0 <= c+dc < COLS and is_path[r+dr][c+dc]
                    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1))
                )
            def _has_grass_nbr(r, c):
                return any(
                    0 <= r+dr < ROWS and 0 <= c+dc < COLS and not is_path[r+dr][c+dc]
                    for dr, dc in ((-1,0),(1,0),(0,-1),(0,1))
                )

            # path + mixed tiles = path-zone cells + grass cells adjacent to path-zone
            non_grass = sum(
                1 for r in range(ROWS) for c in range(COLS)
                if is_path[r][c] or _has_path_nbr(r, c)
            )
            if not (0.50 <= non_grass / TOTAL <= 0.60):
                continue

            tiles = [[0]*COLS for _ in range(ROWS)]
            for r in range(ROWS):
                for c in range(COLS):
                    if is_path[r][c]:
                        tiles[r][c] = (random.choice(mixed_ids) if _has_grass_nbr(r, c)
                                       else random.choice(tile_path_ids_list))
                    else:
                        tiles[r][c] = (random.choice(mixed_ids) if _has_path_nbr(r, c)
                                       else self.TILE_GRASS_ID)
            return tiles, is_path

        # Fallback: all grass
        return ([[self.TILE_GRASS_ID]*COLS for _ in range(ROWS)],
                [[False]*COLS for _ in range(ROWS)])

    # ------------------------------------------------------------------ #
    # Ground object placement
    # ------------------------------------------------------------------ #

    def _place_objects(self) -> dict:
        if not self._obj_imgs:
            return {}
        COLS, ROWS = self.BOARD_COLS, self.BOARD_ROWS
        grass_cells = [
            (r, c)
            for r in range(ROWS) for c in range(COLS)
            if self._board_tiles[r][c] == self.TILE_GRASS_ID
        ]
        random.shuffle(grass_cells)
        occupied: set[tuple[int, int]] = set()
        result:   dict[tuple[int, int], pygame.Surface] = {}
        for r, c in grass_cells:
            adj_busy = any(
                (r+dr, c+dc) in occupied
                for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                if dr or dc
            )
            if not adj_busy and random.random() < 0.55:
                result[(r, c)] = random.choice(self._obj_imgs)
                occupied.add((r, c))
        return result

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    @staticmethod
    def _vec_to_dir(dx: float, dy: float) -> str:
        if abs(dx) >= abs(dy):
            return "D" if dx >= 0 else "A"
        return "S" if dy >= 0 else "W"

    def run(self) -> bool:
        """Run the minigame loop. Returns True if won, False otherwise."""
        px, py    = float(self.w) / 2, float(self.h) / 2
        player_hp = self.PLAYER_MAX_HP
        attack_range = self.PLAYER_RADIUS + self._enemy_hrad + 5
        enemies: list[dict] = []

        score       = 0
        last_attack = -self.ATTACK_COOLDOWN_MS
        last_spawn  = 0
        start_ms    = pygame.time.get_ticks()
        running     = True
        elapsed     = 0.0
        frame_dur   = 1.0 / self._ANIM_FPS

        while running:
            dt        = self.clock.tick(60) / 1000.0
            now       = pygame.time.get_ticks()
            elapsed   = (now - start_ms) / 1000.0
            time_left = max(0.0, self.GAME_DURATION_SEC - elapsed)

            # ── Events ──────────────────────────────────────────────── #
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_w: self._face_dir = "W"
                    elif event.key == pygame.K_s: self._face_dir = "S"
                    elif event.key == pygame.K_a: self._face_dir = "A"
                    elif event.key == pygame.K_d: self._face_dir = "D"

            keys      = pygame.key.get_pressed()
            attacking = pygame.mouse.get_pressed()[0] or keys[pygame.K_SPACE]

            # ── Movement (WASD) ──────────────────────────────────────── #
            mdx = mdy = 0.0
            if keys[pygame.K_w]: mdy -= 1
            if keys[pygame.K_s]: mdy += 1
            if keys[pygame.K_a]: mdx -= 1
            if keys[pygame.K_d]: mdx += 1
            if mdx and mdy:
                mdx *= 0.7071; mdy *= 0.7071
            r = self.PLAYER_RADIUS
            px = max(r, min(self.w - r, px + mdx * self.PLAYER_SPEED * dt))
            py = max(r, min(self.h - r, py + mdy * self.PLAYER_SPEED * dt))

            # ── Melee attack ─────────────────────────────────────────── #
            if attacking and now - last_attack >= self.ATTACK_COOLDOWN_MS:
                last_attack = now
                fdx, fdy    = self._DIR_VEC[self._face_dir]
                hx = px + fdx * self.PLAYER_RADIUS
                hy = py + fdy * self.PLAYER_RADIUS
                for e in enemies:
                    if e["state"] == "Death":
                        continue
                    if math.hypot(hx - e["x"], hy - e["y"]) < self.MELEE_RADIUS + self._enemy_hrad:
                        kd = math.hypot(e["x"] - hx, e["y"] - hy)
                        if kd > 0:
                            e["x"] += (e["x"] - hx) / kd * self.KNOCKBACK_DIST
                            e["y"] += (e["y"] - hy) / kd * self.KNOCKBACK_DIST
                        else:
                            e["x"] += fdx * self.KNOCKBACK_DIST
                            e["y"] += fdy * self.KNOCKBACK_DIST
                        e["state"]        = "Death"
                        e["frame"]        = 0
                        e["elapsed"]      = 0.0
                        e["death_frames"] = self._enemy_sprites.get(e["dir"], {}).get("Death", [])
                        score += 1

            # ── Spawn enemies ────────────────────────────────────────── #
            if now - last_spawn >= self.SPAWN_INTERVAL_MS:
                side  = random.randint(0, 3)
                speed = random.uniform(self.ENEMY_SPEED_MIN, self.ENEMY_SPEED_MAX)
                er    = float(self._enemy_hrad)
                if side == 0:   ex, ey = random.uniform(0, self.w), -er
                elif side == 1: ex, ey = random.uniform(0, self.w), self.h + er
                elif side == 2: ex, ey = -er, random.uniform(0, self.h)
                else:           ex, ey = self.w + er, random.uniform(0, self.h)
                enemies.append({"x": ex, "y": ey, "speed": speed,
                                "dir": "S", "state": "Run",
                                "frame": 0, "elapsed": 0.0,
                                "dead": False, "windup": 0.0, "hit_dealt": False,
                                "death_frames": []})
                last_spawn = now

            # ── Update each enemy ─────────────────────────────────────── #
            for e in enemies:
                if e["dead"]:
                    continue
                if e["state"] == "Death":
                    e["elapsed"] += dt
                    while e["elapsed"] >= frame_dur:
                        e["elapsed"] -= frame_dur
                        e["frame"] += 1
                        if e["frame"] >= len(e["death_frames"]):
                            e["dead"] = True
                            break
                elif e["state"] == "Attack":
                    attack_frames = self._enemy_sprites.get(e["dir"], {}).get("Attack", [])
                    n_atk = len(attack_frames) if attack_frames else 4
                    e["elapsed"] += dt
                    while e["elapsed"] >= frame_dur:
                        e["elapsed"] -= frame_dur
                        e["frame"] += 1
                    # Trừ máu 1 lần khi animation đến nửa sau (frame active)
                    if not e["hit_dealt"] and e["frame"] >= n_atk // 2:
                        if math.hypot(px - e["x"], py - e["y"]) < attack_range:
                            player_hp     -= 1
                            e["hit_dealt"] = True
                    # Animation xong → quay lại Run
                    if e["frame"] >= n_atk:
                        e["state"]     = "Run"
                        e["frame"]     = 0
                        e["elapsed"]   = 0.0
                        e["windup"]    = 0.0
                        e["hit_dealt"] = False
                elif e["state"] == "Windup":
                    ddx, ddy = px - e["x"], py - e["y"]
                    dist = math.hypot(ddx, ddy)
                    e["dir"] = self._vec_to_dir(ddx, ddy)
                    # Đứng yên, giữ nguyên frame (idle ảo)
                    e["windup"] -= dt
                    if dist >= attack_range:
                        # Player đi ra xa → hủy windup
                        e["state"]  = "Run"
                        e["windup"] = 0.0
                    elif e["windup"] <= 0:
                        # Hết thời gian chờ → tấn công
                        e["state"]     = "Attack"
                        e["frame"]     = 0
                        e["elapsed"]   = 0.0
                        e["hit_dealt"] = False
                else:  # "Run"
                    ddx, ddy = px - e["x"], py - e["y"]
                    dist = math.hypot(ddx, ddy)
                    if dist > 0:
                        e["x"]  += (ddx / dist) * e["speed"] * dt
                        e["y"]  += (ddy / dist) * e["speed"] * dt
                        e["dir"] = self._vec_to_dir(ddx, ddy)
                    e["elapsed"] += dt
                    while e["elapsed"] >= frame_dur:
                        e["elapsed"] -= frame_dur
                        run_frames = self._enemy_sprites.get(e["dir"], {}).get("Run", [])
                        if run_frames:
                            e["frame"] = (e["frame"] + 1) % len(run_frames)
                    # Khi lại gần → bắt đầu windup 0.5s
                    if dist < attack_range:
                        e["state"]  = "Windup"
                        e["windup"] = self.ATTACK_WINDUP_SEC

            enemies = [e for e in enemies if not e["dead"]]

            if player_hp <= 0 or time_left <= 0:
                running = False

            # ── Player animation state ────────────────────────────────── #
            moving    = bool(mdx or mdy)
            new_state = "Attack" if attacking else "Run"
            if new_state != self._anim_state:
                self._anim_state   = new_state
                self._anim_frame   = 0
                self._anim_elapsed = 0.0
            if moving or attacking:
                self._anim_elapsed += dt
                while self._anim_elapsed >= frame_dur:
                    self._anim_elapsed -= frame_dur
                    frames = self._sprites.get(self._face_dir, {}).get(self._anim_state, [])
                    if frames:
                        self._anim_frame = (self._anim_frame + 1) % len(frames)
            else:
                self._anim_frame   = 0
                self._anim_elapsed = 0.0

            # ── Draw ─────────────────────────────────────────────────── #
            self._draw_bg()
            self._draw_enemies(enemies)
            self._draw_melee_flash(px, py, now - last_attack)
            self._draw_player(px, py)
            self._draw_hud(player_hp, score, time_left)
            pygame.display.flip()

        return player_hp > 0 and elapsed >= self.GAME_DURATION_SEC - 0.5

    # ------------------------------------------------------------------ #
    # Drawing helpers
    # ------------------------------------------------------------------ #

    def _draw_bg(self) -> None:
        self.surf.fill(self.BG_COLOR)
        for r in range(self.BOARD_ROWS):
            for c in range(self.BOARD_COLS):
                tid = self._board_tiles[r][c]
                x   = self.board_ox + c * self.tile_w
                y   = self.board_oy + r * self.tile_h
                if tid in self._tile_imgs:
                    self.surf.blit(self._tile_imgs[tid], (x, y))
                else:
                    col = (40, 80, 40) if tid == self.TILE_GRASS_ID else (100, 80, 50)
                    pygame.draw.rect(self.surf, col, (x, y, self.tile_w, self.tile_h))
        for (r, c), img in self._board_objects.items():
            x = self.board_ox + c * self.tile_w + (self.tile_w - img.get_width())  // 2
            y = self.board_oy + r * self.tile_h + (self.tile_h - img.get_height()) // 2
            self.surf.blit(img, (x, y))

    def _draw_player(self, x: float, y: float) -> None:
        frames = self._sprites.get(self._face_dir, {}).get(self._anim_state, [])
        if not frames:
            # Fallback triangle using current facing direction
            fdx, fdy = self._DIR_VEC[self._face_dir]
            r        = float(self.PLAYER_RADIUS)
            pdx, pdy = -fdy, fdx
            tip   = (x + fdx*r,                    y + fdy*r)
            left  = (x - fdx*r*0.6 + pdx*r*0.75,  y - fdy*r*0.6 + pdy*r*0.75)
            right = (x - fdx*r*0.6 - pdx*r*0.75,  y - fdy*r*0.6 - pdy*r*0.75)
            pts = [(int(p[0]), int(p[1])) for p in (tip, left, right)]
            pygame.draw.polygon(self.surf, self.PLAYER_COLOR, pts)
            pygame.draw.polygon(self.surf, (200, 240, 255), pts, 2)
            return
        frame = frames[self._anim_frame % len(frames)]
        self.surf.blit(frame, (int(x) - frame.get_width() // 2,
                                int(y) - frame.get_height() // 2))

    def _draw_melee_flash(self, px: float, py: float, ms_since_attack: int) -> None:
        if ms_since_attack >= self.ATTACK_FLASH_MS:
            return
        fdx, fdy = self._DIR_VEC[self._face_dir]
        hx = int(px + fdx * self.PLAYER_RADIUS)
        hy = int(py + fdy * self.PLAYER_RADIUS)
        alpha = int(160 * (1.0 - ms_since_attack / self.ATTACK_FLASH_MS))
        r     = self.MELEE_RADIUS
        s     = self._melee_flash_surf
        s.fill((0, 0, 0, 0))
        pygame.draw.circle(s, (*self.MELEE_COLOR[:3], alpha), (r, r), r)
        self.surf.blit(s, (hx - r, hy - r))

    def _draw_enemies(self, enemies: list) -> None:
        for e in enemies:
            draw_state = "Run" if e["state"] == "Windup" else e["state"]
            frames = self._enemy_sprites.get(e["dir"], {}).get(draw_state, [])
            if frames:
                frame = frames[min(e["frame"], len(frames) - 1)]
                self.surf.blit(frame, (int(e["x"]) - frame.get_width()  // 2,
                                       int(e["y"]) - frame.get_height() // 2))
            else:
                r = self._enemy_hrad
                pygame.draw.circle(self.surf, self.ENEMY_COLOR,  (int(e["x"]), int(e["y"])), r)
                pygame.draw.circle(self.surf, (255, 120, 120),    (int(e["x"]), int(e["y"])), r, 2)

    def _draw_hud(self, hp: int, score: int, time_left: float) -> None:
        for i in range(self.PLAYER_MAX_HP):
            color = self.HP_FULL if i < hp else self.HP_EMPTY
            pygame.draw.circle(self.surf, color, (14 + i*22, 14), 9)
        s_lbl = self.font.render(f"SCORE: {score}", True, self.TEXT_COLOR)
        self.surf.blit(s_lbl, (8, self.h - s_lbl.get_height() - 6))
        t_lbl = self.font.render(f"{int(time_left)}s", True, self.TEXT_COLOR)
        self.surf.blit(t_lbl, (self.w - t_lbl.get_width() - 8, self.h - t_lbl.get_height() - 6))


# ====================================================================== #


class Minesweeper:
    """Minesweeper minigame rendered on a given pygame Surface.

    Controls: Left click to reveal, Right click to flag/unflag, ESC to quit.
    First click is always safe (mines placed after first click).
    Returns True (won) or False (lost/quit) from run().

    difficulty=0 → hard  ( 9×9,  12 mines)
    difficulty=1 → easy  ( 7×7,   7 mines)
    """

    _DIFFICULTY = {
        0: dict(cols=9, rows=9, mines=12),
        1: dict(cols=7, rows=7, mines=7),
    }

    BG_COLOR      = (20,  20,  25)
    COLOR_HIDDEN  = (90,  90,  105)
    COLOR_OPEN    = (190, 190, 195)
    COLOR_FLAG    = (210, 65,  65)
    COLOR_MINE    = (25,  25,  25)
    COLOR_BORDER  = (45,  45,  55)
    COLOR_EXPLODE = (255, 80,  40)
    TEXT_COLOR    = (255, 255, 255)
    NUMBER_COLORS = [
        None,
        (30,  60,  255),   # 1
        (20,  140, 20),    # 2
        (220, 40,  40),    # 3
        (0,   0,   160),   # 4
        (160, 0,   0),     # 5
        (0,   160, 160),   # 6
        (10,  10,  10),    # 7
        (100, 100, 100),   # 8
    ]

    def __init__(self, surf: pygame.Surface, clock: pygame.time.Clock, difficulty: int = 0) -> None:
        self.surf  = surf
        self.clock = clock
        self.w     = surf.get_width()
        self.h     = surf.get_height()

        cfg = self._DIFFICULTY.get(difficulty, self._DIFFICULTY[0])
        self.cols        = cfg["cols"]
        self.rows        = cfg["rows"]
        self.total_mines = cfg["mines"]

        self.cell = min(self.w // self.cols, self.h // self.rows)
        grid_w    = self.cell * self.cols
        grid_h    = self.cell * self.rows
        self.ox   = (self.w - grid_w) // 2
        self.oy   = (self.h - grid_h) // 2

        fs = max(10, self.cell * 11 // 16)
        self.font      = pygame.font.SysFont("monospace", fs, bold=True)
        self.font_big  = pygame.font.SysFont("monospace", max(16, self.w // 12), bold=True)

        self.grid      = [[0]     * self.cols for _ in range(self.rows)]
        self.revealed  = [[False] * self.cols for _ in range(self.rows)]
        self.flagged   = [[False] * self.cols for _ in range(self.rows)]
        self.first_click = True
        self.flags_left  = self.total_mines

    # ------------------------------------------------------------------ #

    def run(self) -> bool:
        running     = True
        game_over   = False
        won         = False
        hit_mine_rc = None   # (r, c) of mine that was clicked

        while running:
            self.clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                    # Adjust mouse pos to surf-local coords
                    sx, sy = self.surf.get_abs_offset()
                    mx, my = event.pos[0] - sx, event.pos[1] - sy
                    cell = self._pixel_to_cell(mx, my)
                    if cell is None:
                        continue
                    r, c = cell

                    if event.button == 1:    # left click → reveal
                        if self.flagged[r][c]:
                            continue
                        if self.first_click:
                            self._place_mines(r, c)
                            self.first_click = False
                        if self.grid[r][c] == -1:
                            self.revealed[r][c] = True
                            hit_mine_rc = (r, c)
                            game_over   = True
                        else:
                            self._flood_reveal(r, c)
                            if self._check_win():
                                won = game_over = True

                    elif event.button == 3:  # right click → flag
                        if not self.revealed[r][c]:
                            if self.flagged[r][c]:
                                self.flagged[r][c] = False
                                self.flags_left += 1
                            elif self.flags_left > 0:
                                self.flagged[r][c] = True
                                self.flags_left -= 1

                # Close result overlay on any click after game ends
                if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                    running = False

            self._draw(hit_mine_rc, won if game_over else None)
            pygame.display.flip()

        return won

    # ------------------------------------------------------------------ #
    # Grid logic
    # ------------------------------------------------------------------ #

    def _place_mines(self, safe_r: int, safe_c: int) -> None:
        safe = {
            (safe_r + dr, safe_c + dc)
            for dr in range(-1, 2) for dc in range(-1, 2)
            if 0 <= safe_r + dr < self.rows and 0 <= safe_c + dc < self.cols
        }
        pool = [(r, c) for r in range(self.rows) for c in range(self.cols) if (r, c) not in safe]
        for r, c in random.sample(pool, min(self.total_mines, len(pool))):
            self.grid[r][c] = -1
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == -1:
                    continue
                self.grid[r][c] = sum(
                    1 for dr in range(-1, 2) for dc in range(-1, 2)
                    if 0 <= r+dr < self.rows and 0 <= c+dc < self.cols
                    and self.grid[r+dr][c+dc] == -1
                )

    def _flood_reveal(self, start_r: int, start_c: int) -> None:
        stack = [(start_r, start_c)]
        while stack:
            r, c = stack.pop()
            if not (0 <= r < self.rows and 0 <= c < self.cols):
                continue
            if self.revealed[r][c] or self.flagged[r][c]:
                continue
            self.revealed[r][c] = True
            if self.grid[r][c] == 0:
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        if dr or dc:
                            stack.append((r + dr, c + dc))

    def _pixel_to_cell(self, mx: int, my: int):
        c = (mx - self.ox) // self.cell
        r = (my - self.oy) // self.cell
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return r, c
        return None

    def _check_win(self) -> bool:
        return all(
            self.revealed[r][c]
            for r in range(self.rows) for c in range(self.cols)
            if self.grid[r][c] != -1
        )

    # ------------------------------------------------------------------ #
    # Drawing
    # ------------------------------------------------------------------ #

    def _draw(self, hit_mine_rc, result) -> None:
        self.surf.fill(self.BG_COLOR)
        cs = self.cell

        for r in range(self.rows):
            for c in range(self.cols):
                x = self.ox + c * cs
                y = self.oy + r * cs
                rect = pygame.Rect(x + 1, y + 1, cs - 2, cs - 2)

                if self.revealed[r][c]:
                    v = self.grid[r][c]
                    if v == -1:
                        # Mine — show red if it was the clicked one
                        color = self.COLOR_EXPLODE if hit_mine_rc == (r, c) else self.COLOR_MINE
                        pygame.draw.rect(self.surf, color, rect, border_radius=3)
                        # Draw X
                        m = cs // 5
                        pygame.draw.line(self.surf, (200, 200, 200),
                                         (x + m, y + m), (x + cs - m, y + cs - m), 2)
                        pygame.draw.line(self.surf, (200, 200, 200),
                                         (x + cs - m, y + m), (x + m, y + cs - m), 2)
                    else:
                        pygame.draw.rect(self.surf, self.COLOR_OPEN, rect, border_radius=3)
                        if v > 0:
                            lbl = self.font.render(str(v), True, self.NUMBER_COLORS[v])
                            self.surf.blit(lbl, (
                                x + (cs - lbl.get_width())  // 2,
                                y + (cs - lbl.get_height()) // 2,
                            ))
                elif self.flagged[r][c]:
                    pygame.draw.rect(self.surf, self.COLOR_HIDDEN, rect, border_radius=3)
                    # Draw flag (F)
                    lbl = self.font.render("F", True, self.COLOR_FLAG)
                    self.surf.blit(lbl, (
                        x + (cs - lbl.get_width())  // 2,
                        y + (cs - lbl.get_height()) // 2,
                    ))
                else:
                    pygame.draw.rect(self.surf, self.COLOR_HIDDEN, rect, border_radius=3)

        # Mines remaining counter — top-left
        lbl = self.font.render(f"Mines: {self.flags_left}", True, self.TEXT_COLOR)
        self.surf.blit(lbl, (4, 4))

        # Result overlay
        if result is not None:
            msg   = "YOU WIN!" if result else "GAME OVER"
            color = (80, 220, 80) if result else (220, 60, 60)
            lbl   = self.font_big.render(msg, True, color)
            bx    = (self.w - lbl.get_width())  // 2
            by    = (self.h - lbl.get_height()) // 2
            pad   = 12
            bg    = pygame.Surface((lbl.get_width() + pad*2, lbl.get_height() + pad*2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            self.surf.blit(bg, (bx - pad, by - pad))
            self.surf.blit(lbl, (bx, by))
            sub = self.font.render("click to continue", True, (200, 200, 200))
            self.surf.blit(sub, ((self.w - sub.get_width()) // 2, by + lbl.get_height() + 6))


# ====================================================================== #


class Snake:
    """Classic Snake minigame rendered on a given pygame Surface.

    Controls: WASD or Arrow keys to change direction, ESC to quit.
    Eat food to grow. Hit a wall or yourself → lose.
    Eat enough food to win.

    difficulty=0 → hard  (faster, more food needed to win)
    difficulty=1 → easy  (slower, less food needed to win)

    Returns True (won) or False (lost/quit) from run().
    """

    _DIFFICULTY = {
        0: dict(cell=20, speed=10, win_score=20),  # hard: 10 moves/sec, need 20 food
        1: dict(cell=28, speed=6,  win_score=10),  # easy:  6 moves/sec, need 10 food
    }

    BG_COLOR      = (15,  20,  15)
    GRID_COLOR    = (25,  32,  25)
    SNAKE_HEAD    = (80,  220, 80)
    SNAKE_BODY    = (50,  170, 50)
    SNAKE_BORDER  = (30,  100, 30)
    FOOD_COLOR    = (220, 60,  60)
    FOOD_BORDER   = (160, 30,  30)
    TEXT_COLOR    = (220, 220, 220)

    def __init__(self, surf: pygame.Surface, clock: pygame.time.Clock, difficulty: int = 0) -> None:
        self.surf  = surf
        self.clock = clock
        self.w     = surf.get_width()
        self.h     = surf.get_height()

        cfg = self._DIFFICULTY.get(difficulty, self._DIFFICULTY[0])
        self.cell      = cfg["cell"]
        self.speed     = cfg["speed"]    # grid steps per second
        self.win_score = cfg["win_score"]

        self.cols = self.w // self.cell
        self.rows = self.h // self.cell
        self.ox   = (self.w - self.cols * self.cell) // 2
        self.oy   = (self.h - self.rows * self.cell) // 2

        fs = max(12, self.w // 20)
        self.font     = pygame.font.SysFont("monospace", fs, bold=True)
        self.font_big = pygame.font.SysFont("monospace", max(18, self.w // 12), bold=True)

    # ------------------------------------------------------------------ #

    def run(self) -> bool:
        # Snake starts in the middle, length 3, moving right
        mid_c = self.cols // 2
        mid_r = self.rows // 2
        snake  = [(mid_r, mid_c), (mid_r, mid_c - 1), (mid_r, mid_c - 2)]
        direc  = (0, 1)   # (dr, dc)
        next_d = direc    # buffered next direction

        score     = 0
        food      = self._spawn_food(snake)
        game_over = False
        won       = False

        step_ms  = int(1000 / self.speed)
        last_step = pygame.time.get_ticks()
        running  = True

        while running:
            self.clock.tick(60)
            now = pygame.time.get_ticks()

            # ── Events ────────────────────────────────────────────────── #
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    # Direction input — cannot reverse 180°
                    elif event.key in (pygame.K_UP,    pygame.K_w) and direc != (1, 0):
                        next_d = (-1, 0)
                    elif event.key in (pygame.K_DOWN,  pygame.K_s) and direc != (-1, 0):
                        next_d = (1, 0)
                    elif event.key in (pygame.K_LEFT,  pygame.K_a) and direc != (0, 1):
                        next_d = (0, -1)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d) and direc != (0, -1):
                        next_d = (0, 1)

                # Click to close result screen
                if event.type == pygame.MOUSEBUTTONDOWN and game_over:
                    running = False

            # ── Step snake ────────────────────────────────────────────── #
            if not game_over and now - last_step >= step_ms:
                last_step = now
                direc = next_d
                head_r, head_c = snake[0]
                new_r = head_r + direc[0]
                new_c = head_c + direc[1]

                # Wall collision
                if not (0 <= new_r < self.rows and 0 <= new_c < self.cols):
                    game_over = True
                # Self collision
                elif (new_r, new_c) in snake:
                    game_over = True
                else:
                    snake.insert(0, (new_r, new_c))
                    if (new_r, new_c) == food:
                        score += 1
                        if score >= self.win_score:
                            won = game_over = True
                        else:
                            food = self._spawn_food(snake)
                    else:
                        snake.pop()   # no growth → remove tail

            # ── Draw ──────────────────────────────────────────────────── #
            self._draw(snake, food, score, won if game_over else None)
            pygame.display.flip()

        return won

    # ------------------------------------------------------------------ #

    def _spawn_food(self, snake: list) -> tuple[int, int]:
        snake_set = set(snake)
        free = [
            (r, c)
            for r in range(self.rows) for c in range(self.cols)
            if (r, c) not in snake_set
        ]
        return random.choice(free) if free else (0, 0)

    def _cell_rect(self, r: int, c: int, inset: int = 1) -> pygame.Rect:
        x = self.ox + c * self.cell + inset
        y = self.oy + r * self.cell + inset
        s = self.cell - inset * 2
        return pygame.Rect(x, y, s, s)

    def _draw(self, snake: list, food: tuple, score: int, result) -> None:
        self.surf.fill(self.BG_COLOR)

        # Subtle grid
        for r in range(self.rows):
            for c in range(self.cols):
                pygame.draw.rect(self.surf, self.GRID_COLOR, self._cell_rect(r, c, 0), 1)

        # Food
        fr, fc = food
        pygame.draw.rect(self.surf, self.FOOD_COLOR,   self._cell_rect(fr, fc, 2), border_radius=4)
        pygame.draw.rect(self.surf, self.FOOD_BORDER,  self._cell_rect(fr, fc, 2), 2, border_radius=4)

        # Snake body
        for i, (r, c) in enumerate(snake):
            color  = self.SNAKE_HEAD if i == 0 else self.SNAKE_BODY
            pygame.draw.rect(self.surf, color,          self._cell_rect(r, c, 1), border_radius=4)
            pygame.draw.rect(self.surf, self.SNAKE_BORDER, self._cell_rect(r, c, 1), 1, border_radius=4)

        # Score & win target
        lbl = self.font.render(f"Score: {score} / {self.win_score}", True, self.TEXT_COLOR)
        self.surf.blit(lbl, (4, 4))

        # Result overlay
        if result is not None:
            msg   = "YOU WIN!" if result else "GAME OVER"
            color = (80, 220, 80) if result else (220, 60, 60)
            lbl   = self.font_big.render(msg, True, color)
            bx    = (self.w - lbl.get_width())  // 2
            by    = (self.h - lbl.get_height()) // 2
            pad   = 12
            bg    = pygame.Surface((lbl.get_width() + pad*2, lbl.get_height() + pad*2), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 180))
            self.surf.blit(bg, (bx - pad, by - pad))
            self.surf.blit(lbl, (bx, by))
            sub = self.font.render("click to continue", True, (200, 200, 200))
            self.surf.blit(sub, ((self.w - sub.get_width()) // 2, by + lbl.get_height() + 6))


# ====================================================================== #


class RandomWheel:
    """Banh xe quay may rui. Click chuot trai de dung.
    Ti le: blank=85%, copper=10%, gold=5%.
    run() tra ve "blank", "copper" hoac "gold".
    """
    SEGMENTS = [
        ("blank",  (80,  80,  80),  85),
        ("copper", (184, 115,  51), 10),
        ("gold",   (212, 175,  55),  5),
    ]
    BG_COLOR   = (20, 20, 25)
    TEXT_COLOR = (255, 255, 255)

    def __init__(self, surf: pygame.Surface, clock: pygame.time.Clock) -> None:
        self.surf  = surf
        self.clock = clock
        self.w     = surf.get_width()
        self.h     = surf.get_height()
        fs = max(16, self.w // 20)
        self.font     = pygame.font.SysFont("monospace", fs, bold=True)
        self.font_big = pygame.font.SysFont("monospace", max(20, self.w // 14), bold=True)
        total = sum(s[2] for s in self.SEGMENTS)
        angle = 0.0
        self.seg_angles = []
        for label, color, weight in self.SEGMENTS:
            span = 360.0 * weight / total
            self.seg_angles.append((angle, angle + span, color, label))
            angle += span

    def run(self) -> str:
        cx, cy = self.w // 2, self.h // 2
        radius = int(min(self.w, self.h) * 0.38)
        speed  = random.uniform(300.0, 600.0)  # degrees/s
        decel  = random.uniform(60.0, 120.0)   # degrees/s2
        angle  = random.uniform(0, 360)
        stopped = False
        result  = "blank"

        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    stopped = True

            if not stopped:
                angle = (angle + speed * dt) % 360
                speed = max(0.0, speed - decel * dt)
                if speed <= 0:
                    stopped = True

            self.surf.fill(self.BG_COLOR)

            # Draw segments as filled polygons
            for start_a, end_a, color, label in self.seg_angles:
                da = start_a + angle
                db = end_a   + angle
                steps = max(4, int(abs(db - da) / 3))
                pts = [(cx, cy)]
                for i in range(steps + 1):
                    a = math.radians(da + (db - da) * i / steps)
                    pts.append((cx + radius * math.cos(a), cy - radius * math.sin(a)))
                pygame.draw.polygon(self.surf, color, pts)
                pygame.draw.polygon(self.surf, (0, 0, 0), pts, 1)

                # Label at segment center
                mid_a = math.radians((da + db) / 2)
                tx = cx + int(radius * 0.62 * math.cos(mid_a))
                ty = cy - int(radius * 0.62 * math.sin(mid_a))
                lbl = self.font.render(label.upper(), True, self.TEXT_COLOR)
                self.surf.blit(lbl, (tx - lbl.get_width() // 2, ty - lbl.get_height() // 2))

            pygame.draw.circle(self.surf, (40, 40, 40), (cx, cy), 16)

            # Pointer at top (0 degrees)
            pygame.draw.polygon(self.surf, (255, 60, 60), [
                (cx, cy - radius - 6),
                (cx - 10, cy - radius + 14),
                (cx + 10, cy - radius + 14),
            ])

            if not stopped or speed > 0:
                hint = self.font.render("Click to stop", True, (200, 200, 200))
                self.surf.blit(hint, (cx - hint.get_width() // 2, self.h - hint.get_height() - 12))

            pygame.display.flip()

            if stopped and speed <= 0:
                # Needle at top = angle 90 in standard math coords
                needle_a = (90.0 - angle) % 360
                for start_a, end_a, _, label in self.seg_angles:
                    s, e = start_a % 360, end_a % 360
                    if s <= e:
                        if s <= needle_a < e:
                            result = label; break
                    else:
                        if needle_a >= s or needle_a < e:
                            result = label; break

                res_colors = {"blank": (120,120,120), "copper": (184,115,51), "gold": (212,175,55)}
                res_lbl = self.font_big.render(result.upper(), True, res_colors.get(result, self.TEXT_COLOR))
                self.surf.blit(res_lbl, (cx - res_lbl.get_width() // 2, cy - res_lbl.get_height() // 2))
                pygame.display.flip()
                pygame.time.wait(1200)
                break

        return result

class TheWheelOfTruth:
    """Vòng xoay liên tục. Click chuột trái để dừng.
    Mũi tên cố định ở vị trí 1 giờ (30° từ đỉnh, theo chiều kim đồng hồ).
    run() trả về "blank", "copper" hoặc "gold".
    Sau khi dừng hiện dialogue box kết quả, click tiếp để đóng.
    Tỉ lệ: blank=85%, copper=10%, gold=5%.
    """

    SEGMENTS = [
        ("blank",  (180,  30,  30),  85),   # đỏ
        ("copper", (184, 115,  51), 10),    # đồng thau
        ("gold",   (212, 175,  55),  5),    # vàng
    ]
    # Mũi tên tại 1 giờ = 60° trong tọa độ toán học (0°=phải, 90°=trên)
    NEEDLE_ANGLE = 60.0

    BG_COLOR   = (15, 15, 20)
    TEXT_COLOR = (240, 230, 210)
    RESULT_COLORS = {
        "blank":  (160, 155, 145),
        "copper": (200, 130,  60),
        "gold":   (230, 190,  50),
    }
    RESULT_LABELS = {
        "blank":  "Nothing...",
        "copper": "Copper!",
        "gold":   "Gold!",
    }

    # offset để chỉnh hướng arrow.png nếu ảnh không mặc định hướng lên
    ARROW_ROTATION_OFFSET = 0

    def __init__(self, surf: pygame.Surface, clock: pygame.time.Clock,
                 wheel_path: str = None, arrow_path: str = None) -> None:
        self.surf  = surf
        self.clock = clock
        self.w     = surf.get_width()
        self.h     = surf.get_height()
        fs = max(14, self.w // 22)
        self.font     = pygame.font.SysFont("monospace", fs, bold=True)
        self.font_big = pygame.font.SysFont("monospace", max(20, self.w // 13), bold=True)

        total = sum(s[2] for s in self.SEGMENTS)
        a = 0.0
        self.seg_angles: list[tuple[float, float, tuple, str]] = []
        for label, color, weight in self.SEGMENTS:
            span = 360.0 * weight / total
            self.seg_angles.append((a, a + span, color, label))
            a += span

        # Load ảnh tùy chọn
        diameter = int(min(self.w, self.h) * 0.76)
        self.wheel_img = None
        self.arrow_img = None
        if wheel_path and os.path.isfile(wheel_path):
            img = pygame.image.load(wheel_path).convert_alpha()
            self.wheel_img = pygame.transform.smoothscale(img, (diameter, diameter))
        if arrow_path and os.path.isfile(arrow_path):
            self.arrow_img = pygame.image.load(arrow_path).convert_alpha()

    # ------------------------------------------------------------------ #

    def _draw_wheel(self, cx: int, cy: int, radius: int, angle: float) -> None:
        """Vẽ vòng xoay. Nếu có wheel.png thì dùng ảnh, fallback vẽ code."""
        if self.wheel_img is not None:
            rotated = pygame.transform.rotozoom(self.wheel_img, angle, 1.0)
            self.surf.blit(rotated, (cx - rotated.get_width() // 2,
                                     cy - rotated.get_height() // 2))
            pygame.draw.circle(self.surf, (40, 35, 30), (cx, cy), 14)
            pygame.draw.circle(self.surf, (200, 190, 170), (cx, cy), 14, 2)
            return

        for start_a, end_a, color, label in self.seg_angles:
            da = start_a + angle
            db = end_a   + angle
            steps = max(4, int(abs(db - da) / 2))
            pts = [(cx, cy)]
            for i in range(steps + 1):
                rad = math.radians(da + (db - da) * i / steps)
                pts.append((cx + radius * math.cos(rad),
                            cy - radius * math.sin(rad)))
            pygame.draw.polygon(self.surf, color, pts)
            pygame.draw.polygon(self.surf, (0, 0, 0), pts, 1)

            # Chỉ blank mới có chữ "FAILED" màu trắng
            if label == "blank":
                mid_rad = math.radians((da + db) / 2)
                tx = cx + int(radius * 0.60 * math.cos(mid_rad))
                ty = cy - int(radius * 0.60 * math.sin(mid_rad))
                lbl = self.font.render("FAILED", True, (255, 255, 255))
                self.surf.blit(lbl, (tx - lbl.get_width() // 2,
                                     ty - lbl.get_height() // 2))

        # Vòng viền ngoài
        pygame.draw.circle(self.surf, (200, 190, 170), (cx, cy), radius, 3)
        # Tâm
        pygame.draw.circle(self.surf, (40, 35, 30), (cx, cy), 14)
        pygame.draw.circle(self.surf, (200, 190, 170), (cx, cy), 14, 2)

    def _draw_needle(self, cx: int, cy: int, radius: int) -> None:
        """Vẽ mũi tên tại 1 giờ. Nếu có arrow.png thì dùng ảnh, fallback vẽ code.
        arrow.png nên hướng lên (12 giờ). Chỉnh ARROW_ROTATION_OFFSET nếu cần."""
        if self.arrow_img is not None:
            # Mũi tên cố định ở NEEDLE_ANGLE, xoay từ hướng mặc định (lên=90°) sang NEEDLE_ANGLE
            # pygame.transform.rotate dương = ngược chiều kim đồng hồ (trên màn hình)
            # Từ 90° (lên) → NEEDLE_ANGLE: xoay (90 - NEEDLE_ANGLE) theo chiều CW trên màn hình
            #   = rotate(-(90 - NEEDLE_ANGLE)) trong pygame
            rotation = -(90 - self.NEEDLE_ANGLE) + self.ARROW_ROTATION_OFFSET
            rotated = pygame.transform.rotozoom(self.arrow_img, rotation, 1.0)
            nad = math.radians(self.NEEDLE_ANGLE)
            # Đặt gốc mũi tên tại rìa vòng
            px = cx + int((radius + rotated.get_height() // 2) * math.cos(nad))
            py = cy - int((radius + rotated.get_height() // 2) * math.sin(nad))
            self.surf.blit(rotated, (px - rotated.get_width() // 2,
                                     py - rotated.get_height() // 2))
            return

        nad = math.radians(self.NEEDLE_ANGLE)
        # Điểm đầu mũi tên (ngoài vòng)
        tip_x = cx + int((radius + 22) * math.cos(nad))
        tip_y = cy - int((radius + 22) * math.sin(nad))
        # Gốc mũi tên (trên vòng)
        base_x = cx + int((radius - 8) * math.cos(nad))
        base_y = cy - int((radius - 8) * math.sin(nad))
        # Hai cánh mũi tên (vuông góc với hướng)
        perp = math.radians(self.NEEDLE_ANGLE + 90)
        wing = 9
        w1x = base_x + int(wing * math.cos(perp))
        w1y = base_y - int(wing * math.sin(perp))
        w2x = base_x - int(wing * math.cos(perp))
        w2y = base_y + int(wing * math.sin(perp))
        pts = [(tip_x, tip_y), (w1x, w1y), (w2x, w2y)]
        pygame.draw.polygon(self.surf, (0, 0, 0), pts, 4)      # viền đen
        pygame.draw.polygon(self.surf, (255, 255, 255), pts)   # fill trắng
        pygame.draw.polygon(self.surf, (0, 0, 0), pts, 2)      # viền đen mỏng trên cùng

    def _get_result(self, angle: float) -> str:
        """Xác định ô mũi tên đang chỉ vào."""
        needle_on_wheel = (self.NEEDLE_ANGLE - angle) % 360
        for start_a, end_a, _, label in self.seg_angles:
            s = start_a % 360
            e = end_a   % 360
            if s < e:
                if s <= needle_on_wheel < e:
                    return label
            else:  # wrap around 360
                if needle_on_wheel >= s or needle_on_wheel < e:
                    return label
        return self.seg_angles[-1][3]

    def _show_result_dialog(self, cx: int, cy: int, result: str) -> None:
        """Hiện dialogue box kết quả, chờ click để đóng."""
        color  = self.RESULT_COLORS.get(result, self.TEXT_COLOR)
        label  = self.RESULT_LABELS.get(result, result.upper())
        box_w, box_h = int(self.w * 0.55), int(self.h * 0.28)
        bx = cx - box_w // 2
        by = cy - box_h // 2

        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.surf.blit(overlay, (0, 0))

        pygame.draw.rect(self.surf, (30, 28, 24),
                         (bx, by, box_w, box_h), border_radius=12)
        pygame.draw.rect(self.surf, color,
                         (bx, by, box_w, box_h), width=3, border_radius=12)

        result_lbl = self.font_big.render(label, True, color)
        hint_lbl   = self.font.render("Click to continue", True, (160, 150, 130))
        self.surf.blit(result_lbl, (cx - result_lbl.get_width() // 2,
                                    by + box_h // 2 - result_lbl.get_height()))
        self.surf.blit(hint_lbl,   (cx - hint_lbl.get_width() // 2,
                                    by + box_h // 2 + 8))
        pygame.display.flip()

        waiting = True
        while waiting:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    waiting = False

    # ------------------------------------------------------------------ #

    def run(self) -> str:
        cx = self.w // 2
        cy = self.h // 2
        radius = int(min(self.w, self.h) * 0.38)
        speed  = random.uniform(180.0, 360.0)  # degrees/s (xoay liên tục)
        angle  = random.uniform(0, 360)
        decel  = random.uniform(120.0, 200.0)  # degrees/s²
        stopping = False

        while True:
            dt = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if not stopping:
                        stopping = True

            if stopping:
                speed = max(0.0, speed - decel * dt)
            else:
                # Xoay liên tục với tốc độ ổn định
                speed = max(speed, random.uniform(180.0, 280.0)) if speed < 100 else speed

            angle = (angle + speed * dt) % 360

            # Vẽ
            self.surf.fill(self.BG_COLOR)
            self._draw_wheel(cx, cy, radius, angle)
            self._draw_needle(cx, cy, radius)

            if not stopping:
                hint = self.font.render("Click to stop", True, (180, 170, 150))
                self.surf.blit(hint, (cx - hint.get_width() // 2,
                                      self.h - hint.get_height() - 16))

            pygame.display.flip()

            if stopping and speed <= 0:
                result = self._get_result(angle)
                self._show_result_dialog(cx, cy, result)
                return result


# ====================================================================== #

if __name__ == "__main__":
    import sys
    difficulty = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    pygame.init()
    screen = pygame.display.set_mode((480, 480), pygame.RESIZABLE)
    pygame.display.set_caption("Fighter – test")
    clock = pygame.time.Clock()
    result = Fighter(screen, clock, difficulty).run()
    print("Result:", "WIN" if result else "LOSE")
    pygame.quit()