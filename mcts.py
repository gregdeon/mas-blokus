import numpy as np
import time
import math
from constants import *
from player import Player
from game import Game

class MCTSNode:
    def __init__(self, game, last_play, parent):
        self.game = game.copy()
        self.last_play = last_play
        self.parent = parent
        self.children = {}
        self.score = (0,0)
        self.num_sims = 0
        self.num_wins = 0
        self.expanded = False


class MCTSTree:
    def __init__(self, game, player_id, max_time, explore_param=1.414, selection_method='ucb1', rollout_heuristic=None):
        self.root = MCTSNode(game, None, None)
        self.start_time = None
        self.player_id = player_id
        self.max_time = max_time
        self.explore_param = explore_param
        self.selection_method = selection_method
        self.rollout_heuristic = rollout_heuristic

    def ucb1(self, wins, node_sims):
        total_sims = self.root.num_sims
        return float(wins)/float(node_sims) + self.explore_param*math.sqrt(math.log(total_sims)/float(node_sims))

    def select_child(self, node):
        curr_node = node
        best_score = None
        best_child = None
        for _, child in curr_node.children.items():
            if child.num_sims == 0:
                return child
            else:
                if self.selection_method == 'ucb1':
                    curr_score = self.ucb1(child.num_wins, child.num_sims)
                    if best_score is None or curr_score > best_score:
                        best_score = curr_score
                        best_child = child
                else:
                    if VERRBOSE:
                        print('ERROR: Unrecognized MCTS selection method')
                    return None
        return best_child

    def rollout(self, node):
        curr_node = node
        while not curr_node.game.is_finished():
            if len(curr_node.children) == 0:
                if self.rollout_heuristic is None:
                    play = curr_node.game.one_possible_play()
                else:
                    play = None
                    if VERBOSE:
                        print('ERROR: Unrecognized rollout heuristic')
                new_game = curr_node.game.copy()
                if play is None:
                    new_game.players[new_game.turn].finished = True
                    new_game.pass_turn()
                    new_child = MCTSNode(new_game, (curr_node.game.turn, -1, -1, -1, -1), curr_node)
                else:
                    new_game.execute_play(new_game.turn, play[0], play[1], play[2], play[3])
                    new_child = MCTSNode(new_game, (curr_node.game.turn,)+play, curr_node)
                curr_node.children[new_child.last_play] = new_child
                curr_node = new_child
            else:
                curr_node = next(iter(curr_node.children.values()))
        self.backprop(curr_node, curr_node.game.get_leaders())

    def backprop(self, node, winners):
        if node.game.turn in winners:
            node.num_wins += 1
        node.num_sims += 1
        if node.parent is not None:
            self.backprop(node.parent, winners)

    #perform MCTS to expand the current tree up to some maximum
    #max is the maximum time (in seconds) for which the search can run
    def expand_tree(self):
        finished = False
        curr_node = self.root
        start_time = time.time()
        while not finished:
            while curr_node.expanded and not curr_node.game.is_finished():
                curr_node = self.select_child(curr_node)
            if not curr_node.game.is_finished():
                possible_plays = curr_node.game.possible_plays()
                if not possible_plays:
                    new_game = curr_node.game.copy()
                    new_game.players[new_game.turn].finished = True
                    new_game.pass_turn()
                    new_child = MCTSNode(new_game, (curr_node.game.turn, -1, -1, -1, -1), curr_node)
                    curr_node.children[new_child.last_play] = new_child
                else:
                    for play in possible_plays:
                        new_game = curr_node.game.copy()
                        new_game.execute_play(new_game.turn, play[0], play[1], play[2], play[3])
                        new_child = MCTSNode(new_game, (curr_node.game.turn,)+play, curr_node)
                        curr_node.children[new_child.last_play] = new_child

            curr_node.expanded = True
            self.rollout(curr_node)
            curr_node = self.root

            if time.time()-start_time >= self.max_time:
                finished = True

    #return the best play currently available
    def get_best_play(self):
        if not self.root.children:
            return (-1,-1,-1,-1)
        else:
            best_score = None
            best_play = None
            missed_count = 0
            for _, child in self.root.children.items():
                if child.num_sims != 0:
                    curr_score = float(child.num_wins)/child.num_sims
                    if best_score is None or curr_score > best_score:
                        best_score = curr_score
                        best_play = child.last_play[1:]
                else:
                    missed_count += 1
            print(str(missed_count) + '/' + str(len(self.root.children)))
        return best_play

    #preserves some of the previously generated game tree when new moves have bee played
    #takes a tuple, play, of the form (player_id, piece_id, piece_or, row, col)
    def rebase_tree(self, play):
        if play in self.root.children:
            self.root = self.root.children[play]
        else:
            new_game = self.root.game.copy()
            if play[1] == -1:
                new_game.pass_turn()
            else:
                new_game.execute_play(play[0], play[1], play[2], play[3], play[4])
            new_root = MCTSNode(new_game, play, None)
            self.root = new_root


class MCTSBot(Player):
    def __init__(self, id, pieces, max_time, explore_param, selection_method, rollout_heuristic):
        Player.__init__(self,id)
        self.tree = MCTSTree(Game(pieces, [Player(i) for i in range(NUM_PLAYERS)]), id, max_time, explore_param, selection_method, rollout_heuristic)

    def get_play(self, game):
        self.tree.expand_tree()
        if VERBOSE:
            game.board.print_board()
        return self.tree.get_best_play()

    def receive_play(self, game, play):
        self.tree.rebase_tree(play)

    #make a deep copy (tree is reset, not copied)
    def copy(self):
        new_player = MCTSBot(self.id,self.tree.root.game.pieces,self.tree.max_time,self.tree.explore_param,self.tree.selection_method,self.tree.rollout_heuristic)
        new_player.score = self.score
        new_player.pieces = np.copy(self.pieces)
        new_player.finished = self.finished
        return new_player