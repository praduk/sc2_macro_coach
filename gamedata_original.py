
from PIL import Image, ImageDraw, ImageTk, ImageOps
import pytesseract
#from pytesseract import Output
#import pyscreenshot as ss
import d3dshot
import threading
import math
import pyttsx3
import time
import queue
import random
import re

from system_hotkey import SystemHotkey

import keyboard

ss = d3dshot.create()


# convert image to black and white
def black_white(im, threshold=50):
    try:
        ret = im.convert('L').point(lambda x : 255 if x > threshold else 0,mode='1')
        return ret
    except Exception as e:
        print(e)
        return im

def get_screenshot(x0,y0,xf,yf,threshold=20):
    #image = 
    #draw = ImageDraw.Draw(image)
    #return black_white(ImageOps.invert(ss.grab(bbox=(x0, y0, xf, yf),childprocess=False).convert('L'))).convert("RGB")
    #return ImageOps.invert(ss.grab(bbox=(x0, y0, xf, yf),childprocess=False).convert('L')).convert("RGB")
    #rgb_image = ss.grab(bbox=(x0, y0, xf, yf),childprocess=False).convert("RGB")
    rgb_image = ss.screenshot(region=(x0,y0,xf,yf)).convert("RGB")
    #black_white_image = black_white(ImageOps.invert(rgb_image.convert('L')),threshold)
    black_white_image = ImageOps.invert(rgb_image.convert('L'))
    #black_white_image.save('timer.png')
    #rgb_image.save('timer.png')
    return black_white_image

def get_number(x0,y0,xf,yf, threshold=50):
    config = '-c tessedit_char_whitelist=0123456789:  --psm 8'
    return pytesseract.image_to_string(get_screenshot(x0,y0,xf,yf,threshold),config=config).partition('\n')[0]
def get_name(x0,y0,xf,yf, threshold=50):
    #config = '-c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<>  --psm 8'
    time.sleep(0.2)
    return pytesseract.image_to_string(get_screenshot(x0,y0,xf,yf,threshold)).partition('\n')[0]




def timer_string(timer_seconds):
    if timer_seconds>0:
        return str(timer_seconds//60) + ":" + str(timer_seconds%60)
    else:
        return "99:99"

def timer_seconds(timer_string,last_time=0):
    s = timer_string.split(':')
    #print("timer_string = " + timer_string)
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

def timer():
    try:
        string = get_number(359,1036,464, 1066,threshold=200)
        seconds = timer_seconds(string)
        return seconds
    except:
        #print("No Timer!")
        return -1

class TimeTracker:
    def __init__(self):
        self.last_time = -1
        self.last_timer = time.time()
        self.failure_count = 0
    def time(self):
        t = timer()
        if self.last_time < 0 and t < 0 :
            return -1
        if self.last_time < 0 and t >= 0:
            self.last_time = t
            self.timer = time.time()
            self.failure_count = 0
            return self.last_time
        time_now = time.time()
        if self.last_time < 0:
            return self.last_time
        predict_time = int(round(self.last_time + + 0.3 + 0.5 + (time_now - self.last_timer)*1.0))
        if abs(t - predict_time) < 2 or t==0:
            self.last_time = t
            self.last_timer = time_now
            self.failure_count = 0
            return self.last_time
        self.failure_count += 1
        if self.failure_count > 20:
            self.last_time = -1
            self.last_timer = time_now
            self.failure_count = 0
            if t > 0:
                self.last_time = t
            return self.last_time
        return predict_time

def idle():
    try:
        return int(get_number(64,997,104,1019))
    except:
        return 0

def minerals():
    try:
        return int(get_number(2025,31-4,2056+100,46+4))
    except:
        return 0

def gas():
    try:
        return int(get_number(2190,31-4,2190+100,46+4))
    except:
        return 0

def supply():
    try: 
        s = get_number(2359,31-4,2359+125,46+4).split('/')
        return (int(s[0]),int(s[1]))
    except:
        return (0,0)

def player_names():
    #p1 = ""
    #p2 = ""
    #try:
    p1=get_name(332,589,584,621)
    print(p1)
    #except:
    #    p1=""
    #try:
    p2=get_name(2046,589,2226,621)
    print(p2)
    #except:
    #    p2=""
    return (p1,p2)


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
        tts_engine.setProperty('voice',tts_engine.getProperty('voices')[2].id)
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

class Monitor(threading.Thread):
    def __init__(self):
        self.tts = TTSThread()
        self.events = {}
        self.last_t = 0
        self.last_scv = -1
        self.remind_scv = False
        self.next_scv_warning = -1

        self.tts.daemon = True
        self.tts.start()
        self.tt = TimeTracker()
    def __del__(self):
        self.tts.kill()
    def tick(self):
        # Worker production reminder
        tnow = time.time()
        self.t = self.tt.time()
        print(self.t)
        if self.t>0:
            if self.last_scv >= 0 and self.remind_scv and (tnow - self.last_scv) >  14:
                self.tts.say("Reminder: Workers")
                self.remind_scv = False
                self.next_scv_warning = tnow + 24
                self.next_scv_warning_count = 0
            if self.next_scv_warning > 0 and tnow > self.next_scv_warning:
                self.next_scv_warning_count = self.next_scv_warning_count + 1
                self.last_scv = -1
                ntimes = self.next_scv_warning_count
                if ntimes == 1:
                    #self.tts.say("Warning: Cut Workers")
                    self.next_scv_warning = self.next_scv_warning + 12
                elif ntimes == 2:
                    #self.tts.say("Warning: Cut Workers Twice")
                    self.next_scv_warning = self.next_scv_warning + 12
                elif ntimes == 3:
                    #self.tts.say("Warning: Cut Workers Thrice")
                    self.next_scv_warning = -1

        #print(str(tnow) + ' time = ' + str(self.t//60) + ":" + str(self.t%60))
        if self.t<0:
            self.last_t = 0
            return
        if self.t == 0:
            if self.last_t > 10 or self.last_t < 0:
                self.tts.say("Game Started")
        if self.t <= self.last_t and self.t > self.last_t-10:
            return

        forward_looking = 2
        ft = self.t + forward_looking
        #if (ft%12) == 0 and ft < 540:
        #    self.tts.say("S C V")

        if ft in self.events:
            self.tts.say(self.events[ft])
        self.last_t = self.t


        #(p1,p2) = player_names()
        #print(p1,p2)


    def hit_scv_hotkey(self):
        self.last_scv = time.time()
        self.remind_scv = True
        self.next_scv_warning = -1
    def reset(self):
        self.last_t = -1
        self.last_scv = -1
        self.remind_scv = False
        self.next_scv_warning = -1

def parse_events(file, offset=0):
    ret = {}
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            s = line.split(" ",maxsplit=1)
            time = timer_seconds(s[0].strip()) + offset
            desc = s[1].strip()
            ret[time] = desc
    return ret

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
    m.reset()

def terran(args):
    #print("Terran")
    m.tts.say("Terran")
    m.events = parse_events("TvT.txt")
    m.reset()

def protoss(args):
    #print("Protoss")
    m.tts.say("Protoss")
    m.events = parse_events("TvP.txt")
    m.reset()

def none(args):
    #print("None")
    m.tts.say("None")
    m.events = {}
    m.reset()

def scv_production():
    #print("SCV Hotkey")
    m.hit_scv_hotkey()

hk = SystemHotkey()
hk.register(('control','shift','z'), callback=zerg)
hk.register(('control','shift','x'), callback=terran)
hk.register(('control','shift','c'), callback=protoss)
hk.register(('control','shift','b'), callback=stop_program)
hk.register(('control','shift','v'), callback=none)

keyboard.add_hotkey('s', scv_production)
#hk.register(('s',), callback=scv_production)

while not stop:
    m.tick()
    time.sleep(0.1)
print("Stopped")

#get_screenshot(64,997,104,1019)
#print(timer())
#print(idle())
#print(minerals())
#print(gas())
#print(supply())
#
#m = Monitor()
#t0 = time.perf_counter()
#m.snapshot()
#tf = time.perf_counter()
#dtime = tf - t0
#print("Snapshot took " + str(dtime) + " seconds")
#
#t0 = time.perf_counter()
#img = ss.screenshot()
#tf = time.perf_counter()
#dtime = tf - t0
#print("Fullscreen took " + str(dtime) + " seconds")
#
#m.say_async("You have " + str(m.m) + " minerals")
#m.say_async("You have " + str(m.g) + " gas")
#m.say_async("You have " + str(m.w) + " idle workers")
#m.say_async("You have " + str(m.s[0]) + " out of " + str(m.s[1]) + " supply")
#m.say_flush()


#test = TTSThread()
#test.start()
#test.say("Hello")
#time.sleep(3)
#test.say("Hello 2")
#test.say("Hello 3")
#test.say("Hello 4")
#test.say("Hello 5")
#time.sleep(2)
#test.kill()
#print("Killed")