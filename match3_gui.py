import json
import jsonschema
import math
import os
import pygame
import pygame_widgets as pygamew
from sys import exit
from pygame import gfxdraw
from enum import Enum, auto
from match3_board import Match3Board


class GameState(Enum):
    MAINMENU = auto()
    CHOOSESIZE = auto()
    RUNNING = auto()
    PAUSED = auto()
    ENDED = auto()
    ENTERHIGHSCORE = auto()
    HIGHSCORES = auto()
    PREFERENCES = auto()
    ABOUT = auto()


class MouseState(Enum):
    WAITING = auto()
    PRESSED = auto()
    MOVING = auto()


class Match3GUI:
    colors = (
        (  0,  0,128),  # 000080 Dark Blue
        (128,  0,  0),  # 800000 Dark Red
        (  0,128,  0),  # 008000 Green
        (255,255,  0),  # FFFF00 Yellow
        (255,255,255),  # FFFFFF White
        (  0,  0,  0),  # 000000 Black
        ( 84, 84, 84),  # 545454 Grey
        (192,  0,192),  # C000C0 Purple-Magenta
        (172,172,255),  # ACACFF Light Blue
        (255, 64, 64),  # FF4040 Light Red
        (192,255,128),  # C0FF80 Pale Green-Yellow
        ( 48,192,192),  # 30C0C0 Greyed Cyan
    )
    border_color = (48, 48, 48)
    background_color = {
        "screen": (0, 0, 0),
        "game": (24, 24, 24),
        "board": (0, 0, 0),
        "sidebar": (48, 48, 48),
    }
    hint_color = (255, 255, 255)
    widget_text_color = (255, 255, 255)
    starting_width = 640
    starting_height = 480
    game_ratio = starting_width / starting_height
    board_scale = 9 / 10
    circle_scale = 18 / 20
    plus_score_ani_time = 500
    hint_ani_time = 500
    swap_ani_time = 200
    shift_down_ani_time = 200
    clear_ani_time = 200
    plus_score_blink_ani_time = 100
    ani_fps = 60
    main_loop_refresh_rate = 30
    flags = pygame.RESIZABLE | pygame.HWSURFACE | pygame.NOFRAME
    min_font_size = 20
    min_char_width = 13.8
    min_char_height = 13.8
    min_char_sep_height = min_char_height / 2
    time_init = 60000
    board_sizes = list(range(5, 14))
    high_score_name_max_len = 20
    high_scores_filename = "high_scores.json"
    high_scores_schema = '''
    {
        "type": "object",
        "additionalProperties": {
            "type": "array",
            "items": {
                "type": "array",
                "items": [
                    {"type": "string", "maxLength": 20},
                    {"type": "integer", "minimum": 1}
                ],
                "additionalProperties": false
            },
            "maxItems": 5
        },
        "propertyNames": {"enum": []}
    }
    '''
    high_scores_schema = json.loads(high_scores_schema)
    high_scores_schema["propertyNames"]["enum"] = [f"{n}x{n}" for n in board_sizes]
    preferences_filename = "preferences.json"
    preferences_schema = '''
    {
        "type": "object",
        "properties": {
            "background_music": {
                "type": "boolean"
            },
            "sound_effects": {
                "type": "boolean"
            }
        },
        "additionalProperties": false
    }
    '''
    preferences_schema = json.loads(preferences_schema)
    media_dir = "media"
    audio_dir = f"{media_dir}/audio"
    sounds_dir = f"{audio_dir}/sounds"
    music_dir = f"{audio_dir}/music"
    background_music_filename = f"{music_dir}/background_music.ogg"

    def __init__(self) -> None:
        self.board = None
        self.screen_surf = None
        self.game_surf = None
        self.board_surf = None
        self.sidebar_surf = None
        self.clock = None
        self.circle_radius = 0
        self.mouse_state = MouseState.WAITING
        self.board_pos_src = None
        self.score = 0
        self.time_left = self.time_init
        self.time_start = 0
        self.time_score = 0
        self.time_left_sec = int(self.time_left / 1000)
        self.active_widgets = {}
        self.hint = False
        self.hint_cut_score = False
        self.plus_score_ani_time_start = 0
        self.curr_plus_score_ani_time = self.plus_score_ani_time + 1
        self.curr_score = 0
        self.curr_time_score = 0
        self.game_state = GameState.MAINMENU
        self.font_size = self.min_font_size
        self.char_width = self.min_char_width
        self.char_height = self.min_char_height
        self.char_sep_height = self.min_char_sep_height
        self.font = None
        self.pause = False
        self.pause_time = 0
        self.time_paused = 0
        self.game_ended = False
        self.prev_state = None
        self.high_scores_state = 5
        self.high_scores = {}
        self.preferences = {}
        self.sounds = {}
        self.life_stage=0#So Sinh,Thieu Nhi,Thieu Nien,Thanh Nien,Truong Thanh
        self.hobby_state=0#0=Trong, 1=Thu vui, 2=Dam me
        self.chance_state=0#0=Trong, 1=Co hoi
        self.time_count=0#so block time trong stage hien tai
        self.hobby_count=0
        self.chance_count=0      
        self.philosopher_turns=0#philo fate
        self.sage_turns=0 #sage fate
        self.prisoner_turns=0#prisoner fate
        self.hobby_icon_s0=None#icon chung state0
        #[type][state]
        self.hobby_icons=[[None,None,None],[None,None,None],[None,None,None]]
        # [type][0]=generic(hobby_boost.png), [type][1]=state1, [type][2]=state2
        self.hobby_boost_icons=[[None,None,None,None],[None,None,None,None],[None,None,None,None]]
        self.hobby_type=None
        self.chance_icon_s0=None
        self.chance_icons=[None, None, None]#(love/religious/mastermind)
        self.chance_boost_icon=None
        self.chance_boost_icons=[None, None, None]  # [type] = chance_{love/religious/mastermind}_boost.png
        self.chance_type=None#randumb
        self.time_icon=[None, None]
        self.fate_icon=None
        self.dialogue_box_img=None
        self.button_img=None         # generic fallback
        self.menu_button_img=None    # menu_button.png — nút ngoài menu
        self.board_button_img=None   # board_button.png — nút trong ván
        self.stat_box_img=None       # stat_box.png — nền chỉ số hobby/chance
        self.time_frame_img=None     # time_frame.png — khung hiển thị stage + hourglass
        self.hourglass_imgs=[]       # hourglass/0.png … 12.png
        self.hint_img=None           # hint.png — icon HINT
        self.pause_img=None          # pause.png — icon PAUSE
        self.block_frame_img=None    # frame.png — viền sau icon hobby/chance
        self.board_bg=None           # backgroundA.png — sidebar
        self.time_imgs=[None]*13     # Time 0.png … Time 12.png (ứng với time_count)
        self.time_plate_img=None     # time_plate.png — khung chứa icon time
        self.board_bg_scaled=None
        self.board_area_bg=None      # backgroundB.png — toàn bộ vùng board
        self.board_area_bg_scaled=None
        self.failedbefore=False
        self.random_wheel_result=None  # "copper"(20%) / "gold"(5%) / None(75%)


    ##################################################
    # Animate functions
    ##################################################

    def animate_swap(self, board_point1: tuple[int, int], board_point2: tuple[int, int]) -> None:
        self.play_sound("swap")

        board_points = (board_point1, board_point2)
        win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

        target_dist = (
            [win_points[1][0] - win_points[0][0], win_points[1][1] - win_points[0][1]],  # [dst_p1_x - src_p1_x, dst_p1_y - src_p1_y]
            [win_points[0][0] - win_points[1][0], win_points[0][1] - win_points[1][1]],  # [dst_p2_x - src_p2_x, dst_p2_y - src_p2_y]
        )
        curr_pos = [list(win_points[0]), list(win_points[1])]

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while curr_pos[0] != win_points[1] or curr_pos[1] != win_points[0]:  # curr_p1 != dst_p1 or curr_p2 != dst_p2
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))
                target_dist = (
                    [win_points[1][0] - win_points[0][0], win_points[1][1] - win_points[0][1]],  # [dst_p1_x - src_p1_x, dst_p1_y - src_p1_y]
                    [win_points[0][0] - win_points[1][0], win_points[0][1] - win_points[1][1]],  # [dst_p2_x - src_p2_x, dst_p2_y - src_p2_y]
                )

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            for p_i in reversed(range(2)):
                # Calculate the new position
                src_pos = win_points[p_i]
                dst_pos = win_points[int(not p_i)]
                curr_dist = (target_dist[p_i][0] * curr_ani_time / self.swap_ani_time, target_dist[p_i][1] * curr_ani_time / self.swap_ani_time)
                curr_pos[p_i] = [src_pos[0] + curr_dist[0], src_pos[1] + curr_dist[1]]
                curr_pos[p_i] = [int(curr_pos[p_i][0]), int(curr_pos[p_i][1])]
                for i in range(2):
                    dir = dst_pos[i] - src_pos[i]
                    if (dir < 0 and curr_pos[p_i][i] < dst_pos[i]) or (dir > 0 and curr_pos[p_i][i] > dst_pos[i]):
                        curr_pos[p_i][i] = dst_pos[i]
                # Draw the moving circles
                color_index = self.board.board[board_points[p_i][1]][board_points[p_i][0]]
                if color_index < 0:
                    continue
                self.draw_circle(curr_pos[p_i][0], curr_pos[p_i][1], self.colors[color_index])

            pygame.display.flip()

    def animate_clear(self, board_points: list[tuple[int, int]], no_more_moves: bool = False) -> None:
        self.play_sound("match")

        win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

        target_transparency = 0
        target_size = 0
        curr_transparency = 255
        curr_size = self.circle_radius

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        clear_ani_time = self.clear_ani_time
        if no_more_moves:
            clear_ani_time *= 5

        while curr_transparency != target_transparency or curr_size != target_size:
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points = [self.board_pos_to_win_pos(*p) for p in board_points]

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            # Calculate the new size and the new transparency
            curr_transparency = int(target_transparency * (1 - curr_ani_time / clear_ani_time))
            if curr_transparency > target_transparency:
                curr_transparency = target_transparency
            curr_size = int(self.circle_radius * (1 - curr_ani_time / clear_ani_time))
            if curr_size < target_size:
                curr_size = target_size

            # Draw the moving circles
            for i, p in enumerate(board_points):
                color_index = self.board.board[p[1]][p[0]]
                if color_index < 0:
                    continue
                self.draw_circle(win_points[i][0], win_points[i][1], self.colors[color_index], curr_size)

            if no_more_moves:
                texts = ("NO MORE MOVES", "REGENERATING BOARD")
                width = (max([len(text) for text in texts]) + 4) * self.char_width
                height = (math.ceil(self.char_height) + math.ceil(self.char_sep_height)) * 2
                x = (self.board_surf.get_width() - width) / 2 + self.board_surf.get_abs_offset()[0]
                y = (self.board_surf.get_height() - height * 2) / 2 + self.board_surf.get_abs_offset()[1]
                for text in texts:
                    button = pygamew.Button(
                        self.screen_surf, x, y, width, height,
                        text=text,
                        textColour=(32, 255, 32),
                        font=self.font,
                        colour=self.background_color["game"],
                        hoverColour=self.background_color["game"],
                        pressedColour=self.background_color["game"]
                    )
                    button.draw()
                    y += height

            pygame.display.flip()

    def animate_shift_down(self, shifted_bp: list[tuple[int, int]], num_vertical_points: int) -> None:
        board_points_dst = shifted_bp
        board_points_src = [(x, y - 1) for (x, y) in board_points_dst]
        win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
        win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]
        color_indices = [self.board.board[y][x] for (x, y) in board_points_dst]

        curr_pos = [[x, y] for (x, y) in win_points_src]

        ani_time = self.shift_down_ani_time / min((num_vertical_points, 2))
        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while any([curr_pos[i] != win_points_dst[i] for i in range(len(curr_pos))]):
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points_dst = [list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
                win_points_src = [list(self.board_pos_to_win_pos(*p)) for p in board_points_src]

            self.draw_board(no_draw_pts=board_points_src + board_points_dst)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            for p_i in range(len(curr_pos)):
                # Calculate the new position
                src_pos = win_points_src[p_i]
                dst_pos = win_points_dst[p_i]
                target_dist = ((dst_pos[0] - src_pos[0]), (dst_pos[1] - src_pos[1]))
                curr_dist = (target_dist[0] * curr_ani_time / ani_time, target_dist[1] * curr_ani_time / ani_time)
                curr_pos[p_i] = [src_pos[0] + curr_dist[0], src_pos[1] + curr_dist[1]]
                curr_pos[p_i] = [int(curr_pos[p_i][0]), int(curr_pos[p_i][1])]
                for i in range(2):
                    dir = dst_pos[i] - src_pos[i]
                    if (dir < 0 and curr_pos[p_i][i] < dst_pos[i]) or (dir > 0 and curr_pos[p_i][i] > dst_pos[i]):
                        curr_pos[p_i][i] = dst_pos[i]
                # Draw the moving circles
                color_index = color_indices[p_i]
                if color_index < 0:
                    continue
                self.draw_circle(curr_pos[p_i][0], curr_pos[p_i][1], self.colors[color_index])

            pygame.display.flip()

    def animate_hint(self, board_point1: tuple[int, int], board_point2: tuple[int, int]) -> None:
        self.play_sound("hint")

        board_points = (board_point1, board_point2)
        win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

        curr_ani_time = 0
        ani_time_start = pygame.time.get_ticks()

        while curr_ani_time <= self.hint_ani_time:
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points = (list(self.board_pos_to_win_pos(*board_points[0])), list(self.board_pos_to_win_pos(*board_points[1])))

            self.draw_board(no_draw_pts=board_points)

            curr_ani_time = pygame.time.get_ticks() - ani_time_start

            for p_i in range(2):
                color_index = self.board.board[board_points[p_i][1]][board_points[p_i][0]]
                if color_index < 0:
                    continue
                self.draw_circle(*win_points[p_i], self.hint_color, self.circle_radius / self.circle_scale)
                self.draw_circle(*win_points[p_i], self.colors[color_index])

            pygame.display.flip()

        self.update_board()

    def animate_plus_score_prev(self) -> None:
        self.curr_plus_score_ani_time = self.plus_score_ani_time + 1
        self.update_sidebar()
        pygame.time.wait(self.plus_score_blink_ani_time)

    def animate_plus_score_post(self) -> None:
        self.curr_plus_score_ani_time = 0
        self.plus_score_ani_time_start = pygame.time.get_ticks()
        self.update_sidebar()

    ##################################################
    # Draw functions
    ##################################################

    def draw_circle(self, x, y, color, radius = None) -> None:
        if radius is None:
            radius = self.circle_radius
        if color != (0, 0, 0):
            gfxdraw.aacircle(self.board_surf, x, y, int(radius * self.circle_scale), color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius * self.circle_scale), color)
        else:
            gfxdraw.aacircle(self.board_surf, x, y, int(radius*self.circle_scale), self.border_color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius*self.circle_scale), self.border_color)
            gfxdraw.aacircle(self.board_surf, x, y, int(radius*(1-(1-self.circle_scale)*2)), color)
            gfxdraw.filled_circle(self.board_surf, x, y, int(radius*(1-(1-self.circle_scale)*2)), color)

    def draw_rounded_square(self, x: int, y: int, color: tuple, size: float = None) -> None:
        """Vẽ block base (state 0) cho hobby và chance"""
        #dùng lại circle_radius của code mẫu để canh size
        if size is None:
            size = self.circle_radius
        diameter = int(size * self.circle_scale * 2)

        if diameter < 2:
            return
        
        half = diameter // 2
        border_radius = max(3, diameter // 4)
        
        rect = pygame.Rect(x - half, y - half, diameter, diameter)
        pygame.draw.rect(self.board_surf, color, rect, border_radius=border_radius)
        pygame.draw.rect(self.board_surf, (31, 39, 72), rect, width=2, border_radius=border_radius)

    
    def draw_parallelogram(self, x: int, y: int, color: tuple, size: float = None) -> None:
        if size is None:
            size=self.circle_radius
        s=size*self.circle_scale
        if s<2:
            return
        hw=max(2, int(s*0.28))
        hh=max(2, int(s*0.72))
        sk=max(1, int(s*0.22))
        pts=[
            (x-hw+sk, y-hh),
            (x+hw+sk, y-hh),
            (x+hw-sk, y+hh),
            (x-hw-sk, y+hh),
        ]
        pygame.draw.polygon(self.board_surf, color, pts)
        highlight=tuple(min(255, c+60) for c in color)
        pygame.draw.polygon(self.board_surf, highlight, pts, 2)

    def draw_tile(self, x: int, y: int, color_index: int, size: float = None) -> None:
        """Cập nhật code xíu để cho icon vào"""
        B = Match3Board
        if size is None:
            size = self.circle_radius
        diameter = int(size * self.circle_scale * 2)
        #Load icon cho các block chance, hobby từ state 1 trở lên
        #và block time, fate.
        icon=None
        if color_index==B.HOBBY:
            if self.hobby_state>0 and self.hobby_type is not None:
                icon=self.hobby_icons[self.hobby_type][self.hobby_state-1]
                if icon is None and self.hobby_state>=2:
                    icon=self.hobby_icons[self.hobby_type][self.hobby_state-2]
                if icon is None:
                    icon=self.hobby_icons[self.hobby_type][0]
            if icon is None:
                icon=self.hobby_icon_s0  # fallback về icon state 0 chung
        elif color_index==B.CHANCE:
            if self.chance_state>0 and self.chance_type is not None:
                icon=self.chance_icons[self.chance_type]
            if icon is None:
                icon=self.chance_icon_s0  # fallback về icon state 0 chung
        elif color_index==B.BOOST_HOBBY:
            if self.hobby_type is not None and self.hobby_state>0:
                # [type][1]=state1, [type][2]=state2/3
                state_idx=min(self.hobby_state, 3)
                icon=self.hobby_boost_icons[self.hobby_type][state_idx]
            if icon is None:
                # state=0 hoặc chưa có icon riêng → dùng generic [0][0]=hobby_boost.png
                icon=self.hobby_boost_icons[0][0]
        elif color_index==B.BOOST_CHANCE:
            if self.chance_type is not None:
                icon=self.chance_boost_icons[self.chance_type] or self.chance_boost_icon
            else:
                icon=self.chance_boost_icon
        elif color_index==B.TIME:
            icon=self.time_icon[0]
        elif color_index==B.BOOST_TIME:
            icon=self.time_icon[1]
        elif color_index==B.FATE:
            icon=self.fate_icon

        if icon is not None and diameter>0:
            full_d=int(self.circle_radius*self.circle_scale*2)
            if diameter==full_d:
                key=(id(icon), diameter)
                if key not in self._icon_cache:
                    self._icon_cache[key]=pygame.transform.smoothscale(icon, (diameter, diameter))
                scaled=self._icon_cache[key]
            else:
                scaled=pygame.transform.scale(icon, (diameter, diameter))
            self.board_surf.blit(scaled, (x-diameter//2, y-diameter//2))
            return

        #hiện tại chưa có ảnh thì vẽ, sẽ xóa sau
        elif color_index == B.HOBBY:
            self.draw_rounded_square(x, y, self.hobby_block_color, size)
        elif color_index == B.CHANCE:
            self.draw_rounded_square(x, y, self.chance_block_color, size)
        elif color_index == B.BOOST_TIME:
            self.draw_circle(x, y, self.boost_time_color, size)
        elif color_index == B.BOOST_HOBBY:
            self.draw_rounded_square(x, y, self.boost_hobby_color, size)
        elif color_index == B.BOOST_CHANCE:
            self.draw_rounded_square(x, y, self.boost_chance_color, size)
        elif color_index == B.FATE:
            self.draw_parallelogram(x, y, self.fate_block_color, size)
        
        

    def _wrap_text(self, text: str, font, max_w: int) -> list[str]:
        """Tách text thành các dòng vừa với max_w pixel."""
        words=text.split()
        lines=[]
        current=""
        for word in words:
            test=current+" "+word if current else word
            if font.size(test)[0]<=max_w:
                current=test
            else:
                if current:
                    lines.append(current)
                current=word
        if current:
            lines.append(current)
        return lines if lines else [""]

    def draw_dialog(self, content, icons=None) -> None:
        gw=self.game_surf.get_width()
        gh=self.game_surf.get_height()
        box_diag=math.sqrt(gw**2+gh**2)*0.52
        box_w=int(box_diag*16/math.sqrt(16**2+9**2))
        box_h=int(box_diag*9/math.sqrt(16**2+9**2))
        # Không vượt quá 90% màn hình
        box_w=min(box_w, int(gw*0.9))
        box_h=min(box_h, int(gh*0.9))
        cx=gw//2
        cy=gh//2
        rect=pygame.Rect(cx-box_w//2, cy-box_h//2, box_w, box_h)
        pad=int(box_w*0.13)
        pad_v=int(box_h*0.18)
        max_text_w=box_w-pad*2
        if self.dialogue_box_img is not None:
            scaled=pygame.transform.smoothscale(self.dialogue_box_img, (box_w, box_h))
            self.game_surf.blit(scaled, rect.topleft)
        else:
            pygame.draw.rect(self.game_surf, (235, 228, 220), rect, border_radius=10)
            pygame.draw.rect(self.game_surf, (180, 168, 155), rect, width=2, border_radius=10)

        # Clip vùng text — mọi thứ vẽ ngoài content_rect sẽ bị cắt tự động
        content_rect=pygame.Rect(rect.left+pad, rect.top+pad_v,
                                  box_w-pad*2, box_h-pad_v*2)
        self.game_surf.set_clip(content_rect)

        fds=self.font_dialog_small or self.font_dialog or self.font
        fdl=self.font_dialog_large or self.font_dialog or self.font
        fdi=fds   # quote — small italic
        fd=fds    # speaker — small
        lh=fds.get_height()+2
        lh_large=fdl.get_height()+4
        sep=2

        DARK_RED=(160, 30, 30)
        COL_QUOTE=(202, 117, 66)
        COL_SPEAKER=(187, 133, 61)
        COL_EFFECT=(138, 69, 51)

        icons=[i for i in (icons or []) if i is not None]
        icon_size=int(lh_large*0.6) if icons else 0
        icon_gap=3 if icons else 0
        icon_row_h=icon_size+sep if icons else 0

        def blit_line(font, text, color, line_h=None, x_center=True, x_right=None):
            nonlocal ty
            lbl=font.render(text, True, color)
            if x_right is not None:
                self.game_surf.blit(lbl, (x_right-lbl.get_width(), ty))
            elif x_center:
                self.game_surf.blit(lbl, (cx-lbl.get_width()//2, ty))
            ty+=(line_h or lh)

        def blit_icons():
            nonlocal ty
            if not icons: return
            total_icon_w=len(icons)*icon_size+(len(icons)-1)*icon_gap
            ix=cx-total_icon_w//2
            for ic in icons:
                si=pygame.transform.smoothscale(ic,(icon_size,icon_size))
                self.game_surf.blit(si,(ix,ty))
                ix+=icon_size+icon_gap
            ty+=icon_row_h

        header=content.get("header") if isinstance(content, dict) else None

        if isinstance(content, dict) and "quote" in content:
            # Fate: icon + header + quote + speaker + effect
            quote_lines=self._wrap_text(content["quote"], fdi, max_text_w)
            speaker_lines=self._wrap_text(content["speaker"], fd, max_text_w)
            effect_lines=self._wrap_text(content["effect"], fdl, max_text_w)
            header_lines=self._wrap_text(header, fdl, max_text_w) if header else []
            total_h=(icon_row_h
                    +len(header_lines)*lh_large+sep
                    +len(quote_lines)*lh+sep
                    +len(speaker_lines)*lh+sep
                    +len(effect_lines)*lh_large)
            ty=max(content_rect.top, cy-total_h//2)
            blit_icons()
            for line in header_lines:
                blit_line(fdl, line, DARK_RED, line_h=lh_large)
            ty+=sep
            for line in quote_lines:
                blit_line(fdi, line, COL_QUOTE)
            ty+=sep
            for line in speaker_lines:
                blit_line(fd, line, COL_SPEAKER, x_center=False, x_right=content_rect.right)
            ty+=sep
            for line in effect_lines:
                blit_line(fdl, line, COL_EFFECT, line_h=lh_large)
        else:
            # hobby / chance / stage / ending: icon + header + lines
            lines=content.get("lines", content) if isinstance(content, dict) else content
            header_lines=self._wrap_text(header, fdl, max_text_w) if header else []
            all_lines=[]
            for line in lines:
                all_lines.extend(self._wrap_text(line, fdl, max_text_w))
            total_h=icon_row_h+len(header_lines)*lh_large+sep+len(all_lines)*lh_large
            ty=max(content_rect.top, cy-total_h//2)
            blit_icons()
            for line in header_lines:
                blit_line(fdl, line, DARK_RED, line_h=lh_large)
            ty+=sep
            for line in all_lines:
                blit_line(fdl, line, COL_EFFECT, line_h=lh_large)

        self.game_surf.set_clip(None)  # bỏ clip sau khi vẽ xong

    def show_dialog_and_wait(self, content, icons=None) -> None:
        """Hiển thị hộp thoại, pause mọi thứ, chờ click chuột để đóng."""
        self.draw_board()
        self.draw_sidebar()
        self.draw_dialog(content, icons)
        pygame.display.flip()
        waiting=True
        while waiting:
            self.clock.tick(30)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    exit()
                if event.type==pygame.MOUSEBUTTONDOWN:
                    waiting=False
                if event.type==pygame.VIDEORESIZE:
                    self.resize_surfaces()
                    self.draw_board()
                    self.draw_sidebar()
                    self.draw_dialog(content, icons)
                    pygame.display.flip()
        # Xóa dialog: vẽ lại screen không có dialog
        self.screen_surf.fill(self.background_color["screen"])
        self.game_surf.fill(self.background_color["game"])
        self.draw_board()
        self.draw_sidebar()
        pygame.display.flip()

    def draw_board(self, no_draw_pts: list[tuple[int, int]] = None) -> None:
        self.board_surf.fill(self.background_color["board"])

        for row in range(self.board.rows):
            for col in range(self.board.cols):
                if no_draw_pts is not None and (col, row) in no_draw_pts:
                    continue
                color_index = self.board.board[row][col]
                if color_index < 0:
                    continue
                pos = self.board_pos_to_win_pos(col, row)
                self.draw_circle(pos[0], pos[1], self.colors[color_index])

    def draw_buttons(self, texts, y, y_separation, surface_name) -> None:
        surface = getattr(self, f"{surface_name}_surf")
        height = (self.char_height + self.char_sep_height) * 2
        for text in texts:
            width = (len(text) + 4) * self.char_width
            x = (surface.get_width() - width) / 2 + surface.get_abs_offset()[0]
            y_abs = y + surface.get_abs_offset()[1]
            border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
            if border_thickness < 1:
                border_thickness = 1
            button_name = text.lower()
            button_name = button_name.replace(' ', '_')
            if button_name not in self.active_widgets:
                button = pygamew.Button(
                    self.screen_surf, x, y_abs, width, height,
                    text=text,
                    textColour=self.widget_text_color,
                    font=self.font,
                    colour=(64, 64, 64),
                    hoverColour=(96, 96, 96),
                    pressedColour=(128, 128, 128),
                    borderColour=(0, 0, 0),
                    hoverBorderColour=(32, 32, 32),
                    pressedBorderColour=(64, 64, 64),
                    shadowColour=[val * 2 / 3 for val in self.background_color[surface_name]],
                    shadowDistance=self.char_sep_height // 2,
                    borderThickness=border_thickness,
                    onRelease=getattr(self, f"{button_name}_clicked")
                )
                self.active_widgets[button_name] = button
            self.active_widgets[button_name].draw()
            y += height + (self.char_height + self.char_sep_height) * y_separation

    def draw_sidebar(self) -> None:
        self.sidebar_surf.fill(self.background_color["sidebar"])

        y = (self.sidebar_surf.get_height() - (self.char_height + self.char_sep_height) * 13) / 2
        for i, text in enumerate(("SCORE", str(self.score), "TIME LEFT", str(self.time_left_sec))):
            if i == 2:
                y += self.char_height + self.char_sep_height
            if i == 3:
                tc = list(self.widget_text_color)
                gb = 255 * self.time_left_sec / (self.time_init / 1000)
                if gb > 255:
                    gb = 255
                elif gb < 0:
                    gb = 0
                tc[1] = gb
                tc[2] = gb
                label = self.font.render(text, True, tc)
            else:
                label = self.font.render(text, True, self.widget_text_color)
            width = len(text) * self.char_width
            x = (self.sidebar_surf.get_width() - width) / 2
            self.sidebar_surf.blit(label, (x, y))
            if self.curr_plus_score_ani_time <= self.plus_score_ani_time:
                if i == 1 or i == 3:
                    label = self.font.render("+" + str({1: self.curr_score, 3: self.curr_time_score / 1000}.get(i)), True, (255, 255, 0))
                    x += width
                    self.sidebar_surf.blit(label, (x, y))
                self.curr_plus_score_ani_time = pygame.time.get_ticks() - self.plus_score_ani_time_start
            y += self.char_height + self.char_sep_height

        y += (self.char_height + self.char_sep_height) * 3

        texts = ("PAUSE", "HINT")
        self.draw_buttons(texts, y, 1, "sidebar")

    def draw_main_menu(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        texts = ["NEW GAME", "HIGH SCORES", "PREFERENCES", "ABOUT", "EXIT"]
        if self.game_state == GameState.PAUSED:
            texts = ["RESUME GAME"] + texts
        y = (self.game_surf.get_height() - len(texts) * (self.char_height + self.char_sep_height) * 3.5 + (self.char_height + self.char_sep_height) * 1.5) / 2
        self.draw_buttons(texts, y, 1.5, "game")

    def draw_choosesize(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 2) / 2
        texts = ("START",)
        self.draw_buttons(texts, y, 0, "game")

        y = (self.game_surf.get_height() - (len(self.board_sizes) + 1) * (self.char_height + self.char_sep_height) * 2) / 2
        text = "Choose Board Size"
        height = (self.char_height + self.char_sep_height) * 2
        width = (len(text) + 4) * self.char_width
        x = (self.game_surf.get_width() - width) / 2 + self.game_surf.get_abs_offset()[0]
        y_abs = y + self.game_surf.get_abs_offset()[1]
        border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
        if border_thickness < 1:
            border_thickness = 1
        dropdown_name = text.lower()
        dropdown_name = dropdown_name.replace(' ', '_')
        if dropdown_name not in self.active_widgets:
            dropdown = pygamew.Dropdown(
                self.screen_surf, x, y_abs, width, height,
                name=text,
                textColour=self.widget_text_color,
                font=self.font,
                inactiveColour=(64, 64, 64),
                hoverColour=(96, 96, 96),
                pressedColour=(128, 128, 128),
                borderColour=(0, 0, 0),
                hoverBorderColour=(32, 32, 32),
                pressedBorderColour=(64, 64, 64),
                borderThickness=border_thickness,
                choices=[f"{n}x{n}" for n in self.board_sizes],
                values=self.board_sizes
            )
            self.active_widgets[dropdown_name] = dropdown
        # FIXME: When window is resized dropdown is regenerated and loses its current selection.
        self.active_widgets[dropdown_name].draw()

    def draw_ended(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 9) / 2
        for i, text in enumerate(("TIME'S UP!", "YOUR SCORE:", str(self.score))):
            width = len(text) * self.char_width
            x = (self.game_surf.get_width() - width) / 2
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height)
            if i == 0:
                y += (self.char_height + self.char_sep_height) * 2

        y += (self.char_height + self.char_sep_height) * 2

        texts = ("CONTINUE",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_enterhighscore(self ) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 11) / 2
        text = "HIGH SCORE ACHIEVED!"
        width = len(text) * self.char_width
        x = (self.game_surf.get_width() - width) / 2
        label = self.font.render(text, True, self.widget_text_color)
        self.game_surf.blit(label, (x, y))

        y += (self.char_height + self.char_sep_height) * 3

        text = "Enter your name:"
        width = len(text) * self.char_width
        x = (self.game_surf.get_width() - width) / 2
        label = self.font.render(text, True, self.widget_text_color)
        self.game_surf.blit(label, (x, y))

        y += (self.char_height + self.char_sep_height) * 2

        width = (self.high_score_name_max_len + 1) * self.char_width
        height = (self.char_height + self.char_sep_height) * 2
        x = (self.game_surf.get_width() - width) / 2 + self.game_surf.get_abs_offset()[0]
        y_abs = y + self.game_surf.get_abs_offset()[1]
        border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
        if border_thickness < 1:
            border_thickness = 1
        textbox_name = "high_score_name"
        if textbox_name not in self.active_widgets:
            textbox = pygamew.TextBox(
                self.screen_surf, x, y_abs, width, height,
                textColour=self.widget_text_color,
                font=self.font,
                colour=(64, 64, 64),
                borderColour=(0, 0, 0),
                borderThickness=border_thickness,
                placeholderText="Enter your name",
                onSubmit=self.ok_clicked
            )
            self.active_widgets[textbox_name] = textbox
        self.active_widgets[textbox_name].draw()

        y += (self.char_height + self.char_sep_height) * 4

        texts = ("OK",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_highscores(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        hsss = f"{self.high_scores_state}x{self.high_scores_state}"

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 15) / 2
        for text in ("HIGH SCORES", hsss, f"Rank Name{' '*(self.high_score_name_max_len-4)} Score"):
            width = len(text) * self.char_width
            x = (self.game_surf.get_width() - width) / 2
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height) * 2

        for i in range(5):
            if hsss in self.high_scores and i < len(self.high_scores[hsss]):
                cols = (
                    f"{i+1:>4}",
                    f"{self.high_scores[hsss][i][0]}{' '*(self.high_score_name_max_len-len(self.high_scores[hsss][i][0]))}",
                    f"{self.high_scores[hsss][i][1]:>5}"
                )
                text = f"{cols[0]} {cols[1]} {cols[2]}"
                width = len(text) * self.char_width
                x = (self.game_surf.get_width() - width) / 2
                label = self.font.render(text, True, self.widget_text_color)
                self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height)

        y += (self.char_height + self.char_sep_height) * 2

        texts = ("BACK",)
        self.draw_buttons(texts, y, 0, "game")

        for i, text in enumerate(("<", ">")):
            width = (len(text) + 2) * self.char_width
            height = (self.char_height + self.char_sep_height) * 5
            x = {0: self.char_width, 1: self.game_surf.get_width() - width - self.char_width}.get(i) + self.game_surf.get_abs_offset()[0]
            y = (self.game_surf.get_height() - height) / 2
            y_abs = y + self.game_surf.get_abs_offset()[1]
            border_thickness = int(2 * self.game_surf.get_width() / self.starting_width)
            if border_thickness < 1:
                border_thickness = 1
            button_name = {0: "left", 1: "right"}.get(i)
            if button_name not in self.active_widgets:
                button = pygamew.Button(
                    self.screen_surf, x, y_abs, width, height,
                    text=text,
                    textColour=self.widget_text_color,
                    font=self.font,
                    colour=(64, 64, 64),
                    hoverColour=(96, 96, 96),
                    pressedColour=(128, 128, 128),
                    borderColour=(0, 0, 0),
                    hoverBorderColour=(32, 32, 32),
                    pressedBorderColour=(64, 64, 64),
                    shadowColour=[val * 2 / 3 for val in self.background_color["game"]],
                    shadowDistance=self.char_sep_height // 2,
                    borderThickness=border_thickness,
                    onRelease=getattr(self, f"{button_name}_clicked")
                )
                self.active_widgets[button_name] = button
            self.active_widgets[button_name].draw()

    def draw_preferences(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 12) / 2
        height = self.char_height + self.char_sep_height
        texts = ("Background music", "Sound effects")
        text_width = max([len(text) for text in texts]) * self.char_width
        spacing_width = 3 * self.char_width
        toggle_width = 3 * self.char_width
        width = text_width + spacing_width + toggle_width
        x_text = (self.game_surf.get_width() - width) / 2
        x_toggle = x_text + text_width + spacing_width
        x_toggle_abs = x_toggle + self.game_surf.get_abs_offset()[0]
        for text in texts:
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x_text, y))
            y_abs = y + self.game_surf.get_abs_offset()[1]
            toggle_name = text.lower()
            toggle_name = toggle_name.replace(' ', '_')
            if toggle_name not in self.active_widgets:
                toggle = pygamew.Toggle(
                    self.screen_surf, int(x_toggle_abs), int(y_abs), int(toggle_width), int(height),
                    startOn = self.preferences.get(toggle_name, True),
                    onColour = (0, 255, 0),
                    offColour = (128, 128, 128),
                    handleOnColour = (0, 128, 0),
                    handleOffColour = (64, 64, 64)
                )
                self.active_widgets[toggle_name] = toggle
            self.active_widgets[toggle_name].draw()
            y += (self.char_height + self.char_sep_height) * 3

        y += (self.char_height + self.char_sep_height) * 4

        texts = ("SAVE",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_about(self) -> None:
        self.game_surf.fill(self.background_color["game"])

        y = (self.game_surf.get_height() - (self.char_height + self.char_sep_height) * 10) / 2
        for text in ("MATCH3PY", "AUTHOR: TOMAS GONZALEZ ARAGON"):
            width = len(text) * self.char_width
            x = (self.game_surf.get_width() - width) / 2
            label = self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y += (self.char_height + self.char_sep_height) * 4

        texts = ("BACK",)
        self.draw_buttons(texts, y, 0, "game")

    def draw_screen(self) -> None:
        self.screen_surf.fill(self.background_color["screen"])

        if self.game_state == GameState.RUNNING:
            self.game_surf.fill(self.background_color["game"])
            self.draw_board()
            self.draw_sidebar()
        elif self.game_state == GameState.MAINMENU or self.game_state == GameState.PAUSED:
            self.draw_main_menu()
        elif self.game_state == GameState.CHOOSESIZE:
            self.draw_choosesize()
        elif self.game_state == GameState.ENDED:
            self.draw_ended()
        elif self.game_state == GameState.ENTERHIGHSCORE:
            self.draw_enterhighscore()
        elif self.game_state == GameState.HIGHSCORES:
            self.draw_highscores()
        elif self.game_state == GameState.PREFERENCES:
            self.draw_preferences()
        elif self.game_state == GameState.ABOUT:
            self.draw_about()

    ##################################################
    # Update functions
    ##################################################

    def update_board(self) -> None:
        self.draw_board()
        pygame.display.flip()

    def update_sidebar(self) -> None:
        self.draw_sidebar()
        pygame.display.flip()

    def update_screen(self) -> None:
        self.active_widgets = {}
        self.draw_screen()
        pygame.display.flip()

    ##################################################
    # On click functions
    ##################################################

    def new_game_clicked(self) -> None:
        self.game_state = GameState.CHOOSESIZE
        self.update_screen()

    def start_clicked(self) -> None:
        size = self.active_widgets["choose_board_size"].getSelected()
        if size is None:
            return
        num_values = size - 1
        if size > 7:
            num_values -= 1
        if size > 10:
            num_values -= 1
        self.board = Match3Board(size, size, num_values)
        self.score = 0
        self.time_left = self.time_init
        self.time_score = 0
        self.time_left_sec = int(self.time_left / 1000)
        self.hint = False
        self.hint_cut_score = False
        self.plus_score_ani_time_start = 0
        self.curr_plus_score_ani_time = self.plus_score_ani_time + 1
        self.curr_score = 0
        self.curr_time_score = 0
        self.time_paused = 0
        self.pause = False
        self.life_stage = 0
        self.hobby_state = 0
        self.hobby_type = None
        self.chance_state = 0
        self.chance_type = None
        self.time_count = 0
        self.hobby_count = 0
        self.chance_count = 0
        self.philosopher_turns=0
        self.sage_turns=0
        self.prisoner_turns=0
        self.turn_taken = False
        self.random_wheel_result=None
        self.game_state = GameState.RUNNING
        self.start_music()
        self.resize_surfaces()
        self.update_screen()
        self.time_start = pygame.time.get_ticks()

    def hint_clicked(self) -> None:
        self.hint = True

    def pause_clicked(self) -> None:
        self.pause = True

    def resume_game_clicked(self) -> None:
        self.game_state = GameState.RUNNING
        self.start_music()
        self.update_screen()
        self.time_paused += pygame.time.get_ticks() - self.pause_time

    def continue_clicked(self) -> None:
        min_hs = 0
        hs = self.high_scores.get(f"{self.board.cols}x{self.board.rows}", list())
        if len(hs) > 0:
            min_hs = min([ns[1] for ns in hs])
        if self.score > 0 and (self.score > min_hs or len(hs) < 5):
            self.game_state = GameState.ENTERHIGHSCORE
            self.play_sound("yay")
        else:
            self.game_state = GameState.MAINMENU
        self.update_screen()

    def ok_clicked(self) -> None:
        name = self.active_widgets["high_score_name"].getText()
        # TODO: Sanitize name.
        if len(name) == 0:
            return
        hs = self.high_scores.get(f"{self.board.cols}x{self.board.rows}", list())
        hs.append([name, self.score])
        hs.sort(key=lambda d: d[1], reverse=True)
        if len(hs) > 5:
            del hs[-1]
        self.high_scores[f"{self.board.cols}x{self.board.rows}"] = hs
        with open(self.high_scores_filename, 'w') as f:
            json.dump(self.high_scores, f)
        self.game_state = GameState.MAINMENU
        self.update_screen()

    def high_scores_clicked(self) -> None:
        self.prev_state = self.game_state
        self.game_state = GameState.HIGHSCORES
        self.update_screen()

    def left_clicked(self) -> None:
        self.high_scores_state -= 1
        if self.high_scores_state < self.board_sizes[0]:
            self.high_scores_state = self.board_sizes[0]
        self.update_screen()

    def right_clicked(self) -> None:
        self.high_scores_state += 1
        if self.high_scores_state > self.board_sizes[-1]:
            self.high_scores_state = self.board_sizes[-1]
        self.update_screen()

    def preferences_clicked(self) -> None:
        self.prev_state = self.game_state
        self.game_state = GameState.PREFERENCES
        self.update_screen()

    def save_clicked(self) -> None:
        for s in ("background_music", "sound_effects"):
            self.preferences[s] = self.active_widgets[s].value
        with open(self.preferences_filename, 'w') as f:
            json.dump(self.preferences, f)
        self.game_state = self.prev_state
        self.update_screen()

    def about_clicked(self) -> None:
        self.prev_state = self.game_state
        self.game_state = GameState.ABOUT
        self.update_screen()

    def back_clicked(self) -> None:
        self.game_state = self.prev_state
        self.update_screen()

    def exit_clicked(self) -> None:
        pygame.quit()
        exit()

    ##################################################
    # Helper functions
    ##################################################

    def win_pos_to_board_pos(self, win_pos_x: int, win_pos_y: int, relative_to_window: bool = False) -> tuple[int, int]:
        if relative_to_window:
            win_pos_x -= self.board_surf.get_abs_offset()[0]
            win_pos_y -= self.board_surf.get_abs_offset()[1]
        col_w = self.board_surf.get_width() / self.board.cols
        row_h = self.board_surf.get_height() / self.board.rows
        board_pos_x = (win_pos_x - col_w / 2) / col_w
        board_pos_y = (win_pos_y - row_h / 2) / row_h
        return (int(round(board_pos_x)), int(round(board_pos_y)))

    def board_pos_to_win_pos(self, board_pos_x: int, board_pos_y: int, relative_to_window: bool = False) -> tuple[int, int]:
        col_w = self.board_surf.get_width() / self.board.cols
        row_h = self.board_surf.get_height() / self.board.rows
        win_pos_x = board_pos_x * col_w + col_w / 2
        win_pos_y = board_pos_y * row_h + row_h / 2
        if relative_to_window:
            win_pos_x += self.board_surf.get_abs_offset()[0]
            win_pos_y += self.board_surf.get_abs_offset()[1]
        return (int(win_pos_x), int(win_pos_y))

    def point_inside_circle(self, point: tuple[int, int], circle_center: tuple[int, int], r: float) -> bool:
        x, y = point
        c_x, c_y = circle_center
        return (x - c_x)**2 + (y - c_y)**2 < r**2

    def get_num_vertical_points(self, points: list[tuple[int, int]]) -> int:
        points_in_line = dict()
        for (col, _) in points:
            points_in_line[col] = points_in_line.get(col, 0) + 1
        return max(points_in_line.values())

    def play_sound(self, sound: str) -> None:
        if self.preferences.get("sound_effects", True) and sound in self.sounds:
            pygame.mixer.Sound.play(self.sounds[sound])

    def start_music(self) -> None:
        if self.preferences.get("background_music", True):
            try:
                pygame.mixer.music.play(-1, 0, 1000)
            except:
                pass

    ##################################################
    # Other functions
    ##################################################

    def resize_surfaces(self) -> None:
        # Calculate new screen size
        sw, sh = self.screen_surf.get_size()
        gw, gh = sw, sh
        gx, gy = 0, 0
        if sw / sh > self.game_ratio:
            gw = sh * self.game_ratio
            gx = (sw - gw) / 2
        else:
            gh = sw / self.game_ratio
            gy = (sh - gh) / 2
        self.game_surf = self.screen_surf.subsurface((gx, gy, gw, gh))
        # Calculate and update new board size and new circle radius
        pos = gh * (1 - self.board_scale) / 2
        side = gh * self.board_scale
        self.board_surf = self.game_surf.subsurface((pos, pos, side, side))
        if self.board is not None:
            self.circle_radius = self.board_surf.get_height() / self.board.cols / 2
        # Calculate and update new sidebar size
        self.sidebar_surf = self.game_surf.subsurface((gh, 0, gw - gh, gh))
        # Calculate and update new font size
        self.font_size = self.min_font_size * self.game_surf.get_width() / self.starting_width
        self.char_width = self.min_char_width * self.game_surf.get_width() / self.starting_width
        self.char_height = self.min_char_height * self.game_surf.get_height() / self.starting_height
        self.char_sep_height = self.min_char_sep_height * self.game_surf.get_height() / self.starting_height
        self.font = pygame.font.SysFont("monospace", int(self.font_size))
        self.font.set_bold(True)
        # Clear active widgets to force a re-draw
        self.active_widgets = {}

    ##################################################
    # Process events functions
    ##################################################
    def _hobby_dialog_icon(self):
        if self.hobby_type is None:
            return self.hobby_icon_s0
        # boost icon index matches current state (capped at 2; state 3 uses index 2)
        idx = min(max(self.hobby_state, 0), 3)
        for i in range(idx, -1, -1):
            ic = self.hobby_boost_icons[self.hobby_type][i]
            if ic is not None:
                return ic
        return self.hobby_icon_s0

    def _chance_dialog_icon(self):
        if self.chance_type is None:
            return self.chance_icon_s0
        return self.chance_boost_icons[self.chance_type] or self.chance_icons[self.chance_type] or self.chance_boost_icon or self.chance_icon_s0

    def endings(self, call_type: int) -> None:
        if call_type==0:
            self.show_dialog_and_wait(self.DIALOG_LINES[call_type][self.hobby_state][self.hobby_type],
                                      icons=[self._hobby_dialog_icon()])
        elif call_type==1:
            self.show_dialog_and_wait(self.DIALOG_LINES[call_type][self.random_wheel_result][self.chance_type],
                                      icons=[self._chance_dialog_icon()])
        else:
            self.active_widgets["start"].show()
        return True

    def running_process_events(self, events, **kwargs) -> bool:
        # End the game if the time has run out
        if self.time_left <= 0:
            self.game_ended = True

        update_display = False

        # Update the time left
        self.time_left = self.time_paused + self.time_init + self.time_score - (pygame.time.get_ticks() - self.time_start)
        if self.time_left_sec != int(round(self.time_left / 1000)):
            self.time_left_sec = int(round(self.time_left / 1000))
            if self.time_left_sec < 0:
                self.time_left_sec = 0
            self.draw_sidebar()
            update_display = True

        # Play beep sound
        if self.time_left_sec <= 5:
            if pygame.time.get_ticks() - self.last_beep_sound_time >= 1000:
                self.last_beep_sound_time = pygame.time.get_ticks()
                self.play_sound("beep")

        # Remove plus score from sidebar if the ani time is up
        if self.curr_plus_score_ani_time <= self.plus_score_ani_time:
            self.curr_plus_score_ani_time = pygame.time.get_ticks() - self.plus_score_ani_time_start
            if self.curr_plus_score_ani_time > self.plus_score_ani_time:
                self.draw_sidebar()
                update_display = True

        # Process events
        if not kwargs.get('mouse', False):
            return
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.WAITING:
                    self.board_pos_src = self.win_pos_to_board_pos(*event.pos, True)
                    if self.board.out_of_bounds(*self.board_pos_src):
                        continue
                    # Check that the mouse is inside a circle
                    circle_center = self.board_pos_to_win_pos(*self.board_pos_src, True)
                    pic = self.point_inside_circle(event.pos, circle_center, self.circle_radius * self.circle_scale)
                    if pic:
                        self.mouse_state = MouseState.PRESSED
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.MOVING
                if self.mouse_state == MouseState.MOVING:
                    board_pos_dst = list(self.win_pos_to_board_pos(*event.pos, True))
                    # Check that the mouse was dragged to a different position in the board
                    if list(self.board_pos_src) == board_pos_dst:
                        continue
                    # If the mouse went to far, move the dst pos back to a neighbor
                    for i in range(2):
                        if self.board_pos_src[i] - board_pos_dst[i] > 1:
                            board_pos_dst[i] = self.board_pos_src[i] - 1
                        elif self.board_pos_src[i] - board_pos_dst[i] < -1:
                            board_pos_dst[i] = self.board_pos_src[i] + 1
                    if self.board.out_of_bounds(*board_pos_dst):
                        continue
                    # Check that the new position is a neighbor
                    swap_valid = False
                    for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        neigh_x = self.board_pos_src[0] + x
                        neigh_y = self.board_pos_src[1] + y
                        if [neigh_x, neigh_y] == board_pos_dst:
                            swap_valid = True
                            break
                    if not swap_valid:
                        self.mouse_state = MouseState.WAITING
                        continue
                    # Do the swap, if it was not a valid play, revert it
                    swap_valid = self.board.is_swap_valid(self.board_pos_src, board_pos_dst)
                    self.animate_swap(self.board_pos_src, tuple(board_pos_dst))
                    self.board.swap(self.board_pos_src, board_pos_dst)
                    if not swap_valid:
                        self.animate_swap(tuple(board_pos_dst), self.board_pos_src)
                        self.board.swap(board_pos_dst, self.board_pos_src)
                    else:
                        self.turn_taken = True

                    self.mouse_state = MouseState.WAITING
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button != 1:
                    continue
                if self.mouse_state == MouseState.PRESSED:
                    self.mouse_state = MouseState.WAITING
                elif self.mouse_state == MouseState.MOVING:
                    self.mouse_state = MouseState.WAITING

        return update_display

    def enterhighscore_process_events(self, events, **kwargs) -> bool:
        self.active_widgets["high_score_name"].listen(events)
        self.draw_screen()
        return True

    def preferences_process_events(self, events, **kwargs) -> bool:
        self.active_widgets["background_music"].listen(events)
        self.active_widgets["sound_effects"].listen(events)
        self.draw_screen()
        return True

    def process_events(self, fps: int = -1, **kwargs) -> bool:
        # Wait until frame time
        if fps < 0:
            fps = self.ani_fps
        self.clock.tick(fps)

        # Process generic events
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.VIDEORESIZE:
                self.resize_surfaces()
                return True
            elif event.type == pygame.QUIT:
                pygame.quit()
                exit()

        # Process specific events related to the current game state
        gs = self.game_state.name
        gs = gs.lower()
        try:
            func = getattr(self, f"{gs}_process_events")
        except AttributeError:
            func = None
        update_display = False
        if func is not None:
            update_display = func(events, **kwargs)

        # Listen to button events
        for button in self.active_widgets.values():
            if type(button) == pygamew.Button:
                color = button.colour
                button.listen(events)
                if color != button.colour:
                    button.draw()
                    update_display = True

        if update_display:
            pygame.display.flip()

        return False
    
    def load_icon(self):
        p="media/images/ui/dialogue_box.png"
        if os.path.isfile(p):
            self.dialogue_box_img=pygame.image.load(p).convert_alpha()

        bp="media/images/ui/button.png"
        if os.path.isfile(bp):
            self.button_img=pygame.image.load(bp).convert_alpha()
        for attr, path in (
            ("menu_button_img",  "media/images/ui/menu_button.png"),
            ("board_button_img", "media/images/ui/board_button.png"),
            ("block_frame_img",  "media/images/ui/frame.png"),
            ("stat_box_img",     "media/images/ui/stat_box.png"),
            ("time_frame_img",   "media/images/ui/time_frame.png"),
            ("hint_img",         "media/images/ui/hint.png"),
            ("pause_img",        "media/images/ui/pause.png"),
        ):
            if os.path.isfile(path):
                setattr(self, attr, pygame.image.load(path).convert_alpha())

        for i in range(13):
            p=f"media/images/ui/Time {i}.png"
            if os.path.isfile(p):
                self.time_imgs[i]=pygame.image.load(p).convert_alpha()
        tp="media/images/ui/time_plate.png"
        if os.path.isfile(tp):
            self.time_plate_img=pygame.image.load(tp).convert_alpha()

        bg="media/images/ui/backgroundA.png"
        if os.path.isfile(bg):
            self.board_bg=pygame.image.load(bg).convert()
        bgb="media/images/ui/backgroundB.png"
        if os.path.isfile(bgb):
            self.board_area_bg=pygame.image.load(bgb).convert()

        if os.path.isfile("media/images/block/hobby_0.png"):
            self.hobby_icon_s0=pygame.image.load("media/images/block/hobby_0.png").convert_alpha()
        if os.path.isfile("media/images/block/chance_0.png"):
            self.chance_icon_s0=pygame.image.load("media/images/block/chance_0.png").convert_alpha()

        hobby_types=["handicraft", "military", "forge"]
        for t, tname in enumerate(hobby_types):
            for s, stage in enumerate(["1", "2", "3"]):
                path=f"media/images/block/hobby_{tname}{stage}.png"
                if os.path.isfile(path):
                    self.hobby_icons[t][s]=pygame.image.load(path).convert_alpha()
            for s, stage in enumerate(["1", "2", "3"]):
                path=f"media/images/block/hobby_{tname}{stage}_boost.png"
                if os.path.isfile(path):
                    self.hobby_boost_icons[t][s+1]=pygame.image.load(path).convert_alpha()

        # hobby_boost.png: index [t][0] cho tất cả type (dùng khi state=0)
        if os.path.isfile("media/images/block/hobby_boost.png"):
            generic=pygame.image.load("media/images/block/hobby_boost.png").convert_alpha()
            for t in range(3):
                self.hobby_boost_icons[t][0]=generic

        chance_types=["love", "religious", "mastermind"]
        for t, tname in enumerate(chance_types):
            path=f"media/images/block/chance_{tname}.png"
            if os.path.isfile(path):
                self.chance_icons[t]=pygame.image.load(path).convert_alpha()
        boost_chance_path="media/images/block/chance_boost.png"
        if os.path.isfile(boost_chance_path):
            self.chance_boost_icon=pygame.image.load(boost_chance_path).convert_alpha()
        for t, tname in enumerate(chance_types):
            path=f"media/images/block/chance_{tname}_boost.png"
            if os.path.isfile(path):
                self.chance_boost_icons[t]=pygame.image.load(path).convert_alpha()

        for i, path in enumerate(["media/images/block/time_0.png", "media/images/block/time_boost.png"]):
            if os.path.isfile(path):
                self.time_icon[i]=pygame.image.load(path).convert_alpha()

        fate_path="media/images/block/fate.png"
        if os.path.isfile(fate_path):
            self.fate_icon=pygame.image.load(fate_path).convert_alpha()

        self.hourglass_imgs=[]
        for i in range(13):  # 0..12
            p=f"media/images/ui/hourglass/{i}.png"
            if os.path.isfile(p):
                self.hourglass_imgs.append(pygame.image.load(p).convert_alpha())
            else:
                self.hourglass_imgs.append(None)


    ##################################################
    # Main game loop functions
    ##################################################
    def minigame(self):
        difficulty = int(self.failedbefore)
        if self.hobby_type == 0:#handicraft
            result = minigame.Tailor(self.board_surf, self.clock, difficulty).run()
        elif self.hobby_type == 1:#military
            result = minigame.Fighter(self.board_surf, self.clock, difficulty).run()
        else:#forge
            result = minigame.Minesweeper(self.board_surf, self.clock, difficulty).run()

        if result:
            self.endings(0)
        else:
            self.failedbefore=True
            self.hobby_state=3   #giảm độ khó
            self.hobby_count=40  #reset về đầu state 2 để tích lại
            if "hobby_state_3" in self.DIALOG_LINES and self.hobby_type is not None:
                self.show_dialog_and_wait(self.DIALOG_LINES["hobby_state_3"][self.hobby_type],
                                          icons=[self._hobby_dialog_icon()])

    def check_stat_thresholds(self, check_time: bool = True) -> None:
        if check_time and self.time_count>=12:
            if self.life_stage>=4:
                self.game_ended=True
                return
            self.life_stage+=1
            self.time_count=0
            key=f"stage_{self.life_stage}"
            if key in self.DIALOG_LINES:
                self.show_dialog_and_wait(self.DIALOG_LINES[key],
                                          icons=[self.time_icon[0]] if self.time_icon[0] else None)

        new_hobby=min(self.hobby_count//20, 2)
        if new_hobby>self.hobby_state and self.hobby_state!=3:
            if new_hobby==1 and self.hobby_type is None:
                self.hobby_type=random.randint(0, 2)
            self.hobby_state=new_hobby
            key=f"hobby_state_{self.hobby_state}"
            if key in self.DIALOG_LINES and self.hobby_type is not None:
                self.show_dialog_and_wait(self.DIALOG_LINES[key][self.hobby_type],
                                          icons=[self._hobby_dialog_icon()])

        if self.hobby_state>=2 and self.hobby_count>=60:
            self.hobby_count=60
            self.minigame()

        new_chance=min(self.chance_count//25, 1)
        if new_chance>self.chance_state:
            if new_chance==1 and self.chance_type is None:
                self.chance_type=random.randint(0, 2)
            self.chance_state=new_chance
            if self.chance_state==1 and self.chance_type is not None:
                self.show_dialog_and_wait(self.DIALOG_LINES["chance_state_1"][self.chance_type],
                                          icons=[self._chance_dialog_icon()])

        # Khi chance_count >= 50: xác định kết quả (gold 5%, copper 10%, blank 85%)
        if self.chance_count>=50 and self.random_wheel_result is None:
            roll = random.random()
            result = "gold" if roll < 0.05 else "copper" if roll < 0.15 else "blank"
            self.random_wheel_result = result if result != "blank" else None
            if self.random_wheel_result is not None:
                self.endings(1)

    def _apply_fate_event(self) -> None:
        sx, sy = self.board_pos_src
        event=random.choice(["philosopher", "seer", "sage", "thief", "brute", "prisoner"])

       
        # Set hiệu ứng turns TRƯỚC khi clear để cascade sau đó không cộng điểm
        if event=="philosopher": self.philosopher_turns=2
        elif event=="sage":      self.sage_turns=2
        elif event=="prisoner":  self.prisoner_turns=2

        dialog_key=f"fate_{event}"
        if dialog_key in self.DIALOG_LINES:
            self.show_dialog_and_wait(self.DIALOG_LINES[dialog_key],
                                      icons=[self.fate_icon] if self.fate_icon else None)

        fate_pt=[(sx, sy)]
        self.animate_clear(fate_pt)
        self.board.clear(fate_pt)
        while not self.board.is_full():
            shifted=self.board.shift_down()
            shifted+=self.board.populate(rows=[0, 1], no_valid_play_check=False, no_match3_group_check=False)
            self.animate_shift_down(shifted, 1)
        self.play_sound("drop")
        self.update_board()

        # philosopher/sage/prisoner đã set ở trên, chỉ xử lý các event còn lại
        if event=="seer":
            chance_pts=[
                (c, r)
                for r in range(self.board.rows)
                for c in range(self.board.cols)
                if self.board.board[r][c]==Match3Board.CHANCE
            ]
            if chance_pts:
                self.chance_count+=len(chance_pts)
                self.animate_clear(chance_pts)
                self.board.clear(chance_pts)
                while not self.board.is_full():
                    shifted=self.board.shift_down()
                    shifted+=self.board.populate(rows=[0, 1], no_valid_play_check=False, no_match3_group_check=False)
                    self.animate_shift_down(shifted, self.get_num_vertical_points(chance_pts))
                self.play_sound("drop")
                self.check_stat_thresholds()
                self.update_board()
        elif event=="thief":
            floor=(self.hobby_count//20)*20
            self.hobby_count=max(self.hobby_count-5, floor)
            self.update_sidebar()
        elif event=="brute":
            floor=(self.chance_count//25)*25
            self.chance_count=max(self.chance_count-5, floor)
            self.update_sidebar()

    def animate_time_increment(self, gain: int) -> None:
        """Tăng time_count từng nấc, mỗi nấc cập nhật icon time indicator."""
        STEP_MS = 80  # ms giữa mỗi nấc
        for _ in range(gain):
            self.time_count = min(self.time_count + 1, 12)
            self.draw_board()
            self.draw_sidebar()
            pygame.display.flip()
            pygame.time.wait(STEP_MS)
            if self.time_count >= 12:
                break

    def running(self) -> None:
        # Let the computer play (for debug)
        # play = self.board.find_better_play()
        # if len(play) > 0:
        #     (swap_points, groups) = play
        #     self.animate_swap(swap_points[0], swap_points[1])
        #     self.board.swap(swap_points[0], swap_points[1])

        # Find all the match3 groups and update the board state by
        # clearing them and then filling the board with new tiles from the top
        # while shifting down the ones floating
        # Do this until the board state is stabilized
        groups = self.board.get_valid_groups()
        bonus_score = 0
        bonus = 0
        while len(groups) > 0:
            # Clear any old plus score in the sidbar
            self.animate_plus_score_prev()
            # Calculate the score from the match3 groups, add extra time poportional to the score
            self.curr_score = self.board.calc_score(groups) + bonus_score
            group_bonus_score = 0
            group_bonus = 0
            for _ in range(len(groups) - 1):
                group_bonus += 1
                group_bonus_score += group_bonus
            self.curr_time_score = ((self.curr_score + bonus_score + group_bonus_score) * 100)
            if self.hint_cut_score:
                self.curr_score //= 2
                self.curr_time_score = self.curr_score * 100
                self.hint_cut_score = False
            self.score += self.curr_score
            self.time_score += self.curr_time_score
            # Show plus score in the sidebar
            self.animate_plus_score_post()
            # Clear the tiles that create a match3 group
            points = [point for group in groups for point in group]
            self.animate_clear(points)
            self.board.clear(points)
            # Shift down the tiles that are floating and create new tiles in the top row
            # Do this until the board is filled
            while not self.board.is_full():
                shifted = self.board.shift_down()
                shifted += self.board.populate(rows=[0, 1], no_valid_play_check=False, no_match3_group_check=False)
                self.animate_shift_down(shifted, self.get_num_vertical_points(points))
            self.play_sound("drop")
            groups = self.board.get_valid_groups()
            bonus += 1
            bonus_score += bonus

        if getattr(self, 'turn_taken', False):
            if self.philosopher_turns > 0: self.philosopher_turns -= 1
            if self.sage_turns > 0: self.sage_turns -= 1
            if self.prisoner_turns > 0: self.prisoner_turns -= 1
            self.turn_taken = False
            
        #check coi còn chơi được k
        play = self.board.find_a_play()
        if len(play) == 0:
            self.animate_clear([(x, y) for y in range(self.board.rows) for x in range(self.board.cols)], True)
            self.board.clear()
            try:
                self.board.populate()
            except RecursionError:
                print(f"FATAL: Couldn't regenerate the the board.")
                pygame.quit()
                exit(1)
            self.update_board()

        if self.hint:
            self.hint = False
            play = self.board.find_a_play()
            if len(play) > 0:
                (swap_points, groups) = play
                self.animate_hint(*swap_points)
            self.hint_cut_score = True
        if self.game_ended:
            self.game_ended = False
            self.game_state = GameState.ENDED
            self.play_sound("end")
            pygame.mixer.music.fadeout(1000)
            self.update_screen()
        elif self.pause:
            self.pause = False
            self.game_state = GameState.PAUSED
            self.music_pos = pygame.mixer.music.get_pos()
            pygame.mixer.music.fadeout(1000)
            self.update_screen()
            self.pause_time = pygame.time.get_ticks()

    def run(self) -> None:
        # Load high scores and preferences
        for name in ("high_scores", "preferences"):
            filename = getattr(self, f"{name}_filename")
            schema = getattr(self, f"{name}_schema")
            data = dict()
            try:
                with open(filename, 'r') as file:
                    try:
                        data = json.load(file)
                        try:
                            jsonschema.validate(data, schema)
                        except jsonschema.ValidationError:
                            print(f"ERROR: In file {filename}: json doesn't conform to schema.")
                    except json.JSONDecodeError:
                        print(f"ERROR: In file {filename}: json not valid.")
            except FileNotFoundError:
                pass
            setattr(self, name, data)

        pygame.init()
        pygame.mixer.init()
        self.font = pygame.font.SysFont("monospace", int(self.font_size))
        self.font.set_bold(True)
        self.clock = pygame.time.Clock()
        icon = pygame.image.load("icon32x32.png")
        pygame.display.set_icon(icon)
        pygame.display.set_caption("MATCH3PY")
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        display_info = pygame.display.Info()
        self.screen_surf = pygame.display.set_mode((display_info.current_w, display_info.current_h), self.flags, vsync=1)
        self.resize_surfaces()
        self.update_screen()

        # Load audio
        if os.path.isfile(self.background_music_filename):
            pygame.mixer.music.load(self.background_music_filename)
        if os.path.isdir(self.sounds_dir):
            for filename in os.listdir(self.sounds_dir):
                sound_name = os.path.splitext(filename)[0]
                self.sounds[sound_name] = pygame.mixer.Sound(f"{self.sounds_dir}/{filename}")

        while True:
            if self.process_events(fps=self.main_loop_refresh_rate, mouse=True):
                self.update_screen()

            if self.game_state == GameState.RUNNING:
                self.running()
