from tkinter import *
from tkinter.ttk import * 
from tkinter.font import Font
# from typing import Any

import threading


class GUI(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.start()
        # self.number = 1

    def callback(self):
        self.root.quit()

    def run(self):
        def updateHorizontal(location):
            self.variable2.set(str(int(float(location))) + u'\u00b0')
        def updateVertical(location):
            self.variable3.set(str(int(float(location))) + u'\u00b0')
        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)


        self.font = Font(self.root, size=9)
        self.w0 = Label(self.root, text = "Using HRTF set: ", font=self.font).place(x=10, y=11)


        self.hrtfSelector = StringVar(self.root)
        self.hrtfSelector.set("MIT") # default value
        # self.w3 = OptionMenu(self.root, self.variable, "LISTEN", "MIT", "LISTEN", "SOFA").place(x=110, y=10)
        self.w3 = OptionMenu(self.root, self.hrtfSelector, "LISTEN", "MIT", "LISTEN").place(x=110, y=10)


        self.variable2 = StringVar(self.root)
        self.variable2.set("0" + u'\u00b0') # default value
        self.horAngle = Scale(self.root, from_=-180, to=180, length=200, orient='horizontal', command=updateHorizontal)
        self.horAngle.place(x=50, y=60)
        self.a1 = Label(self.root, textvariable=self.variable2, font=self.font).place(x=15,y=60)
        # self.w1.set(0)
        # self.w1.pack(padx=10,pady=10)

        self.variable3 = StringVar(self.root)
        self.variable3.set("0" + u'\u00b0') # default value
        self.vertAngle = Scale(self.root, from_=90, to=-90, length=200, orient='vertical', command=updateVertical)
        self.vertAngle.place(x=140, y=110)
        self.a2 = Label(self.root, textvariable=self.variable3, font=self.font).place(x=15,y=200)
        # self.w2.set(0)
        # self.w2.pack(padx=10,pady=10)
        
        self.root.geometry("280x330")
        self.root.mainloop()


