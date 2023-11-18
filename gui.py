import tkinter as tk
from tkinter.ttk import * 
from tkinter.font import Font

import sv_ttk
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

        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.callback)

        # Style
        self.font = Font(self.root,
                         family="Segoe UI Variable Small", 
                         size=12)
        self.s = Style()
        self.s.configure('BIN.TButton', bd=0)
        self.s.configure('ROOM.TButton', foreground='green2')


        # Binaural audio selector =====================
        self.w0 = Label(self.root, 
                        text = "Use Binaural Audio: ",
                        font=self.font).place(x=40, y=15)

        self.useBin = tk.BooleanVar()
        self.w1 = Checkbutton(self.root, 
                              style='Switch.TCheckbutton', 
                              variable=self.useBin).place(x=220, y=12)

        self.hrtfSelector = tk.StringVar(self.root)
        self.hrtfSelector.set("MIT") # default value
        self.w3 = Combobox(self.root, 
                           textvariable=self.hrtfSelector, 
                           values=["LISTEN", "MIT", "SOFA"]).place(x=290, y=10, width=150)
        
        self.s0 = Separator(self.root, 
                            orient='horizontal').place(x=30, y=52, width=420)



        # Room FIR selector =====================
        self.w0 = Label(self.root, 
                        text = "Using Room FIR: ",
                        font=self.font).place(x=40, y=69)
        
        self.colorRoom = tk.BooleanVar()
        self.w2 = Checkbutton(self.root, 
                              style='Switch.TCheckbutton', 
                              variable=self.colorRoom).place(x=220, y=65)

        self.firSelector = tk.StringVar(self.root)
        self.firSelector.set('Aula Carolina')
        self.w4 = Combobox(self.root, 
                           textvariable=self.firSelector, 
                           values=['Booth',     'Office',       'Meeting',
                                   'Lecture 1', 'Lecture 2',    'Stairway 1',
                                   'Stairway 2','Stairway 3',   'Corridor',
                                   'Bathroom',  'Aula Carolina']).place(x=290, y=63, width=150)


        self.s0 = Separator(self.root, 
                            orient='horizontal').place(x=30, y=105, width=420)

        
        # Frame for Binaural Settings ========
        self.frm = Labelframe(self.root, text='Binaural Settings').place(x=30, y=130, width=420, height=330)
        
        # Sliders ============================
        self.variable2 = tk.StringVar(self.root)
        self.variable2.set("0" + u'\u00b0') # default value for Azimuth slider
        self.horAngle = Scale(self.root, 
                              from_=-180, 
                              to=180, 
                              length=200, 
                              orient='horizontal', 
                              command=updateHorizontal)
        self.horAngle.place(x=140, y=180)   # Placing the azimuth slider
        self.a1 = Label(self.root,          # Value displaying the azimuth
                        textvariable=self.variable2, 
                        font=self.font).place(x=105,y=180)


        self.variable3 = tk.StringVar(self.root)
        self.variable3.set("0" + u'\u00b0') # default value for elevation slider
        self.vertAngle = Scale(self.root, 
                               from_=90, 
                               to=-90, 
                               length=200, 
                               orient='vertical', 
                               command=updateVertical)
        self.vertAngle.place(x=230, y=230)  # Placing the elevation slider
        self.a2 = Label(self.root,          # Value displaying the elevation
                        textvariable=self.variable3, 
                        font=self.font).place(x=105,y=320)


        sv_ttk.set_theme("dark")        # Set the theme 
        self.root.geometry("480x490")   # Create the window size
        self.root.mainloop()


