import random
from constants import *
from player import Player

#a bot that plays randomly until it runs out of moves
class RandomBot(Player):
    def __init__(self, id):
        Player.__init__(self,id)

    def get_play(self, game):
        global stats
        possibilities = game.possible_plays(self.id)
        if TRACK_STATS:
            stats['num_plays'][-1] += 1
            stats['num_branch'][-1].append(len(possibilities))
        if possibilities:
            choice = possibilities[random.randint(0,len(possibilities)-1)]
        else:
            choice = (-1,-1,-1,-1)
        if VERBOSE:
            game.board.print_board()
            input()
        return choice