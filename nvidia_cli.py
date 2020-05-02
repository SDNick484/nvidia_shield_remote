#! /usr/bin/env python
import sys
import nvidia
import configparser

### Specify your Shield TV's IP & Port here to avoid needing to specify on CLI
### e.g. SHIELD_IP_PORT = "192.168.1.130:5555"
SHIELD_IP_PORT = "192.168.1.130:5555"
#SHIELD_IP_PORT = None


### Set up device
device = nvidia.shield( SHIELD_IP_PORT ) # device name (or IP address) and port

### Check if Shield's IP & Port are set
if not SHIELD_IP_PORT:
    print("Please udpate nvidia_cli.py with your Shield's IP and port")
    quit()

### Geneic help menu
def help_menu():
    print("  -c <command>\n")
    print("  -a <app>\n")

### If no parameters are specified, print error and exit
if (len(sys.argv)) == 1:
    print("\nInvalid syntax, please use: python ./nvidia_cli.py -c <command> OR python ./nvidia_cly.py -a <app>\n")
    help_menu()
    quit()

### If one parameter specified, check if valid [-c, -a, or -h] and print help otherwise print error and exit
if (len(sys.argv)) == 2:
    if sys.argv[1] == "-h" or sys.argv[1] == "-H":
        print("\nExample: python ./nvidia_cli.py -c home OR python ./nvidia_cly.py -a netflix\n")
        help_menu()
        quit()
    elif sys.argv[1] == "-c" or sys.argv[1] == "-C":
        print("\nSyntax error, python ./nvidia_cli.py -c <command>\n")
        print("""Valid command options:
		'power'
		'sleep'
		'wake'
		'home'
		'back'
		'search'
		'up'
		'down'
		'left'
		'right'
		'center'
		'volume up'
		'volume down'
		'rewind'
		'ff'
		'play/pause'
		'previous'
		'next'\n""")
        quit()
    elif sys.argv[1] == "-a" or sys.argv[1] == "-A":
        print("\nSyntax error, python ./nvidia_cli.py -a <app>\n")
        print("""Valid app options:
      		'hbo'
		'prime'
		'music'
		'youtube'
		'ted'
                'hulu'
                'netflix'
                'youtubetv'
		'disney'
                'kodi'
                'twitch'
                'plex'
		'cbs'
		'pbs'
		'amazonmusic'
		'pandora'
		'spotify'
		'games'\n""")
        quit()
    else:
        print("\nInvalid syntax, please use: python ./nvidia_cli.py -c <command> OR python ./nvidia_cly.py -a <app>\n")
        help_menu()
        quit()

### If three parameters specific, check if valid (-c or -a) and execute command or print error and exit
if (len(sys.argv)) == 3:
    if sys.argv[1] == "-c" or sys.argv[1] == "-C":
        nv_command = sys.argv[2]
        device.press(nv_command) 
    elif sys.argv[1] == "-a" or sys.argv[1] == "-A":
        nv_command = sys.argv[2]
        device.launch(nv_command) 
    else:
        print("\nInvalid syntax, please use: python ./nvidia_cli.py -c <command> OR python ./nvidia_cly.py -a <app>\n")
        help_menu()
        quit()
 
