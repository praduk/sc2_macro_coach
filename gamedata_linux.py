#!/usr/bin/python3
import collections
try:
    collectionsAbc = collections.abc
except AttributeError:
    collectionsAbc = collections

from re import I
from sys import platform
import threading
import math
import time
import queue
import random
import json
import socket
import hashlib
import os
import collections
from system_hotkey import SystemHotkey
from datetime import datetime

import gtts
from audioplayer import AudioPlayer

self_names = set(line.strip() for line in open('player_names.txt'))
bo_files = list(line.strip() for line in open('build_order_files.txt'))

enable_timer = True
enable_in_replay = True
mute = False

made_scv = False
time_of_1 = datetime.now()
made_orbital = False


print("Self Names:")
print(self_names)

print("Build Order Files vs [T, Z, P, R]:")
print(bo_files)


def timer_string(timer_seconds):
    timer_seconds = int(timer_seconds)
    if timer_seconds>0:
        return str(timer_seconds//60).zfill(2) + ":" + str(timer_seconds%60).zfill(2)
    else:
        return "99:99"

def dtimer_string(timer_seconds):
    timer_seconds = int(timer_seconds)
    if timer_seconds>=0:
        return " " + str(timer_seconds//60).zfill(2) + ":" + str(timer_seconds%60).zfill(2)
    else:
        timer_seconds = -timer_seconds
        return "-" + str(timer_seconds//60).zfill(2) + ":" + str(timer_seconds%60).zfill(2)

def timer_seconds(timer_string,last_time=0):
    s = timer_string.split(':')
    min = 0
    ses = 0
    if( len(s) == 1):
        min = 0
        secs = int(s[0])
    else:
        if len(s[0])==0:
            min = 0
        else:
            min = int(s[0])
        secs = int(s[1])
        if min > 30:
            if min > 100:
                min = min % 100
            else:                    
                min = min % 10
        while secs > 60:           
            secs = secs // 10
    #print( "parsed_time = " + str(min) + ":" + str(secs))
    return 60*min + secs

class GameState:
    def __init__(self):
        self.in_game = False
        self.is_replay = False
        self.t = 0
        self.player = ""
        self.race = ""
        self.type = ""

game_time_buffer = collections.deque(maxlen=10)
def game_state():
    gs = GameState()

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('localhost',6119))
    s.sendall(b"GET /ui HTTP/1.1\nHost: localhost\n\n")
    s.recv(4096) # remove headers
    raw = s.recv(4096).decode()
    data = None
    try:
        data = json.loads(raw)
    except:
        return None

    if data["activeScreens"]:
        return gs

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('localhost',6119))
    s.sendall(b"GET /game HTTP/1.1\nHost: localhost\n\n")
    s.recv(4096) # remove headera
    try
        raw = s.recv(4096).decode()
    except
        return None
    data = json.loads(raw)

    if data['isReplay']:
        gs.is_replay = True
    else:
        gs.is_replay = False
    gs.t = data['displayTime']
    if not data['players']:
        return gs
    if data['players'][0]["result"] != "Undecided":
        return gs
    gs.in_game = True

    # self_names = {'Slumdog','Mechachu','llllllllllll'}
    player_index = 0
    if data['players'][0]["name"] in self_names and data['players'][0]["race"][0].upper() == 'T':
        player_index = 1
    if data['players'][1]["name"] in self_names and data['players'][1]["race"][0].upper() == 'T':
        player_index = 0

    gs.player = data['players'][player_index]["name"]
    gs.race = data['players'][player_index]["race"][0].upper()
    gs.type = data['players'][player_index]["type"][0]

    # adjust gs.t
    global game_time_buffer
    if gs.t==0:
        for i in range(0,10):
            game_time_buffer.append(0)
    game_time_buffer.append(gs.t)
    gs.tf = sum(game_time_buffer)/len(game_time_buffer) + 0.5
    gs.t = int(math.floor(gs.tf))

    return gs

class TTSThread(threading.Thread):
     def __init__(self):
         self.tts_queue = queue.Queue()
         self.done = False
         super().__init__()
     def kill(self):
         self.done=True
     def say(self, text):
         print("Say: " + text)
         self.tts_queue.put(text)
     def run(self):
         while True:
             if self.done:
                 break
             if self.tts_queue.empty():
                 time.sleep(0.1)
             else:
                 text = self.tts_queue.get()
                 if not mute:
                     filename = "tts/" + hashlib.sha256(text.encode()).hexdigest() + ".mp3"
                     if not os.path.exists("tts"):
                         os.makedirs("tts")
                     if not os.path.exists(filename):
                         tts = gtts.gTTS(text)
                         tts.save(filename)
                     if os.path.exists(filename):
                         ap = AudioPlayer(filename)
                         ap.volume = 25
                         ap.play(block=True)

class Monitor(threading.Thread):
    def __init__(self):
        self.tts = TTSThread()
        self.events = {}
        self.last_t = -1
        self.tts.daemon = True
        self.tts.start()
        self.scv_sync = 0
        self.last_scv = 1
        super().__init__()
    def __del__(self):
        self.tts.kill()

    def process_command(self, command, gs, forward_looking):
        print('Command : ' + command)
        if command=="scv_sync":
            if not forward_looking:
                self.scv_sync = gs.t
        if command=="barracks":
            if forward_looking:
                self.tts.say("Barracks")
            else:
                self.scv_sync = gs.t
        elif command=="orbital":
            if forward_looking:
                self.tts.say("Orbital")
            else:
                self.scv_sync = gs.t + 24
        elif command.startswith("stop_scv_until"):
            if not forward_looking:
                s = command.split(" ",maxsplit=1)
                time = timer_seconds(s[1].strip())
                self.scv_sync = time

    def init(self):
        self.last_t = -1
        made_scv = False
        self.last_scv = 0
        self.scv_sync = 0
        self.scv_warning = False


    def tick(self):
        global made_scv
        global made_orbital

        gs = game_state()

        if gs is None:
            return

        global enable_in_replay
        if not gs.in_game or ((not enable_in_replay) and gs.is_replay):
            self.init()
            return
        if self.last_t < 0:
            bo_files = list(line.strip() for line in open('build_order_files.txt'))
            # Load Events
            if gs.race == "T":
                m.events = parse_events(bo_files[0])
            elif gs.race == "Z":
                m.events = parse_events(bo_files[1])
            elif gs.race == "P":
                m.events = parse_events(bo_files[2])
            elif gs.race == "R":
                m.events = parse_events(bo_files[3])
            self.init()

            # Player Introductions
            notes = player_notes(gs.player, gs.type)
            if notes:
                self.tts.say("opponent likes " + notes)


        if gs.t > self.last_t:
            forward_looking = 4
            ft = gs.t + forward_looking
            if ft in self.events:
                data = self.events[ft]
                if data[0] != '!':
                    self.tts.say(self.events[ft])
                else:
                    self.process_command(data[1:],gs,True)
            if gs.t in self.events:
                data = self.events[gs.t]
                if data[0] == '!':
                    self.process_command(data[1:], gs, False)
        
        self.last_t = gs.t

        

def parse_events(file, offset=0):
    ret = {}
    try:
        with open(file) as f:
            lines = f.readlines()
            for line in lines:
                s = line.split(" ",maxsplit=1)
                time = timer_seconds(s[0].strip()) + offset
                desc = s[1].strip()
                ret[time] = desc
    except:
        print("parse_events: EXCEPTION!")
        pass
    return ret

def player_notes(player_name, race):
    augmented_player_name = player_name + "_" + race
    ret = {}
    with open("player_notes") as f:
        lines = f.readlines()
        for line in lines:
            s = line.split(":",maxsplit=1)
            if s[0]==player_name or s[0]==augmented_player_name:
                return s[1].strip()
    return None

m = Monitor()
stop = False

def stop_program(args):
    global stop
    print("Stop")
    m.tts.kill()
    stop = True
    print('Stopped')


def zerg(args):
    #print("Zerg")
    m.tts.say("Zerg")
    #m.events = parse_events("TvZ.txt")
    bo_files = list(line.strip() for line in open('build_order_files.txt'))
    m.events = parse_events(bo_files[1])

def terran(args):
    #print("Terran")
    m.tts.say("Terran")
    #m.events = parse_events("TvT.txt")
    bo_files = list(line.strip() for line in open('build_order_files.txt'))
    m.events = parse_events(bo_files[0])

def protoss(args):
    #print("Protoss")
    m.tts.say("Protoss")
    #m.events = parse_events("TvP.txt")
    bo_files = list(line.strip() for line in open('build_order_files.txt'))
    m.events = parse_events(bo_files[2])

def none(args):
    #print("None")
    m.tts.say("None")
    m.events = {}

def overlay_toggle(args):
    global enable_overlay
    enable_overlay = not enable_overlay

def mute_toggle(args):
    global mute
    mute = not mute

#def scv_production():
#    #print("SCV Hotkey")
#    m.hit_scv_hotkey()

hk = SystemHotkey()
hk.register(('control','shift','z'), callback=zerg)
hk.register(('control','shift','x'), callback=terran)
hk.register(('control','shift','c'), callback=protoss)
hk.register(('control','shift','b'), callback=stop_program)
hk.register(('control','shift','v'), callback=none)
hk.register(('control','shift','f'), callback=overlay_toggle)
hk.register(('control','shift','space'), callback=mute_toggle)

def main_function():
    m.tick()
main_function()


while not stop:
    main_function()
    time.sleep(0.1)

print("Stopped")
