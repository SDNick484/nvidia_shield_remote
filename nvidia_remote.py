#! /usr/bin/env python

from adb import adb_commands
from adb.sign_pythonrsa import PythonRSASigner
import nvidia
import tkinter as tk
import pathlib

### Specify your Shield TV's IP & Port here
#SHIELD_IP_PORT = "192.168.1.130:5555" #<-- Example
SHIELD_IP_PORT = None

def main():
    window = tk.Tk()
    window.wm_title("Nvidia Shield Remote") #Makes the title that will appear in the top left
    window.config(background = "#000000")

    # POWER
    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Power", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("power"))
    frame.grid(row=0, column=0, padx=5, pady=5)

    # MENU
    window.columnconfigure(2, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Menu", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("menu"))
    frame.grid(row=0, column=2, padx=5, pady=5)

    # UP
    window.columnconfigure(1, weight=1)
    window.rowconfigure(1, weight=1)
    frame = tk.Button( master=window, text="Up", relief=tk.RAISED, borderwidth=1, height = 1, width = 3, command = lambda : device.press("up"))
    frame.grid(row=1, column=1, padx=5, pady=5)

    # LEFT
    window.columnconfigure(2, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Left", relief=tk.RAISED, borderwidth=1, height = 1, width = 3, command = lambda : device.press("left"))
    frame.grid(row=2, column=0, padx=5, pady=5)

    # ENTER
    window.columnconfigure(2, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Enter", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("center"))
    frame.grid(row=2, column=1, padx=5, pady=5)

    # RIGHT
    window.columnconfigure(2, weight=1)
    window.rowconfigure(2, weight=1)
    frame = tk.Button( master=window, text="Right", relief=tk.RAISED, borderwidth=1, height = 1, width = 3, command = lambda : device.press("right"))
    frame.grid(row=2, column=2, padx=5, pady=5)

    # DOWN
    window.columnconfigure(1, weight=1)
    window.rowconfigure(3, weight=1)
    frame = tk.Button( master=window, text="Down", relief=tk.RAISED, borderwidth=1, height = 1, width = 3, command = lambda : device.press("down"))
    frame.grid(row=3, column=1, padx=5, pady=5)

    # REWIND
    window.columnconfigure(4, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Rewind", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("rewind"))
    frame.grid(row=4, column=0, padx=5, pady=5)

    # FAST FORWARD
    window.columnconfigure(4, weight=1)
    window.rowconfigure(2, weight=1)
    frame = tk.Button( master=window, text="F Fwrd", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("ff"))
    frame.grid(row=4, column=2, padx=5, pady=5)

    # VOL UP
    window.columnconfigure(4, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Vol Up", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("volume up") )
    frame.grid(row=5, column=0, padx=5, pady=5)

    # PLAY
    window.columnconfigure(4, weight=1)
    window.rowconfigure(2, weight=1)
    frame = tk.Button( master=window, text="Play", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("play/pause") )
    frame.grid(row=5, column=2, padx=5, pady=5)

    # VOL DOWN
    window.columnconfigure(4, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Vol Dn", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("volume down") )
    frame.grid(row=6, column=0, padx=5, pady=5)

    # HOME
    window.columnconfigure(4, weight=1)
    window.rowconfigure(0, weight=1)
    frame = tk.Button( master=window, text="Home", relief=tk.RAISED, borderwidth=1, height = 2, width = 5, command = lambda : device.press("home") )
    frame.grid(row=6, column=2, padx=5, pady=5)

    # NETFLIX
    logo = tk.PhotoImage(file="./assets/netflix_logo.png")
    frame = tk.Button( master=window, image = logo, bg="black", highlightbackground="black", highlightcolor="black", borderwidth=0, command = lambda : device.launch("netflix") )
    frame.grid(row=7, column=1)

    # HULU
    hulu= tk.PhotoImage(file="./assets/hulu_logo.png")
    frame = tk.Button( master=window, image = hulu, bg="black", highlightbackground="black", highlightcolor="black", borderwidth=0, command = lambda : device.launch("hulu") )
    frame.grid(row=8, column=1)

    # YOUTUBE
    yt = tk.PhotoImage(file="./assets/youtube_logo.png")
    frame = tk.Button( master=window, image = yt, bg="black", highlightbackground="black", highlightcolor="black", borderwidth=0, command = lambda : device.launch("youtube") )
    frame.grid(row=9, column=1)

    # YOUTUBE TV
    yttv= tk.PhotoImage(file="./assets/youtube_tv_logo.png")
    frame = tk.Button( master=window, image = yttv, bg="black", highlightbackground="black", highlightcolor="black", borderwidth=0, command = lambda : device.launch("youtubetv") )
    frame.grid(row=10, column=1)

    # VUDU
    vudu = tk.PhotoImage(file="./assets/vudu_logo.png")
    frame = tk.Button( master=window, image = vudu, bg="black", highlightbackground="black", highlightcolor="black", borderwidth=0, command = lambda : device.launch("vudu") )
    frame.grid(row=11, column=1)

    # DISNEY+
    disney= tk.PhotoImage(file="./assets/disney_logo.png")
    frame = tk.Button( master=window, image = disney, bg="black", highlightbackground="black", highlightcolor="black", borderwidth=0, command = lambda : device.launch("disney") )
    frame.grid(row=12, column=1)

    window.mainloop()

if __name__ == "__main__":
    
    ### Checking for ADB Keys before proceeding
    file = pathlib.Path("adbkey.pub")
    if not file.exists ():
        print ("ADB Key not found, please set up Remote ADB before proceeding")
        quit()

    ### Check if Shield's IP & Port are set
    if not SHIELD_IP_PORT:
        print("Please udpate nvidia_cli.py with your Shield's IP and port")
        quit()

    ### Set up device
    device = nvidia.shield( SHIELD_IP_PORT ) 

    main()

