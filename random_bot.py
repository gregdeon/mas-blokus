import random
from constants import *
from player import Player

#a bot that plays randomly until it runs out of moves
class RandomBot(Player):
    def __init__(self, id):
        Player.__init__(self,id)

    def get_play(self, game):
        global stats
        if False:
            stats['num_plays'][-1] += 1
            stats['num_branch'][-1].append(len(possibilities))
            possibilities = game.possible_plays(self.id)
            if possibilities:
                choice = possibilities[random.randint(0,len(possibilities)-1)]
            else:
                choice = (-1,-1,-1,-1)
        else:
            stats['num_plays'][-1] += 1
            stats['num_branch'][-1].append(1)
            possibility = game.one_possible_play(self.id)
            if possibility is not None:
                choice = possibility
            else:
                choice = (-1,-1,-1,-1)
        if VERBOSE:
            game.board.print_board()
            # print(game.board.board)
            # piece_arrays = [player.pieces for player in game.players]
            # for arr in piece_arrays:
            #     print(arr)
            # print(game.turn)

            #input()
        return choice
