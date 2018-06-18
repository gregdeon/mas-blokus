import numpy as np
from constants import *
from util import *


#NOT the complete game state
#contains the board state as a numpy array
#values are treated as bit string where the ith player is indicated by 1 << i
#agents may want to use this to track their own possible board states
class Board:

    def __init__(self, other_board=None):
        #default constructor
        if other_board is None:
            #actual piece locations
            self.board = np.zeros((BOARD_HEIGHT+2, BOARD_WIDTH+2), dtype=np.uint8)
            self.board[0][0] = CORNER_SENTINEL
            self.board[0][BOARD_WIDTH+1] = CORNER_SENTINEL
            self.board[BOARD_HEIGHT+1][0] = CORNER_SENTINEL
            self.board[BOARD_HEIGHT+1][BOARD_WIDTH+1] = CORNER_SENTINEL

            #locations adjacent to pieces, but not covered by them
            self.adj_board = np.zeros((BOARD_HEIGHT + 2, BOARD_WIDTH + 2), dtype=np.uint8)

            #locations diagonal to pieces, but not covered by any piece or adjacent to own colour
            self.diag_board = np.zeros((BOARD_HEIGHT + 2, BOARD_WIDTH + 2), dtype=np.uint8)
            self.diag_board[1][1] = CORNER_SENTINEL
            self.diag_board[1][BOARD_WIDTH] = CORNER_SENTINEL
            self.diag_board[BOARD_HEIGHT][1] = CORNER_SENTINEL
            self.diag_board[BOARD_HEIGHT][BOARD_WIDTH] = CORNER_SENTINEL

        #constructs a board by deep copying a given Board
        elif isinstance(other_board, Board):
            self.board = np.copy(other_board.board)
            self.adj_board = np.copy(other_board.adj_board)
            self.diag_board = np.copy(other_board.diag_board)

        #constructs a board from a numpy array
        elif isinstance(other_board, np.ndarray):
            num_rows = np.shape(other_board)[0]
            num_cols = np.shape(other_board)[1]
            if num_rows == BOARD_HEIGHT+2 and num_cols == BOARD_WIDTH+2:
                self.board = np.copy(other_board)
            elif num_rows == BOARD_HEIGHT and num_cols == BOARD_WIDTH:
                self.board = np.zeros((BOARD_HEIGHT+2, BOARD_WIDTH+2), dtype=np.uint8)
                self.board[0][0] = CORNER_SENTINEL
                self.board[0][BOARD_WIDTH+1] = CORNER_SENTINEL
                self.board[BOARD_HEIGHT+1][0] = CORNER_SENTINEL
                self.board[BOARD_HEIGHT+1][BOARD_WIDTH+1] = CORNER_SENTINEL
                self.board[1:-1,1:-1] = np.copy(other_board)
            else:
                if VERBOSE:
                    print("ERROR: numpy array of invalid size given to Board constructor")
                return
            self.adj_board = np.zeros((BOARD_HEIGHT + 2, BOARD_WIDTH + 2), dtype=np.uint8)
            self.diag_board = np.zeros((BOARD_HEIGHT + 2, BOARD_WIDTH + 2), dtype=np.uint8)
            if EXTRA_TRACKING:
                unoccupied = ALL_ONES*np.logical_not(self.board)
                #update adj locations
                adj_candidates = [np.pad(self.board[1:,:],((0,1),(0,0)),'constant'),
                                  np.pad(self.board[:-1,:],((1,0),(0,0)),'constant'),
                                  np.pad(self.board[:,1:],((0,0),(0,1)),'constant'),
                                  np.pad(self.board[:,:-1],((0,0),(1,0)),'constant')]
                for cand in adj_candidates:
                    self.adj_board = np.bitwise_or(self.adj_board, cand)
                self.adj_board = np.bitwise_and(self.adj_board, unoccupied)
                #update diag locations
                diag_candidates = [np.pad(self.board[1:,:-1],((0,1),(1,0)),'constant'),
                                   np.pad(self.board[1:,1:],((0,1),(0,1)),'constant'),
                                   np.pad(self.board[:-1,1:],((1,0),(0,1)),'constant'),
                                   np.pad(self.board[:-1,:-1],((1,0),(1,0)),'constant')]
                for cand in diag_candidates:
                    self.diag_board = np.bitwise_or(self.diag_board, cand)
                self.diag_board = np.bitwise_and(self.diag_board, unoccupied)
                self.diag_board = np.bitwise_and(self.diag_board, np.bitwise_not(self.adj_board))

        #constructs a board from another Board (deep copy)
        elif isinstance(other_board, Board):
            self.board = np.copy(other_board.board)
            self.adj_board = np.copy(other_board.adj_board)
            self.diag_board = np.copy(other_board.diag_board)

        else:
            if VERBOSE:
                print("ERROR: Invalid arguments given to Board constructor")


    def __hash__(self):
        return hash(self.board.tobytes())

    def __eq__(self, other):
        return np.all(self.board==other.board)

    #make a deep copy
    def copy(self):
        return Board(self)


    def print_board(self):
        if PRINT_COLOUR:
            self.print_board_coloured()
        else:
            print(str(bitstoid(self.board[1:BOARD_HEIGHT+1,1:BOARD_WIDTH+1])+1) + '\n')

    def print_board_coloured(self):
        for y in range(BOARD_HEIGHT):
            line = ''
            for x in range(BOARD_WIDTH):
                piece = bitstoid(self.board[y+1][x+1])
                if(piece >= 0):
                    line += FORE_ARRAY[piece] + BACK_ARRAY[piece] + str(piece)
                else:
                    line += Style.RESET_ALL + '.'
            line += Style.RESET_ALL
            print(line)
        print('')

    # returns True iff the given piece, orientation, and position satisfy the rules of Blokus
    # note that player_id and piece_id inputs are assumed to be valid
    def legal_play(self, player_id, piece, piece_or, row, col, verbose=False):
        area_mask = piece.area_masks[piece_or]
        adj_mask = piece.adj_masks[piece_or]
        diag_mask = piece.diag_masks[piece_or]
        if row < 0 or row+np.shape(area_mask)[0] > BOARD_HEIGHT or col < 0 or col+np.shape(area_mask)[1] > BOARD_WIDTH:
            if verbose:
                print('Row or Column out of range')
            return False

        board_chunk = self.board[row+1:row+1+np.shape(area_mask)[0],col+1:col+1+np.shape(area_mask)[1]]
        padded_board_chunk = self.board[row:row+np.shape(adj_mask)[0],col:col+np.shape(adj_mask)[1]]
        player_mask = 1 << player_id
        padded_board_chunk = padded_board_chunk & player_mask

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

    # updates the board state after a move has been made
    # note that all parameters must correspond to a valid move
    def execute_play(self, player_id, piece, piece_or, row, col):
        #update piece locations
        player_mask = 1 << player_id
        piece_stamp = player_mask*(piece.area_masks[piece_or])
        piece_shape = np.shape(piece_stamp)
        board_chunk = self.board[row+1:row+1+piece_shape[0],col+1:col+1+piece_shape[1]]
        self.board[row+1:row+1+piece_shape[0],col+1:col+1+piece_shape[1]] = np.bitwise_or(board_chunk,piece_stamp)

        if EXTRA_TRACKING:
            #update adj locations
            board_chunk = self.board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2]
            adj_chunk = self.adj_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2]
            self.adj_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2] = np.bitwise_and(adj_chunk,np.bitwise_not(board_chunk))
            adj_stamp = player_mask*(np.logical_and(piece.adj_masks[piece_or],np.logical_not(board_chunk)))
            self.adj_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2] = np.bitwise_or(adj_chunk,adj_stamp)

            #update diag locations
            adj_chunk = self.adj_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2]
            diag_chunk = self.diag_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2]
            self.diag_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2] = np.bitwise_and(diag_chunk,np.bitwise_not(board_chunk))
            diag_stamp = np.logical_and(piece.diag_masks[piece_or],np.logical_not(board_chunk))
            diag_stamp = np.logical_and(diag_stamp, np.logical_not(adj_chunk & player_mask))
            diag_stamp = player_mask*diag_stamp
            self.diag_board[row:row+piece_shape[0]+2,col:col+piece_shape[1]+2] = np.bitwise_or(diag_chunk, diag_stamp)


    #produces a tuple of all possible plays for the given player ID and piece ID list
    #in the form (piece_id, piece_or, row, col)
    def possible_plays(self, player_id, piece_ids_left, pieces):
        ans = set()
        player_mask = 1 << player_id
        player_diags = np.bitwise_and(player_mask, self.diag_board)

        #locate corners for each of 4 types
        bshp = np.shape(self.board)
        shifted_boards = [np.bitwise_and(np.pad(self.board[1:,:bshp[1]-1],((0,1),(1,0)),'constant'),player_mask),
                          np.bitwise_and(np.pad(self.board[1:,1:],((0,1),(0,1)),'constant'),player_mask),
                          np.bitwise_and(np.pad(self.board[:bshp[0]-1,1:],((1,0),(0,1)),'constant'),player_mask),
                          np.bitwise_and(np.pad(self.board[:bshp[0]-1,:bshp[1]-1],((1,0),(1,0)),'constant'),player_mask)]
        for i in range(4):
            rows, cols = np.where(np.logical_and(shifted_boards[i],player_diags))
            piece_i = (i+2) % 4

            #for each corner try all complimentary corners of all orientations of all available pieces
            for j in range(len(rows)):
                row = rows[j]
                col = cols[j]
                for pid in range(len(piece_ids_left)):
                    if piece_ids_left[pid]:
                        curr_piece = pieces[pid]
                        for por in curr_piece.unique_ors:
                            for posn in curr_piece.diag_locs[por][piece_i]:
                                board_row = row - posn[0] - 1
                                board_col = col - posn[1] - 1
                                if self.legal_play(player_id, curr_piece, por, board_row, board_col, False):
                                    ans.add((pid, por, board_row, board_col))
        return tuple(ans)


if __name__ == '__main__':
    pass
#     ar = np.zeros((BOARD_HEIGHT, BOARD_WIDTH), dtype=np.uint8)
#     ar[2][2] = 1
#     ar[2][3] = 1
#     ar[3][3] = 1
#     ar[2][4] = 4
#     ar[3][4] = 4
#     ar[4][4] = 4
#     test_board = Board(ar)
#     print(test_board.print_board())
#     print("Board")
#     print(test_board.board)
#     print("Adj Board")
#     print(test_board.adj_board)
#     print("Diag Board")
#     print(test_board.diag_board)