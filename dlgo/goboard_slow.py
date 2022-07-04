import numpy as np
# tag::imports[]
import copy
from dlgo.gotypes import Player
# end::imports[]
from dlgo.gotypes import Point
from dlgo.scoring import compute_game_result

__all__ = [
    'Board',
    'GameState',
    'Move',
]

"""
    解读：
        定义了三个类的数据结构
            GameState是游戏本身 也即游戏的管理者和统筹者
                其储存一个棋盘Board对象 作为棋盘状况
                    棋盘维护一个字典
                        键-棋子位置：值-所属棋块
                每回合其接收一个Move作为行动 以更新棋盘
        其中 GoString用于构成棋盘
            棋盘由一个个子组成
                每个子都被标记了属于特定棋块
                这样或许方便ai进行分析
                所属棋块相当于身份 同一棋块的子会被统一对待
            棋块储存
                阵营
                所有子的位置
                气的数量和位置
        棋块和棋盘的棋子字典是冗余的
            旧的棋块依然存在
            棋盘字典才是棋盘状况的根本依据
"""


class IllegalMoveError(Exception):
    pass


# 棋块的数据结构 棋块具有阵营属性 棋块中包含有很多子
# tag::strings[]
class GoString():  # <1>
    def __init__(self, color, stones, liberties):
        # 棋块颜色
        self.color = color
        # 棋子集（一堆point）
        self.stones = set(stones)
        # 气的数量和位置
        self.liberties = set(liberties)

    # 被紧一口气 将气的位置去掉
    def remove_liberty(self, point):
        self.liberties.remove(point)

    # 添一口气 应该是被提子了
    def add_liberty(self, point):
        self.liberties.add(point)

    # 相连棋块合并
    def merged_with(self, go_string):  # <2>
        # 检查双方是否是同一阵营
        assert go_string.color == self.color
        # 集合取并集
        combined_stones = self.stones | go_string.stones
        # 返回一个船新的棋块 旧的依然存在（可能这就是冗余的原因 处理棋块很潇洒 没必要删了旧的）
        return GoString(
            self.color,
            combined_stones,
            (self.liberties | go_string.liberties) - combined_stones)

    # 计算还有几口气
    @property
    def num_liberties(self):
        return len(self.liberties)

    # 棋块相等判断接口 一旦各个参数吻合 则相同
    def __eq__(self, other):
        return isinstance(other, GoString) and \
               self.color == other.color and \
               self.stones == other.stones and \
               self.liberties == other.liberties


# <1> Go strings are stones that are linked by a chain of connected stones of the same color.
# <2> Return a new Go string containing all stones in both strings.
# end::strings[]


# 棋盘 数据结构对象 储存了棋盘的大小和一个不知道干嘛用和怎么用的_grid
# tag::board_init[]
class Board():  # <1>
    def __init__(self, num_rows, num_cols):
        # 基本参数 行列
        self.num_rows = num_rows
        self.num_cols = num_cols
        # 棋块的集合 键是棋块中的没个点 值是棋块对象
        self._grid = {}

    # <1> A board is initialized as empty grid with the specified number of rows and columns.
    # end::board_init[]

    # 更新棋盘用的 输入阵营和落子点 在那个点上加上那个字 然后刷新棋块状态
    # 棋块方法的理解入口
    # tag::board_place_0[]
    def place_stone(self, player, point):
        # assert用于错误检查 若变量为False则报错
        # 此处显然是在判断point是否在棋盘内 是否合法
        assert self.is_on_grid(point)
        # 此处显然是在point的点上是不是已经有子了 如果已经有子了 则不能在此处落子
        assert self._grid.get(point) is None
        # 初始化
        # 朋友数组
        adjacent_same_color = []
        # 敌人数组
        adjacent_opposite_color = []
        # 气的点？
        liberties = []

        # 遍历落子的所有邻居
        for neighbor in point.neighbors():  # <1>
            # 如果邻居不在棋盘内 则邻居不用被讨论了
            if not self.is_on_grid(neighbor):
                continue
            # 看看这个邻居是什么子
            neighbor_string = self._grid.get(neighbor)
            # 如果邻居是空的 没有子 放入自由数组中
            if neighbor_string is None:
                liberties.append(neighbor)
            # 如果邻居上的子是自己人 放入相邻朋友数组中
            elif neighbor_string.color == player:
                # 如果友方邻居不在
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            # 如果邻居上的子是敌人 放入相邻敌人数组中
            else:
                # 如果敌方邻居不在
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)
        # 创造新棋块
        new_string = GoString(player, [point], liberties)
        # <1> First, we examine direct neighbors of this point.
        # end::board_place_0[]
        # tag::board_place_1[]
        # 和所有邻居所在的棋块合并
        for same_color_string in adjacent_same_color:  # <1>
            new_string = new_string.merged_with(same_color_string)
        # 新棋块中的每个点录入字典 旧的值会被抹去 所有棋子都属于新的棋块了 因此旧的棋块不用删去
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string
        # 紧住相连的敌人一口气
        for other_color_string in adjacent_opposite_color:  # <2>
            other_color_string.remove_liberty(point)
        # 如果相连的敌人没气了 就被提子
        for other_color_string in adjacent_opposite_color:  # <3>
            if other_color_string.num_liberties == 0:
                self._remove_string(other_color_string)

    # <1> Merge any adjacent strings of the same color.
    # <2> Reduce liberties of any adjacent strings of the opposite color.
    # <3> If any opposite color strings now have zero liberties, remove them.
    # end::board_place_1[]

    # 似乎是棋块被杀时调用的 提子
    # tag::board_remove[]
    def _remove_string(self, string):
        # 所有被杀棋块的点
        for point in string.stones:
            # 找到所有邻居
            for neighbor in point.neighbors():  # <1>
                # 如果邻居上无子 则不讨论
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                # 若有子
                if neighbor_string is not string:
                    # 该子所在的棋块加长一口气
                    neighbor_string.add_liberty(point)
            # 该子从棋盘上抹除
            del (self._grid[point])

    # <1> Removing a string can create liberties for other strings.
    # end::board_remove[]

    # 判断一个落子点是否出界
    # tag::board_utils[]
    def is_on_grid(self, point):
        return 1 <= point.row <= self.num_rows and \
               1 <= point.col <= self.num_cols

    # 判断一个落子点上是否有子 若有 是什么阵营的
    def get(self, point):  # <1>
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    # 输入落子点 取得该点所从属的棋块 若此处无子 则返回None
    def get_go_string(self, point):  # <2>
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    # <1> Returns the content of a point on the board:  a Player if there is a stone on that point or else None.
    # <2> Returns the entire string of stones at a point: a GoString if there is a stone on that point or else None.
    # end::board_utils[]

    # 判断一个棋块是不是和另一个一样
    def __eq__(self, other):
        return isinstance(other, Board) and \
               self.num_rows == other.num_rows and \
               self.num_cols == other.num_cols and \
               self._grid == other._grid


# 数据结构 动作 交给棋盘处理的数据结构 具有落子 pass 和 认输 三个互斥状态
# tag::moves[]
class Move():  # <1>
    def __init__(self, point=None, is_pass=False, is_resign=False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    # 用于得到落子动作的数据结构 输入一个point数据结构 输出一个point状态的move
    @classmethod
    def play(cls, point):  # <2>
        return Move(point=point)

    # 用于得到pass动作的数据结构
    @classmethod
    def pass_turn(cls):  # <3>
        return Move(is_pass=True)

    # 用于得到认输动作的数据结构
    @classmethod
    def resign(cls):  # <4>
        return Move(is_resign=True)


# <1> Any action a player can play on a turn, either is_play, is_pass or is_resign will be set.
# <2> This move places a stone on the board.
# <3> This move passes.
# <4> This move resigns the current game
# end::moves[]


# 棋盘 储存棋盘状态 储存落子顺序 处理move和更新棋盘
# tag::game_state[]
class GameState():
    def __init__(self, board, next_player, previous, move):
        # 棋盘状态
        self.board = board
        # 落子顺序
        self.next_player = next_player
        # 储存前一状态 用链的形式储存棋谱（状态） 也就是上一个自己
        self.previous_state = previous
        # 储存上一move
        self.last_move = move

    # 以move更新棋盘
    def apply_move(self, move):  # <1>
        # 创建一个next_board变量 作为下一个状态的棋盘
        if move.is_play:
            # 如果落子了 就把落子点加上
            # 深复制棋盘 加上新子
            next_board = copy.deepcopy(self.board)
            # 注意place_stone这个方法 落子更新棋块 使得棋盘变成船新的棋盘
            next_board.place_stone(self.next_player, move.point)
        else:
            # 如果没落子 就棋盘原封不动
            next_board = self.board
        # 返回下一个状态 注意返回了一个新的GameState对象
        return GameState(next_board, self.next_player.other, self, move)

    # 生成一个初始状态 自己生成自己的类方法
    @classmethod
    def new_game(cls, board_size):
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    # <1> Return the new GameState after applying the move.
    # end::game_state[]

    #
    # tag::self_capture[]
    def is_move_self_capture(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        new_string = next_board.get_go_string(move.point)
        return new_string.num_liberties == 0

    # end::self_capture[]

    # tag::is_ko[]
    @property
    def situation(self):
        return (self.next_player, self.board)

    def does_move_violate_ko(self, player, move):
        if not move.is_play:
            return False
        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board)
        past_state = self.previous_state
        while past_state is not None:
            if past_state.situation == next_situation:
                return True
            past_state = past_state.previous_state
        return False

    # end::is_ko[]

    # 判断一个落子点是否合法
    # tag::is_valid_move[]
    def is_valid_move(self, move):
        if self.is_over():
            return False
        if move.is_pass or move.is_resign:
            return True
        return (
                self.board.get(move.point) is None and
                not self.is_move_self_capture(self.next_player, move) and
                not self.does_move_violate_ko(self.next_player, move))

    # end::is_valid_move[]
    # 如果连续两次pass 则结束
    # tag::is_over[]
    def is_over(self):
        # 如果处于刚开始的时候 就没结束
        if self.last_move is None:
            return False
        # 如果上一步是一个人认输 就结束
        if self.last_move.is_resign:
            return True
        # 取上上一步
        second_last_move = self.previous_state.last_move
        # 如果处于刚开始的时候 就没结束
        if second_last_move is None:
            return False
        # 如果连续两次pass 则结束
        return self.last_move.is_pass and second_last_move.is_pass

    # 返回所有合法落子点的move
    # end::is_over[]
    def legal_moves(self):
        moves = []

        for row in range(1, self.board.num_rows + 1):
            for col in range(1, self.board.num_cols + 1):
                move = Move.play(Point(row, col))
                if self.is_valid_move(move):
                    moves.append(move)
        # These two moves are always legal.
        moves.append(Move.pass_turn())
        moves.append(Move.resign())

        return moves

    # 判断谁是赢家
    def winner(self):
        if not self.is_over():
            return None
        if self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner
