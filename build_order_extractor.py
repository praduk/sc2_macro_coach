#!/usr/bin/python3

import glob
import os
import pathlib
import spawningtool.parser
from pprint import pprint
import subprocess

############### HELPER ROUTINES ###################

def get_replay_files(path):
    return pathlib.Path(path).rglob('*.SC2Replay')

############### MAIN ###################

replay_path_root = r'C:\Users\Pradu\Documents\StarCraft II\Accounts\837153526\1-S2-1-12516159\Replays\Multiplayer\Build_Orders'

# List of Directories to Search
for replay_path in get_replay_files(replay_path_root):
    replay_file = str(replay_path)
    replay_stem = replay_path.stem
    output_file = os.path.splitext(replay_file)[0] + ".txt"
    if os.path.exists(output_file):
        continue
    parse = spawningtool.parser.parse_replay(replay_file)

    # Select Player
    player = None
    if parse["players"][1]["race"] == "Terran" and parse["players"][2]["race"] == "Terran":
        if parse["players"][2]["is_winner"]:
            player = parse["players"][2]
        else:
            player = parse["players"][1]
    else:
        if parse["players"][2]["race"] == "Terran":
            player = parse["players"][2]
        else:
            player = parse["players"][1]
    if player is None:
        continue

    print(replay_file + " (" + player["name"] + ") ")

    with open(output_file, 'w') as f:
        first_orbital = True
        first_barracks = True
        for action in player["buildOrder"]:
            if action["is_worker"]:
                continue
            itemName = action["name"]
            if itemName == "SupplyDepot":
                itemName = "Depot"
            if itemName == "Barracks" and first_barracks:
                itemName = "!barracks"
                first_barracks = False
            if itemName == "CommandCenter":
                itemName = "Command Center"
            if itemName == "OrbitalCommand":
                itemName = "Orbital Command"
            if itemName == "Orbital Command" and first_orbital:
                itemName = "!orbital"
                first_orbital = False
            if itemName == "Viking Fighter":
                itemName = "Viking"
            if itemName == "SiegeTank":
                itemName = "Siege Tank"
            if itemName == "FactoryTechLab":
                itemName = "Factory Tech Lab"
            if itemName == "BarracksTechLab":
                itemName = "Barracks Tech Lab"
            if itemName == "StarportTechLab":
                itemName = "Starport Tech Lab"
            if itemName == "FactoryReactor":
                itemName = "Factory Reactor"
            if itemName == "BarracksReactor":
                itemName = "Barracks Reactor"
            if itemName == "StarportReactor":
                itemName = "Starport Reactor"
            print(action["time"] + " " + itemName, file=f)

os.startfile(replay_path_root)