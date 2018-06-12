from constants import *
from board import Board

#keeps the whole game state
class Game:
    #note that a list of Pieces is take as input
    #this is because you only want to initialize the Piece list once, regardless of the number of games played
    def __init__(self, pieces, players):
        self.board = Board()
        self.players = players
        self.pieces = pieces

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
        player = self.players[player_id]
        player.pieces[piece_id] = False
        player.score -= self.pieces[piece_id].value
        self.board.execute_play(player_id, self.pieces[piece_id], piece_or, row, col)

    #produces a tuple of all possible plays for the given player ID
    #in the form (piece_id, piece_or, row, col)
    def possible_plays(self, player_id):
        return self.board.possible_plays(player_id, self.players[player_id].pieces,self.pieces)


#play a 4-player game of Blokus
#takes a list of Pieces and Players as input
def play_game(pieces, players):
    global stats
    if TRACK_STATS:
        stats['num_games'] += 1

    game = Game(pieces, players)
    game_finished = False
    turn = 0

    while not game_finished:
        curr_player = game.players[turn]
        if not curr_player.finished:
            valid_play = False
            while not valid_play:
                piece_id, piece_or, row, col = curr_player.get_play(game)
                if piece_id == -1:
                    curr_player.finished = True
                    if VERBOSE:
                        print("Player " + str(turn+1) + " has finished playing!\n")
                    break
                else:
                    valid_play = game.legal_play(turn, piece_id, piece_or, row, col, VERBOSE)
                    if VERBOSE and not valid_play:
                        print('ERROR: Illegal play')
            if piece_id >= 0:
                game.execute_play(turn, piece_id, piece_or, row, col)

        game_finished = True
        for player in game.players:
            if not player.finished:
                game_finished = False
        turn = (turn+1) % NUM_PLAYERS

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