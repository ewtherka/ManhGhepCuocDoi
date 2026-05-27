from Board import mainBoard
from match3_gui import Match3GUI, GameState, MouseState
import json
import jsonschema
import math
import os
import random
import pygame
import minigame
import pygame_widgets as pygamew
from sys import exit
from pygame import gfxdraw

class mainGUI(Match3GUI):
    background_color = {
        "screen": (0, 0, 0),
        "game": (24, 24, 24),
        "board": (52, 56, 76),#doi mau board thanh xam dam
        "sidebar": (48, 48, 48),
    }
    hint_color = (255, 255, 255)
    widget_text_color = (255, 255, 255)
    starting_width = 640
    starting_height = 480
    game_ratio = starting_width / starting_height
    board_scale = 9 / 10
    circle_scale = 18 / 20
    hint_ani_time = 500
    swap_ani_time = 200
    shift_down_ani_time = 200
    clear_ani_time = 200
    ani_fps = 60
    main_loop_refresh_rate = 30
    flags = pygame.RESIZABLE | pygame.HWSURFACE | pygame.NOFRAME
    min_font_size = 20
    min_char_width = 13.8
    min_char_height = 13.8
    min_char_sep_height = min_char_height / 2
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
    background_music_filename = f"{music_dir}/background_music.mp3"

    #dialog box
    DIALOG_LINES = {
        #fate — {"quote", "speaker", "effect"}
        "fate_philosopher": {"quote": "When we give someone our time, we actually give a portion of our life that we will never take back.", "speaker": "Alexander the Great",  "effect": "Time shall stand still for two turns hence."},
        "fate_seer":        {"quote": "Will the future bring your wisdom to me?",                                                           "speaker": "Michel de Nostredame", "effect": "All Chance blocks upon the board are gathered unto thee."},
        "fate_sage":        {"quote": "As you cannot do what you want, want what you can do.",                                              "speaker": "Leonardo da Vinci",    "effect": "Thy craft yields double reward for two turns."},
        "fate_thief":       {"quote": "No one should be discouraged who can make constant progress, even though it be slow.",               "speaker": "Plato",                "effect": "Five tokens of thy craft are taken from thee."},
        "fate_brute":       {"quote": "Ich liebe den Verrat, aber ich hasse den Verraeter.",                                               "speaker": "Gaius Julius Caesar",  "effect": "Five tokens of fortune are struck from thy count."},
        "fate_prisoner":    {"quote": "Time crumbles things; everything grows old and is forgotten through the lapse of Time.",             "speaker": "Aristoteles",          "effect": "Time flows twofold in thy favour for two turns."},

        #0=handicraft, 1=military, 2=forge — {"lines"}
        "hobby_state_1": {
            0: {"lines": ["A fondness for cloth and thread hath taken root within thy heart."]},
            1: {"lines": ["A love of mock battle and war-play hath stirred within thy breast."]},
            2: {"lines": ["A delight in gathering stones of the earth hath blossomed within thee."]},
        },
        "hobby_state_2": {
            0: {"lines": ["Thou hast resolved to become a craftsman of great skill and renown."]},
            1: {"lines": ["Thou hast sworn to walk the path of a valiant soldier."]},
            2: {"lines": ["Thou hast set thy will upon becoming a master of the forge."]},
        },
        "hobby_state_3": {
            0: {"lines": ["Alas. Thy hands are fit only for the work of a nameless apprentice."]},
            1: {"lines": ["So it must be. Thou shalt serve as a footman rather than a warrior."]},
            2: {"lines": ["The forge's door is shut to thee. Thou art naught but a bellows-hand."]},
        },

        #0=love, 1=religious, 2=mastermind — {"lines"}
        "chance_state_1": {
            0: {"lines": ["Thou hast met the love of thy life — the daughter of a wealthy merchant in the land. Whither shall this affair lead thee?"]},
            1: {"lines": ["Knock, knock. A stranger appeareth at thy door, calling himself a cleric from the East, seeking thy aid in gathering new followers to his cause."]},
            2: {"lines": ["By fortune's hand, thou didst save the King from an assassin's blade, and wast duly appointed as his Royal Chamberlain."]},
        },

        #age — {"lines"}
        "stage_1": {"lines": ["Thou hast grown into a lively and restless child."]},
        "stage_2": {"lines": ["Wonder stirs within thee — thou art now a curious and keen-eyed youth."]},
        "stage_3": {"lines": ["A new chapter of life openeth before thee, full of ambition and hope."]},
        "stage_4": {"lines": ["Thou enterest the years of middle age. The final road doth beckon."]},

        # ── ENDINGS — integer keys khớp với hàm endings() ─────────────── #

        # call_type=0: DIALOG_LINES[0][hobby_state][hobby_type]
        0: {
            2: {  # hobby_state=2 (thắng lần đầu)
                0: {"header": "A master is born.", "lines": ["Thy nimble fingers hath shaped wonders beyond measure. The finest craftsman in all the land — that is what thou hast become."]},
                1: {"header": "Steel and glory.", "lines": ["Steel in thy heart, fire in thy eyes — thou hast risen to become a warrior of great renown."]},
                2: {"header": "The forge singeth thy name.", "lines": ["Master of iron and flame — none can match the craft of thy hands. The forge doth bear thy legend."]},
            },
            3: {  # hobby_state=3 (thắng sau khi thất bại)
                0: {"header": "Hard-won glory.", "lines": ["Though the road was not without stumble, thy hands hath found their calling. A craftsman of respectable skill and honest toil."]},
                1: {"header": "A soldier forged in hardship.", "lines": ["Thou hast earned thy place among the soldiers, though not without struggle. A loyal fighter, true to the last."]},
                2: {"header": "Soot and pride.", "lines": ["Through sweat and soot, thou hast forged not only metal, but a life worthy of pride."]},
            },
        },

        # call_type=1: DIALOG_LINES[1][random_wheel_result][chance_type]
        1: {
            "copper": {
                0: {"header": "A love torn apart.", "lines": ["Her family never approved. The door was shut in your face, and the heartbreak never healed. You spent the rest of your days drinking and gambling away what little was left."]},
                1: {"header": "The offering.", "lines": ["The cleric smiled as the villagers gathered around you. Too late, you understood — you were not a helper. You were the sacrifice."]},
                2: {"header": "Executed at dawn.", "lines": ["You joined the uprising, believing in the cause. When it failed, the King showed no mercy. You were the first name on the list."]},
            },
            "gold": {
                0: {"header": "A life well lived.", "lines": ["You married her and never looked back. Years passed in quiet happiness — a warm home, a full heart, and someone always beside you until the very end."]},
                1: {"header": "Leader of the flock.", "lines": ["The congregation grew, and in time you became their leader. A small village, a humble life — but every soul there called you their shepherd."]},
                2: {"header": "The King's most trusted.", "lines": ["Of all the King's men, none stood closer than you. You whispered in his ear, shaped his decisions, and lived in comfort and honor to a ripe old age."]},
            },
        },

        # call_type=2: DIALOG_LINES[2][hobby_type or chance_type or 4]
        2: {
            0: {"header": "A life chasing a dream.", "lines": ["You never stopped trying. Not even when the money ran out. Some days you ate, some days you didn't — but the dream was always there, just out of reach."]},
            1: {"header": "Always one step behind.", "lines": ["You kept reaching back for a life that had already moved on. No matter how far you ran, the past was faster. You never truly lived in the present."]},
            2: {"header": "A flame that never caught.", "lines": ["You chased power and purpose all your life, never settling, never arriving. The fire inside you burned bright — but it burned alone."]},
            4: {"header": "Lost in the middle of it all.", "lines": ["No calling. No stroke of luck. Just one ordinary day after another. You lived, and that was all — a quiet life that left no mark and asked for none."]},
        },
    }
    def __init__(self):
        #Board
        self.board=None
        self.screen_surf=None
        self.game_surf=None
        self.board_surf=None
        self.sidebar_surf=None
        self.clock=None
        self.circle_radius=0
        self._icon_cache={}

        #Input cho chuot
        self.mouse_state=MouseState.WAITING
        self.board_pos_src=None

        #Widget
        self.active_widgets={}
        self.button_rects={}

        #Game state
        self.hint=False
        self.pause=False
        self.game_ended=False
        self.game_state=GameState.MAINMENU
        self.prev_state=None

        #Font cho dialogue, UI cac thu
        self.font_size=self.min_font_size
        self.char_width=self.min_char_width
        self.char_height=self.min_char_height
        self.char_sep_height=self.min_char_sep_height
        self.font=None
        self.font_italic=None
        self.font_dialog=None
        self.font_dialog_italic=None
        self.font_dialog_large=None
        self.font_dialog_small=None

        #Setting
        self.preferences={}
        self.sounds={}

        #Game flow
        self.life_stage=0
        self.hobby_state=0
        self.chance_state=0
        self.time_count=0
        self.hobby_count=0
        self.chance_count=0
        self.philosopher_turns=0
        self.sage_turns=0
        self.prisoner_turns=0
        self.hobby_type=None
        self.chance_type=None
        self.failedbefore=False
        self.random_wheel_result=None

        #Block icon
        self.hobby_icon_s0=None
        self.hobby_icons=[[None,None,None],[None,None,None],[None,None,None]]
        self.hobby_boost_icons=[[None,None,None,None],[None,None,None,None],[None,None,None,None]] #KVan sua
        self.chance_icon_s0=None
        self.chance_icons=[None,None,None]
        self.chance_boost_icon=None
        self.chance_boost_icons=[None,None,None]
        self.time_icon=[None,None]
        self.fate_icon=None

        #UI icon
        self.dialogue_box_img=None
        self.button_img=None
        self.menu_button_img=None
        self.board_button_img=None
        self.stat_box_img=None
        self.time_frame_img=None
        self.hourglass_imgs=[]
        self.hint_img=None
        self.pause_img=None
        self.block_frame_img=None
        self.board_bg=None
        self.board_bg_scaled=None
        self.board_area_bg=None
        self.board_area_bg_scaled=None
        self.time_imgs=[None]*13
        self.time_plate_img=None


    ###DRAWING METHODS###
    def draw_tile(self, x, y, color_index, size=None):
        B=mainBoard
        #mặc định dùng circle_radius khi không đang animate
        if size is None:
            size=self.circle_radius
        diameter=int(size*self.circle_scale*2)
        icon=None
        #HOBBY: chọn icon theo type và state hiện tại, lùi về state thấp hơn nếu thiếu
        if color_index==B.HOBBY:
            if self.hobby_state>0 and self.hobby_type is not None:
                icon=self.hobby_icons[self.hobby_type][self.hobby_state-1]
                if icon is None and self.hobby_state>=2:
                    icon=self.hobby_icons[self.hobby_type][self.hobby_state-2]
                if icon is None:
                    icon=self.hobby_icons[self.hobby_type][0]
            if icon is None:
                icon=self.hobby_icon_s0

        #CHANCE: dùng icon theo type khi đã lộ type, ngược lại dùng icon chung
        elif color_index==B.CHANCE:
            if self.chance_state>0 and self.chance_type is not None:
                icon=self.chance_icons[self.chance_type]
            if icon is None:
                icon=self.chance_icon_s0

        #BOOST_HOBBY: icon boost theo type×state, fallback về ô [0][0] (icon boost chung)
        elif color_index==B.BOOST_HOBBY:
            if self.hobby_type is not None and self.hobby_state>0:
                state_idx=min(self.hobby_state, 3) #KVan sua
                icon=self.hobby_boost_icons[self.hobby_type][state_idx]
            if icon is None:
                icon=self.hobby_boost_icons[0][0]

        #BOOST_CHANCE: icon boost theo type, fallback về icon boost chung
        elif color_index==B.BOOST_CHANCE:
            if self.chance_type is not None:
                icon=self.chance_boost_icons[self.chance_type] or self.chance_boost_icon
            else:
                icon=self.chance_boost_icon

        #TIME / BOOST_TIME / FATE: mỗi loại có một icon cố định
        elif color_index==B.TIME:
            icon=self.time_icon[0]

        elif color_index==B.BOOST_TIME:
            icon=self.time_icon[1]

        elif color_index==B.FATE:
            icon=self.fate_icon

        if icon is not None and diameter>0:
            full_d=int(self.circle_radius*self.circle_scale*2)
            #kích thước đầy đủ: dùng cache để không smoothscale lại mỗi frame
            if diameter==full_d:
                key=(id(icon), diameter)
                if key not in self._icon_cache:
                    self._icon_cache[key]=pygame.transform.smoothscale(icon, (diameter, diameter))
                scaled=self._icon_cache[key]
            #kích thước thu nhỏ (animation): bỏ qua cache, scale nhanh
            else:
                scaled=pygame.transform.scale(icon, (diameter, diameter))
            self.board_surf.blit(scaled, (x-diameter//2, y-diameter//2))
            return
        #fallback màu khi chưa load được icon — tránh ô trống
        fallback={
            B.TIME:        (100,160,220),
            B.HOBBY:       (100,200,120),
            B.CHANCE:      (220,100,100),
            B.FATE:        (200,160,60),
            B.BOOST_TIME:  (60,120,200),
            B.BOOST_HOBBY: (60,160,80),
            B.BOOST_CHANCE:(200,60,60),
        }
        color=fallback.get(color_index, (128,128,128))
        if color_index in (B.BOOST_TIME, B.BOOST_HOBBY, B.BOOST_CHANCE):
            self.draw_parallelogram(x, y, color, size)
        else:
            self.draw_rounded_square(x, y, color, size)

    def _draw_button(self, x, y_abs, width, height, text, name, callback, btn_img=None, text_y_offset=0):
        fd=self.font_dialog or self.font
        bx,by=int(x),int(y_abs)
        bw,bh=int(width),int(height)
        #ưu tiên btn_img truyền vào, fallback về button_img chung
        src=btn_img or self.button_img
        if src is not None:
            #scale PNG vừa khung, giữ tỉ lệ, căn giữa trong slot
            ow,oh=src.get_size()
            scale=min(bw/ow, bh/oh)
            nw,nh=int(ow*scale),int(oh*scale)
            bx+=(bw-nw)//2
            by+=(bh-nh)//2
            bw,bh=nw,nh
            rect=pygame.Rect(bx, by, bw, bh)
            img=pygame.transform.smoothscale(src, (bw, bh))
            self.screen_surf.blit(img, (bx, by))
        else:
            #không có ảnh: vẽ hình chữ nhật xám bo góc
            rect=pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(self.screen_surf, (64,64,64), rect, border_radius=4)
        #căn giữa nhãn chữ lên rect, cho phép dịch dọc qua text_y_offset
        if text and fd:
            lbl=fd.render(text, True, self.widget_text_color)
            self.screen_surf.blit(lbl, (rect.x+(rect.w-lbl.get_width())//2,
                                        rect.y+(rect.h-lbl.get_height())//2+text_y_offset))
        #lưu rect+callback để process_events nhận click
        self.button_rects[name]=(rect, callback)

    ###DIALOGUE METHODS###

    def _wrap_text(self, text, font, max_w):
        words=text.split()
        lines=[]
        current=""
        #ghép từ vào dòng hiện tại cho đến khi vượt max_w thì xuống dòng mới
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

    def _hobby_dialog_icon(self):
        #chưa biết type: trả về icon chung chưa lộ
        if self.hobby_type is None:
            return self.hobby_icon_s0
        #thử boost icon ở state hiện tại, lùi dần về state thấp nếu thiếu
        idx=min(max(self.hobby_state, 0), 3) #KVan sua
        for i in range(idx, -1, -1): #KVan sua
            ic=self.hobby_boost_icons[self.hobby_type][i]
            if ic is not None:
                return ic
        return self.hobby_icon_s0

    def _chance_dialog_icon(self):
        #chưa biết type: trả về icon chung chưa lộ
        if self.chance_type is None:
            return self.chance_icon_s0
        #ưu tiên: boost theo type → icon theo type → boost chung → icon chung
        return self.chance_boost_icons[self.chance_type] or self.chance_icons[self.chance_type] or self.chance_boost_icon or self.chance_icon_s0

    def draw_dialog(self, content, icons=None):
        gw=self.game_surf.get_width()
        gh=self.game_surf.get_height()
        #kích thước hộp tính từ đường chéo màn hình để tỉ lệ đúng ở mọi độ phân giải
        box_diag=math.sqrt(gw**2+gh**2)*0.52
        box_w=int(box_diag*16/math.sqrt(16**2+9**2))
        box_h=int(box_diag*9/math.sqrt(16**2+9**2))
        box_w=min(box_w, int(gw*0.9))
        box_h=min(box_h, int(gh*0.9))
        cx=gw//2
        cy=gh//2
        rect=pygame.Rect(cx-box_w//2, cy-box_h//2, box_w, box_h)
        pad=int(box_w*0.13)
        pad_v=int(box_h*0.18)
        max_text_w=box_w-pad*2
        #vẽ ảnh hộp thoại hoặc hình chữ nhật màu giấy da nếu thiếu ảnh
        if self.dialogue_box_img is not None:
            scaled=pygame.transform.smoothscale(self.dialogue_box_img, (box_w, box_h))
            self.game_surf.blit(scaled, rect.topleft)
        else:
            pygame.draw.rect(self.game_surf, (235,228,220), rect, border_radius=10)
            pygame.draw.rect(self.game_surf, (180,168,155), rect, width=2, border_radius=10)

        #giới hạn vùng vẽ vào content_rect để chữ không tràn ra ngoài padding
        content_rect=pygame.Rect(rect.left+pad, rect.top+pad_v, box_w-pad*2, box_h-pad_v*2)
        self.game_surf.set_clip(content_rect)

        #thiết lập font và chiều cao dòng
        fds=self.font_dialog_small or self.font_dialog or self.font
        fdl=self.font_dialog_large or self.font_dialog or self.font
        lh=fds.get_height()+2
        lh_large=fdl.get_height()+4
        sep=2

        #bảng màu cho dialog fate (quote/speaker/effect) và dialog thường (header/body)
        DARK_RED=(160,30,30)
        COL_QUOTE=(202,117,66)
        COL_SPEAKER=(187,133,61)
        COL_EFFECT=(138,69,51)

        #thông số hàng icon (chiều cao = 0 khi không có icon)
        icons=[i for i in (icons or []) if i is not None]
        icon_size=int(lh_large*0.6) if icons else 0
        icon_gap=3 if icons else 0
        icon_row_h=icon_size+sep if icons else 0

        ty=0

        #vẽ một dòng văn bản tại vị trí ty hiện tại rồi tăng ty
        def blit_line(font, text, color, line_h=None, x_center=True, x_right=None):
            nonlocal ty
            lbl=font.render(text, True, color)
            if x_right is not None:
                self.game_surf.blit(lbl, (x_right-lbl.get_width(), ty))
            elif x_center:
                self.game_surf.blit(lbl, (cx-lbl.get_width()//2, ty))
            ty+=(line_h or lh)

        #vẽ tất cả icon xếp hàng ngang giữa rồi tăng ty
        def blit_icons():
            nonlocal ty
            if not icons:
                return
            total_icon_w=len(icons)*icon_size+(len(icons)-1)*icon_gap
            ix=cx-total_icon_w//2
            for ic in icons:
                si=pygame.transform.smoothscale(ic, (icon_size, icon_size))
                self.game_surf.blit(si, (ix, ty))
                ix+=icon_size+icon_gap
            ty+=icon_row_h

        header=content.get("header") if isinstance(content, dict) else None

        #nhánh fate dialog: content có key "quote", "speaker", "effect"
        if isinstance(content, dict) and "quote" in content:
            quote_lines=self._wrap_text(content["quote"], fds, max_text_w)
            speaker_lines=self._wrap_text(content["speaker"], fds, max_text_w)
            effect_lines=self._wrap_text(content["effect"], fdl, max_text_w)
            header_lines=self._wrap_text(header, fdl, max_text_w) if header else []
            #tính tổng chiều cao để căn giữa dọc toàn bộ khối
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
                blit_line(fds, line, COL_QUOTE)
            ty+=sep
            #tên speaker căn phải
            for line in speaker_lines:
                blit_line(fds, line, COL_SPEAKER, x_center=False, x_right=content_rect.right)
            ty+=sep
            for line in effect_lines:
                blit_line(fdl, line, COL_EFFECT, line_h=lh_large)
        else:
            #nhánh dialog thường: content có key "header" và "lines" (hoặc list thuần)
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

        self.game_surf.set_clip(None)

    def show_dialog_and_wait(self, content, icons=None):
        #vẽ trạng thái board hiện tại phía sau, sau đó overlay dialog lên trên
        self.draw_board()
        self.draw_sidebar()
        self.draw_dialog(content, icons)
        pygame.display.flip()
        #chặn cho đến khi click chuột; vẽ lại khi resize để layout đúng
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
        #khôi phục board sạch sau khi đóng dialog
        self.screen_surf.fill(self.background_color["screen"])
        self.game_surf.fill(self.background_color["game"])
        self.draw_board()
        self.draw_sidebar()
        pygame.display.flip()

    ###DRAW METHODS###

    def draw_rounded_square(self, x, y, color, size=None):
        #hình fallback cho block TIME khi chưa load được icon
        if size is None:
            size=self.circle_radius
        diameter=int(size*self.circle_scale*2)
        if diameter<2:
            return
        half=diameter//2
        border_radius=max(3, diameter//4)
        rect=pygame.Rect(x-half, y-half, diameter, diameter)
        pygame.draw.rect(self.board_surf, color, rect, border_radius=border_radius)
        #viền tối khớp màu nền board
        pygame.draw.rect(self.board_surf, (31,39,72), rect, width=2, border_radius=border_radius)

    def draw_parallelogram(self, x, y, color, size=None):
        #hình fallback cho block BOOST (nghiêng để phân biệt với ô thường)
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
        #viền sáng hơn dọc các cạnh tạo cảm giác nổi 3D
        highlight=tuple(min(255, c+60) for c in color)
        pygame.draw.polygon(self.board_surf, highlight, pts, 2)

    def draw_board(self, no_draw_pts=None):
        #lấp nửa trái bằng ảnh nền hoặc màu board đặc
        if self.board_area_bg_scaled is not None:
            self.game_surf.blit(self.board_area_bg_scaled, (0, 0))
        else:
            self.board_surf.fill(self.background_color["board"])
        #vẽ từng ô có nội dung; bỏ qua no_draw_pts (animation tự vẽ riêng các ô đó)
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                if no_draw_pts is not None and (col, row) in no_draw_pts:
                    continue
                color_index=self.board.board[row][col]
                if color_index<0:
                    continue
                pos=self.board_pos_to_win_pos(col, row)
                self.draw_tile(pos[0], pos[1], color_index)

    def draw_buttons(self, texts, y, y_separation, surface_name):
        #size each button to fit its label text plus padding
        surface=getattr(self, f"{surface_name}_surf")
        height=(self.char_height+self.char_sep_height)*3.5
        for text in texts:
            width=(len(text)+10)*self.char_width
            #center the button horizontally in the given surface
            x=(surface.get_width()-width)/2+surface.get_abs_offset()[0]
            y_abs=y+surface.get_abs_offset()[1]
            #derive callback name from button text ("NEW GAME" → new_game_clicked)
            button_name=text.lower().replace(' ', '_')
            self._draw_button(x, y_abs, width, height, text,
                              button_name, getattr(self, f"{button_name}_clicked"),
                              btn_img=self.menu_button_img,
                              text_y_offset=int(height*0.08))
            y+=height+(self.char_height+self.char_sep_height)*y_separation

    def draw_sidebar(self):
        #fill right panel with background image or solid color
        if self.board_bg_scaled is not None:
            self.sidebar_surf.blit(self.board_bg_scaled, (0, 0))
        else:
            self.sidebar_surf.fill(self.background_color["sidebar"])
        sw=self.sidebar_surf.get_width()
        sh=self.sidebar_surf.get_height()
        sx_off=self.sidebar_surf.get_abs_offset()[0]
        sy_off=self.sidebar_surf.get_abs_offset()[1]
        unit=self.char_height+self.char_sep_height
        pad=max(4, int(sw*0.07))

        #PAUSE + HINT buttons at the bottom of the sidebar
        btn_h=int(unit*3.5)
        btn_w=(sw-pad*3)//2
        btn_y=sh-int(sh*0.01)-btn_h
        icon_map={"pause": self.pause_img, "hint": self.hint_img}
        for i, (bname, btext) in enumerate((("pause","PAUSE"),("hint","HINT"))):
            bx=pad+i*(btn_w+pad)
            icon=icon_map[bname] or self.board_button_img
            label=btext if icon_map[bname] is None else ""
            self._draw_button(int(bx+sx_off), int(btn_y+sy_off),
                              int(btn_w), int(btn_h), label,
                              bname, getattr(self, f"{bname}_clicked"),
                              btn_img=icon)

        #HOBBY and CHANCE progress indicators (icon + count/limit label)
        icon_r=max(4, int(unit*0.75))
        ind_h=icon_r*2
        gap=max(2, int(unit*0.35))
        chance_top=btn_y-gap*2-ind_h
        hobby_top=chance_top-gap*3-ind_h

        #temporarily redirect board_surf to sidebar so draw_tile renders there
        orig_bsurf=self.board_surf
        self.board_surf=self.sidebar_surf
        for row_y, btype, count in (
            (hobby_top,  mainBoard.HOBBY,  self.hobby_count%20),
            (chance_top, mainBoard.CHANCE, self.chance_count%25),
        ):
            icon_cx=pad+icon_r
            icon_cy=row_y+ind_h//2
            #decorative frame around the block icon
            if self.block_frame_img is not None:
                fd_size=int(icon_r*2*1.3)
                fw,fh=self.block_frame_img.get_size()
                fs=min(fd_size/fw, fd_size/fh)
                fnw,fnh=int(fw*fs),int(fh*fs)
                fr=pygame.transform.smoothscale(self.block_frame_img, (fnw, fnh))
                self.sidebar_surf.blit(fr, (icon_cx-fnw//2, icon_cy-fnh//2))
            self.draw_tile(icon_cx, icon_cy, btype, icon_r)
            #count/limit label: shows progress within the current tier (mod resets at tier boundary)
            limit=20 if btype==mainBoard.HOBBY else 25
            feff=self.font_dialog_large or self.font
            lbl=feff.render(f"{count} / {limit}", True, (138,69,51))
            lbl_w,lbl_h=lbl.get_size()
            txt_x=icon_cx+icon_r+pad*2
            txt_y=icon_cy-lbl_h//2
            #optional stat box image behind the count label
            if self.stat_box_img is not None:
                box_w=int(lbl_w*2.0)
                box_h=int(lbl_h*2.2)
                bw_img,bh_img=self.stat_box_img.get_size()
                bs=min(box_w/bw_img, box_h/bh_img)
                bnw,bnh=int(bw_img*bs),int(bh_img*bs)
                box_scaled=pygame.transform.smoothscale(self.stat_box_img, (bnw, bnh))
                bx=txt_x+(lbl_w-bnw)//2
                by=txt_y+(lbl_h-bnh)//2
                self.sidebar_surf.blit(box_scaled, (bx, by))
                lbl_x=bx+(bnw-lbl_w)//2-int(bnw*0.03)
            else:
                lbl_x=txt_x
            self.sidebar_surf.blit(lbl, (lbl_x, txt_y))
        self.board_surf=orig_bsurf

        #Time counter plate + current time_count icon (frame 0–12)
        t_r=int(icon_r*1.6)
        t_cx=sw-pad-t_r-int(pad*1.5)
        bottom_y=chance_top+ind_h
        plate_size=int(t_r*2*1.9)
        if self.time_plate_img is not None:
            pw,ph=self.time_plate_img.get_size()
            ps=min(plate_size/pw, plate_size/ph)
            pnw,pnh=int(pw*ps),int(ph*ps)
            plate_scaled=pygame.transform.smoothscale(self.time_plate_img, (pnw, pnh))
            py=bottom_y-pnh
            self.sidebar_surf.blit(plate_scaled, (t_cx-pnw//2, py))
            t_cy=py+pnh//2
        else:
            t_cy=bottom_y-t_r
        idx=min(max(self.time_count, 0), 12)
        t_img=self.time_imgs[idx]
        if t_img is not None:
            tw,th=t_img.get_size()
            ts=min(t_r*2/tw, t_r*2/th)
            tnw,tnh=int(tw*ts),int(th*ts)
            t_scaled=pygame.transform.smoothscale(t_img, (tnw, tnh))
            self.sidebar_surf.blit(t_scaled, (t_cx-tnw//2, t_cy-tnh//2))

        #Time frame at the top: current life stage name + hourglass animation
        stage_names=["Newborn","Child","Teenager","Youth","Adult"]
        tf_margin=int(sh*0.02)
        tf_top=tf_margin
        tf_bottom=hobby_top-gap*2
        tf_h=max(40, tf_bottom-tf_top)
        tf_w=int(sw*0.85)
        tf_x=(sw-tf_w)//2
        if self.time_frame_img is not None:
            tf_scaled=pygame.transform.smoothscale(self.time_frame_img, (tf_w, tf_h))
            self.sidebar_surf.blit(tf_scaled, (tf_x, tf_top))
        fd=self.font_dialog_large or self.font_dialog or self.font
        stage_lbl=fd.render(stage_names[min(self.life_stage, 4)], True, (138,69,51))
        self.sidebar_surf.blit(stage_lbl, (tf_x+(tf_w-stage_lbl.get_width())//2,
                                           tf_top+int(tf_h*0.20)))
        hg_idx=min(self.time_count, 12)
        hg_img=self.hourglass_imgs[hg_idx] if hg_idx<len(self.hourglass_imgs) else None
        if hg_img is not None:
            hg_area_h=int(tf_h*0.60)
            hg_area_w=int(tf_w*0.70)
            hw,hh=hg_img.get_size()
            hs=min(hg_area_w/hw, hg_area_h/hh)
            hnw,hnh=int(hw*hs),int(hh*hs)
            hg_scaled=pygame.transform.smoothscale(hg_img, (hnw, hnh))
            hx=tf_x+(tf_w-hnw)//2
            hy=tf_top+tf_h-hnh-int(tf_h*0.06)
            self.sidebar_surf.blit(hg_scaled, (hx, hy))

    def draw_main_menu(self):
        self.game_surf.fill(self.background_color["game"])
        texts=["NEW GAME","PREFERENCES","ABOUT","EXIT"]
        if self.game_state==GameState.PAUSED:
            texts=["RESUME GAME"]+texts
        unit=self.char_height+self.char_sep_height
        btn_h=unit*3.5
        sep=unit*1.0
        total=len(texts)*btn_h+(len(texts)-1)*sep
        y=(self.game_surf.get_height()-total)/2
        self.draw_buttons(texts, y, 1.0, "game")

    def draw_ended(self):
        self.game_surf.fill(self.background_color["game"])
        y=(self.game_surf.get_height()-(self.char_height+self.char_sep_height)*6)/2
        text="GAME OVER"
        width=len(text)*self.char_width
        x=(self.game_surf.get_width()-width)/2
        label=self.font.render(text, True, self.widget_text_color)
        self.game_surf.blit(label, (x, y))
        y+=(self.char_height+self.char_sep_height)*4
        self.draw_buttons(("CONTINUE",), y, 0, "game")

    def draw_preferences(self):
        self.game_surf.fill(self.background_color["game"])
        y=(self.game_surf.get_height()-(self.char_height+self.char_sep_height)*12)/2
        height=self.char_height+self.char_sep_height
        texts=("Background music","Sound effects")
        text_width=max([len(t) for t in texts])*self.char_width
        spacing_width=3*self.char_width
        toggle_width=3*self.char_width
        width=text_width+spacing_width+toggle_width
        x_text=(self.game_surf.get_width()-width)/2
        x_toggle=x_text+text_width+spacing_width
        x_toggle_abs=x_toggle+self.game_surf.get_abs_offset()[0]
        for text in texts:
            label=self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x_text, y))
            y_abs=y+self.game_surf.get_abs_offset()[1]
            toggle_name=text.lower().replace(' ', '_')
            if toggle_name not in self.active_widgets:
                toggle=pygamew.Toggle(
                    self.screen_surf, int(x_toggle_abs), int(y_abs), int(toggle_width), int(height),
                    startOn=self.preferences.get(toggle_name, True),
                    onColour=(0,255,0),
                    offColour=(128,128,128),
                    handleOnColour=(0,128,0),
                    handleOffColour=(64,64,64)
                )
                self.active_widgets[toggle_name]=toggle
            self.active_widgets[toggle_name].draw()
            y+=(self.char_height+self.char_sep_height)*3
        y+=(self.char_height+self.char_sep_height)*4
        self.draw_buttons(("SAVE",), y, 0, "game")

    def draw_about(self):
        self.game_surf.fill(self.background_color["game"])
        y=(self.game_surf.get_height()-(self.char_height+self.char_sep_height)*10)/2
        for text in ("MATCH3PY","AUTHOR: TOMAS GONZALEZ ARAGON"):
            width=len(text)*self.char_width
            x=(self.game_surf.get_width()-width)/2
            label=self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x, y))
            y+=(self.char_height+self.char_sep_height)*4
        self.draw_buttons(("BACK",), y, 0, "game")

    def draw_screen(self):
        self.screen_surf.fill(self.background_color["screen"])
        if self.game_state==GameState.RUNNING:
            self.game_surf.fill(self.background_color["game"])
            self.draw_board()
            self.draw_sidebar()
        elif self.game_state in (GameState.MAINMENU, GameState.PAUSED):
            self.draw_main_menu()
        elif self.game_state==GameState.ENDED:
            self.draw_ended()
        elif self.game_state==GameState.PREFERENCES:
            self.draw_preferences()
        elif self.game_state==GameState.ABOUT:
            self.draw_about()

    ###UPDATE METHODS###

    def update_board(self):
        self.draw_board()
        pygame.display.flip()

    def update_sidebar(self):
        self.draw_sidebar()
        pygame.display.flip()

    def update_screen(self):
        self.active_widgets={}
        self.button_rects={}
        self.draw_screen()
        pygame.display.flip()

    ###CLICK HANDLERS###

    def new_game_clicked(self):
        self.board=mainBoard(6, 6, 3)
        self.hint=False
        self.pause=False
        self.life_stage=0
        self.hobby_state=0
        self.hobby_type=None
        self.chance_state=0
        self.chance_type=None
        self.time_count=0
        self.hobby_count=0
        self.chance_count=0
        self.philosopher_turns=0
        self.sage_turns=0
        self.prisoner_turns=0
        self.turn_taken=False #KVan sua
        self.random_wheel_result=None
        self.failedbefore=False
        self.game_state=GameState.RUNNING
        self.start_music()
        self.resize_surfaces()
        self.update_screen()

    def hint_clicked(self):
        self.hint=True

    def pause_clicked(self):
        self.pause=True

    def resume_game_clicked(self):
        self.game_state=GameState.RUNNING
        self.start_music()
        self.update_screen()

    def continue_clicked(self):
        self.game_state=GameState.MAINMENU
        self.update_screen()

    def preferences_clicked(self):
        self.prev_state=self.game_state
        self.game_state=GameState.PREFERENCES
        self.update_screen()

    def save_clicked(self):
        for s in ("background_music","sound_effects"):
            self.preferences[s]=self.active_widgets[s].value
        with open(self.preferences_filename, 'w') as f:
            json.dump(self.preferences, f)
        self.game_state=self.prev_state
        self.update_screen()

    def about_clicked(self):
        self.prev_state=self.game_state
        self.game_state=GameState.ABOUT
        self.update_screen()

    def back_clicked(self):
        self.game_state=self.prev_state
        self.update_screen()

    def exit_clicked(self):
        pygame.quit()
        exit()

    ###HELPER METHODS###

    def win_pos_to_board_pos(self, win_pos_x, win_pos_y, relative_to_window=False):
        if relative_to_window:
            win_pos_x-=self.board_surf.get_abs_offset()[0]
            win_pos_y-=self.board_surf.get_abs_offset()[1]
        col_w=self.board_surf.get_width()/self.board.cols
        row_h=self.board_surf.get_height()/self.board.rows
        board_pos_x=(win_pos_x-col_w/2)/col_w
        board_pos_y=(win_pos_y-row_h/2)/row_h
        return (int(round(board_pos_x)), int(round(board_pos_y)))

    def board_pos_to_win_pos(self, board_pos_x, board_pos_y, relative_to_window=False):
        col_w=self.board_surf.get_width()/self.board.cols
        row_h=self.board_surf.get_height()/self.board.rows
        win_pos_x=board_pos_x*col_w+col_w/2
        win_pos_y=board_pos_y*row_h+row_h/2
        if relative_to_window:
            win_pos_x+=self.board_surf.get_abs_offset()[0]
            win_pos_y+=self.board_surf.get_abs_offset()[1]
        return (int(win_pos_x), int(win_pos_y))

    def point_inside_circle(self, point, circle_center, r):
        x,y=point
        c_x,c_y=circle_center
        return (x-c_x)**2+(y-c_y)**2<r**2

    def get_num_vertical_points(self, points):
        points_in_line=dict()
        for (col, _) in points:
            points_in_line[col]=points_in_line.get(col, 0)+1
        return max(points_in_line.values())

    def play_sound(self, sound):
        if self.preferences.get("sound_effects", True) and sound in self.sounds:
            pygame.mixer.Sound.play(self.sounds[sound])

    def start_music(self):
        if self.preferences.get("background_music", True):
            try:
                pygame.mixer.music.play(-1, 0, 1000)
            except:
                pass

    ###RESIZE###

    def resize_surfaces(self):
        sw,sh=self.screen_surf.get_size()
        gw,gh=sw,sh
        self.game_surf=self.screen_surf.subsurface((0, 0, gw, gh))
        left_w=int(gw*0.6)
        board_side=min(left_w, gh)
        board_top=(gh-board_side)//2
        self.board_surf=self.game_surf.subsurface((0, board_top, board_side, board_side))
        if self.board is not None:
            self.circle_radius=board_side/(self.board.cols*2)
        self.sidebar_surf=self.game_surf.subsurface((left_w, 0, gw-left_w, gh))
        if self.board_bg is not None:
            self.board_bg_scaled=pygame.transform.smoothscale(self.board_bg, (gw-left_w, gh))
        if self.board_area_bg is not None:
            self.board_area_bg_scaled=pygame.transform.smoothscale(self.board_area_bg, (left_w, gh))
        self.font_size=self.min_font_size*gw/self.starting_width
        self.char_width=self.min_char_width*gw/self.starting_width
        self.char_height=self.min_char_height*gh/self.starting_height
        self.char_sep_height=self.min_char_sep_height*gh/self.starting_height
        self.font=pygame.font.SysFont("monospace", int(self.font_size))
        self.font.set_bold(True)
        self.font_italic=pygame.font.SysFont("monospace", int(self.font_size))
        self.font_italic.set_italic(True)
        dialog_size=max(12, int(self.font_size*0.58))
        dialog_size_large=max(16, int(self.font_size*0.76))
        dialog_size_small=max(10, int(self.font_size*0.40))
        _font_path="media/font/RobotikaPixelGreek-nAWJR.otf"
        if os.path.isfile(_font_path):
            self.font_dialog=pygame.font.Font(_font_path, dialog_size)
            self.font_dialog_italic=pygame.font.Font(_font_path, dialog_size)
            self.font_dialog_large=pygame.font.Font(_font_path, dialog_size_large)
            self.font_dialog_small=pygame.font.Font(_font_path, dialog_size_small)
        else:
            self.font_dialog=pygame.font.SysFont("segoeui", dialog_size)
            self.font_dialog_italic=pygame.font.SysFont("segoeui", dialog_size)
            self.font_dialog_large=pygame.font.SysFont("segoeui", dialog_size_large)
            self.font_dialog_small=pygame.font.SysFont("segoeui", dialog_size_small)
        self.font_dialog_italic.set_italic(True)
        self.font_dialog_small.set_italic(True)
        self.font_italic.set_italic(True)
        self.active_widgets={}
        self._icon_cache={}

    ###ANIMATE METHODS###

    def animate_swap(self, board_point1, board_point2):
        self.play_sound("swap")
        board_points=(board_point1, board_point2)
        win_points=(list(self.board_pos_to_win_pos(*board_points[0])),
                    list(self.board_pos_to_win_pos(*board_points[1])))
        target_dist=(
            [win_points[1][0]-win_points[0][0], win_points[1][1]-win_points[0][1]],
            [win_points[0][0]-win_points[1][0], win_points[0][1]-win_points[1][1]],
        )
        curr_pos=[list(win_points[0]), list(win_points[1])]
        curr_ani_time=0
        ani_time_start=pygame.time.get_ticks()
        while curr_pos[0]!=win_points[1] or curr_pos[1]!=win_points[0]:
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points=(list(self.board_pos_to_win_pos(*board_points[0])),
                            list(self.board_pos_to_win_pos(*board_points[1])))
                target_dist=(
                    [win_points[1][0]-win_points[0][0], win_points[1][1]-win_points[0][1]],
                    [win_points[0][0]-win_points[1][0], win_points[0][1]-win_points[1][1]],
                )
            self.draw_board(no_draw_pts=board_points)
            curr_ani_time=pygame.time.get_ticks()-ani_time_start
            for p_i in reversed(range(2)):
                src_pos=win_points[p_i]
                dst_pos=win_points[int(not p_i)]
                curr_dist=(target_dist[p_i][0]*curr_ani_time/self.swap_ani_time,
                           target_dist[p_i][1]*curr_ani_time/self.swap_ani_time)
                curr_pos[p_i]=[src_pos[0]+curr_dist[0], src_pos[1]+curr_dist[1]]
                curr_pos[p_i]=[int(curr_pos[p_i][0]), int(curr_pos[p_i][1])]
                for i in range(2):
                    dir=dst_pos[i]-src_pos[i]
                    if (dir<0 and curr_pos[p_i][i]<dst_pos[i]) or (dir>0 and curr_pos[p_i][i]>dst_pos[i]):
                        curr_pos[p_i][i]=dst_pos[i]
                color_index=self.board.board[board_points[p_i][1]][board_points[p_i][0]]
                if color_index<0:
                    continue
                self.draw_tile(curr_pos[p_i][0], curr_pos[p_i][1], color_index)
            pygame.display.flip()

    def animate_clear(self, board_points, no_more_moves=False):
        self.play_sound("match")
        win_points=[self.board_pos_to_win_pos(*p) for p in board_points]
        curr_transparency=255
        curr_size=self.circle_radius
        curr_ani_time=0
        ani_time_start=pygame.time.get_ticks()
        clear_ani_time=self.clear_ani_time*(5 if no_more_moves else 1)
        while curr_transparency!=0 or curr_size!=0:
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points=[self.board_pos_to_win_pos(*p) for p in board_points]
            self.draw_board(no_draw_pts=board_points)
            curr_ani_time=pygame.time.get_ticks()-ani_time_start
            curr_transparency=int(255*(1-curr_ani_time/clear_ani_time))
            if curr_transparency<0:
                curr_transparency=0
            curr_size=int(self.circle_radius*(1-curr_ani_time/clear_ani_time))
            if curr_size<0:
                curr_size=0
            for i, p in enumerate(board_points):
                color_index=self.board.board[p[1]][p[0]]
                if color_index<0:
                    continue
                self.draw_tile(win_points[i][0], win_points[i][1], color_index, curr_size)
            if no_more_moves:
                texts=("NO MORE MOVES","REGENERATING BOARD")
                width=(max([len(t) for t in texts])+4)*self.char_width
                height=(math.ceil(self.char_height)+math.ceil(self.char_sep_height))*2
                x=(self.board_surf.get_width()-width)/2+self.board_surf.get_abs_offset()[0]
                y=(self.board_surf.get_height()-height*2)/2+self.board_surf.get_abs_offset()[1]
                for text in texts:
                    btn=pygamew.Button(
                        self.screen_surf, x, y, width, height,
                        text=text, textColour=(32,255,32), font=self.font,
                        colour=self.background_color["game"],
                        hoverColour=self.background_color["game"],
                        pressedColour=self.background_color["game"]
                    )
                    btn.draw()
                    y+=height
            pygame.display.flip()

    def animate_shift_down(self, shifted_bp, num_vertical_points, src_pts=None):
        board_points_dst=shifted_bp
        board_points_src=src_pts if src_pts is not None else [(x, y-1) for (x, y) in board_points_dst]
        win_points_dst=[list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
        win_points_src=[list(self.board_pos_to_win_pos(*p)) for p in board_points_src]
        color_indices=[self.board.board[y][x] for (x, y) in board_points_dst]
        curr_pos=[[x, y] for (x, y) in win_points_src]
        ani_time=self.shift_down_ani_time/min(num_vertical_points, 2)
        curr_ani_time=0
        ani_time_start=pygame.time.get_ticks()
        while any([curr_pos[i]!=win_points_dst[i] for i in range(len(curr_pos))]):
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points_dst=[list(self.board_pos_to_win_pos(*p)) for p in board_points_dst]
                win_points_src=[list(self.board_pos_to_win_pos(*p)) for p in board_points_src]
            self.draw_board(no_draw_pts=board_points_src+board_points_dst)
            curr_ani_time=pygame.time.get_ticks()-ani_time_start
            for p_i in range(len(curr_pos)):
                src_pos=win_points_src[p_i]
                dst_pos=win_points_dst[p_i]
                target_dist=((dst_pos[0]-src_pos[0]), (dst_pos[1]-src_pos[1]))
                curr_dist=(target_dist[0]*curr_ani_time/ani_time, target_dist[1]*curr_ani_time/ani_time)
                curr_pos[p_i]=[src_pos[0]+curr_dist[0], src_pos[1]+curr_dist[1]]
                curr_pos[p_i]=[int(curr_pos[p_i][0]), int(curr_pos[p_i][1])]
                for i in range(2):
                    dir=dst_pos[i]-src_pos[i]
                    if (dir<0 and curr_pos[p_i][i]<dst_pos[i]) or (dir>0 and curr_pos[p_i][i]>dst_pos[i]):
                        curr_pos[p_i][i]=dst_pos[i]
                color_index=color_indices[p_i]
                if color_index<0:
                    continue
                self.draw_tile(curr_pos[p_i][0], curr_pos[p_i][1], color_index)
            pygame.display.flip()

    def animate_hint(self, board_point1, board_point2):
        self.play_sound("hint")
        board_points=(board_point1, board_point2)
        win_points=[list(self.board_pos_to_win_pos(*board_points[0])),
                    list(self.board_pos_to_win_pos(*board_points[1]))]
        SHAKE_DURATION=1500
        AMPLITUDE=max(4, int(self.circle_radius*0.18))
        FREQ=18.0
        ani_time_start=pygame.time.get_ticks()
        while True:
            curr_ani_time=pygame.time.get_ticks()-ani_time_start
            if curr_ani_time>SHAKE_DURATION:
                break
            if self.process_events():
                self.screen_surf.fill(self.background_color["screen"])
                self.game_surf.fill(self.background_color["game"])
                self.draw_sidebar()
                win_points=[list(self.board_pos_to_win_pos(*board_points[0])),
                            list(self.board_pos_to_win_pos(*board_points[1]))]
            self.draw_board(no_draw_pts=board_points)
            t=curr_ani_time/1000.0
            decay=max(0.0, 1.0-t/(SHAKE_DURATION/1000.0))
            shake_x=int(math.sin(t*FREQ*2*math.pi)*AMPLITUDE*decay)
            shake_y=int(math.sin(t*FREQ*2*math.pi*1.3+1.0)*AMPLITUDE*0.4*decay)
            for p_i in range(2):
                color_index=self.board.board[board_points[p_i][1]][board_points[p_i][0]]
                if color_index<0:
                    continue
                wx=win_points[p_i][0]+shake_x*(1 if p_i==0 else -1)
                wy=win_points[p_i][1]+shake_y
                self.draw_tile(wx, wy, color_index)
            pygame.display.flip()
        self.update_board()

    ###GAME LOGIC###

    def endings(self, call_type):
        if call_type==0:
            self.show_dialog_and_wait(self.DIALOG_LINES[call_type][self.hobby_state][self.hobby_type],
                                      icons=[self._hobby_dialog_icon()])
        elif call_type==1:
            self.show_dialog_and_wait(self.DIALOG_LINES[call_type][self.random_wheel_result][self.chance_type],
                                      icons=[self._chance_dialog_icon()])
        else:
            if self.hobby_count>=50:
                self.show_dialog_and_wait(self.DIALOG_LINES[call_type][self.hobby_type],
                                          icons=[self._hobby_dialog_icon()])
            elif self.chance_count>=40:
                self.show_dialog_and_wait(self.DIALOG_LINES[call_type][self.chance_type],
                                          icons=[self._chance_dialog_icon()])
            else:
                lost_icons=[i for i in [self._chance_dialog_icon(), self._hobby_dialog_icon()] if i]
                self.show_dialog_and_wait(self.DIALOG_LINES[call_type][4],
                                          icons=lost_icons or None)
        self.game_ended=True

    def _apply_fate_event(self):
        sx,sy=self.board_pos_src
        event=random.choice(["philosopher","seer","sage","thief","brute","prisoner"])
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
        pre_shift_cols={}
        for y in range(self.board.rows):
            for x in range(self.board.cols):
                if self.board.board[y][x]!=self.board.empty:
                    pre_shift_cols.setdefault(x, []).append(y)
        while True:
            shifted=self.board.shift_down()
            real=[(x,y) for (x,y) in shifted if self.board.board[y][x]!=self.board.empty]
            if not real:
                break
        anim_dst,anim_src=[],[]
        for x,pre_rows in pre_shift_cols.items():
            post_rows=[y for y in range(self.board.rows) if self.board.board[y][x]!=self.board.empty]
            for i in range(len(pre_rows)):
                if pre_rows[i]!=post_rows[i]:
                    anim_src.append((x, pre_rows[i]))
                    anim_dst.append((x, post_rows[i]))
        num_empties_col={
            x: sum(1 for y in range(self.board.rows) if self.board.board[y][x]==self.board.empty)
            for x in range(self.board.cols)
        }
        populated=self.board.populate(rows=(0, self.board.rows),
                                      no_valid_play_check=False,
                                      no_match3_group_check=True)
        anim_dst+=populated
        anim_src+=[(x, y-num_empties_col.get(x, 1)) for (x, y) in populated]
        if anim_dst:
            self.animate_shift_down(anim_dst, 1, src_pts=anim_src)
        self.play_sound("drop")
        self.update_board()
        if event=="seer":
            chance_pts=[(c,r) for r in range(self.board.rows)
                        for c in range(self.board.cols)
                        if self.board.board[r][c]==mainBoard.CHANCE]
            if chance_pts:
                self.chance_count+=len(chance_pts)
                self.animate_clear(chance_pts)
                self.board.clear(chance_pts)
                pre_shift_cols={}
                for y in range(self.board.rows):
                    for x in range(self.board.cols):
                        if self.board.board[y][x]!=self.board.empty:
                            pre_shift_cols.setdefault(x, []).append(y)
                while True:
                    shifted=self.board.shift_down()
                    real=[(x,y) for (x,y) in shifted if self.board.board[y][x]!=self.board.empty]
                    if not real:
                        break
                anim_dst,anim_src=[],[]
                for x,pre_rows in pre_shift_cols.items():
                    post_rows=[y for y in range(self.board.rows) if self.board.board[y][x]!=self.board.empty]
                    for i in range(len(pre_rows)):
                        if pre_rows[i]!=post_rows[i]:
                            anim_src.append((x, pre_rows[i]))
                            anim_dst.append((x, post_rows[i]))
                num_empties_col={
                    x: sum(1 for y in range(self.board.rows) if self.board.board[y][x]==self.board.empty)
                    for x in range(self.board.cols)
                }
                populated=self.board.populate(rows=(0, self.board.rows),
                                              no_valid_play_check=False,
                                              no_match3_group_check=True)
                anim_dst+=populated
                anim_src+=[(x, y-num_empties_col.get(x, 1)) for (x, y) in populated]
                if anim_dst:
                    self.animate_shift_down(anim_dst, self.get_num_vertical_points(chance_pts), src_pts=anim_src)
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

    def animate_time_increment(self, gain):
        STEP_MS=80
        for _ in range(gain):
            self.time_count=min(self.time_count+1, 12)
            self.draw_board()
            self.draw_sidebar()
            pygame.display.flip()
            pygame.time.wait(STEP_MS)
            if self.time_count>=12:
                break

    def minigame(self):
        difficulty=int(self.failedbefore)
        if self.hobby_type==0:
            result=minigame.Tailor(self.board_surf, self.clock, difficulty).run() #KVan sua
        elif self.hobby_type==1:
            result=minigame.Fighter(self.board_surf, self.clock, difficulty).run()
        else:
            result=minigame.Minesweeper(self.board_surf, self.clock, difficulty).run()
        if result:
            self.endings(0)
        else:
            self.failedbefore=True
            self.hobby_state=3
            self.hobby_count=40
            if "hobby_state_3" in self.DIALOG_LINES and self.hobby_type is not None:
                self.show_dialog_and_wait(self.DIALOG_LINES["hobby_state_3"][self.hobby_type],
                                          icons=[self._hobby_dialog_icon()])

    def check_stat_thresholds(self, check_time=True):
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
        if self.chance_count>=50 and self.random_wheel_result is None:
            roll=random.random()
            result="gold" if roll<0.05 else "copper" if roll<0.15 else "blank"
            self.random_wheel_result=result if result!="blank" else None
            if self.random_wheel_result is not None:
                self.endings(1)

    ###EVENT PROCESSING###

    def running_process_events(self, events, **kwargs):
        update_display=False
        if not kwargs.get('mouse', False):
            return update_display
        for event in events:
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button!=1:
                    continue
                if self.mouse_state==MouseState.WAITING:
                    self.board_pos_src=self.win_pos_to_board_pos(*event.pos, True)
                    if self.board.out_of_bounds(*self.board_pos_src):
                        continue
                    circle_center=self.board_pos_to_win_pos(*self.board_pos_src, True)
                    if self.point_inside_circle(event.pos, circle_center, self.circle_radius*self.circle_scale):
                        self.mouse_state=MouseState.PRESSED
            elif event.type==pygame.MOUSEMOTION:
                if self.mouse_state==MouseState.PRESSED:
                    self.mouse_state=MouseState.MOVING
                if self.mouse_state==MouseState.MOVING:
                    board_pos_dst=list(self.win_pos_to_board_pos(*event.pos, True))
                    if list(self.board_pos_src)==board_pos_dst:
                        continue
                    for i in range(2):
                        if self.board_pos_src[i]-board_pos_dst[i]>1:
                            board_pos_dst[i]=self.board_pos_src[i]-1
                        elif self.board_pos_src[i]-board_pos_dst[i]<-1:
                            board_pos_dst[i]=self.board_pos_src[i]+1
                    if self.board.out_of_bounds(*board_pos_dst):
                        continue
                    swap_valid=False
                    for (x, y) in ((-1,0),(1,0),(0,-1),(0,1)):
                        if [self.board_pos_src[0]+x, self.board_pos_src[1]+y]==board_pos_dst:
                            swap_valid=True
                            break
                    if not swap_valid:
                        self.mouse_state=MouseState.WAITING
                        continue
                    swap_valid=self.board.is_swap_valid(self.board_pos_src, board_pos_dst)
                    self.animate_swap(self.board_pos_src, tuple(board_pos_dst))
                    self.board.swap(self.board_pos_src, board_pos_dst)
                    if not swap_valid:
                        self.animate_swap(tuple(board_pos_dst), self.board_pos_src)
                        self.board.swap(board_pos_dst, self.board_pos_src)
                    else: #KVan sua
                        self.turn_taken=True #KVan sua
                    self.mouse_state=MouseState.WAITING
            elif event.type==pygame.MOUSEBUTTONUP:
                if event.button!=1:
                    continue
                if self.mouse_state==MouseState.PRESSED:
                    sx,sy=self.board_pos_src
                    if self.board.board[sy][sx]==mainBoard.FATE:
                        self._apply_fate_event()
                    self.mouse_state=MouseState.WAITING
                elif self.mouse_state==MouseState.MOVING:
                    self.mouse_state=MouseState.WAITING
        return update_display

    def preferences_process_events(self, events, **_):
        self.active_widgets["background_music"].listen(events)
        self.active_widgets["sound_effects"].listen(events)
        self.draw_screen()
        return True

    def process_events(self, fps=-1, **kwargs):
        if fps<0:
            fps=self.ani_fps
        self.clock.tick(fps)
        events=pygame.event.get()
        for event in events:
            if event.type==pygame.VIDEORESIZE:
                self.resize_surfaces()
                return True
            elif event.type==pygame.QUIT:
                pygame.quit()
                exit()
        gs=self.game_state.name.lower()
        try:
            func=getattr(self, f"{gs}_process_events")
        except AttributeError:
            func=None
        update_display=False
        if func is not None:
            update_display=func(events, **kwargs)
        for widget in self.active_widgets.values():
            if type(widget)!=pygamew.Button:
                widget.listen(events)
        for event in events:
            if event.type==pygame.MOUSEBUTTONUP and event.button==1:
                for rect, callback in self.button_rects.values():
                    if rect.collidepoint(event.pos):
                        callback()
                        break
        if update_display:
            pygame.display.flip()
        return False

    ###MAIN LOOP###

    def running(self):
        groups=self.board.get_valid_groups()
        cascade_from_new=0
        populated_set=set()
        while len(groups)>0:
            #chi tang cascade_from_new khi group chua block moi duoc populate
            if populated_set and any(p in populated_set for g in groups for p in g):
                cascade_from_new+=1
                if cascade_from_new>2:
                    break
            points=[point for group in groups for point in group]
            time_raw,hobby_raw,chance_raw=0,0,0
            has_boost_time=has_boost_hobby=has_boost_chance=False
            for (cx,cy) in points:
                bv=self.board.board[cy][cx]
                if   bv==mainBoard.TIME:         time_raw+=1
                elif bv==mainBoard.BOOST_TIME:   time_raw+=1;  has_boost_time=True
                elif bv==mainBoard.HOBBY:        hobby_raw+=1
                elif bv==mainBoard.BOOST_HOBBY:  hobby_raw+=1; has_boost_hobby=True
                elif bv==mainBoard.CHANCE:       chance_raw+=1
                elif bv==mainBoard.BOOST_CHANCE: chance_raw+=1; has_boost_chance=True
            time_mult=2 if self.prisoner_turns>0 else 1
            hobby_mult=2 if self.sage_turns>0 else 1
            time_gain=0 if self.philosopher_turns>0 else int(time_raw*(1.5 if has_boost_time else 1))*time_mult
            time_pts=[(c,r) for (c,r) in points
                      if self.board.board[r][c] in (mainBoard.TIME, mainBoard.BOOST_TIME)]
            self.hobby_count=min(self.hobby_count+int(hobby_raw*(1.5 if has_boost_hobby else 1))*hobby_mult, 60)
            self.chance_count+=int(chance_raw*(1.5 if has_boost_chance else 1))
            spawns=self.board._special_block_spawn(groups)
            self.check_stat_thresholds(check_time=False)
            if self.game_ended:
                break
            self.draw_sidebar()
            self.animate_clear(points)
            self.board.clear(points)
            for (pos, btype) in spawns:
                sx,sy=pos
                if not self.board.out_of_bounds(sx, sy) and self.board.board[sy][sx]==self.board.empty:
                    self.board.board[sy][sx]=btype
            pre_shift_cols={}
            for y in range(self.board.rows):
                for x in range(self.board.cols):
                    if self.board.board[y][x]!=self.board.empty:
                        pre_shift_cols.setdefault(x, []).append(y)
            while True:
                shifted=self.board.shift_down()
                real=[(x,y) for (x,y) in shifted if self.board.board[y][x]!=self.board.empty]
                if not real:
                    break
            anim_dst,anim_src=[],[]
            for x,pre_rows in pre_shift_cols.items():
                post_rows=[y for y in range(self.board.rows) if self.board.board[y][x]!=self.board.empty]
                for i in range(len(pre_rows)):
                    if pre_rows[i]!=post_rows[i]:
                        anim_src.append((x, pre_rows[i]))
                        anim_dst.append((x, post_rows[i]))
            num_empties_col={
                x: sum(1 for y in range(self.board.rows) if self.board.board[y][x]==self.board.empty)
                for x in range(self.board.cols)
            }
            populated=self.board.populate(rows=(0, self.board.rows),
                                          no_valid_play_check=False,
                                          no_match3_group_check=True)
            anim_dst+=populated
            anim_src+=[(x, y-num_empties_col.get(x, 1)) for (x, y) in populated]
            if anim_dst:
                self.animate_shift_down(anim_dst, self.get_num_vertical_points(points), src_pts=anim_src)
            self.play_sound("drop")
            if time_gain>0 and time_pts:
                self.animate_time_increment(time_gain)
            elif time_gain>0:
                self.time_count=min(self.time_count+time_gain, 12)
            self.check_stat_thresholds(check_time=True)
            if self.game_ended:
                break
            populated_set=set(populated)
            groups=self.board.get_valid_groups()
        if getattr(self, 'turn_taken', False): #KVan sua
            if self.philosopher_turns>0: self.philosopher_turns-=1
            if self.sage_turns>0: self.sage_turns-=1
            if self.prisoner_turns>0: self.prisoner_turns-=1
            self.turn_taken=False #KVan sua
        play=self.board.find_a_play()
        if len(play)==0:
            self.animate_clear([(x,y) for y in range(self.board.rows) for x in range(self.board.cols)], True)
            self.board.clear()
            try:
                self.board.populate()
            except RecursionError:
                print("FATAL: Couldn't regenerate the board.")
                pygame.quit()
                exit(1)
            self.update_board()
        if self.hint:
            self.hint=False
            play=self.board.find_a_play()
            if len(play)>0:
                (swap_points, groups)=play
                self.animate_hint(*swap_points)
        if self.game_ended:
            self.game_ended=False
            self.game_state=GameState.ENDED
            self.play_sound("end")
            pygame.mixer.music.fadeout(1000)
            self.update_screen()
        elif self.pause:
            self.pause=False
            self.game_state=GameState.PAUSED
            self.music_pos=pygame.mixer.music.get_pos()
            pygame.mixer.music.fadeout(1000)
            self.update_screen()

    ###LOAD AND RUN###

    def load_icon(self):
        #UI chung: dialog box, các loại button, frame, stat box, time frame, hint/pause icon, time plate
        for attr, path in (
            ("dialogue_box_img",  "media/images/ui/dialogue_box.png"),
            ("button_img",        "media/images/ui/button.png"),
            ("menu_button_img",   "media/images/ui/menu_button.png"),
            ("board_button_img",  "media/images/ui/board_button.png"),
            ("block_frame_img",   "media/images/ui/frame.png"),
            ("stat_box_img",      "media/images/ui/stat_box.png"),
            ("time_frame_img",    "media/images/ui/time_frame.png"),
            ("hint_img",          "media/images/ui/hint.png"),
            ("pause_img",         "media/images/ui/pause.png"),
            ("time_plate_img",    "media/images/ui/time_plate.png"),
        ):
            if os.path.isfile(path):
                setattr(self, attr, pygame.image.load(path).convert_alpha())

        #Background: dùng convert() thay convert_alpha() vì không cần alpha channel
        if os.path.isfile("media/images/ui/backgroundA.png"):
            self.board_bg=pygame.image.load("media/images/ui/backgroundA.png").convert()
        if os.path.isfile("media/images/ui/backgroundB.png"):
            self.board_area_bg=pygame.image.load("media/images/ui/backgroundB.png").convert()

        #Time counter icon (Time 0.png → Time 12.png tương ứng time_count 0–12)
        for i in range(13):
            p=f"media/images/ui/Time {i}.png"
            if os.path.isfile(p):
                self.time_imgs[i]=pygame.image.load(p).convert_alpha()

        #Hobby block icon: state 0 chung, sau đó theo từng type (handicraft/military/forge) × state (1/2/3)
        #và boost icon tương ứng từng type × state (1/2), plus generic boost (state 0)
        if os.path.isfile("media/images/block/hobby_0.png"):
            self.hobby_icon_s0=pygame.image.load("media/images/block/hobby_0.png").convert_alpha()
        hobby_types=["handicraft","military","forge"]
        for t, tname in enumerate(hobby_types):
            for s, stage in enumerate(["1","2","3"]):
                p=f"media/images/block/hobby_{tname}{stage}.png"
                if os.path.isfile(p):
                    self.hobby_icons[t][s]=pygame.image.load(p).convert_alpha()
            for s, stage in enumerate(["1","2","3"]): #KVan sua
                p=f"media/images/block/hobby_{tname}{stage}_boost.png"
                if os.path.isfile(p):
                    self.hobby_boost_icons[t][s+1]=pygame.image.load(p).convert_alpha()
        if os.path.isfile("media/images/block/hobby_boost.png"):
            generic=pygame.image.load("media/images/block/hobby_boost.png").convert_alpha()
            for t in range(3):
                self.hobby_boost_icons[t][0]=generic

        #Chance block icon: state 0 chung, sau đó theo từng type (love/religious/mastermind)
        #và boost icon tương ứng từng type, plus generic boost
        if os.path.isfile("media/images/block/chance_0.png"):
            self.chance_icon_s0=pygame.image.load("media/images/block/chance_0.png").convert_alpha()
        chance_types=["love","religious","mastermind"]
        for t, tname in enumerate(chance_types):
            p=f"media/images/block/chance_{tname}.png"
            if os.path.isfile(p):
                self.chance_icons[t]=pygame.image.load(p).convert_alpha()
        if os.path.isfile("media/images/block/chance_boost.png"):
            self.chance_boost_icon=pygame.image.load("media/images/block/chance_boost.png").convert_alpha()
        for t, tname in enumerate(chance_types):
            p=f"media/images/block/chance_{tname}_boost.png"
            if os.path.isfile(p):
                self.chance_boost_icons[t]=pygame.image.load(p).convert_alpha()

        #Time block icon: index 0=time_0 (block thường), index 1=time_boost
        for i, path in enumerate(["media/images/block/time_0.png","media/images/block/time_boost.png"]):
            if os.path.isfile(path):
                self.time_icon[i]=pygame.image.load(path).convert_alpha()

        #Fate block icon
        if os.path.isfile("media/images/block/fate.png"):
            self.fate_icon=pygame.image.load("media/images/block/fate.png").convert_alpha()

        #Hourglass animation (0.png → 12.png tương ứng time_count 0–12 trong sidebar)
        self.hourglass_imgs=[]
        for i in range(13):
            p=f"media/images/ui/hourglass/{i}.png"
            if os.path.isfile(p):
                self.hourglass_imgs.append(pygame.image.load(p).convert_alpha())
            else:
                self.hourglass_imgs.append(None)

    def run(self):
        data=dict()
        try:
            with open(self.preferences_filename, 'r') as file:
                try:
                    data=json.load(file)
                    try:
                        jsonschema.validate(data, self.preferences_schema)
                    except jsonschema.ValidationError:
                        print(f"ERROR: In file {self.preferences_filename}: json doesn't conform to schema.")
                except json.JSONDecodeError:
                    print(f"ERROR: In file {self.preferences_filename}: json not valid.")
        except FileNotFoundError:
            pass
        self.preferences=data
        pygame.init()
        pygame.mixer.init()
        self.font=pygame.font.SysFont("monospace", int(self.font_size))
        self.font.set_bold(True)
        self.clock=pygame.time.Clock()
        icon=pygame.image.load("icon32x32.png")
        pygame.display.set_icon(icon)
        pygame.display.set_caption("MATCH3PY")
        os.environ['SDL_VIDEO_CENTERED']='1'
        display_info=pygame.display.Info()
        self.screen_surf=pygame.display.set_mode(
            (display_info.current_w, display_info.current_h), self.flags, vsync=1)
        self.load_icon()
        self.resize_surfaces()
        self.update_screen()
        if os.path.isfile(self.background_music_filename):
            pygame.mixer.music.load(self.background_music_filename)
        if os.path.isdir(self.sounds_dir):
            for filename in os.listdir(self.sounds_dir):
                sound_name=os.path.splitext(filename)[0]
                self.sounds[sound_name]=pygame.mixer.Sound(f"{self.sounds_dir}/{filename}")
        while True:
            if self.process_events(fps=self.main_loop_refresh_rate, mouse=True):
                self.update_screen()
            if self.game_state==GameState.RUNNING:
                self.running()
