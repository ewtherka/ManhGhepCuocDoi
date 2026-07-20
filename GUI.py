from Board import mainBoard
from match3_gui import Match3GUI, GameState, MouseState
from dialogues import DIALOG_LINES, ABOUT_TEXT
import json
import jsonschema
import math
import os
import random
import pygame
import minigame
import pygame_widgets as pygamew
from sys import exit

class mainGUI(Match3GUI):
    background_color = {
        "screen": (0, 0, 0),
        "game": (24, 24, 24),
        "board": (52, 56, 76),#doi mau board thanh xam dam
        "sidebar": (48, 48, 48),
    }
    hint_color = (255, 255, 255)
    widget_text_color = (255, 255, 255)
    starting_width = 640#base resolution
    starting_height = 480
    game_ratio = starting_width / starting_height
    board_scale = 9 / 10
    circle_scale = 18 / 20#scale de khong bi dinh chum
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
    preferences_schema = json.loads(preferences_schema)#chuyen string trong file json thanh dict de quan li pref
    media_dir = "media"#co the doi thanh dir khac neu can
    audio_dir = f"{media_dir}/audio"
    sounds_dir = f"{audio_dir}/sounds"
    music_dir = f"{audio_dir}/music"
    background_music_filename = f"{music_dir}/background_music.mp3"

    #dialog box
    DIALOG_LINES = DIALOG_LINES
    def __init__(self):
        #Board
        self.board=None
        self.screen_surf=None#canvas màn
        self.game_surf=None#canvas game chung
        self.board_surf=None#canvas game board
        self.sidebar_surf=None#canvas side board
        self.clock=None
        self.circle_radius=0
        self._icon_cache={}

        #Input cho chuot
        self.mouse_state=MouseState.WAITING
        self.board_pos_src=None#chua coord cua block dau tien click vao

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
        self.hobby_icons=[[None,None,None],[None,None,None],[None,None,None]]#3 type 4 state (state 0 o trne roi)
        self.hobby_boost_icons=[[None,None,None,None],[None,None,None,None],[None,None,None,None]]#3 type 4 state
        self.chance_icon_s0=None
        self.chance_icons=[None,None,None]#state 1 (3 type)
        self.chance_boost_icon=None
        self.chance_boost_icons=[None,None,None]#boost cho state 1 (3type)
        self.time_icon=[None,None]
        self.fate_icon=None

        #UI icon
        self.dialogue_box_img=None
        self.button_img=None
        self.menu_button_img=None
        self.board_button_img=None
        self.stat_box_img=None
        self.time_frame_img=None
        self.hint_img=None
        self.pause_img=None
        self.block_frame_img=None
        self.sidebar_bg=None#sidebar
        self.sidebar_bg_scaled=None
        self.board_area_bg=None#gameboard
        self.board_area_bg_scaled=None
        self.time_imgs=[None]*13
        self.time_plate_img=None
        self.character_imgs=[None]*5


    ###DRAWING METHODS###
    def draw_tile(self, x, y, color_index, size=None, ice_hp=0):
        B=mainBoard
        #mặc định dùng circle_radius khi không đang animate
        if size is None:
            size=self.circle_radius
        diameter=int(size*2*self.circle_scale)#diameter thuc te
        icon=None
        #HOBBY: chọn icon theo type và state hiện tại, lùi về state thấp hơn nếu thiếu (fallback)
        if color_index==B.HOBBY:
            if self.hobby_state>0 and self.hobby_type is not None:
                icon=self.hobby_icons[self.hobby_type][self.hobby_state-1]
                if icon is None and self.hobby_state>=2:
                    icon=self.hobby_icons[self.hobby_type][self.hobby_state-2]
                if icon is None:
                    icon=self.hobby_icons[self.hobby_type][0]
            if icon is None:
                icon=self.hobby_icon_s0

        #CHANCE: dùng icon theo type khi đã rand type, ngược lại dùng icon chung
        elif color_index==B.CHANCE:
            if self.chance_state>0 and self.chance_type is not None:
                icon=self.chance_icons[self.chance_type]
            if icon is None:
                icon=self.chance_icon_s0

        #BOOST_HOBBY: icon boost theo type va state, fallback về ô [0][0] (icon boost chung)
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

        #TIME/BOOST_TIME/FATE: mỗi loại có một icon cố định
        elif color_index==B.TIME:
            icon=self.time_icon[0]

        elif color_index==B.BOOST_TIME:
            icon=self.time_icon[1]

        elif color_index==B.FATE:
            icon=self.fate_icon

        if icon is not None and diameter>0:
            full_d=int(self.circle_radius*2*self.circle_scale)#diameter full khi nằm trên ô
            #kích thước đầy đủ: dùng cache để không smoothscale lại mỗi frame
            if diameter==full_d:
                key=(id(icon), diameter)#mot bo gom dia chi vung nho chua anh va diameter cua anh
                if key not in self._icon_cache:
                    self._icon_cache[key]=pygame.transform.smoothscale(icon, (diameter, diameter))
                scaled=self._icon_cache[key]
            #kích thước thu nhỏ (animation): bỏ qua cache, scale nhanh (scale nhanh hơn smoothscale)
            else:
                scaled=pygame.transform.scale(icon, (diameter, diameter))
            self.board_surf.blit(scaled, (x-diameter//2, y-diameter//2))

            # Vẽ khối băng
            if ice_hp > 0:
                ice_scale = 1.06 
                ice_diameter = int(diameter * ice_scale)
                
                ice_surf = pygame.Surface((ice_diameter, ice_diameter), pygame.SRCALPHA)
                ice_color = (0, 206, 209, 220)
                
                if ice_hp == 2:
                    pygame.draw.rect(ice_surf, ice_color, ice_surf.get_rect(), border_radius=8)
                    pygame.draw.rect(ice_surf, (255, 255, 255, 100), ice_surf.get_rect(), width=2, border_radius=8)
                
                elif ice_hp == 1:
                    half_rect = pygame.Rect(0, ice_diameter // 2, ice_diameter, ice_diameter // 2)
                    pygame.draw.rect(ice_surf, ice_color, half_rect, border_bottom_left_radius=8, border_bottom_right_radius=8)
                    pygame.draw.rect(ice_surf, (255, 255, 255, 100), half_rect, width=2, border_bottom_left_radius=8, border_bottom_right_radius=8)
                    
                self.board_surf.blit(ice_surf, (x - ice_diameter // 2, y - ice_diameter // 2))
            return
        
    

    def _draw_button(self, x_abs, y_abs, width, height, text, name, callback, btn_img=None, text_y_offset=0):

        fd=self.font_dialog
        bx,by=int(x_abs),int(y_abs)
        bw,bh=int(width),int(height)
        
        src=btn_img or self.button_img
        if src is not None:
            ow,oh=src.get_size()
            #tìm ratio để scale
            scale=min(bw/ow, bh/oh)#lay ratio min de vua khung
            nw,nh=int(ow*scale),int(oh*scale)
            bx+=(bw-nw)//2#cong them padding de canh giua
            by+=(bh-nh)//2
            bw,bh=nw,nh
            #tạo rect pygame
            rect=pygame.Rect(bx, by, bw, bh)
            img=pygame.transform.smoothscale(src, (bw, bh))
            self.screen_surf.blit(img, (bx, by))
        else:
            rect=pygame.Rect(bx, by, bw, bh)
            pygame.draw.rect(self.screen_surf, (64,64,64), rect, border_radius=4)
        
        if text and fd:
            lbl=fd.render(text, True, self.widget_text_color)#chuyen text sang img de tao label
            self.screen_surf.blit(lbl, (rect.x+(rect.w-lbl.get_width())//2,
                                        rect.y+(rect.h-lbl.get_height())//2+text_y_offset))#phải cộng thêm offset cho y vì nút có hình dạng đặc biệt
        #tạo button rect chứa tham chiếu hàm và rect
        self.button_rects[name]=(rect, callback)

    ###DIALOGUE METHODS###

    def _wrap_text(self, text, font, max_w):
        words=text.split()
        lines=[]
        current=""
        for word in words:
            #thêm thử vào test
            test=current+" "+word if current else word
            if font.size(test)[0]<=max_w:
                #nếu <= thì cho vào 1 hàng current
                current=test
            else:
                #nếu > thì ngắt và bỏ current (chưa thêm word) vào 1 hàng
                if current:
                    lines.append(current)
                current=word#lấy phần thừa cho vào dòng mới (hiện tại)
        if current:
            lines.append(current)
        return lines if lines else [""]

    def _hobby_dialog_icon(self):
        #chưa biết type: trả về icon chung
        if self.hobby_type is None:
            return self.hobby_icon_s0
        
        idx=min(max(self.hobby_state, 0), 3) #KVan sua
        for i in range(idx, -1, -1): #KVan sua
            ic=self.hobby_boost_icons[self.hobby_type][i]
            if ic is not None:
                return ic
        return self.hobby_icon_s0

    def _chance_dialog_icon(self):
        if self.chance_type is None:
            return self.chance_icon_s0
        #ưu tiên: boost theo type → icon theo type → boost chung → icon chung
        return self.chance_boost_icons[self.chance_type] or self.chance_icons[self.chance_type] or self.chance_boost_icon or self.chance_icon_s0

    def draw_dialog(self, content, icons=None):
        gw=self.game_surf.get_width()
        gh=self.game_surf.get_height()
        #kích thước hộp tính từ đường chéo màn hình để tỉ lệ đúng ở mọi độ phân giải
        box_diag=math.sqrt(gw**2+gh**2)*0.52#tính đường chéo bằng pytago, sau đó nhân với 52% để dialogue bõ k bị nhỏ quá
        box_w=int(box_diag*16/math.sqrt(16**2+9**2))#lấy (đường chéo hiện tại / đường chéo chuẩn 16:9).cạnh
        box_h=int(box_diag*9/math.sqrt(16**2+9**2))
        box_w=min(box_w, int(gw*0.9))
        box_h=min(box_h, int(gh*0.9))

        cx=gw//2#lấy center để gắn box vào
        cy=gh//2

        #x y của pygame tính từ trái qua, trên xuống nên từ tâm lùi qua trái 1 nửa chiều cao, lùi lên trên 1 nửa chiều rộng
        rect=pygame.Rect(cx-box_w//2, cy-box_h//2, box_w, box_h)
        pad=int(box_w*0.13)#padding 13%, 18% cho hợp với img
        pad_v=int(box_h*0.18)
        max_text_w=box_w-pad*2


        #vẽ ảnh hộp thoại hoặc hình chữ nhật màu giấy da nếu thiếu ảnh
        if self.dialogue_box_img is not None:
            scaled=pygame.transform.smoothscale(self.dialogue_box_img, (box_w, box_h))
            self.game_surf.blit(scaled, rect.topleft)
        else:
            pygame.draw.rect(self.game_surf, (235,228,220), rect, border_radius=10)
            pygame.draw.rect(self.game_surf, (180,168,155), rect, width=2, border_radius=10)

        #giới hạn vùng vẽ vào content_rect để chữ không tràn ra ngoài padding, lùi sang bên phải/dưới một khoảng pad
        content_rect=pygame.Rect(rect.left+pad, rect.top+pad_v, box_w-pad*2, box_h-pad_v*2)
        self.game_surf.set_clip(content_rect)#cắt xuống dưới nếu quá dài

        #thiết lập font và chiều cao dòng
        fds=self.font_dialog_small or self.font_dialog or self.font
        fdl=self.font_dialog_large or self.font_dialog or self.font
        lh=fds.get_height()+2 #set khoảng cách dòng là 2
        lh_large=fdl.get_height()+4 #4 cho large
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

        ty=0 #con trỏ dòng

        #vẽ một dòng văn bản tại vị trí ty hiện tại rồi tăng ty
        def blit_line(font, text, color, line_h=None, x_center=True, x_right=None):
            nonlocal ty #truy cập vào ty ở hàm ngoài
            lbl=font.render(text, True, color)
            if x_right is not None:#nếu căn lề phải
                self.game_surf.blit(lbl, (x_right-lbl.get_width(), ty))
            elif x_center:#nếu căn giữa
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


    def draw_board(self, no_draw_pts=None):
        #lấp nửa trái bằng ảnh nền hoặc màu board đặc
        if self.board_area_bg_scaled is not None:
            self.game_surf.blit(self.board_area_bg_scaled, (0, 0))#bỏ background cho game board vào
        else:
            self.board_surf.fill(self.background_color["board"])#fallback fill solid color
        #vẽ từng ô có nội dung; bỏ qua no_draw_pts (animation tự vẽ riêng các ô đó)
        for row in range(self.board.rows):
            for col in range(self.board.cols):
                if no_draw_pts is not None and (col, row) in no_draw_pts:
                    continue
                color_index=self.board.board[row][col]
                if color_index<0:
                    continue
                pos=self.board_pos_to_win_pos(col, row)
                ice_hp = self.board.ice_board[row][col] if hasattr(self.board, 'ice_board') else 0
                self.draw_tile(pos[0], pos[1], color_index, ice_hp=ice_hp)

    def draw_buttons(self, texts, y, y_separation, surface_name):
        #lấy canvas hiện tại
        surface=getattr(self, f"{surface_name}_surf")

        #chiều cao mặc định 3.5 unit
        height=(self.char_height+self.char_sep_height)*3.5

        for text in texts:
            width=(len(text)+10)*self.char_width
            #canh giua theo absolute coord
            x=(surface.get_width()-width)/2+surface.get_abs_offset()[0]
            y_abs=y+surface.get_abs_offset()[1]
            
            button_name=text.lower().replace(' ', '_')
            self._draw_button(x, y_abs, width, height, text,
                              button_name, getattr(self, f"{button_name}_clicked"),
                              btn_img=self.menu_button_img,
                              text_y_offset=int(height*0.08))
            
            #move cursor
            y+=height+(self.char_height+self.char_sep_height)*y_separation

    def draw_sidebar(self):
        
        if self.sidebar_bg_scaled is not None:
            self.sidebar_surf.blit(self.sidebar_bg_scaled, (0, 0))
        else:
            self.sidebar_surf.fill(self.background_color["sidebar"])
        sw=self.sidebar_surf.get_width()
        sh=self.sidebar_surf.get_height()
        #lay abs coord va unit
        sx_off=self.sidebar_surf.get_abs_offset()[0]
        sy_off=self.sidebar_surf.get_abs_offset()[1]
        unit=self.char_height+self.char_sep_height
        #set dynamic padding = 7% sidebar hoac 4
        pad=max(4, int(sw*0.07))

        #Ve nut
        btn_h=int(unit*3.5)
        btn_w=(sw-pad*3)//2

        btn_y=sh-int(sh*0.01)-btn_h

        icon_map={"pause": self.pause_img, "hint": self.hint_img}
        for i, (bname, btext) in enumerate((("pause","PAUSE"),("hint","HINT"))):
            bx=pad+i*(btn_w+pad)#tu dong dich qua
            icon=icon_map[bname] or self.board_button_img
            #fallback neu lo thieu icon
            label=btext if icon_map[bname] is None else ""
            self._draw_button(int(bx+sx_off), int(btn_y+sy_off),
                              int(btn_w), int(btn_h), label,
                              bname, getattr(self, f"{bname}_clicked"),
                              btn_img=icon)

        #ve indicator
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
            (chance_top, mainBoard.CHANCE, self.chance_count%30),
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
            limit=20 if btype==mainBoard.HOBBY else 30
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
                                           
        char_idx=min(self.life_stage, 4)
        c_img=self.character_imgs[char_idx]
        if c_img is not None:
            c_area_h=int(tf_h*0.65)
            c_area_w=int(tf_w*0.90)
            cw,ch=c_img.get_size()
            cs=min(c_area_w/cw, c_area_h/ch)
            cnw,cnh=int(cw*cs),int(ch*cs)
            c_scaled=pygame.transform.smoothscale(c_img, (cnw, cnh))
            cx=tf_x+(tf_w-cnw)//2
            cy=tf_top+int(tf_h*0.30)
            self.sidebar_surf.blit(c_scaled, (cx, cy))

        hg_idx=min(self.time_count, 12)
        hg_img=self.hourglass_imgs[hg_idx] if hg_idx<len(self.hourglass_imgs) else None
        if hg_img is not None:
            hg_area_h=int(tf_h*0.15)
            hg_area_w=int(tf_w*0.40)
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

        unit=self.char_height+self.char_sep_height#lấy height chữ và gap làm mốc
        btn_h=unit*3.5#chiều cao của nút
        sep=unit*1.0#khoảng cách giữa 2 nút
        total=len(texts)*btn_h+(len(texts)-1)*sep#tổng height ủa các nút
        y=(self.game_surf.get_height()-total)/2
        self.draw_buttons(texts, y, 1.0, "game")

    def draw_ended(self):
        self.game_surf.fill(self.background_color["game"])

        y=(self.game_surf.get_height()-(self.char_height+self.char_sep_height)*6)/2#canh giữa, gap 1.5, continue 3.5 còn game over 1
        
        text="GAME OVER"
        width=len(text)*self.char_width#căn giữa trục x
        x=(self.game_surf.get_width()-width)/2

        label=self.font.render(text, True, self.widget_text_color)#chuyển sang img r blit vào
        self.game_surf.blit(label, (x, y))

        y+=(self.char_height+self.char_sep_height)*4#dịch xuống để vẽ btn
        self.draw_buttons(("CONTINUE",), y, 0, "game")

    def draw_preferences(self):
        self.game_surf.fill(self.background_color["game"])
        y=(self.game_surf.get_height()-(self.char_height+self.char_sep_height)*12)/2
        height=self.char_height+self.char_sep_height
        texts=("Background music","Sound effects")
        text_width=max([len(t) for t in texts])*self.char_width
        spacing_width=3*self.char_width
        toggle_width=4*self.char_width
        width=text_width+spacing_width+toggle_width
        x_text=(self.game_surf.get_width()-width)/2
        x_toggle=x_text+text_width+spacing_width
        x_toggle_abs=x_toggle+self.game_surf.get_abs_offset()[0]
        
        for text in texts:
            label=self.font.render(text, True, self.widget_text_color)
            self.game_surf.blit(label, (x_text, y))
            y_abs=y+self.game_surf.get_abs_offset()[1]
            toggle_name=text.lower().replace(' ', '_')
            
            is_on = self.preferences.get(toggle_name, True) # dùng thay cho pgw toggle, tạo nút on off để click
            btn_text = "ON" if is_on else "OFF"
            
            def make_callback(name, current_state):
                return lambda: self.toggle_pref(name, current_state)
            
            self._draw_button(
                x_toggle_abs, y_abs, toggle_width * 2.25, height * 2.25, 
                btn_text, toggle_name, 
                make_callback(toggle_name, is_on),
                btn_img=self.time_plate_img
            )
            
            y+=(self.char_height+self.char_sep_height)*3
            
        y+=(self.char_height+self.char_sep_height)*4
        self.draw_buttons(("SAVE",), y, 0, "game")

    def toggle_pref(self, name, current_state):
        self.preferences[name] = not current_state
        self.update_screen()

    def draw_about(self):
        self.game_surf.fill(self.background_color["game"])
        
        max_w = self.game_surf.get_width() - 40
        all_lines = []
        
        for text in ABOUT_TEXT:
            for line in text.split('\n'):
                wrapped = self._wrap_text(line, self.font, max_w)
                all_lines.extend(wrapped)
            all_lines.append("")
            
        total_height = len(all_lines) * (self.char_height + self.char_sep_height) * 1.5
        y = (self.game_surf.get_height() - total_height) / 2
        
        for line in all_lines:
            if line:
                label = self.font.render(line, True, self.widget_text_color)
                base_x = (self.game_surf.get_width() - label.get_width()) / 2
                self.game_surf.blit(label, (base_x, y))
            y += (self.char_height + self.char_sep_height) * 1.5
            
        self.draw_buttons(("BACK",), y, 0, "game")

    def draw_screen(self):
        #clear toàn bộ trước khi vẽ
        self.screen_surf.fill(self.background_color["screen"])

        #nếu đang trong game
        if self.game_state==GameState.RUNNING:
            self.game_surf.fill(self.background_color["game"])
            self.draw_board()
            self.draw_sidebar()

        #nếu đang ở menu
        elif self.game_state in (GameState.MAINMENU, GameState.PAUSED):
            self.draw_main_menu()

        #nếu tạch
        elif self.game_state==GameState.ENDED:
            self.draw_ended()

        #nếu chọn pref
        elif self.game_state==GameState.PREFERENCES:
            self.draw_preferences()

        #nếu chọn abt
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
        self.board=mainBoard()
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
        sw,sh=self.screen_surf.get_size()#lấy size của canvas màn
        gw,gh=sw,sh

        self.game_surf=self.screen_surf.subsurface((0, 0, gw, gh))#canvas game = canvas màn

        left_w=int(gw*0.6)#lấy 60%
        board_side=min(left_w, gh)#lấy min để tạo thành hình vuông
        board_top=(gh-board_side)//2#lấy margin trên dưới

        self.board_surf=self.game_surf.subsurface((0, board_top, board_side, board_side))#vẽ từ 0->board size và từ top -> boardsize cho canvas board

        if self.board is not None:
            self.circle_radius=board_side/(self.board.cols*2)#bán kính = (boardsize/số cột(hàng))/2

        self.sidebar_surf=self.game_surf.subsurface((left_w, 0, gw-left_w, gh))#canvas sideboard từ left->hết và 0->hết

        if self.sidebar_bg is not None:
            self.sidebar_bg_scaled=pygame.transform.smoothscale(self.sidebar_bg, (gw-left_w, gh))#actually board bg là của sizebar...

        if self.board_area_bg is not None:
            self.board_area_bg_scaled=pygame.transform.smoothscale(self.board_area_bg, (left_w, gh))

        #scale font
        self.font_size=self.min_font_size*gw/self.starting_width
        self.char_width=self.min_char_width*gw/self.starting_width
        self.char_height=self.min_char_height*gh/self.starting_height
        self.char_sep_height=self.min_char_sep_height*gh/self.starting_height
        dialog_size=max(12, int(self.font_size*0.58))
        dialog_size_large=max(16, int(self.font_size*0.76))
        dialog_size_small=max(10, int(self.font_size*0.40))
        _font_path="media/font/RobotikaPixelGreek-nAWJR.otf"
        if os.path.isfile(_font_path):
            self.font=pygame.font.Font(_font_path, int(self.font_size))
            self.font_italic=pygame.font.Font(_font_path, int(self.font_size))
            self.font_dialog=pygame.font.Font(_font_path, dialog_size)
            self.font_dialog_italic=pygame.font.Font(_font_path, dialog_size)
            self.font_dialog_large=pygame.font.Font(_font_path, dialog_size_large)
            self.font_dialog_small=pygame.font.Font(_font_path, dialog_size_small)
        #nếu k có font trong folder thì fallback
        else:
            self.font=pygame.font.SysFont("monospace", int(self.font_size))
            self.font.set_bold(True)
            self.font_italic=pygame.font.SysFont("monospace", int(self.font_size))
            self.font_italic.set_italic(True)
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
                ice_hp = self.board.ice_board[board_points[p_i][1]][board_points[p_i][0]] if hasattr(self.board, 'ice_board') else 0
                self.draw_tile(curr_pos[p_i][0], curr_pos[p_i][1], color_index, ice_hp=ice_hp)
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
                ice_hp = self.board.ice_board[p[1]][p[0]] if hasattr(self.board, 'ice_board') else 0
                self.draw_tile(win_points[i][0], win_points[i][1], color_index, size=curr_size, ice_hp=ice_hp)
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
            self.draw_board(no_draw_pts=board_points_dst)
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

                dst_x, dst_y = board_points_dst[p_i]
                ice_hp = self.board.ice_board[dst_y][dst_x] if hasattr(self.board, 'ice_board') else 0
                self.draw_tile(curr_pos[p_i][0], curr_pos[p_i][1], color_index, ice_hp=ice_hp)
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
            elif self.chance_count>=48:
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
        
        while True:
            movements = self.board.resolve_gravity()
            anim_dst = list(movements.keys())
            anim_src = list(movements.values())

            num_empties_col={x: sum(1 for y in range(self.board.rows) if self.board.board[y][x]==self.board.empty) for x in range(self.board.cols)}
            populated = self.board.populate(rows=(0, self.board.rows), no_valid_play_check=False, no_match3_group_check=True)
            
            if not movements and not populated: break
                
            anim_dst += populated
            anim_src += [(x, y-num_empties_col.get(x, 1)) for (x, y) in populated]
            
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
                
            while True:
                # Rơi các khối cũ đã có trên bảng
                movements = self.board.resolve_gravity()
                anim_dst = list(movements.keys())
                anim_src = list(movements.values())
                # Duyệt xem số ô trống và sinh thêm khối mới
                num_empties_col={x: sum(1 for y in range(self.board.rows) if self.board.board[y][x]==self.board.empty) for x in range(self.board.cols)}
                populated = self.board.populate(rows=(0, self.board.rows), no_valid_play_check=False, no_match3_group_check=True)
                
                if not movements and not populated: break
                    
                anim_dst += populated
                anim_src += [(x, y-num_empties_col.get(x, 1)) for (x, y) in populated]
                
                if anim_dst:
                    self.animate_shift_down(anim_dst, self.get_num_vertical_points(chance_pts), src_pts=anim_src)
                self.play_sound("drop")
                self.update_board()
                
        elif event=="thief":
            floor=(self.hobby_count//20)*20
            self.hobby_count=max(self.hobby_count-5, floor)
            self.update_sidebar()
        elif event=="brute":
            floor=(self.chance_count//30)*30
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
            # Tạo băng mỗi khi đổi giai đoạn
            if hasattr(self.board, 'ice_board'):
                possible = [(c, r) for r in range(self.board.rows) for c in range(self.board.cols)
                            if self.board.board[r][c] not in (mainBoard.FATE, self.board.empty) 
                            and self.board.ice_board[r][c] == 0]
                
                num_freeze = min(random.randint(8,10), len(possible))
                for fx, fy in random.sample(possible, num_freeze):
                    self.board.ice_board[fy][fx] = 2

            self.update_board()

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
        new_chance=min(self.chance_count//30, 1)
        if new_chance>self.chance_state:
            if new_chance==1 and self.chance_type is None:
                self.chance_type=random.randint(0, 2)
            self.chance_state=new_chance
            if self.chance_state==1 and self.chance_type is not None:
                self.show_dialog_and_wait(self.DIALOG_LINES["chance_state_1"][self.chance_type],
                                          icons=[self._chance_dialog_icon()])
        if self.chance_count>=60 and self.random_wheel_result is None:
            result_spin = minigame.SlotMachine(self.board_surf, self.clock).run()
            self.random_wheel_result = result_spin if result_spin != "FAILED" else None
            
            if self.random_wheel_result is not None:
                self.endings(1)
            else:
                #đã fix: nếu thua thì đưa về lại đầu state 1;
                self.chance_count = 30

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
                    # ngăn swap khối băng
                    sx, sy = self.board_pos_src
                    dx, dy = board_pos_dst
                    if hasattr(self.board, 'ice_board') and (self.board.ice_board[sy][sx] > 0 or self.board.ice_board[dy][dx] > 0):
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
        return False

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
        groups=self.board.get_valid_groups()#kiểm tra và lấy ra các group  đã match
        populated_set=set()#khởi tạo set để lưu tọa độ các block sắp populate
        while len(groups)>0:
            points=[point for group in groups for point in group]

            # Giảm HP của băng
            if hasattr(self.board, 'ice_board'):
                ice_broken = set()
                for (cx, cy) in points:
                    for (dx, dy) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nx, ny = cx + dx, cy + dy
                        if not self.board.out_of_bounds(nx, ny):
                            if self.board.ice_board[ny][nx] > 0:
                                ice_broken.add((nx, ny))
                                
                for (nx, ny) in ice_broken:
                    self.board.ice_board[ny][nx] -= 1

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
            
            while True:
                movements = self.board.resolve_gravity()
                anim_dst = list(movements.keys())
                anim_src = list(movements.values())

                num_empties_col={x: sum(1 for y in range(self.board.rows) if self.board.board[y][x]==self.board.empty) for x in range(self.board.cols)}
                populated = self.board.populate(rows=(0, self.board.rows), no_valid_play_check=False, no_match3_group_check=True)
                
                if not movements and not populated: break
                    
                anim_dst += populated
                anim_src += [(x, y-num_empties_col.get(x, 1)) for (x, y) in populated]
                
                if anim_dst:
                    self.animate_shift_down(anim_dst, self.get_num_vertical_points(points), src_pts=anim_src)
                self.play_sound("drop")
                self.update_board()
            if time_gain>0 and time_pts:
                self.animate_time_increment(time_gain)
            elif time_gain>0:
                self.time_count=min(self.time_count+time_gain, 12)
            self.check_stat_thresholds(check_time=True)
            if self.game_ended:
                break

            self.update_board()

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
            self.sidebar_bg=pygame.image.load("media/images/ui/backgroundA.png").convert()
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
                
        #Character icons
        stage_names=["Newborn","Child","Teenager","Youth","Adult"]
        for i, name in enumerate(stage_names):
            p = f"media/images/character/{name}.png"
            if os.path.isfile(p):
                self.character_imgs[i] = pygame.image.load(p).convert_alpha()

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
        _font_path="media/font/RobotikaPixelGreek-nAWJR.otf"
        if os.path.isfile(_font_path):
            self.font=pygame.font.Font(_font_path, int(self.font_size))
        else:
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
