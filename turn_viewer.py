import os
import json
import numpy as np

from colorama import Fore, Back, Style, init
from game import Board
from game import idtobits

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
while(True):
	game_input = input("game: ")
	if(game_input == "n"):
		game_num += 1
	elif(game_input == "exit"):
		break
	else:
		game_num = int(game_input)
	turn_num = 0
	game = all_data[game_num]
	while(True):
		turn_input = input("turn: ")
		if(turn_input == "n" or turn_input == ""):
			turn_num += 1
		elif(turn_input == "b"):
			break
		else:
			turn_num = int(turn_input)
		states = game["states"]
		turn = states[turn_num]
		not_board = Board()

		not_board.board[1:-1, 1:-1] = idtobits(np.array(turn["board"]))

		not_board.print_board()
		print(turn["player_turn"]-1)
		print(turn["pieces_left"])
	
#interesting games:
#599

