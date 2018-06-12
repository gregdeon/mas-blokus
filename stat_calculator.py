import time
import numpy as np
from constants import *
from game import play_game
from util import *

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