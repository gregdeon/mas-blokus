import numpy as np
import random

"""
Running this file will start a 4-(human)-player game of Blokus.
Each turn, a player must enter a piece ID (0-20),
a piece orientation (0-7), representing 90 degree CCW rotations from 0-3, and a flip followed by rotations from 4-7,
a column and row corresponding to the top left of the piece's bounding box (even if that is a hole in the piece).
Note that the origin of the board is also the top left.

Alternately, a player can enter -1 as a piece ID to retire with whatever score they have.
"""

BOARD_WIDTH = 20
BOARD_HEIGHT = 20
NUM_PIECES = 21
START_SCORE = 89
NUM_PLAYERS = 4
CORNER_SENTINEL = 255
PIECES_FILE = 'pieces.txt'
VERBOSE = True
PRINT_COLOUR = True

if PRINT_COLOUR:
    from colorama import Fore, Back, Style, init
    init(convert=True)
    FORE_ARRAY = [Style.RESET_ALL, Fore.RED, Fore.BLUE, Fore.GREEN, Fore.YELLOW]
    BACK_ARRAY = [Style.RESET_ALL, Back.RED, Back.BLUE, Back.GREEN, Back.YELLOW]


#NOT the complete game state
#contains the board state as a numpy array
#agents may want to use this to track their own possible board states
class Board:
    def __init__(self):
        self.board = np.zeros((BOARD_HEIGHT+2, BOARD_WIDTH+2), dtype=np.uint8)
        self.board[0][0] = CORNER_SENTINEL
        self.board[0][BOARD_WIDTH+1] = CORNER_SENTINEL
        self.board[BOARD_HEIGHT+1][0] = CORNER_SENTINEL
        self.board[BOARD_HEIGHT+1][BOARD_WIDTH+1] = CORNER_SENTINEL

    def print_board(self):
        if PRINT_COLOUR:
            self.print_board_coloured()
        else:
            print(str(self.board[1:BOARD_HEIGHT+1,1:BOARD_WIDTH+1]) + '\n')

    def print_board_coloured(self):
        for y in range(BOARD_HEIGHT):
            line = ''
            for x in range(BOARD_WIDTH):
                piece = self.board[y+1][x+1]
                if(piece > 0):
                    line += FORE_ARRAY[piece] + BACK_ARRAY[piece] + str(piece)
                else:
                    line += Style.RESET_ALL + '.'
            line += Style.RESET_ALL
            print(line)
        print('')

    # returns True iff the given piece, orientation, and position satisfy the rules of Blokus
    # note that player_id and piece_id inputs are assumed to be valid
    def legal_play(self, player_id, first_round, piece, piece_or, row, col, verbose=VERBOSE):
        area_mask = piece.area_masks[piece_or]
        adj_mask = piece.adj_masks[piece_or]
        diag_mask = piece.diag_masks[piece_or]
        if row < 0 or row+np.shape(area_mask)[0] > BOARD_HEIGHT or col < 0 or col+np.shape(area_mask)[1] > BOARD_WIDTH:
            if verbose:
                print('Row or Column out of range')
            return False

        board_chunk = self.board[row+1:row+1+np.shape(area_mask)[0],col+1:col+1+np.shape(area_mask)[1]]
        padded_board_chunk = self.board[row:row+np.shape(adj_mask)[0],col:col+np.shape(adj_mask)[1]]
        # Note: there's no reason for this check because the first move is guaranteed to take over the corner
        if first_round:
            padded_board_chunk = (padded_board_chunk==player_id) + (padded_board_chunk==CORNER_SENTINEL)
        else:
            padded_board_chunk = padded_board_chunk==player_id

        if np.any(np.logical_and(board_chunk, area_mask)):
            if verbose:
                print('Overlapping another piece')
            return False
        if np.any(np.logical_and(padded_board_chunk, adj_mask)):
            if verbose:
                print('Directly adjacent to your own piece')
            return False
        if not np.any(np.logical_and(padded_board_chunk, diag_mask)):
            if verbose:
                print('Not diagonally touching your own piece')
            return False
        return True

#inherit from this class for bots
class Player:
    def __init__(self, id):
        self.id = id
        self.score = START_SCORE
        self.pieces = np.ones(NUM_PIECES, dtype=np.bool) #array of bools tracking which pieces are left
        self.finished = False #true when the player is done playing (must manually enter -1 on turn)

    #this method should be overridden by autonomous agents
    #it is currently set up to take keyboard input from a human user
    #the entire game is passed as a parameter
    #it would be expensive to duplicate it, so just super promise not to alter game
    #a tuple of 4 values is produced:
    #   piece_id - the numeric ID of the piece chosen
    #   piece_or - the numeric value (0-7) of the piece's orientation
    #   row - grid row for the top left corner to be placed
    #   col - grid column for the top left corner to be placed
    def get_play(self, game):
        piece_id = -1
        piece_or = -1
        row = -1
        col = -1
        valid_input = False

        if VERBOSE:
            game.board.print_board()

            # Print all legal moves to help pick a good one
            print(game.get_legal_moves(self.id))

        while not valid_input:
            key_str = input('Player ' + str(self.id) + ', enter piece ID and orientation (e.g. 0 0):\n')
            tokens = key_str.split()
            if len(tokens) >= 2:
                try:
                    piece_id = int(tokens[0])
                    piece_or = int(tokens[1])
                    if piece_id >= -1 and piece_id < NUM_PIECES and piece_or >= 0 and piece_or < 8:
                        valid_input = True
                        if VERBOSE and piece_id >= 0:
                            game.pieces[piece_id].print_piece(piece_or, self.id)
                    else:
                        if VERBOSE:
                            print('ERROR: Piece ID or orientation out of range\n')
                except:
                    if VERBOSE:
                        print('ERROR: Non-integer input\n')
            elif len(tokens) == 1:
                try:
                    piece_id = int(tokens[0])
                    if piece_id == -1:
                        valid_input = True
                    elif VERBOSE:
                        print('ERROR: Too few input tokens\n')
                except:
                    if VERBOSE:
                        print('ERROR: Non-integer input\n')
            else:
                if VERBOSE:
                    print('ERROR: Too few input tokens\n')

        valid_input = False
        while not valid_input and piece_id != -1:
            key_str = input('Enter column and row to place the top left corner of the piece (e.g. 0 0):\n')
            tokens = key_str.split()
            if len(tokens) >= 2:
                try:
                    col = int(tokens[0])
                    row = int(tokens[1])
                    valid_input = True
                except:
                    if VERBOSE:
                        print('ERROR: Non-integer input\n')
            else:
                if VERBOSE:
                    print('ERROR: Too few input tokens\n')

        return piece_id, piece_or, row, col

class RandomPlayer(Player):
    def get_play(self, game):
        legal_moves = game.get_legal_moves(self.id)
        try: 
            move = random.sample(legal_moves, 1)[0]
            (piece_id, orientation, col, row) = move
            return piece_id, orientation, row, col
        except ValueError:
            # There are no legal moves
            return (-1, -1, -1, -1)


#keeps all of the masks associated with one of the 21 pieces
#the top left corner is (0,0) for all masks, even if there is a gap in the piece there
class Piece:
    def __init__(self, id, value, area_mask, adj_mask, diag_mask):
        self.id = id
        self.value = value
        self.area_masks = []
        self.adj_masks = []
        self.diag_masks = []

        for _ in range(4):
            self.area_masks.append(np.copy(area_mask))
            self.adj_masks.append(np.copy(adj_mask))
            self.diag_masks.append(np.copy(diag_mask))
            area_mask = np.rot90(area_mask)
            adj_mask = np.rot90(adj_mask)
            diag_mask = np.rot90(diag_mask)

        area_mask = np.flip(area_mask,1)
        adj_mask = np.flip(adj_mask,1)
        diag_mask = np.flip(diag_mask,1)

        for _ in range(4):
            self.area_masks.append(np.copy(area_mask))
            self.adj_masks.append(np.copy(adj_mask))
            self.diag_masks.append(np.copy(diag_mask))
            area_mask = np.rot90(area_mask)
            adj_mask = np.rot90(adj_mask)
            diag_mask = np.rot90(diag_mask)

    def print_piece(self, piece_or, player_id):
        print(str(player_id*(np.array(self.area_masks[piece_or], dtype=np.uint8))) + '\n')


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
    def legal_play(self, player_id, first_round, piece_id, piece_or, row, col):
        player = self.players[player_id-1]
        if piece_id < 0 or piece_id >= NUM_PIECES or not player.pieces[piece_id]:
            if VERBOSE:
                print('Piece ID invalid or already used')
            return False
        return self.board.legal_play(player_id, first_round, self.pieces[piece_id], piece_or, row, col)

    #updates the game state after a move has been made
    #note that all parameters must correspond to a valid move
    def execute_play(self, player_id, piece_id, piece_or, row, col):
        player = self.players[player_id-1]
        player.pieces[piece_id] = False
        player.score -= self.pieces[piece_id].value
        piece_stamp = player_id*(self.pieces[piece_id].area_masks[piece_or])
        piece_shape = np.shape(piece_stamp)
        board_chunk = self.board.board[row+1:row+1+piece_shape[0],col+1:col+1+piece_shape[1]]
        self.board.board[row+1:row+1+piece_shape[0],col+1:col+1+piece_shape[1]] = np.bitwise_or(board_chunk,piece_stamp)

    def get_legal_moves(self, player_id):
        moves_set = set()

        player = self.players[player_id - 1]
        piece_list = self.pieces
        for piece_id in range(len(piece_list)):
            if not player.pieces[piece_id]:
                continue

            piece = piece_list[piece_id]
            for orientation in range(8):
                for col in range(BOARD_HEIGHT):
                    for row in range(BOARD_WIDTH):
                        if(self.board.legal_play(player_id, True, piece, orientation, row, col, verbose=False)):
                            moves_set.add((piece_id, orientation, col, row))

        return list(moves_set)

#reads all of the different piece shapes from a file
#only call this ONCE, even if many games are played
#it's pretty expensive
def read_pieces(file_name):
    read_file = open(file_name, 'r')
    areas = []
    pieces = []
    curr_area = []

    for line in read_file:
        tokens = line.split()
        if not tokens:
            if curr_area:
                areas.append(np.array(curr_area, dtype=np.bool))
                curr_area = []
        else:
            curr_area.append([bool(int(tokens[0][i])) for i in range(len(tokens[0]))])
    if curr_area:
        areas.append(np.array(curr_area, dtype=np.bool))
    read_file.close()

    for i in range(len(areas)):
        curr_area = areas[i]
        area_shape = np.shape(curr_area)
        curr_adj = np.zeros((area_shape[0]+2,area_shape[1]+2), dtype=np.bool)
        curr_diag = np.zeros((area_shape[0]+2,area_shape[1]+2), dtype=np.bool)
        for row in range(len(curr_area)):
            for col in range(len(curr_area[row])):
                if curr_area[row][col] == True:
                    curr_adj[row+1][col] = True
                    curr_adj[row+1][col+2] = True
                    curr_adj[row][col+1] = True
                    curr_adj[row+2][col+1] = True
                    curr_diag[row][col] = True
                    curr_diag[row+2][col] = True
                    curr_diag[row][col+2] = True
                    curr_diag[row+2][col+2] = True
        padded_area = np.zeros(np.shape(curr_adj), dtype=np.bool)
        padded_area[1:np.shape(curr_area)[0]+1,1:np.shape(curr_area)[1]+1] = curr_area
        curr_diag = np.logical_and(curr_diag, np.logical_not(curr_adj))
        curr_diag = np.logical_and(curr_diag, np.logical_not(padded_area))
        curr_adj = np.logical_and(curr_adj, np.logical_not(padded_area))
        pieces.append(Piece(i,np.count_nonzero(curr_area),curr_area,curr_adj,curr_diag))
    return pieces


#print out pieces for debugging purposes
def print_pieces(pieces):
    for piece in pieces:
        print ("Piece " + str(piece.id) + ", value " + str(piece.value))
        print ("Area Masks:")
        for mask in piece.area_masks:
            print(np.array(mask, dtype=np.uint8))
        print("Adj Masks:")
        for mask in piece.adj_masks:
            print(np.array(mask, dtype=np.uint8))
        print("Diag Masks:")
        for mask in piece.diag_masks:
            print(np.array(mask, dtype=np.uint8))
        print("")


#play a 4-player game of Blokus
#takes a list of Pieces and Players as input
def play_game(pieces, players):
    game = Game(pieces, players)
    game_finished = False
    first_round = True
    turn = 1

    while not game_finished:
        curr_player = game.players[turn - 1]
        if not curr_player.finished:
            valid_play = False
            while not valid_play:
                piece_id, piece_or, row, col = curr_player.get_play(game)
                if piece_id == -1:
                    curr_player.finished = True
                    if VERBOSE:
                        print("Player " + str(turn) + " has finished playing!\n")
                    break
                else:
                    valid_play = game.legal_play(turn, first_round, piece_id, piece_or, row, col)
                    if VERBOSE and not valid_play:
                        print('ERROR: Illegal play')
            if piece_id >= 0:
                game.execute_play(turn, piece_id, piece_or, row, col)

        game_finished = True
        for player in game.players:
            if not player.finished:
                game_finished = False
        turn = turn % NUM_PLAYERS + 1
        if turn == 1:
            first_round = False

        if VERBOSE:
            game.board.print_board()

    scores = [player.score for player in game.players]
    min_score = min(scores)
    winners = []
    for i in range(len(game.players)):
        if game.players[i].score == min_score:
            winners.append(i+1)
    if VERBOSE:
        if len(winners) == 1:
            print('The winner is Player ' + str(winners[0]) + ' with score ' + str(min_score) + '!\n')
        else:
            print('The winners are Players ' + str(winners) + ' with score ' + str(min_score) + '!\n')
    return winners


if __name__ == '__main__':
    pieces = read_pieces(PIECES_FILE)
    #players = [Player(i) for i in range(1,NUM_PLAYERS+1)]
    players = [RandomPlayer(i) for i in range(1,NUM_PLAYERS+1)]
    play_game(pieces, players)

