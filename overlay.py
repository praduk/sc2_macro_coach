
import tkinter as tk

class Overlay:
    """
    Creates an overlay window using tkinter
    Uses the "-topmost" property to always stay on top of other Windows
    """
    def __init__(self):
        self.root = tk.Tk()

        # Set up Ping Label
        self.text = tk.StringVar()
        self.label = tk.Label(
            self.root,
            textvariable=self.text,
            font=('Consolas', '64'),
            fg='white',
            bg='grey19',
            anchor='e',
            justify=tk.LEFT
        )
        self.label.grid(row=0, column=1)
        self.closed = False


        # Define Window Geometery
        self.root.overrideredirect(True)
        self.root.geometry("+5+5")
        self.root.lift()
        self.root.wm_attributes("-topmost", True)
        self.root.wm_attributes("-disabled", True)
        self.root.wm_attributes("-transparentcolor", "grey19")
 

    def set(self, text) -> None:
        self.text.set(text)
        self.root.update()

    def get(self,text):
        return self.text.get()

    def run(self) -> None:
        self.root.mainloop()