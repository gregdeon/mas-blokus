import numpy as np
import random
import time

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
NUM_STATS_GAMES = 100
PIECES_FILE = 'pieces.txt'
VERBOSE = False
EXTRA_TRACKING = True
TRACK_STATS = True
PRINT_COLOUR = True

#global vars for stats
stats = {}
stats['num_games'] = 0
stats['num_wins'] = [0 for _ in range(4)]
stats['game_time'] = []
stats['num_plays'] = []
stats['num_branch'] = []
stats['avg_branch'] = []
stats['max_branch'] = []
stats['max_branch_turn'] = []

if PRINT_COLOUR:
    from colorama import Fore, Back, Style, init
    init(convert=True)
    FORE_ARRAY = [Fore.RED, Fore.BLUE, Fore.GREEN, Fore.YELLOW]
    BACK_ARRAY = [Back.RED, Back.BLUE, Back.GREEN, Back.YELLOW]


#NOT the complete game state
#contains the board state as a numpy array
#values are treated as bit string where the ith player is indicated by 1 << i
#agents may want to use this to track their own possible board states
class Board:
    def __init__(self):
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

    def print_board(self):
        print(str(bitstoid(self.board[1:BOARD_HEIGHT+1,1:BOARD_WIDTH+1])+1) + '\n')
        # print()
        # print(str(bitstoid(self.adj_board[1:BOARD_HEIGHT + 1, 1:BOARD_WIDTH + 1]) + 1) + '\n')
        # print()
        # print(str(bitstoid(self.diag_board[1:BOARD_HEIGHT + 1, 1:BOARD_WIDTH + 1]) + 1) + '\n')

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


#keeps all of the masks associated with one of the 21 pieces
#the top left corner is (0,0) for all masks, even if there is a gap in the piece there
class Piece:
    def __init__(self, id, value, area_mask, adj_mask, diag_mask):
        self.id = id
        self.value = value
        self.area_masks = []
        self.adj_masks = []
        self.diag_masks = []
        self.diag_locs = [[None for _ in range(4)] for _ in range(8)]
        self.unique_ors = []

        #generate all 8 orientations
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

        #determine which orientations are unique
        unique_masks = []
        for i in range(len(self.area_masks)):
            candidate = self.area_masks[i]
            unique = True
            for mask in unique_masks:
                unique = unique and (not np.all(mask == candidate))
            if unique:
                self.unique_ors.append(i)
                unique_masks.append(candidate)

        #get locations with adjacent corners
        padding_shapes = (((0,2),(2,0)),
                          ((0,2),(0,2)),
                          ((2,0),(0,2)),
                          ((2,0),(2,0)))
        reverse_shift = ((0,-2),(0,0),(-2,0),(-2,-2))
        for i in range(len(self.area_masks)):
            area = self.area_masks[i]
            diag = self.diag_masks[i]
            for j in range(4):
                padded_area = np.pad(area,padding_shapes[j],'constant')
                selected = np.logical_and(padded_area,diag)
                row,col = np.where(selected)
                self.diag_locs[i][j] = [(row[k]+reverse_shift[j][0],col[k]+reverse_shift[j][1]) for k in range(len(row))]

    def print_piece(self, piece_or, player_id):
        print(str((player_id+1)*(np.array(self.area_masks[piece_or], dtype=np.uint8))) + '\n')


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


#takes a uint8 and produces the first player ID that matches
#100 is an error value
def bitstoid(bits):
    if bits == 0:
        return -1
    else:
        for i in range(8):
            if bits & 1 != 0:
                return i
            bits = bits >> 1
    if VERBOSE:
        print('ERROR: bitstoid received an invalid bitstring')
    return 100
bitstoid = np.vectorize(bitstoid)


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
        print("Diag Points:")
        for i in range(8):
            for j in range(4):
                print("Quadrant " + str(j+1) + ": " + str(piece.diag_locs[i][j]))
        print("Unique Orientations:")
        print(piece.unique_ors)
        print("")


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


#nice formatting for number printing
def print_num(num):
    return str(int(100*np.round(num,2))/100.0)


#calculate and print out some basic stats for a large number of games
def calc_stats(pieces, player_type):
    global stats
    for i in range(NUM_STATS_GAMES):
        stats['num_plays'].append(0)
        stats['num_branch'].append([])

        players = [player_type(i) for i in range(NUM_PLAYERS)]
        game_start_time = time.time()
        play_game(pieces, players)
        game_end_time = time.time()

        stats['game_time'].append(game_end_time - game_start_time)
        stats['avg_branch'].append(np.mean(stats['num_branch'][-1]))
        stats['max_branch'].append(np.max(stats['num_branch'][-1]))
        stats['max_branch_turn'].append(np.argmax(stats['num_branch'][-1]))

        if ((i+1)*10)%NUM_STATS_GAMES == 0:
            print(str(int(100*(i+1.0)/NUM_STATS_GAMES)) + '%')

    print()
    print('Games played: ' + str(stats['num_games']))
    print_str = 'Win %:'
    for i in range(NUM_PLAYERS):
        print_str += ' Player ' + str(i+1) + ' - ' + print_num(100*float(stats['num_wins'][i])/stats['num_games']) + ', '
    print(print_str)
    print('Time per game (s): ' + print_num(np.mean(stats['game_time'])) + ' +\\- ' + print_num(np.std(stats['game_time'])))
    print('Plays per game: ' + print_num(np.mean(stats['num_plays'])) + ' +\\- ' + print_num(np.std(stats['num_plays'])))
    print('Avg. branching factor: ' + print_num(np.mean(stats['avg_branch'])) + ' +\\- ' + print_num(np.std(stats['avg_branch'])))
    print('Max branching factor: ' + print_num(np.mean(stats['max_branch'])) + ' +\\- ' + print_num(np.std(stats['max_branch'])))
    print('Max branching turn: ' + print_num(np.mean(stats['max_branch_turn'])) + ' +\\- ' + print_num(np.std(stats['max_branch_turn'])) \
          + ' (round ' + str(int(np.floor(np.mean(stats['max_branch_turn'])/NUM_PLAYERS))) + ')')


if __name__ == '__main__':
    pieces = read_pieces(PIECES_FILE)
    players = [RandomBot(i) for i in range(NUM_PLAYERS)]
    if TRACK_STATS:
        calc_stats(pieces, RandomBot)
    else:
        play_game(pieces, players)
