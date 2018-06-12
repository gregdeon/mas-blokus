"""
Running this file will start a 4-(human)-player game of Blokus.
Each turn, a player must enter a piece ID (0-20),
a piece orientation (0-7), representing 90 degree CCW rotations from 0-3, and a flip followed by rotations from 4-7,
a column and row corresponding to the top left of the piece's bounding box (even if that is a hole in the piece).
Note that the origin of the board is also the top left.

Alternately, a player can enter -1 as a piece ID to retire with whatever score they have.
"""

import numpy as np
from constants import *
from board import *
from player import Player
from random_bot import RandomBot
from stat_calculator import *
from game import *
from piece import *


if __name__ == '__main__':
    pieces = read_pieces(PIECES_FILE)
    players = [RandomBot(i) for i in range(NUM_PLAYERS)]
    if TRACK_STATS:
        calc_stats(pieces, RandomBot)
    else:
        play_game(pieces, players)
