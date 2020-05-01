from adb import adb_commands
from adb.sign_pythonrsa import PythonRSASigner
import tkinter as tk
import pathlib

SHIELD_IP_PORT = '192.168.1.130:5555'

## Checking for ADB Keys before proceeding
file = pathlib.Path("adbkey.pub")
if not file.exists ():
    print ("ADB Key not found, please set up Remote ADB before proceeding")
    quit()


class shield:
	buttons = { 
		'power': 'KEYCODE_POWER',
		'home': 'KEYCODE_HOME',
		'back': 'KEYCODE_BACK',
		'up': 'KEYCODE_DPAD_UP',
		'down': 'KEYCODE_DPAD_DOWN',
		'left': 'KEYCODE_DPAD_LEFT',
		'right': 'KEYCODE_DPAD_RIGHT',
		'center': 'KEYCODE_DPAD_CENTER',
		'volume up': 'KEYCODE_VOLUME_UP',
		'volume down': 'KEYCODE_VOLUME_DOWN',
		'rewind': 'KEYCODE_MEDIA_REWIND',
		'ff': 'KEYCODE_MEDIA_FAST_FORWARD',
		'play/pause': 'KEYCODE_MEDIA_PLAY_PAUSE',
		# Below are not used by GUI
		'sleep': 'KEYCODE_SLEEP',
		'wake': 'KEYCODE_WAKEUP',
                'next': 'KEYCODE_MEDIA_NEXT',
		'previous': 'KEYCODE_MEDIA_PREVIOUS',
		'search': 'KEYCODE_SEARCH',
	}

	apps = {
                'netflix': 'com.netflix.ninja/.MainActivity',
                'hulu': 'com.hulu.livingroomplus/.WKFactivity',
		'youtube': 'com.google.android.youtube.tv/com.google.android.apps.youtube.tv.activity.ShellActivity',
                'youtubetv': 'com.google.android.youtube.tvunplugged/com.google.android.apps.youtube.tvunplugged.activity.MainActivity',
		'disney': 'com.disney.disneyplus/com.bamtechmedia.dominguez.main.MainActivity',
                'vudu': 'air.com.vudu.air.DownloaderTablet/.TvMainActivity',
		# Below are not used by GUI
                'hbo': 'com.hbo.hbonow/com.hbo.go.LaunchActivity',
		'prime': 'com.amazon.amazonvideo.livingroom/com.amazon.ignition.IgnitionActivity',
		'music': 'com.google.android.music/.tv.HomeActivity',
		'ted':  'com.ted.android.tv/.view.MainActivity',
                'kodi': 'org.xbmc.kodi/.Splash',
                'twitch': 'tv.twitch.android.app/tv.twitch.android.apps.TwitchActivity',
                'plex': 'com.plexapp.android/com.plexapp.plex.activities.SplashActivity',
		'cbs': 'com.cbs.ott/com.cbs.app.tv.ui.activity.SplashActivity',
		'pbs': 'com.pbs.video/.ui.main.activities.StartupActivity',
		'amazonmusic': 'com.amazon.music.tv/.activity.MainActivity',
		'pandora': 'com.pandora.android.atv/com.pandora.android.MainActivity',
		'spotify': 'com.spotify.tv.android/.SpotifyTVActivity',
		'games': 'com.nvidia.tegrazone3/com.nvidia.tegrazone.leanback.LBMainActivity'
	}

	def __init__( self, ip = b'SHIELD:5555' ):
		if isinstance( ip, str ):
			ip = str.encode( ip )
		self.shield_ip_and_port = ip
		self.connect()

	def connect( self ):
		signed_key = PythonRSASigner.FromRSAKeyPath( 'adbkey' )
		self.device = adb_commands.AdbCommands().ConnectDevice( serial=self.shield_ip_and_port, rsa_keys=[ signed_key ] )

	def shell( self, arg ):
		# Nvidia disconnects inactive debuggers so we reconnect and retry on failure
		for i in range(2):
			try:
				self.device.Shell( arg )
				return
			except ConnectionResetError:
				self.connect()

	def press( self, button ):
		if button not in self.buttons:
			return { 'error': f'unknown button "{button}"'}

		self.shell( f'input keyevent {self.buttons[ button ]}' )

	def launch( self, app ):
		if app not in self.apps:
			return { 'error': f'no such app "{app}"' }

		app_launch_activity = self.apps[ app ]
		self.shell( f'am start -n {app_launch_activity}')

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
    device = shield( SHIELD_IP_PORT ) # device name (or IP address) and port
    main()

