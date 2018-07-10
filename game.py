import numpy as np
from constants import *
from board import Board

#keeps the whole game state
class Game:
    #note that a list of Pieces is take as input
    #this is because you only want to initialize the Piece list once, regardless of the number of games played
    def __init__(self, pieces, players, board=None, player_pieces=None, turn=None):
        self.players = players
        self.pieces = pieces
        if board is None:
            self.board = Board()
            self.turn = 0
        else:
            self.board = Board(board)
            self.turn = turn
            for i in range(len(player_pieces)):
                curr = player_pieces[i]
                score = START_SCORE
                for p_id in range(len(curr)):
                    if not curr[p_id]:
                        score -= pieces[p_id].value
                self.players[i].pieces = curr
                self.players[i].score = score

    #Note: does not hash on pieces
    def __hash__(self):
        player_tuple = tuple([hash(player) for player in self.players])
        return hash((hash(self.board),self.turn)+player_tuple)

    #Note: does not compare pieces
    def __eq__(self, other):
        player_bool = np.all([self.players[i]==other.players[i] for i in range(len(self.players))])
        return self.board==other.board and player_bool and self.turn==other.turn

    #make a deep copy
    #the list of pieces will be deep copied only if deep_copy_pieces is set to True
    #(which is expensive and should only be done if you're super worried about someone changing them)
    def copy(self, deep_copy_pieces=False):
        if deep_copy_pieces:
            new_pieces = [piece.copy() for piece in self.pieces]
        else:
            new_pieces = self.pieces
        new_players = [player.copy() for player in self.players]
        new_game = Game(new_pieces, new_players)
        new_game.board = self.board.copy()
        new_game.turn = self.turn
        return new_game

    #returns True iff the player actually has the piece chosen and the board position is valid
    #note that player_id and piece_id inputs are assumed to be valid
    def legal_play(self, player_id, piece_id, piece_or, row, col, verbose=False):
        player = self.players[player_id]
        if piece_id < 0 or piece_id >= NUM_PIECES or not player.pieces[piece_id]:
            if VERBOSE:
                print('Piece ID invalid or already used')
            return False
        return self.board.legal_play(player_id, self.pieces[piece_id], piece_or, row, col, verbose)

    #updates the game state after a move has been made
    #note that all parameters must correspond to a valid move
    def execute_play(self, player_id, piece_id, piece_or, row, col):
        if VERBOSE and player_id != self.turn:
            print("Player " + str(player_id) + " is playing out of turn!")
        for p in self.players:
            p.receive_play(self, (player_id, piece_id, piece_or, row, col))
        player = self.players[player_id]
        player.pieces[piece_id] = False
        player.score -= self.pieces[piece_id].value
        self.board.execute_play(player_id, self.pieces[piece_id], piece_or, row, col)
        self.turn = (self.turn+1) % NUM_PLAYERS

    #move to the next turn without doing anything
    def pass_turn(self):
        for p in self.players:
            p.receive_play(self, (self.turn, -1, -1, -1, -1))
        self.turn = (self.turn+1) % NUM_PLAYERS

    #produces a tuple of all possible plays for the given player ID
    #in the form (piece_id, piece_or, row, col)
    def possible_plays(self, player_id=None):
        if player_id is None:
            player_id = self.turn
        return self.board.possible_plays(player_id, self.players[player_id].pieces,self.pieces)

    #produces one possible play for the given player ID in the form (piece_id, piece_or, row, col)
    def one_possible_play(self, player_id=None):
        if player_id is None:
            player_id = self.turn
        return self.board.one_possible_play(player_id, self.players[player_id].pieces,self.pieces)

    #returns True if the game is over, else returns False
    def is_finished(self):
        game_finished = True
        for player in self.players:
            if not player.finished:
                game_finished = False
        return game_finished

    #returns a list of the player IDs of players currently in the lead
    def get_leaders(self):
        scores = [player.score for player in self.players]
        min_score = min(scores)
        leaders = []
        for player in self.players:
            if player.score == min_score:
                leaders.append(player.id)
        return leaders


#play a 4-player game of Blokus
#takes a list of Pieces and Players as input
def play_game(pieces, players):
    global stats
    if TRACK_STATS:
        stats['num_games'] += 1

    game = Game(pieces, players)
    game_finished = False

    while not game_finished:
        curr_player = game.players[game.turn]
        if not curr_player.finished:
            valid_play = False
            while not valid_play:
                piece_id, piece_or, row, col = curr_player.get_play(game)
                if piece_id == -1:
                    curr_player.finished = True
                    if VERBOSE:
                        print("Player " + str(game.turn+1) + " has finished playing!\n")
                    break
                else:
                    valid_play = game.legal_play(game.turn, piece_id, piece_or, row, col, VERBOSE)
                    if VERBOSE and not valid_play:
                        print('ERROR: Illegal play')
            if piece_id >= 0:
                game.execute_play(game.turn, piece_id, piece_or, row, col)
            else:
                game.pass_turn()
        else:
            game.pass_turn()
        game_finished = game.is_finished()

    scores = [player.score for player in game.players]
    min_score = min(scores)
    winners = []
    for i in range(len(game.players)):
        if game.players[i].score == min_score:
            if TRACK_STATS:
                stats['num_wins'][i] += 1
            winners.append(i+1)
    if VERBOSE:
        if len(winners) == 1:
            print('The winner is Player ' + str(winners[0]) + ' with score ' + str(min_score) + '!\n')
        else:
            print('The winners are Players ' + str(winners) + ' with score ' + str(min_score) + '!\n')
    return winners


if __name__ == '__main__':
    pass
    # from piece import read_pieces
    # from random_bot import RandomBot
    # pieces = read_pieces(PIECES_FILE)
    # players = [RandomBot(i) for i in range(NUM_PLAYERS)]
    # test_game = Game(pieces, players)
    # copy_game = test_game.copy()
    # copy_game.execute_play(0, 1, 0, 0, 0)
    # print("Original State")
    # print(test_game.board.print_board())
    # print("Copy State")
    # print(copy_game.board.print_board())