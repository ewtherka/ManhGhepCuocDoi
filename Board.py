from match3_board import Match3Board

class mainBoard(Match3Board):
    TIME=0
    HOBBY=1
    CHANCE=2

    FATE=4
    
    BOOST_TIME=5
    BOOST_HOBBY=6
    BOOST_CHANCE=7

    BASE={5:0,6:1,7:2}
    BOOST={0:5,1:6,2:7}


    def __init__(self, cols=6, rows=6, num_values=3):
        super().__init__(cols, rows, num_values)

    def  _get_block_type(self,block):
        return  self.BASE.get(block,block)

    def _special_block_spawn(self,matched_group):
        special_block=[]#Tập hợp các special block (boost, destiny card) sẽ tạo
        for match_line in matched_group:#Dò từng hàng/cột trong nhóm CLEAR được (nhóm khối T sẽ có 1 dòng 1 cột)
            n=len(match_line)
            if n<4: continue
            type=None
            for (col,row) in match_line:
                block=self.board[row][col]
                if block!=self.empty:#phòng th block đã bị delete khỏi mảng (gọi sau clear)
                    type=self._get_block_type(block)#Tìm type của dòng được CLEAR
                    break
            if type is None: continue
            #spawn o o duoi cung roi phai cung trong nhom (dam bao nam trong nhom, khong phai chi o bounding box)
            spawn_col,spawn_row=max(match_line, key=lambda p:(p[1],p[0]))
            special_block_type= self.FATE if n>=5 else self.BOOST[type]
            special_block.append(((spawn_col,spawn_row),special_block_type))
        return special_block
    
    def get_group(self, col: int, row: int, group: list[tuple[int, int]] = None) -> list[tuple[int, int]]:
        if group is None:
            group = list()
        for (offset_x, offset_y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neigh_x = col + offset_x
            neigh_y = row + offset_y
            if self.out_of_bounds(neigh_x, neigh_y):
                continue
            if self._get_block_type(self.board[row][col]) != self._get_block_type(self.board[neigh_y][neigh_x]):#dùng get block type kiểm tra loại block
                continue
            if (neigh_x, neigh_y) in group:
                continue
            group.append((neigh_x, neigh_y))
            group = list(self.get_group(neigh_x, neigh_y, group))
        return group
    
    def find_a_play(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], list[list[tuple[int, int]]]]:
        for row in range(self.rows):
            for col in range(self.cols):
                for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neigh_x = col + x
                    neigh_y = row + y
                    if self.out_of_bounds(neigh_x, neigh_y) or self._get_block_type(self.board[row][col]) == self._get_block_type(self.board[neigh_y][neigh_x]):
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
    
    def find_better_play(self) -> tuple[tuple[tuple[int, int], tuple[int, int]], list[list[tuple[int, int]]]]:
        best_play = tuple()
        best_score = 0
        for row in range(self.rows):
            for col in range(self.cols):
                if self._get_block_type(self.board[row][col])==self.FATE: continue
                
                for (x, y) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neigh_x = col + x
                    neigh_y = row + y
                    #Skip nếu ô lân cận out of bound hoặc là FATE
                    if self.out_of_bounds(neigh_x, neigh_y) or self.board[neigh_y][neigh_x] == self.FATE:
                        continue
                    #Skip 2 ô cùng loại (swap cũng k tạo CLEAR được)
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
                    score = self.calc_score(groups)
                    if score >= best_score:
                        best_score = score
                        best_play = (swap_points, groups)
        return best_play