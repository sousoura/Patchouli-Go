from __future__ import print_function
# tag::play_against_your_bot[]
from dlgo import agent
from dlgo import goboard_slow as goboard
from dlgo import gotypes
from dlgo.utils import print_board, print_move, point_from_coords
from six.moves import input
from dlgo.agent.naive import RandomBot
from exhibitor import Exhibitor

"""
    解读：
        game对应棋盘
            其是一个GameState对象
            由GameState的类方法new_game()生成
            其储存
                一个棋盘 board
                落子者 next_player
                移动 last_move
            其存在以下方法：
                is_over(): 返回bool值 用于棋局是否结束
                apply_move(): 输入一个move变量 使棋盘引用move的变化
        程序运作逻辑
            程序通过给予move值 game运用move值的方式推进
            给予move值的可以是bot对象 也可以是人类的键盘输入
        move是一个动作 其可以是pass 落子 或 认输
"""


def main():
    # 初始化 定义棋盘大小
    board_size = 9
    # 生成对应大小的棋盘 使用类内的方法生成
    game = goboard.GameState.new_game(board_size)
    # 生成bot对象 可以接收一个棋盘作为输入 输出一个落子方案
    bot = RandomBot()
    exhibitor = Exhibitor(board_size, 50)

    # 判断游戏是否结束 否则一直进行轮流落子
    while not game.is_over():
        # 这一行做什么完全不清楚
        # ANSI escape, 清空终端用的
        # print(chr(27) + "[2J")

        # 打印棋盘
        # print_board(game.board)
        exhibitor.display(game)
        # 判断这一步由谁下
        if game.next_player == gotypes.Player.black:
            # 若由黑棋下 则人类玩家决定这一步下在哪
            # # 人类玩家输入落子点 数据结构是两个字符
            # human_move = input('-- ')
            # # 数据结构转换为point 人类玩家似乎不能认输或pass
            # point = point_from_coords(human_move.strip())
            # # move变量是另一个数据结构 用于传输落子点给game
            # move = goboard.Move.play(point)

            # 让机器人下这一步
            move = bot.select_move(game)
        else:
            # 给bot棋盘 bot生成一个动作
            move = bot.select_move(game)
        # 打印 谁 下了哪部（或干了别的什么）
        print_move(game.next_player, move)
        # 将move交给game 应用变化
        game = game.apply_move(move)
    print(game.winner(), "win this game")


if __name__ == '__main__':
    main()
# end::play_against_your_bot[]
