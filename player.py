import numpy as np
from constants import *

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

        while not valid_input:
            key_str = input('Player ' + str(self.id+1) + ', enter piece ID and orientation (e.g. 0 0):\n')
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
            key_str = input('Enter row and column to place the top left corner of the piece (e.g. 0 0):\n')
            tokens = key_str.split()
            if len(tokens) >= 2:
                try:
                    row = int(tokens[0])
                    col = int(tokens[1])
                    valid_input = True
                except:
                    if VERBOSE:
                        print('ERROR: Non-integer input\n')
            else:
                if VERBOSE:
                    print('ERROR: Too few input tokens\n')

        return piece_id, piece_or, row, col