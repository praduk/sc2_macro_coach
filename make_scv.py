import threading
import pyttsx3
import time
import queue
import keyboard
from system_hotkey import SystemHotkey

voice_volume = 0.8 # from 0 to 1

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
        tts_engine.setProperty('voice',tts_engine.getProperty('voices')[1].id)
        tts_engine.setProperty('volume',voice_volume)
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


done = False
quiet = False
tts = TTSThread()
tts.start()

def quiet_toggle(args):
    global quiet
    quiet = not quiet
    
def done_trigger(args):
    global done
    done = True

hk = SystemHotkey()
hk.register(('control','shift','z'), callback=quiet_toggle)
hk.register(('control','shift','x'), callback=done_trigger)

while not done:
    if not quiet:
        tts.say("Make SCV")
        for i in range(90):
            time.sleep(0.1)
            if done:
                break
    else:
        time.sleep(0.1)

tts.kill()