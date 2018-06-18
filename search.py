import numpy as np
from constants import *

class SearchNode:
    def __init__(self, game, last_play, parent):
        self.game = game.copy()
        self.last_play = last_play
        self.parent = parent
        self.children = []
        self.score = None


class SearchTree:
    def __init__(self, game):
        self.root = SearchNode(game, None, None)
        self.num_nodes = 1

    #exhaustively search all possible moves, expanding up to max_nodes
    #returns (None, None) if max_nodes exceeded
    #otherwise, returns a tuple containing a list of all possible plays and a corresponding list of (wins,losses)
    #resulting from those plays
    def exhaustive_search(self, max_nodes=None):
        results = {}
        orig_player = self.root.game.turn
        too_many_nodes = False

        #a helper for the helper
        #expands a node for a finished player
        def expand_pass(curr_node):
            self.num_nodes += 1
            curr_node.score = [0,0]
            new_game = curr_node.game.copy()
            new_game.pass_turn()
            new_child = SearchNode(new_game, (curr_node.game.turn, -1, -1, -1, -1), curr_node)
            curr_node.children.append(new_child)
            expand_child(new_child)
            if new_child.score is not None:
                curr_node.score[0] += new_child.score[0]
                curr_node.score[1] += new_child.score[1]

        #recursive helper function
        def expand_child(curr_node):
            nonlocal too_many_nodes
            if max_nodes is None or self.num_nodes<=max_nodes: #not too many nodes
                if curr_node.game not in results: #state hasn't already been looked at
                    if curr_node.game.players[curr_node.game.turn].finished: #current player has quit
                        expand_pass(curr_node)
                    else:
                        possible_plays = curr_node.game.possible_plays()
                        if not possible_plays: #current player has just run out of plays
                            curr_node.game.players[curr_node.game.turn].finished = True
                            finished = True
                            for player in curr_node.game.players:
                                finished = finished and player.finished
                            if finished: #all players are out of plays; the game is over
                                win = False
                                if curr_node.game.players[orig_player].score == min([player.score for player in curr_node.game.players]):
                                    win = True
                                if win:
                                    results[curr_node.game] = [1,0]
                                    curr_node.score = [1,0]
                                else:
                                    results[curr_node.game] = [0,1]
                                    curr_node.score = [0,1]
                            else:
                                expand_pass(curr_node)
                        else:
                            self.num_nodes += len(possible_plays)
                            curr_node.score = [0,0]
                            for play in possible_plays:
                                new_game = curr_node.game.copy()
                                new_game.execute_play(new_game.turn, play[0], play[1], play[2], play[3])
                                new_child = SearchNode(new_game, play, curr_node)
                                curr_node.children.append(new_child)
                                expand_child(new_child)
                                if new_child.score is not None:
                                    curr_node.score[0] += new_child.score[0]
                                    curr_node.score[1] += new_child.score[1]
                                # if curr_node.parent == None:
                                #     print(play)
                                #     print(new_child.score)
                        results[curr_node.game] = curr_node.score
                else:
                    curr_node.score = results[curr_node.game]
            else:
                too_many_nodes = True

        expand_child(self.root)
        if too_many_nodes:
            if VERBOSE:
                print('Exhaustive search failed to finish with less than ' + str(max_nodes) + ' nodes')
            possible_plays = None
            play_values = None
        else:
            possible_plays = [child.last_play for child in self.root.children]
            play_values = [child.score for child in self.root.children]
        return possible_plays, play_values


if __name__ == '__main__':
    pass
    from piece import read_pieces
    from random_bot import RandomBot
    from game import Game
    pieces = read_pieces(PIECES_FILE)
    players = [RandomBot(i) for i in range(NUM_PLAYERS)]
    test_board = [[255,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,255],
                  [0,4,0,4,4,0,0,0,4,0,4,4,0,0,0,0,0,0,0,0,8,0],
                  [0,4,4,0,4,0,0,0,4,0,4,4,0,0,8,0,0,0,8,8,8,0],
                  [0,0,0,0,4,0,0,4,4,4,8,8,0,0,8,8,0,0,8,0,0,0],
                  [0,0,0,0,0,4,4,0,0,0,0,8,8,0,8,0,8,8,0,8,0,0],
                  [0,0,4,0,4,4,0,0,8,0,0,8,0,8,0,0,8,8,0,0,0,0],
                  [0,4,4,4,0,4,0,0,8,8,8,0,8,8,0,0,0,8,0,8,0,0],
                  [0,0,0,0,4,0,0,4,8,0,0,8,8,4,0,0,8,0,8,8,0,0],
                  [0,0,1,0,4,4,4,0,0,8,4,0,4,4,4,8,8,0,8,2,2,0],
                  [0,1,1,0,0,0,4,0,8,8,4,4,2,4,0,8,0,2,2,8,8,0],
                  [0,1,1,4,4,4,0,4,0,0,0,4,2,2,0,8,0,2,0,0,8,0],
                  [0,0,0,1,1,1,0,4,4,4,4,0,1,2,2,0,0,2,2,0,8,0],
                  [0,0,0,0,1,0,1,1,1,0,0,1,1,0,0,2,2,8,0,2,8,0],
                  [0,0,1,1,0,0,1,0,0,0,1,1,0,0,1,2,2,8,8,8,0,0],
                  [0,1,1,0,0,0,1,0,0,0,0,0,1,1,1,0,2,0,2,2,0,0],
                  [0,0,0,0,1,1,0,1,0,1,1,1,0,0,1,0,0,2,0,2,2,0],
                  [0,0,0,0,1,0,1,1,1,0,0,1,1,2,2,2,0,2,0,2,0,0],
                  [0,0,0,0,1,0,0,0,1,0,2,2,2,0,2,0,2,2,0,0,0,0],
                  [0,0,0,0,1,0,0,1,0,1,0,0,2,0,0,0,2,0,2,2,2,0],
                  [0,1,1,1,0,1,1,1,1,0,2,2,0,0,0,2,0,0,0,0,2,0],
                  [0,1,0,0,0,0,0,0,0,2,2,0,0,0,2,2,0,0,0,0,2,0],
                  [255,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,255]]
    pieces_left = [[True,False,False,False,True,False,True,False,False,False,False,True,True,False,False,False,True,True,True,True,False],
                   [True,False,False,False,False,True,True,False,True,False,True,True,True,False,False,False,True,False,True,False,False],
                   [False,True,False,True,True,False,False,True,True,True,False,True,False,False,False,False,True,False,False,True,False],
                   [True,False,False,False,True,False,False,True,True,False,False,True,True,False,False,False,True,False,True,True,False]]
    turn = 0
    test_board = np.array(test_board, dtype=np.uint8)
    test_game = Game(pieces, players,test_board,pieces_left,turn)
    tree = SearchTree(test_game)
    print(tree.exhaustive_search(100000))