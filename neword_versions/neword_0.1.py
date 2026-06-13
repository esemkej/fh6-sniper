from pynput import keyboard
from pynput.keyboard import Controller, Key
from pyautogui import screenshot
from time import sleep
from random import uniform
import win32gui, threading, os, sys

# <--- Global variables --->
caller = None

# <--- Keyboard binding class --->
class Binding():
    def __init__(self):
        super().__init__()
        self.keymap = {}
        self.key_states = {}
        self.modifiers = set()
    def bind_key(self, char, func, modifiers=None):
        # modifiers is a frozenset of Key enums, e.g. frozenset({Key.ctrl})
        mod_combo = frozenset(modifiers) if modifiers else frozenset()
        self.keymap[(char.lower(), mod_combo)] = func
    def unbind_key(self, char, modifiers=None):
        mod_combo = frozenset(modifiers) if modifiers else frozenset()
        combo = (char.lower(), mod_combo)
        self.keymap.pop(combo, None)
        self.key_states.pop(combo, None)
    def on_press(self, key):
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.modifiers.add(keyboard.Key.ctrl)
        elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.modifiers.add(keyboard.Key.shift)
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.modifiers.add(keyboard.Key.alt)
        try:
            char = key.char
            if char is None:
                return
            # When Ctrl is held, key.char returns a control character e.g. '\x11' for Q
            # Recover the actual letter by offsetting from the control char value
            if keyboard.Key.ctrl in self.modifiers and ord(char) < 32:
                char = chr(ord(char) + 96)
            else:
                char = char.lower()
            combo = (char, frozenset(self.modifiers))
            if combo in self.keymap and not self.key_states.get(combo, False):
                self.key_states[combo] = True
                self.keymap[combo]()
        except AttributeError:
            pass
    def on_release(self, key):
        if key in (keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            self.modifiers.discard(keyboard.Key.ctrl)
        elif key in (keyboard.Key.shift_l, keyboard.Key.shift_r):
            self.modifiers.discard(keyboard.Key.shift)
        elif key in (keyboard.Key.alt_l, keyboard.Key.alt_r):
            self.modifiers.discard(keyboard.Key.alt)
        try:
            char = key.char
            if char is None:
                return
            if keyboard.Key.ctrl in self.modifiers and ord(char) < 32:
                char = chr(ord(char) + 96)
            else:
                char = char.lower()
            combo = (char, frozenset(self.modifiers))
            self.key_states[combo] = False
        except AttributeError:
            pass
    def start_key_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

# <--- Command line interface class --->
class CLILogic():
    def __init__(self):
        super().__init__()

        # <--- Variables --->
        self.debug = False
        self.running = True
        self.infinite = False
        self.sniper_mode = 0 # 0 - normal, 1 - quick, 2 - safe, 3 - custom
        self.sniper_thread = None

        # Configurations
        self.normal_config = {"initial": 1, "quick_click": 0.3, "safe": 1, "auction_check": 1.2, "buyout_wait": 5, "collect_wait": 10}
        self.quick_config = {"initial": 0.8, "quick_click": 0.3, "safe": 1, "auction_check": 0.85, "buyout_wait": 5, "collect_wait": 10}
        self.custom_config = {}
        self.delay_config = self.normal_config

        # <--- Initialization --->

        # Check if either game is running and calculate coordinates
        self.calculate_coords()

        # <--- Binds --->
        self.binding = Binding()
        self.binding.bind_key("r", self.toggle_sniper, modifiers={keyboard.Key.ctrl})
        self.binding.bind_key("q", self.quit, modifiers={keyboard.Key.ctrl})
        self.binding.start_key_listener()

        # WARNING: Don't put anything under command loop otherwise it'll never run
        self.command_loop()
    def get_bbox(self):
        def enum_callback(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                for i in ["forza horizon 5", "forza horizon 6"]:
                    if i in win32gui.GetWindowText(hwnd).lower():
                        result.append(hwnd)
                        break
        hwnds = []
        win32gui.EnumWindows(enum_callback, hwnds)
        if not hwnds:
            ask_debug = input("Forza window not found!\nLaunch in debug mode? (y/n):\n")
            if ask_debug.lower() == "y":
                self.debug = True
                self.running = True
                return {"x": 0, "y": 0, "width": 0, "height": 0}
            else:
                print("Please start Forza and launch again")
                self.running = False
                sys.exit()

        hwnd = hwnds[0]
        rect = win32gui.GetClientRect(hwnd)
        x, y = win32gui.ClientToScreen(hwnd, (0, 0))
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        self.running = True
        return {"x": x, "y": y, "width": width, "height": height}
    def calculate_coords(self):
        bbox = self.get_bbox()

        rel1_x, rel1_y = 1000 / 2560, 300 / 1440
        rel2_x, rel2_y = 1500 / 2560, 620 / 1440
        rel3_x, rel3_y = 315 / 2560, 290 / 1440

        self.auction_x = round(rel1_x * bbox["width"]) + bbox["x"]
        self.auction_y = round(rel1_y * bbox["height"]) + bbox["y"]
        self.buyout_x = round(rel2_x * bbox["width"]) + bbox["x"]
        self.buyout_y = round(rel2_y * bbox["height"]) + bbox["y"]
        self.sold_x = round(rel3_x * bbox["width"]) + bbox["x"]
        self.sold_y = round(rel3_y * bbox["height"]) + bbox["y"]
    def command_loop(self):
        self.print_logo()
        while self.running:
            command = input("Enter command:\n").lower().split()
            if len(command) > 1:
                args = command[1]
                command = command[0]
            else:
                args = ""
                command = command[0]

            if command == "start":
                if args and not args.isdigit():
                    print(f"Invalid argument: {args}")
                    continue

                self.wait(int(args) if args else 5)
                self.sniper_thread = Sniper(self)
                self.sniper_thread.start()
                print("Sniping started")
            elif command == "mode":
                if args:
                    if args in ("normal", "0"):
                        self.sniper_mode = 0
                        self.delay_config = self.normal_config
                        print("Switched to normal mode")
                    elif args in ("quick", "1"):
                        self.sniper_mode = 1
                        self.delay_config = self.quick_config
                        print("Switched to quick mode")
                    elif args in ("fastest", "2"):
                        self.sniper_mode = 2
                        self.delay_config = 0
                        print("Switched to fastest mode")
                    elif args in ("safe", "3"):
                        self.sniper_mode = 3
                        self.delay_config = None
                        print("Switched to safe mode")
                    elif args in ("custom", "4"):
                        cancelled = False
                        for delay in self.normal_config: # <-- Walk through every delay in normal config and let the user change each one
                            value = input(f"{delay.replace("_", " ").capitalize()} delay (Current value: {self.normal_config[delay]}):\n")
                            while not value.isdigit():
                                if value in ("exit", "quit", "close"):
                                    cancelled = True
                                    break
                                else:
                                    value = input(f"Invalid value: {value}\n{delay.replace("_", " ").capitalize()} delay (Current value: {self.delay_config[delay]}):\n")
                            
                            if cancelled: break
                            self.custom_config[delay] = value
                        
                        if cancelled:
                            self.sniper_mode = 0
                            self.delay_config = self.normal_config
                            print("Reverted to normal mode")
                            continue

                        self.sniper_mode = 4
                        self.delay_config = self.custom_config
                        print("Switched to custom mode")
                    else:
                        print(f"Invalid argument: {args}")
                else:
                    modes = ["Normal", "Quick", "Fastest", "Safe", "Custom"]
                    print(f"Current mode: {modes[self.sniper_mode]}")
            elif command == "infinite":
                if args:
                    if args in ("0", "off", "false"):
                        self.infinite = False
                        print("Infinite sniping turned off")
                    elif args in ("1", "on", "true"):
                        self.infinite = True
                        print("Infinite sniping turned on")
                    else:
                        print(f"Invalid argument: {args}")
                else:
                    print(f"Infinite sniping is {"on" if self.infinite else "off"}")
            elif command == "recalculate":
                self.calculate_coords()
                print("Coordinates recalculated")
            elif command == "help":
                WHITE = "\033[97m"
                TEXTCOLOR = "\033[36m"
                print(f'''Commands:
"start [{TEXTCOLOR}delay{WHITE}]"     : Starts the bot after entered amount of seconds, or 5 if no argument is provided
"mode [{TEXTCOLOR}type{WHITE}]"       : Changes mode [{TEXTCOLOR}normal{WHITE}, {TEXTCOLOR}quick{WHITE}, {TEXTCOLOR}fastest{WHITE}, {TEXTCOLOR}safe{WHITE}, {TEXTCOLOR}custom{WHITE}] based on argument, or shows current mode if none are provided
"infinite [{TEXTCOLOR}on{WHITE}/{TEXTCOLOR}off{WHITE}]" : Switches the infinite mode based on argument, or shows current state if none are provided
"recalculate"       : Recalculates the coordinates of Forza window - use after changing res or window size
"exit/close/quit"   : Terminates the program
---------------------------------------------------------------------------------------------------------------------------------------
Keybinds:
{TEXTCOLOR}Ctrl{WHITE} + {TEXTCOLOR}R{WHITE}                              : Toggles bot on/off
{TEXTCOLOR}Ctrl{WHITE} + {TEXTCOLOR}Q{WHITE}                              : Terminates the program
---------------------------------------------------------------------------------------------------------------------------------------
Delays:
{TEXTCOLOR}Initial{WHITE} Delay       : Delay before the bot starts - shouldn\'t be set lower than 0.8
{TEXTCOLOR}Quick Click{WHITE} Delay   : Delay between repeated clicks (e.g. double enter to load auctions)
{TEXTCOLOR}Auction Check{WHITE} Delay : Delay before letting the bot check if it sees an auction - you may need to increase this depending on your system
{TEXTCOLOR}Buyout Wait{WHITE} Delay   : Delay after trying to buy out a car
{TEXTCOLOR}Collect Wait{WHITE} Delay  : Delay after claiming a successfully sniped car
{TEXTCOLOR}Safe{WHITE} Delay          : Delay between repeated clicks when it does not need to be fast - can be set to 0.3 like Quick Click delay
---------------------------------------------------------------------------------------------------------------------------------------
Problem:                              : Fix:
{TEXTCOLOR}Auction{WHITE} check being {TEXTCOLOR}skipped{WHITE}           : Increase the {TEXTCOLOR}initial delay{WHITE} - bot isn\'t giving Forza enough time to return to main page
{TEXTCOLOR}Bot{WHITE} getting {TEXTCOLOR}stuck{WHITE} with sold listings  : Increase the {TEXTCOLOR}auction check delay{WHITE} - Forza doesn\'t always load listings quickly enough
{TEXTCOLOR}Bot doesn\'t collect{WHITE} sniped cars       : Make sure {TEXTCOLOR}text size{WHITE} is increased to {TEXTCOLOR}150%{WHITE} in Forza\'s visual settings
{TEXTCOLOR}Ctrl{WHITE} + {TEXTCOLOR}R{WHITE} not working properly         : Windows loves to {TEXTCOLOR}intercept keybinds{WHITE}, sometimes you have to press them {TEXTCOLOR}twice{WHITE}
{TEXTCOLOR}Buyouts{WHITE} keep {TEXTCOLOR}failing{WHITE}                  : Try using a {TEXTCOLOR}faster bot mode{WHITE} and keep in mind that thousands of people are sniping the same cars
{TEXTCOLOR}Bot{WHITE} keeps getting {TEXTCOLOR}stuck{WHITE} in {TEXTCOLOR}general{WHITE}    : Try using a {TEXTCOLOR}slower bot mode{WHITE}, turn off {TEXTCOLOR}moving backgrounds{WHITE} and {TEXTCOLOR}ui motion blur{WHITE}
{TEXTCOLOR}Tested{WHITE} with these {TEXTCOLOR}settings{WHITE}            : Graphics - {TEXTCOLOR}low{WHITE}, ui motion blur - {TEXTCOLOR}off{WHITE}, moving backgrounds - {TEXTCOLOR}off{WHITE}, text size - {TEXTCOLOR}150%{WHITE}, {TEXTCOLOR}1440p 140fps{WHITE}
{TEXTCOLOR}Resolutions{WHITE} and {TEXTCOLOR}aspect ratios{WHITE}         : The bot will only work with {TEXTCOLOR}16:9{WHITE} resolutions and the game does not have to be maximized
---------------------------------------------------------------------------------------------------------------------------------------
Additionally, if the FH6 logo shows as {"\033[92m"}green {WHITE}instead of {TEXTCOLOR}cyan{WHITE}, debug mode is turned on''')
            elif command in ("exit", "quit", "close"):
                print("Goodbye")
                self.running = False
            else:
                print(f"Invalid command: {command}")

        sys.exit()
    def wait(self, seconds):
        for i in range(seconds):
            print(f"Waiting for {seconds - i} {"second" if i == seconds - 1 else "seconds"}")
            sleep(1)
    def get_config(self):
        return {"auction_x": self.auction_x, "auction_y": self.auction_y, "buyout_x": self.buyout_x, "buyout_y": self.buyout_y, "sold_x": self.sold_x, "sold_y": self.sold_y, "delay_config": self.delay_config, "infinite": self.infinite, "binding": self.binding}
    def toggle_sniper(self):
        if self.sniper_thread and self.sniper_thread.is_alive():
            self.sniper_thread.running = False
            self.sniper_thread = None
            print("Sniping stopped")
        else:
            self.wait(3)
            self.sniper_thread = Sniper(self)
            self.sniper_thread.start()
            print("Sniping started")
    def quit(self):
        print("Force stopped (Ctrl + Q)")
        self.running = False
        os._exit(0)
    def print_logo(self):
        WHITE = "\033[97m"
        TEXTCOLOR = "\033[92m" if self.debug else "\033[36m"
        SAKURA_CENTER = "\033[38;2;162;16;34m"
        SAKURA_EDGE = "\033[38;2;255;183;197m"
        logo = TEXTCOLOR + '''     ________ .---.  .---.   .------.             ____      ___    _     _______ ,---------. ''' + SAKURA_EDGE + ".-./`)" + TEXTCOLOR + '''     ,-----.    ,---.   .--.         _______       ,-----.  ,---------.  
    |        ||   |  |''' + SAKURA_EDGE + "_ _" + TEXTCOLOR + "|  /  .-.   \\          .'  __ `. .'   |  | |   /   __  \\\\          \\" + SAKURA_EDGE + "\\" + SAKURA_CENTER + " .-." + SAKURA_EDGE + "')" + TEXTCOLOR + "  .'" + SAKURA_EDGE + "  .-," + TEXTCOLOR + "  '.  |    \\  |  |        \\  ____  \\   .'" + SAKURA_EDGE + "  .-," + TEXTCOLOR + """  '.\\          \\ 
    |   .----'|   |  """ + SAKURA_EDGE + "( ' )" + TEXTCOLOR + " /  /   `--'         /   '  \\  \\|   .'  | |  | ,_/  \\__)`--.  ,---'" + SAKURA_EDGE + "/" + SAKURA_CENTER + " `-' " + SAKURA_EDGE + "\\" + TEXTCOLOR + " /" + SAKURA_EDGE + " ,-.|  \\ _" + TEXTCOLOR + " \\ |  ,  \\ |  |        | |    \\ |  /" + SAKURA_EDGE + " ,-.|  \\ _" + TEXTCOLOR + """ \\`--.  ,---' 
    |""" + SAKURA_EDGE + "  _" + TEXTCOLOR + "|____ |   '-" + SAKURA_EDGE + "(_" + SAKURA_CENTER + r"{;}" + SAKURA_EDGE + "_)" + TEXTCOLOR + "|  .----.           |___|  /  |.'  '" + SAKURA_EDGE + "_" + TEXTCOLOR + "  | |" + SAKURA_EDGE + ",-./  )" + TEXTCOLOR + "         |   \\    " + SAKURA_EDGE + "`-'`\"`" + TEXTCOLOR + ";" + SAKURA_EDGE + "  \\  '" + SAKURA_CENTER + "_" + SAKURA_EDGE + " /  |" + TEXTCOLOR + " :|  |\\" + SAKURA_EDGE + "_" + TEXTCOLOR + " \\|  |        | |____/ / ;  " + SAKURA_EDGE + "\\  '" + SAKURA_CENTER + "_" + SAKURA_EDGE + " /  |" + TEXTCOLOR + """ :  |   \\    
    |""" + SAKURA_EDGE + "_( )_" + TEXTCOLOR + "   ||      " + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + " |   " + SAKURA_EDGE + "_ _" + TEXTCOLOR + "  '.            _.-`   |'   " + SAKURA_EDGE + "( \\.-." + TEXTCOLOR + "|" + SAKURA_EDGE + "\\  '" + SAKURA_CENTER + "_" + SAKURA_EDGE + " '`)" + TEXTCOLOR + "       :" + SAKURA_EDGE + "_ _" + TEXTCOLOR + ":    .---. |  " + SAKURA_EDGE + "_`" + SAKURA_CENTER + ",/ \\" + SAKURA_EDGE + " _/" + TEXTCOLOR + "  ||  " + SAKURA_EDGE + "_( )_" + TEXTCOLOR + "\\  |        |   " + SAKURA_EDGE + "_ _" + TEXTCOLOR + " '. |  " + SAKURA_EDGE + "_`" + SAKURA_CENTER + ",/ \\" + SAKURA_EDGE + " _/" + TEXTCOLOR + "  |  :" + SAKURA_EDGE + "_ _" + TEXTCOLOR + """:    
    """ + SAKURA_EDGE + "(_" + SAKURA_CENTER + " o." + SAKURA_EDGE + "_)" + TEXTCOLOR + "__|| " + SAKURA_EDGE + "_ _" + TEXTCOLOR + "--.   | |  " + SAKURA_EDGE + "( ' )" + TEXTCOLOR + "   \\        .'   " + SAKURA_EDGE + "_" + TEXTCOLOR + "    |' " + SAKURA_EDGE + "(`" + SAKURA_CENTER + ". _` " + SAKURA_EDGE + "/" + TEXTCOLOR + "| " + SAKURA_EDGE + ">" + SAKURA_CENTER + " (_)" + SAKURA_EDGE + "  )" + TEXTCOLOR + "  __   " + SAKURA_EDGE + "(_I_)" + TEXTCOLOR + "    |   | : " + SAKURA_EDGE + "(  " + SAKURA_CENTER + "'\\_/" + SAKURA_EDGE + " \\" + TEXTCOLOR + "   ;| " + SAKURA_EDGE + "(_" + SAKURA_CENTER + " o" + SAKURA_EDGE + " _)" + TEXTCOLOR + "  |        |  " + SAKURA_EDGE + "( ' )" + TEXTCOLOR + "  \\: " + SAKURA_EDGE + "(" + SAKURA_CENTER + "  '\\_/" + SAKURA_EDGE + " \\" + TEXTCOLOR + "   ;  " + SAKURA_EDGE + "(_I_)" + TEXTCOLOR + """    
    |""" + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + "    |" + SAKURA_EDGE + "( ' )" + TEXTCOLOR + " |   | | " + SAKURA_EDGE + "(_" + SAKURA_CENTER + r"{;}" + SAKURA_EDGE + "_)" + TEXTCOLOR + "  |        |  " + SAKURA_EDGE + "_( )_" + TEXTCOLOR + "  || " + SAKURA_EDGE + "(_" + SAKURA_CENTER + " (_)" + SAKURA_EDGE + " _)(  .  .-'" + TEXTCOLOR + "_/  ) " + SAKURA_EDGE + "(_" + SAKURA_CENTER + "(=)" + SAKURA_EDGE + "_)" + TEXTCOLOR + "   |   |  \\ " + SAKURA_EDGE + "`\"/  \\  )" + TEXTCOLOR
        logo = logo + " / |  " + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + "\\  |        | " + SAKURA_EDGE + "(_" + SAKURA_CENTER + r"{;}" + SAKURA_EDGE + "_)" + TEXTCOLOR + " | \\ " + SAKURA_EDGE + "`\"/  \\  )" + TEXTCOLOR + " /  " + SAKURA_EDGE + "(_" + SAKURA_CENTER + "(=)" + SAKURA_EDGE + "_)" + TEXTCOLOR + """   
    |   |     """ + SAKURA_EDGE + "(_" + SAKURA_CENTER + r"{;}" + SAKURA_EDGE + "_)" + TEXTCOLOR + "|   | \\  " + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + "  /         \\ " + SAKURA_EDGE + "(_" + SAKURA_CENTER + " o" + SAKURA_EDGE + " _)" + TEXTCOLOR + " / \\ " + SAKURA_EDGE + "/  . \\" + TEXTCOLOR + " / " + SAKURA_EDGE + "`-'`-'" + TEXTCOLOR + "     /   " + SAKURA_EDGE + "(_I_)" + TEXTCOLOR + "    |   |   '. " + SAKURA_EDGE + "\\_/``\"" + TEXTCOLOR + ".'  |  |    |  |        |  " + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + "  /  '. " + SAKURA_EDGE + "\\_/``\"" + TEXTCOLOR + ".'    " + SAKURA_EDGE + "(_I_)" + TEXTCOLOR + """    
    '---'     '""" + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + " '---'  `...__..'           '." + SAKURA_EDGE + "(_,_)" + TEXTCOLOR + ".'   `" + SAKURA_EDGE + "`-'`-'" + TEXTCOLOR + "'    `._____.'    '---'    '---'     '-----'    '--'    '--'        /_______.'     '-----'      '---'    " + WHITE
        print("\n\n" + logo + "\n")
        print("""
    ----------------------------------------------------------------------------------------------
    | Version  : 0.1 (CLI)     | Type "help"        | for         | adittional        | info     | 
    | Modes    : Safe          | Normal             | Quick       | Fastest           | Custom   |
    | Commands : start [delay] | mode [type]        | recalculate | infinite [on/off] | exit     |
    | Author   : esemkej       | github.com/esemkej | No          | liability         | assumed  |
    ----------------------------------------------------------------------------------------------
              
        """)

# <--- Sniper class --->
class Sniper(threading.Thread):
    def __init__(self, caller):
        super().__init__(daemon=True)

        # <--- Variables --->
        self.running = True
        self.caller = caller
        self.config = self.caller.get_config() # Config includes pixel positions and delays
        self.auction_x = self.config["auction_x"]
        self.auction_y = self.config["auction_y"]
        self.buyout_x = self.config["buyout_x"]
        self.buyout_y = self.config["buyout_y"]
        self.sold_x = self.config["sold_x"]
        self.sold_y = self.config["sold_y"]
        self.delay_config = self.config["delay_config"]
        self.infinite = self.config["infinite"]
        self.binding = self.config["binding"]
        self.kboard = Controller()
    def snipe(self):
        sleep(self.delay_config["initial"])
        self.kboard.tap(Key.enter)
        sleep(self.delay_config["quick_click"])
        self.kboard.tap(Key.enter)
        sleep(self.delay_config["auction_check"])

        # Check if there's an active auction that hasn't been sold
        r, g, b = screenshot().getpixel((self.auction_x, self.auction_y))
        r1, g1, b1 = screenshot().getpixel((self.sold_x, self.sold_y))
        if (r >= 230 and g >= 230 and b >= 230) and not (abs(r1 - 234) <= 20 and abs(g1 - 222) <= 15 and abs(b1 - 0) <= 10):
            self.kboard.tap("y")
            sleep(self.delay_config["quick_click"])
            self.kboard.tap(Key.down)
            sleep(self.delay_config["quick_click"])
            self.kboard.tap(Key.enter)
            sleep(self.delay_config["quick_click"])
            self.kboard.tap(Key.enter)
            sleep(self.delay_config["buyout_wait"])

            # Check if the buyout was successful
            r, g, b = screenshot().getpixel((self.buyout_x, self.buyout_y))
            if r <= 25 and g <= 25 and b <= 25:
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["safe"])
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["collect_wait"])
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["safe"])
                self.kboard.tap(Key.esc)
                sleep(self.delay_config["safe"])
                self.kboard.tap(Key.esc)

                if self.infinite:
                    print("Car collected")
                else:
                    print("Sniping finished")
                    self.running = False
            else:
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["safe"])
                self.kboard.tap(Key.esc)
                sleep(self.delay_config["safe"])
                self.kboard.tap(Key.esc)
        else:
            self.kboard.tap(Key.esc)
    def fastest_snipe(self):
        sleep(0.8)
        self.kboard.tap(Key.enter)
        sleep(0.3)
        self.kboard.tap(Key.enter)
        sleep(0.95)

        # Check if there's an active auction that hasn't been sold
        r, g, b = screenshot().getpixel((self.auction_x, self.auction_y))
        r1, g1, b1 = screenshot().getpixel((self.sold_x, self.sold_y))
        if (r >= 230 and g >= 230 and b >= 230) and not (abs(r1 - 234) <= 20 and abs(g1 - 222) <= 15 and abs(b1 - 0) <= 10):
            self.kboard.tap("y")
            sleep(0.2)
            self.kboard.tap(Key.down)
            sleep(0.1)
            self.kboard.tap(Key.enter)
            sleep(0.2)
            self.kboard.tap(Key.enter)
            sleep(5)

            # Check if the buyout was successful
            r, g, b = screenshot().getpixel((self.buyout_x, self.buyout_y))
            if r <= 25 and g <= 25 and b <= 25:
                self.kboard.tap(Key.enter)
                sleep(1)
                self.kboard.tap(Key.enter)
                sleep(10)
                self.kboard.tap(Key.enter)
                sleep(1)
                self.kboard.tap(Key.esc)
                sleep(1)
                self.kboard.tap(Key.esc)

                if self.infinite:
                    print("Car collected")
                else:
                    print("Sniping finished")
                    self.running = False
            else:
                self.kboard.tap(Key.enter)
                sleep(1)
                self.kboard.tap(Key.esc)
                sleep(1)
                self.kboard.tap(Key.esc)
        else:
            self.kboard.tap(Key.esc)
    def safe_snipe(self):
        sleep(uniform(1, 1.5))
        self.kboard.tap(Key.enter)
        sleep(uniform(0.3, 0.8))
        self.kboard.tap(Key.enter)
        sleep(uniform(1, 1.4))

        # Check if there's an active auction that hasn't been sold
        r, g, b = screenshot().getpixel((self.auction_x, self.auction_y))
        r1, g1, b1 = screenshot().getpixel((self.sold_x, self.sold_y))
        if (r >= 230 and g >= 230 and b >= 230) and not (abs(r1 - 234) <= 20 and abs(g1 - 222) <= 15 and abs(b1 - 0) <= 10):
            self.kboard.tap("y")
            sleep(uniform(0.3, 0.5))
            self.kboard.tap(Key.down)
            sleep(uniform(0.3, 0.5))
            self.kboard.tap(Key.enter)
            sleep(uniform(0.3, 0.5))
            self.kboard.tap(Key.enter)
            sleep(uniform(5, 6))

            # Check if the buyout was successful
            r, g, b = screenshot().getpixel((self.buyout_x, self.buyout_y))
            if r <= 25 and g <= 25 and b <= 25:
                self.kboard.tap(Key.enter)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.enter)
                sleep(uniform(10, 13))
                self.kboard.tap(Key.enter)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)

                if self.infinite:
                    print("Car collected")
                else:
                    print("Sniping finished")
                    self.running = False
            else:
                self.kboard.tap(Key.enter)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
        else:
            self.kboard.tap(Key.esc)
    def run(self):
        while self.running:
            if self.delay_config is None:
                self.safe_snipe() # <-- Use safe snipe mode instead
            elif self.delay_config == 0:
                self.fastest_snipe() # <-- Use fastest snipe mode instead
            else:
                self.snipe()

if __name__ == "__main__":
    CLILogic()