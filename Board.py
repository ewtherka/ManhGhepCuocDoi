from match3_board import Match3Board
import copy
import random

class mainBoard(Match3Board):
    TIME = 0
    HOBBY = 1
    CHANCE = 2

    FATE = 4
    
    BOOST_TIME = 5
    BOOST_HOBBY = 6
    BOOST_CHANCE = 7
    
    # Chuyển ID từ boost về base và ngược lại
    BASE = {5:0,6:1,7:2}
    BOOST = {0:5,1:6,2:7}

    def __init__(self, cols = 9, rows = 9, num_values = 3):
        '''
        Khởi tạo bảng game, kế thừa từ hàm gốc ở match3_board.
        '''
        self.ice_board = [[0 for _ in range(cols)] for _ in range(rows)]
        super().__init__(cols, rows, num_values)

    def  _get_block_type(self, block):
        '''
        Khi truyền vào khối boost, hệ thống sẽ trả về khối thường.
        Để hệ thống xác định khối thường và boost có thể match nhau.
        '''
        return  self.BASE.get(block, block)

    def _special_block_spawn(self, matched_group):
        '''
        Xét điều kiện để tạo thành special block (boost, destiny card)
        và vị trí block sau khi người chơi CLEAR
        '''
        # Tập hợp các special block (boost, destiny card) sẽ tạo
        special_block = []

        # Dò từng hàng/cột trong nhóm CLEAR được (nhóm khối T sẽ có 1 dòng 1 cột)
        for match_line in matched_group:
            n = len(match_line)

            # Nếu không tạo thành special block thì continue
            if n < 4: continue

            type = None
            for (col, row) in match_line:
                block = self.board[row][col]
                if block != self.empty: # Phòng TH block đã bị delete khỏi mảng (gọi sau clear)
                    type = self._get_block_type(block) # Tìm type của dòng được CLEAR
                    break
            
            if type is None: continue

            # Spawn special block ở ô dưới cùng bên phải của nhóm
            spawn_col, spawn_row = max(match_line, key=lambda p:(p[1],p[0]))

            special_block_type = self.FATE if n >= 5 else self.BOOST[type]

            special_block.append(((spawn_col, spawn_row), special_block_type))
        return special_block
    
    def populate(self, cols: tuple[int, int] = None, rows: tuple[int, int] = None, no_valid_play_check: bool = True, no_match3_group_check: bool = True, _retry_count: int = 0) -> list[tuple[int, int]]:
        '''
        Rải khối cho bảng chơi.
        '''
        populated = list()
        
        if cols is None:
            cols = (0, self.cols)
        if rows is None:
            rows = (0, self.rows)
            
        backup_board = copy.deepcopy(self.board)
        
        for row in range(rows[0], rows[1]):
            for col in range(cols[0], cols[1]):
                if self.board[row][col] == self.empty:
                    is_shadowed = False
                    for r in range(row - 1, -1, -1):
                        if self.ice_board[r][col] > 0:
                            is_shadowed = True
                            break
                    if is_shadowed:
                        continue 
                        
                    values_left = list(self.values)
                    
                    while len(values_left) > 0:
                        value = random.choice(values_left)
                        values_left.remove(value)
                        self.board[row][col] = value
                        
                        # Đảm bảo khối tạo ra không tạo thành match-3
                        if not no_match3_group_check or not self.filter_group(self.get_group(col, row)):
                            break
                            
                    if no_match3_group_check and len(values_left) == 0:
                        self.board = backup_board
                        if _retry_count > 10:
                            return self.populate(cols, rows, no_valid_play_check, False, 0)
                        else:
                            return self.populate(cols, rows, no_valid_play_check, no_match3_group_check, _retry_count + 1)
                            
                    populated.append((col, row))
                    
        if no_valid_play_check and len(self.find_a_play()) == 0:
            self.board = backup_board
            if _retry_count > 10:
                return []
            return self.populate(cols, rows, no_valid_play_check, no_match3_group_check, _retry_count + 1)
            
        return populated

    def clear(self, points: list[tuple[int, int]] = None) -> None:
        '''
        Đảm bảo khi khối bị xóa hoặc bàn cờ xáo trộn lại, băng cũng được xóa theo.
        '''
        super().clear(points)
        if points is None:
            self.ice_board = [[0 for _ in range(self.cols)] for _ in range(self.rows)]
        else:
            for (x, y) in points:
                self.ice_board[y][x] = 0

    def swap(self, point1: tuple[int, int], point2: tuple[int, int]) -> None:
        '''
        Đảm bảo mỗi khi game cần đổi chỗ 2 khối, lớp băng cũng được đổi chỗ theo.
        '''
        super().swap(point1, point2)
        (x1, y1), (x2, y2) = point1, point2
        self.ice_board[y1][x1], self.ice_board[y2][x2] = self.ice_board[y2][x2], self.ice_board[y1][x1]

    def get_group(self, col: int, row: int, group: list[tuple[int, int]] = None) -> list[tuple[int, int]]:
        '''
        Tìm các cụm block liền kề nhau. Trừ block FATE và block bị đóng băng.
        '''
        if self.board[row][col] == self.FATE or self.ice_board[row][col] > 0:
            return group if group is not None else []
        
        if group is None:
            group = list()
        
        for (offset_x, offset_y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neigh_x = col + offset_x
            neigh_y = row + offset_y

            if self.out_of_bounds(neigh_x, neigh_y):
                continue

            if self.board[neigh_y][neigh_x] == self.FATE or self.ice_board[neigh_y][neigh_x] > 0:
                continue

            if self._get_block_type(self.board[row][col]) != self._get_block_type(self.board[neigh_y][neigh_x]):
                continue

            if (neigh_x, neigh_y) in group:
                continue
             
            group.append((neigh_x, neigh_y))
            group = list(self.get_group(neigh_x, neigh_y, group))
        return group
    
    def is_swap_valid(self, point1: tuple[int, int], point2: tuple[int, int]) -> bool:
        '''
        Đảm bảo nước đi hợp lệ (trừ trường hợp swap khối ngoài bảng chơi và khối đóng băng).
        '''
        if self.out_of_bounds(*point1) or self.out_of_bounds(*point2):
            return False
        
        (x1, y1), (x2, y2) = point1, point2

        if self.ice_board[y1][x1] > 0 or self.ice_board[y2][x2] > 0:
            return False
        
        self.swap(point1, point2)
        groups = list()

        for (x, y) in (point1, point2):
            group = self.filter_group(self.get_group(x, y))
            if len(group) > 0:
                groups.append(group)

        self.swap(point1, point2)
        return len(groups) > 0
    
    def find_a_play(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], list[list[tuple[int, int]]]]:
        '''
        Tìm một nước đi hợp lệ để xác định bảng chơi vẫn còn đường đi và không cần trộn lại.
        '''
        for row in range(self.rows):
            for col in range(self.cols):
                
                if self.ice_board[row][col] > 0:
                    continue

                if self.board[row][col] == self.FATE:
                    return (((col, row), (col, row)), [])
                
                for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neigh_x = col + x
                    neigh_y = row + y

                    if self.out_of_bounds(neigh_x, neigh_y) or self.ice_board[neigh_y][neigh_x] > 0:
                        continue

                    if self._get_block_type(self.board[row][col]) == self._get_block_type(self.board[neigh_y][neigh_x]):
                        continue

                    swap_points = ((col, row), (neigh_x, neigh_y))
                    self.swap(*swap_points)

                    groups = list()

                    for (x, y) in swap_points:
                        group = self.filter_group(self.get_group(x, y))
                        if len(group) > 0:
                            groups.append(group)

                    self.swap(*swap_points)

                    if len(groups) > 0:
                        return (swap_points, groups)
        return tuple()
    
    def resolve_gravity(self) -> dict:
        '''
        Xử lý rơi khối thẳng và chéo.
        '''
        # Xác định vị trí ban đầu của khối
        initial_positions = {}
        for r in range(self.rows):
            for c in range(self.cols):
                if self.board[r][c] != self.empty:
                    initial_positions[(c, r)] = (c, r)
                    
        moved = True
        while moved:
            moved = False
            for row in reversed(range(0, self.rows - 1)):
                for col in range(self.cols):
                    if self.board[row + 1][col] == self.empty:
                        # Xử lí khối rơi thẳng đứng
                        if self.board[row][col] != self.empty and self.ice_board[row][col] == 0:
                            self.swap((col, row), (col, row + 1))
                            initial_positions[(col, row + 1)] = initial_positions.pop((col, row))
                            moved = True
                            continue
                        
                        # Xử lý khối bị chắn bởi băng (Rơi chéo)
                        is_shadowed = False
                        if self.ice_board[row][col] > 0:
                            is_shadowed = True
                        else:
                            for r in range(row - 1, -1, -1):
                                if self.ice_board[r][col] > 0:
                                    is_shadowed = True
                                    break
                                    
                        if is_shadowed:
                            dirs = [-1, 1]
                            random.shuffle(dirs)
                            
                            for dx in dirs:
                                nx = col + dx
                                if not self.out_of_bounds(nx, row) and self.board[row][nx] != self.empty and self.ice_board[row][nx] == 0:
                                    if self.board[row + 1][nx] != self.empty or self.ice_board[row + 1][nx] > 0:
                                        self.swap((nx, row), (col, row + 1))
                                        initial_positions[(col, row + 1)] = initial_positions.pop((nx, row))
                                        moved = True
                                        break
                                        
        return {dst: src for dst, src in initial_positions.items() if dst != src}
