BOARD_WIDTH = 20
BOARD_HEIGHT = 20
NUM_PIECES = 21
START_SCORE = 89
NUM_PLAYERS = 4
ALL_ONES = 255
CORNER_SENTINEL = ALL_ONES
NUM_STATS_GAMES = 100
PIECES_FILE = 'pieces.txt'
VERBOSE = False
EXTRA_TRACKING = True
TRACK_STATS = True
PRINT_COLOUR = True

if PRINT_COLOUR:
    from colorama import Fore, Back, Style, init
    init(convert=True)
    FORE_ARRAY = [Fore.RED, Fore.BLUE, Fore.GREEN, Fore.YELLOW]
    BACK_ARRAY = [Back.RED, Back.BLUE, Back.GREEN, Back.YELLOW]

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