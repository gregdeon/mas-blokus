import os
import json
import numpy as np

from constants import *
from board import *
from player import Player
from random_bot import RandomBot
from stat_calculator import *
from game import *
from piece import *
from colorama import Fore, Back, Style, init

'''
Looks for files in "game_data/"
enter a game number to select a game
enter a turn number to select a turn 
or hit enter to jump to the next turn

'''


all_data = []
for root, dirs, files in os.walk("game_data"):   
    for file in files:
        if file.endswith(".txt"):
            d = json.load(open(root + "/" + file, "r"))
            all_data.append(d)
           
#list of games from individual perspectives

print("ready")

game_num = 0

turns_from_end = 20

for curr_game in all_data:
	turn_num = 0

	pieces = read_pieces(PIECES_FILE)
	players = [RandomBot(i) for i in range(NUM_PLAYERS)]
	game = Game(pieces, players)
	
	states = curr_game["states"]
	turn = states[-1*turns_from_end]
	game.board = Board(idtobits(np.array(turn["board"])))
	player = turn["player_turn"]-1
	
	if(len(game.possible_plays()) > 200):
		game.board.print_board()
		print("game: " + str(game_num))
		print("possible_plays: " + str(len(game.possible_plays())))
		print("player: " + str(turn["player_turn"]-1))
		print(turn["pieces_left"])
		
		game_input = input("enter for next ")
		if(game_input == "n" or game_input == ""):
			game_num += 1
		elif(game_input == "exit" or game_input = "e"):
			break
	
#interesting games:
#599

