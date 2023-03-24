
import tkinter as tk
from win32gui import GetForegroundWindow, ShowWindow, FindWindow, SetWindowLong, GetWindowLong, SetLayeredWindowAttributes
from win32con import SW_MINIMIZE, WS_EX_LAYERED, WS_EX_TRANSPARENT, GWL_EXSTYLE, LWA_ALPHA, WS_EX_NOACTIVATE

class Overlay:
    """
    Creates an overlay window using tkinter
    Uses the "-topmost" property to always stay on top of other Windows
    """
    def __init__(self):
        self.set_text = ""
        self.root = tk.Tk()

        # Set up Ping Label
        #self.text = tk.StringVar()

        #self.label = tk.Label(
        #    self.root,
        #    textvariable=self.text,
        #    font=('Consolas', '32'),
        #    fg='white',
        #    bg='grey19',
        #    anchor='nw',
        #    justify=tk.LEFT
        #)
        
        self.canvas = tk.Canvas(self.root, width=2560, height=1440, bd=0, highlightthickness=0, bg="white",takefocus=0,state="disabled")
        self.center = self.canvas.create_text((2560/2,100),text="Test",font=('Consolas','32'),fill='white')
        self.top = self.canvas.create_text( (int(2560/4)+50,int(1440 - 1440/8)),text="Test",font=('Consolas','120'),fill='white',anchor='w')
        #self.border = self.canvas.create_rectangle(0,0, 2560,1440, width=0, outline='white')
        self.border = self.canvas.create_rectangle(484,1172, 1823,1426, width=0, outline='white')


        #self.progress = self.canvas.create_rectangle(484,1172, 1823, 1172+12, width=0, outline='red', fill='red')
        #self.steps = 1823 - 484
        
        self.progressL = self.canvas.create_rectangle(0,1440-20, 2560, 1440, width=0, outline='red', fill='red')
        self.progressR = self.canvas.create_rectangle(0,1440-20, 2560, 1440, width=0, outline='red', fill='red')
        self.steps = 2560
        self.set_progress(0)


        #self.label.grid(row=0, column=0)
        #self.center.grid(row=1,column=1)
        #self.label.pack(fill=tk.BOTH,expand=True)
        #self.center.pack(fill=tk.BOTH,expand=True)
        #self.center.place(relx=0.0,rely=0.0,relheight=1.0,relwidth=1.0)
        
        #self.label.place(relx=0.0,rely=0.0,relheight=1.0,relwidth=1.0)
        self.canvas.place(relx=0.5,rely=0.5,anchor='center',relheight=1.0, relwidth=1.0)


        # Define Window Geometery
        self.root.overrideredirect(True)
        #self.setClickthrough(self.root.winfo_id())
        #self.setClickthrough(self.canvas.winfo_id())
        #self.root.geometry("+5+5")
        self.root.geometry("2560x1440")
        self.root.lift()
        self.root.configure(background="white",takefocus=0)
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-disabled", True)
        self.root.wm_attributes("-transparentcolor", "white")
        self.root.attributes('-alpha',0.5)
        self.root.config(takefocus=0)
        #self.root.attributes('-fullscreen', True)
        #self.canvas.config(insertbackground='white',state="disabled")

    def setClickthrough(self, hwnd):
        print("setting window properties")
        try:
            styles = GetWindowLong(hwnd, GWL_EXSTYLE)
            #styles = styles | WS_EX_LAYERED | WS_EX_TRANSPARENT
            styles = styles | WS_EX_NOACTIVATE | WS_EX_TRANSPARENT
            SetWindowLong(hwnd, GWL_EXSTYLE, styles)
            #SetLayeredWindowAttributes(hwnd, 0, 255, LWA_ALPHA)
        except Exception as e:
            print(e)

    def set(self, text, color='grey98') -> None:
        self.set_text = text
        #self.text.set(text)
        self.canvas.itemconfig(self.center,text=text)
        self.canvas.itemconfig(self.center,fill=color)
        self.root.update()

    def set_top(self, text, color='grey98') -> None:
        self.canvas.itemconfig(self.top,text=text)
        self.canvas.itemconfig(self.top,fill=color)
        self.root.update()
    
    def set_border(self, width=0, color='grey98') -> None:
        self.canvas.itemconfig(self.border,width=width)
        self.canvas.itemconfig(self.border,outline=color)
    def set_progress(self, p=0, lcolor='grey98', rcolor='white'):
        x0, y0, x1, y1 = self.canvas.coords(self.progressL)
        self.canvas.coords(self.progressL,x0,y0,x0+int(p*self.steps),y1)
        self.canvas.itemconfig(self.progressL,outline=lcolor,fill=lcolor)
        x0, y0, x1, y1 = self.canvas.coords(self.progressR)
        self.canvas.coords(self.progressR,x1-int((1-p)*self.steps),y0,x1,y1)
        self.canvas.itemconfig(self.progressR,outline=rcolor,fill=rcolor)

    def get(self):
        return self.set_text

    def run(self) -> None:
        self.root.mainloop()