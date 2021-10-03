#!/usr/bin/python3

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
from system_hotkey import SystemHotkey

import keyboard

if platform =='win32':
    import pyttsx3
else:
    import gtts
    from playsound import playsound

self_names = set(line.strip() for line in open('player_names.txt'))
bo_files = list(line.strip() for line in open('build_order_files.txt'))

print("Self Names:")
print(self_names)

print("Build Order Files vs [T, Z, P, R]:")
print(bo_files)

def timer_string(timer_seconds):
    if timer_seconds>0:
        return str(timer_seconds//60) + ":" + str(timer_seconds%60)
    else:
        return "99:99"

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

def game_state():
    gs = GameState()

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('localhost',6119))
    s.sendall(b"GET /ui HTTP/1.1\nHost: localhost\n\n")
    s.recv(4096) # remove headera
    raw = s.recv(4096).decode()
    data = json.loads(raw)

    if data["activeScreens"]:
        return gs

    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.connect(('localhost',6119))
    s.sendall(b"GET /game HTTP/1.1\nHost: localhost\n\n")
    s.recv(4096) # remove headera
    raw = s.recv(4096).decode()
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
    return gs

if platform == 'win32':
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
            tts_engine = pyttsx3.init()
            if platform == "win32":
                tts_engine.setProperty('voice',tts_engine.getProperty('voices')[1].id)
            tts_engine.setProperty('volume',1.0)
            tts_engine.startLoop(False)
            while True:
                if self.done:
                    break
                if self.tts_queue.empty():
                    tts_engine.iterate()
                    time.sleep(0.1)
                else:
                    data = self.tts_queue.get()
                    tts_engine.say(data)
            tts_engine.endLoop()
else:
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
                    filename = "tts/" + hashlib.sha256(text.encode()).hexdigest() + ".mp3"
                    if not os.path.exists("tts"):
                        os.makedirs("tts")
                    if not os.path.exists(filename):
                        tts = gtts.gTTS(text)
                        tts.save(filename)
                    playsound(filename)

class Monitor(threading.Thread):
    def __init__(self):
        self.tts = TTSThread()
        self.events = {}
        self.last_t = -1
        self.tts.daemon = True
        self.tts.start()
    def __del__(self):
        self.tts.kill()
    def tick(self):
        gs = game_state()
        if not gs.in_game:
        #if not gs.in_game or gs.is_replay:
            self.last_t = -1
            return
        if self.last_t < 0:
            # Load Events
            if gs.race == "T":
                m.events = parse_events(bo_files[0])
            elif gs.race == "Z":
                m.events = parse_events(bo_files[1])
            elif gs.race == "P":
                m.events = parse_events(bo_files[2])
            elif gs.race == "R":
                m.events = parse_events(bo_files[3])

            # Player Introductions
            notes = player_notes(gs.player, gs.type)
            if notes:
                self.tts.say("opponent likes " + notes)

        if gs.t > self.last_t:
            forward_looking = 2
            ft = gs.t + forward_looking
            if ft in self.events:
                self.tts.say(self.events[ft])

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


def zerg(args):
    #print("Zerg")
    m.tts.say("Zerg")
    m.events = parse_events("TvZ.txt")

def terran(args):
    #print("Terran")
    m.tts.say("Terran")
    m.events = parse_events("TvT.txt")

def protoss(args):
    #print("Protoss")
    m.tts.say("Protoss")
    m.events = parse_events("TvP.txt")

def none(args):
    #print("None")
    m.tts.say("None")
    m.events = {}

#def scv_production():
#    #print("SCV Hotkey")
#    m.hit_scv_hotkey()

hk = SystemHotkey()
hk.register(('control','shift','z'), callback=zerg)
hk.register(('control','shift','x'), callback=terran)
hk.register(('control','shift','c'), callback=protoss)
hk.register(('control','shift','b'), callback=stop_program)
hk.register(('control','shift','v'), callback=none)

#keyboard.add_hotkey('s', scv_production)
while not stop:
    m.tick()
    time.sleep(0.1)
print("Stopped")
