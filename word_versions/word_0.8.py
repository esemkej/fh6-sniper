from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QInputDialog
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from pyautogui import screenshot
from time import sleep
from pynput import keyboard
from pynput.keyboard import Controller, Key
from threading import Thread
from random import uniform
import sys, win32gui, ctypes, os

#hiding console after launching gui
WM_CLOSE = 0x0010
SW_HIDE  = 0
def get_console_hwnd():
    try:
        return ctypes.windll.kernel32.GetConsoleWindow()
    except Exception:
        return 0
def free_console():
    hwnd = get_console_hwnd()
    if not hwnd:
        return
    try:
        ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
    except Exception:
        pass
    try:
        ctypes.windll.kernel32.FreeConsole()
    except Exception:
        pass
    try:
        still = get_console_hwnd()
        if still:
            ctypes.windll.user32.PostMessageW(still, WM_CLOSE, 0, 0)
    except Exception:
        pass
    try:
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
        sys.stdin  = open(os.devnull, "r")
    except Exception:
        pass

class KeyDispatcher(QObject):
    key_released = pyqtSignal(str)
    message = pyqtSignal(str, bool)
    update_buttons = pyqtSignal()
    finish_snipe = pyqtSignal()
class Logic():
    def __init__(self):
        super().__init__()

        #variables
        self.keymap = {}
        self.key_states = {}
        self.kboard = Controller()

        self.version = "0.8"
        self.debug = False
        self.running = False
        self.cli_running = False
        self.infinite = False
        self.snipe_type = "safe"

        if self.debug:
            self.defaults = [1, 0.3, 1.2, 5, 10, 1, 0.5, 0, 0, 0, 0]
            self.x, self.y, self.pixel_x, self.pixel_y = 0, 0, 0, 0
        else:
            self.calculate_pixel_coords()
            self.defaults = [1, 0.3, 1.2, 5, 10, 1, 0.5, self.pixel_x, self.pixel_y, self.x, self.y]

        self.normal_delay_config = {
            "initial_delay": 1,
            "quick_click_delay": 0.3,
            "auction_check_delay": 1.2,
            "short_wait_delay": 5,
            "long_wait_delay": 10,
            "safe_delay": 1,
            "end_delay": 0.5,
            "auction_pixel_x": self.pixel_x,
            "auction_pixel_y": self.pixel_y,
            "buyout_pixel_x": self.x,
            "buyout_pixel_y": self.y
        }
        self.quick_delay_config = {
            "initial_delay": 1,
            "quick_click_delay": 0.3,
            "auction_check_delay": 0.85,
            "short_wait_delay": 5,
            "long_wait_delay": 10,
            "safe_delay": 1,
            "end_delay": 0.5,
            "auction_pixel_x": self.pixel_x,
            "auction_pixel_y": self.pixel_y,
            "buyout_pixel_x": self.x,
            "buyout_pixel_y": self.y
        }
        self.delay_config = self.normal_delay_config

        decision = input("Command line interface or GUI mode? (cli/gui): ").strip().lower()
        while decision not in ["cli", "gui"]:
            decision = input("Command line interface or GUI mode? (cli/gui): ").strip().lower()
        if decision == "cli":
            print("Starting CLI...")
            self.build_cli()
        else:
            print("Starting GUI...")
            self.build_gui()
    def safe(self):
        self.snipe_type = "safe"
        self.message("Safe sniping on", True)
        self.safe_btn.setStyleSheet(self.button_style_focused)
        self.normal_btn.setStyleSheet(self.button_style_unfocused)
        self.custom_btn.setStyleSheet(self.button_style_unfocused)
        self.quick_btn.setStyleSheet(self.button_style_unfocused)
    def normal(self):
        self.snipe_type = "normal"
        self.delay_config = self.normal_delay_config
        self.message("Normal sniping on", True)
        self.safe_btn.setStyleSheet(self.button_style_unfocused)
        self.normal_btn.setStyleSheet(self.button_style_focused)
        self.custom_btn.setStyleSheet(self.button_style_unfocused)
        self.quick_btn.setStyleSheet(self.button_style_unfocused)
    def quick(self):
        self.snipe_type = "quick"
        self.delay_config = self.quick_delay_config
        self.message("Quick sniping on", True)
        self.safe_btn.setStyleSheet(self.button_style_unfocused)
        self.normal_btn.setStyleSheet(self.button_style_unfocused)
        self.custom_btn.setStyleSheet(self.button_style_unfocused)
        self.quick_btn.setStyleSheet(self.button_style_focused)
    def custom(self):
        self.snipe_type = "custom"
        self.message("Input custom values", False)
        self.safe_btn.setStyleSheet(self.button_style_unfocused)
        self.normal_btn.setStyleSheet(self.button_style_unfocused)
        self.quick_btn.setStyleSheet(self.button_style_unfocused)
        self.custom_btn.setStyleSheet(self.button_style_focused)

        for i, key in enumerate(self.delay_config):
            label = key.replace("_", " ").title()
            is_pixel = "pixel" in key.lower()

            if is_pixel:
                prompt = f"Enter {label} (default value: {self.defaults[i]}):"
                decimals = 0
            else:
                prompt = f"Enter {label} in seconds (default value: {self.defaults[i]}):"
                decimals = 2

            value, ok = QInputDialog.getDouble(self.window, label, prompt, decimals=decimals)

            if ok and value >= 0:
                self.delay_config[key] = int(value) if is_pixel else value
            else:
                self.message("Invalid value set", True)
                self.snipe_type = "safe"
                self.update_button_state()
                return None
        self.message("Values set", True)
    def update_button_state(self):
        if self.running:
            for button in self.state_buttons:
                button.setStyleSheet(self.button_style_disabled)
                button.setEnabled(False)
        else:
            for button in self.state_buttons:
                button.setStyleSheet(self.button_style_unfocused)
                button.setEnabled(True)
            if self.infinite:
                self.inf_btn.setStyleSheet(self.button_style_focused)
            if self.snipe_type == "safe":
                self.safe_btn.setStyleSheet(self.button_style_focused)
            elif self.snipe_type == "normal":
                self.normal_btn.setStyleSheet(self.button_style_focused)
            elif self.snipe_type == "custom":
                self.custom_btn.setStyleSheet(self.button_style_focused)
            else:
                self.quick_btn.setStyleSheet(self.button_style_focused)
    def get_window_bbox(self, title):
        def enum_callback(hwnd, result):
            if win32gui.IsWindowVisible(hwnd) and title.lower() in win32gui.GetWindowText(hwnd).lower():
                result.append(hwnd)
        
        hwnds = []
        win32gui.EnumWindows(enum_callback, hwnds)
        if not hwnds:
            print(f"{title} not found")
            return None
        hwnd = hwnds[0]
        self.target_hwnd = hwnd
        rect = win32gui.GetClientRect(hwnd)
        self.x, self.y = win32gui.ClientToScreen(hwnd, (0, 0))
        width = rect[2] - rect[0]
        height = rect[3] - rect[1]
        return {"x": self.x, "y": self.y, "width": width, "height": height}
    def calculate_pixel_coords(self):
        if not self.debug:
            tries = 0
            bbox = self.get_window_bbox("Forza Horizon 5")
            while not bbox:
                if tries < 5:
                    tries += 1
                    sleep(2)
                    bbox = self.get_window_bbox("Forza Horizon 5")
                else:
                    print("Launch Forza and try again")
                    sys.exit()

            rel1_x, rel1_y = 1095 / 1920, 480 / 1080
            rel2_x, rel2_y = 570 / 1920, 370 / 1080

            self.pixel_x = int(rel2_x * bbox['width']) + bbox['x']
            self.pixel_y = int(rel2_y * bbox['height']) + bbox['y']

            self.x = int(rel1_x * bbox['width']) + bbox['x']
            self.y = int(rel1_y * bbox['height']) + bbox['y']
        else:
            self.x, self.y, self.pixel_x, self.pixel_y = 0, 0, 0, 0
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos["pos"] = event.globalPos() - self.window.frameGeometry().topLeft()
    def mouseMoveEvent(self, event):
        if self.drag_pos["pos"]:
            self.window.move(event.globalPos() - self.drag_pos["pos"])
    def mouseReleaseEvent(self, _):
        self.drag_pos["pos"] = None
    def bind_key(self, char, func):
        self.keymap[char.lower()] = func
    def on_press(self, key):
        try:
            char = key.char.lower()
            if char in self.keymap and not self.key_states.get(char, False):
                self.key_states[char] = True
                self.dispatcher.key_released.emit(char)
        except AttributeError:
            pass
    def on_release(self, key):
        try:
            char = key.char.lower()
            self.key_states[char] = False
        except AttributeError:
            pass
    def start_key_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()
    def handle_keybind(self, char):
        func = self.keymap.get(char.lower())
        if func:
            func()
    def message(self, text, timed):
        self.timer.stop()
        try:
            self.timer.timeout.disconnect()
        except TypeError:
            pass
        if timed:
            self.message_txt.setText(text)
            self.timer.timeout.connect(self.clear_msg)
            self.timer.start(3000)
        else:
            self.message_txt.setText(text)
    def clear_msg(self):
        self.message("", False)
    def infinite_snipe(self):
        if self.infinite:
            self.inf_btn.setStyleSheet(self.button_style_unfocused)
            self.inf_btn.setText("Infinite sniping")
            self.message("Infinite sniping off", True)
            self.infinite = False
        else:
            self.inf_btn.setStyleSheet(self.button_style_focused)
            self.inf_btn.setText("Infinite sniping")
            self.message("Infinite sniping on", True)
            self.infinite = True
    def is_focused(self):
        if self.debug:
            return True
        try:
            fg = win32gui.GetForegroundWindow()
        except Exception:
            return False

        fh5_focused = hasattr(self, "target_hwnd") and self.target_hwnd and fg == self.target_hwnd
        window_title = win32gui.GetWindowText(fg).lower() if fg else ""
        allowed_titles = ["python", "word", f"word_{self.version}"]
        allowed_focused = any(title.lower() in window_title for title in allowed_titles)

        return (fh5_focused, "forza") or allowed_focused
    def start(self):
        if self.is_focused():
            if self.running:
                self.start_btn.setStyleSheet(self.button_style_unfocused)
                self.start_btn.setText("Start (S)")
                self.running = False
                self.update_button_state()
                self.message("", False)
            else:
                self.start_btn.setStyleSheet(self.button_style_focused)
                self.start_btn.setText("Stop (S)")
                self.running = True
                self.update_button_state()
                if self.infinite:
                    self.message("Looking for auctions...", True)
                else:
                    self.message("Looking for auctions...", False)
                Thread(target=self.background_loop, daemon=True).start()
    def quit(self):
        if self.is_focused():
            self.app.quit()
            sys.exit()
    def background_loop(self):
        while self.running:
            focus = self.is_focused()
            if focus[0] and focus[1] == "forza":
                if self.snipe_type == "safe":
                    self.safe_snipe()
                else:
                    self.snipe()
            else:
                self.running = False
                if self.cli_running:
                    print("Forza focus lost - sniper stopped\nDon't mind if you're seeing bunch of Invalid command messages")
                else:
                    self.ui_message("Forza focus lost\nSniper stopped", False)
                    self.ui_finish_snipe()
    def safe_snipe(self):
        self.calculate_pixel_coords()
        sleep(uniform(1, 1.5))
        self.kboard.tap(Key.enter)
        sleep(uniform(0.3, 0.8))
        self.kboard.tap(Key.enter)
        sleep(uniform(1, 1.4))

        r, g, b = screenshot().getpixel((self.pixel_x, self.pixel_y))
        if r >= 230 and g >= 230 and b >= 230:
            self.kboard.tap("y")
            sleep(uniform(0.3, 0.5))
            self.kboard.tap(Key.down)
            sleep(uniform(0.3, 0.5))
            self.kboard.tap(Key.enter)
            sleep(uniform(0.3, 0.5))
            self.kboard.tap(Key.enter)
            sleep(uniform(5, 5.9))
            r, g, b = screenshot().getpixel((self.x, self.y))
            if r >= 230 and g >= 230 and b >= 230:
                self.kboard.tap(Key.enter)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.enter)
                sleep(uniform(9.5, 12.7))
                self.kboard.tap(Key.enter)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
                if self.infinite:
                    self.ui_message("Car collected", True)
                else:
                    self.ui_message("Auction finished", False)
                    self.finish_snipe()
            else:
                self.kboard.tap(Key.enter)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
                sleep(uniform(0.5, 1.5))
                self.kboard.tap(Key.esc)
                sleep(uniform(0.5, 1.5))
        else:
            self.kboard.tap(Key.esc)
            sleep(uniform(0.5, 1.5))
    def snipe(self):
        sleep(self.delay_config["initial_delay"])
        self.kboard.tap(Key.enter)

        sleep(self.delay_config["quick_click_delay"])
        self.kboard.tap(Key.enter)

        sleep(self.delay_config["auction_check_delay"])
        r, g, b = screenshot().getpixel((self.delay_config["auction_pixel_x"], self.delay_config["auction_pixel_y"]))

        if r >= 230 and g >= 230 and b >= 230:
            self.kboard.tap("y")
            sleep(self.delay_config["quick_click_delay"])
            self.kboard.tap(Key.down)
            sleep(self.delay_config["quick_click_delay"])
            self.kboard.tap(Key.enter)
            sleep(self.delay_config["quick_click_delay"])
            self.kboard.tap(Key.enter)

            sleep(self.delay_config["short_wait_delay"])
            r, g, b = screenshot().getpixel((self.delay_config["buyout_pixel_x"], self.delay_config["buyout_pixel_y"]))

            if r >= 230 and g >= 230 and b >= 230:
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["safe_delay"])
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["long_wait_delay"])
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["safe_delay"])
                self.kboard.tap(Key.esc)
                sleep(self.delay_config["safe_delay"])
                self.kboard.tap(Key.esc)

                if self.infinite:
                    self.ui_message("Car collected", True)
                else:
                    self.ui_message("Auction finished", False)
                    self.finish_snipe()
            else:
                self.kboard.tap(Key.enter)
                sleep(self.delay_config["safe_delay"])
                self.kboard.tap(Key.esc)
                sleep(self.delay_config["safe_delay"])
                self.kboard.tap(Key.esc)
                if self.snipe_type in ("normal", "custom"):
                    sleep(self.delay_config["end_delay"])
        else:
            self.kboard.tap(Key.esc)
            if self.snipe_type in ("normal", "custom"):
                sleep(self.delay_config["end_delay"])
    def finish_snipe(self):
        self.start_btn.setStyleSheet(self.button_style_unfocused)
        self.start_btn.setText("Start (S)")
        self.running = False
        self.update_button_state()
    def build_gui(self):
        #layouts and windows
        self.app = QApplication([])
        self.window = QWidget()

        self.dispatcher = KeyDispatcher()
        self.dispatcher.key_released.connect(self.handle_keybind)
        self.dispatcher.message.connect(self.message)
        self.dispatcher.update_buttons.connect(self.update_button_state)
        self.dispatcher.finish_snipe.connect(self.finish_snipe)

        self.timer = QTimer()
        self.timer.setSingleShot(True)

        parent_layout = QVBoxLayout()
        parent_layout.setContentsMargins(0, 0, 0, 0)
        parent_layout.setSpacing(0)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(8, 8, 8, 8)
        button_layout.setSpacing(8)
        topbar_layout = QHBoxLayout()
        topbar_layout.setContentsMargins(6, 6, 6, 6)
        topbar_layout.setSpacing(4)
        midbtn_layout = QVBoxLayout()
        midbtn_layout.setContentsMargins(0, 0, 0, 0)
        midbtn_layout.setSpacing(8)
        self.window.setFixedSize(400, 500)
        self.window.setLayout(parent_layout)
        self.window.setWindowFlags(Qt.FramelessWindowHint)
        self.window.setAttribute(Qt.WA_TranslucentBackground)
        self.window.setStyleSheet("border-radius: 4px")
        parent_frame = QFrame()
        parent_frame.setStyleSheet("background-color: #1a181d")
        button_frame = QFrame()
        topbar_frame = QFrame()
        topbar_frame.setStyleSheet("background-color: #232029")
        midbtn_frame = QFrame()

        #styles
        self.button_style_unfocused = """
        QPushButton {
            border: none;
            background-color: #925cf2;
            color: white;
            padding: 8px;
            font-size: 14px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #4d3676;
        }
        """
        self.button_style_focused = """
        QPushButton {
            border: none;
            background-color: #4d3676;
            color: white;
            padding: 8px;
            font-size: 14px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #63429a;
        }
        """
        self.button_style_disabled = """
        QPushButton {
            border: none;
            background-color: #444444;
            color: white;
            padding: 8px;
            font-size: 14px;
            border-radius: 4px;
        }
        """
        title_text_style = """
            color: #ffffff;
            font-size: 12pt;
            margin: 0px;
            padding: 0px
        """
        text_style = """
            color: #ffffff;
            font-size: 10pt;
            margin: 0px;
            padding: 0px
        """

        #widgets
        self.start_btn = QPushButton("Start (S)")
        self.start_btn.setStyleSheet(self.button_style_unfocused)
        self.quit_btn = QPushButton("Quit (Q)")
        self.quit_btn.setStyleSheet(self.button_style_unfocused)
        self.inf_btn = QPushButton("Infinite sniping")
        self.inf_btn.setStyleSheet(self.button_style_unfocused)
        self.safe_btn = QPushButton("Safe sniping")
        self.safe_btn.setStyleSheet(self.button_style_focused)
        self.normal_btn = QPushButton("Normal sniping")
        self.normal_btn.setStyleSheet(self.button_style_unfocused)
        self.custom_btn = QPushButton("Custom sniping")
        self.custom_btn.setStyleSheet(self.button_style_unfocused)
        self.quick_btn = QPushButton("Quick sniping")
        self.quick_btn.setStyleSheet(self.button_style_unfocused)
        self.state_buttons = [self.inf_btn, self.safe_btn, self.normal_btn, self.custom_btn, self.quick_btn]

        main_txt = QLabel("FH5 Auction Bot")
        main_txt.setStyleSheet(title_text_style)
        debug_txt = QLabel("Debug on")
        debug_txt.setStyleSheet(text_style)
        debug_txt.setAlignment(Qt.AlignCenter)
        self.message_txt = QLabel()
        self.message_txt.setStyleSheet(text_style)
        self.message_txt.setMaximumWidth(250)
        self.message_txt.setWordWrap(True)
        self.message_txt.setAlignment(Qt.AlignCenter)

        #adding widgets
        parent_layout.addWidget(parent_frame)
        parent_frame.setLayout(main_layout)
        main_layout.addWidget(topbar_frame, alignment=Qt.AlignTop)
        topbar_frame.setLayout(topbar_layout)
        topbar_layout.addWidget(main_txt, alignment=Qt.AlignCenter)
        main_layout.addWidget(midbtn_frame, alignment=Qt.AlignCenter)
        midbtn_frame.setLayout(midbtn_layout)
        if self.debug:
            midbtn_layout.addWidget(debug_txt)
        midbtn_layout.addWidget(self.inf_btn)
        midbtn_layout.addWidget(self.safe_btn)
        midbtn_layout.addWidget(self.normal_btn)
        midbtn_layout.addWidget(self.custom_btn)
        midbtn_layout.addWidget(self.quick_btn)
        midbtn_layout.addWidget(self.message_txt)
        main_layout.addWidget(button_frame, alignment=Qt.AlignBottom)
        button_frame.setLayout(button_layout)
        button_layout.addWidget(self.quit_btn)
        button_layout.addWidget(self.start_btn)

        #window moving
        self.drag_pos = {"pos": None}
        topbar_frame.setCursor(Qt.OpenHandCursor)
        topbar_frame.mousePressEvent = self.mousePressEvent
        topbar_frame.mouseMoveEvent = self.mouseMoveEvent
        topbar_frame.mouseReleaseEvent = self.mouseReleaseEvent

        Thread(target=self.start_key_listener, daemon=True).start()

        #binds
        self.start_btn.clicked.connect(self.start)
        self.quit_btn.clicked.connect(self.quit)
        self.inf_btn.clicked.connect(self.infinite_snipe)
        self.safe_btn.clicked.connect(self.safe)
        self.normal_btn.clicked.connect(self.normal)
        self.custom_btn.clicked.connect(self.custom)
        self.quick_btn.clicked.connect(self.quick)
        self.bind_key("s", self.start)
        self.bind_key("q", self.quit)

        self.window.show()
        self.app.processEvents()
        if sys.platform.startswith("win"):
            free_console()
        self.app.exec_()
    def build_cli(self):
        WHITE = "\033[97m"
        PINK = "\033[95m"
        GREEN = "\033[92m"
        print("\033[2S", end="")
        print(rf'''{GREEN if self.debug else PINK}
     ______ _    _   _____                      _   _               ____        _   
    |  ____| |  | | | ____|     /\             | | (_)             |  _ \      | |  
    | |__  | |__| | | |__      /  \  _   _  ___| |_ _  ___  _ __   | |_) | ___ | |_ 
    |  __| |  __  | |___ \    / /\ \| | | |/ __| __| |/ _ \| '_ \  |  _ < / _ \| __|
    | |    | |  | |  ___) |  / ____ \ |_| | (__| |_| | (_) | | | | | |_) | (_) | |_ 
    |_|    |_|  |_| |____/  /_/    \_\__,_|\___|\__|_|\___/|_| |_| |____/ \___/ \__|{WHITE}
              
    --------------------------------------------------------------------------------------------

    Version  : 0.8 (CLI)     | Type "help"        | for         | adittional        | info     | 
    Modes    : Safe          | Normal             | Quick       | Custom            | Infinite |
    Commands : start [delay] | stop               | mode [type] | infinite [on/off] | exit     |
    Author   : esemkej       | github.com/esemkej | No          | liability         | assumed  |
''')
        self.cli_running = True
        while self.cli_running:
            if self.running:
                sleep(0.05)
                continue
            else:
                command = input("Enter a command: ").lower().strip().split()
                if not command:
                    print("Invalid command")
                    continue
                args = None
                if len(command) > 1:
                    args = command[1]
                    command = command[0]
                else:
                    command = command[0]

                if command == "start":
                    if not self.running:
                        if args:
                            num = float(args)
                            print(f"Waiting for {num} seconds")
                            sleep(num)
                        else:
                            print("Waiting for 5 seconds")
                            sleep(5)
                        self.running = True
                        Thread(target=self.background_loop, daemon=True).start()
                        print("Looking for auctions...")
                    else:
                        print("Sniper already running")
                elif command == "stop":
                    if self.running:
                        self.running = False
                        print("Sniper stopped")
                    else:
                        print("Sniper is not running")
                elif command == "mode":
                    if args:
                        if args == "custom":
                            for i, key in enumerate(self.delay_config):
                                label = key.replace("_", " ").title()
                                is_pixel = "pixel" in key.lower()
                                if is_pixel:
                                    value = int(input(f"Enter {label} (default value: {self.defaults[i]}): "))
                                else:
                                    value = float(input(f"Enter {label} in seconds (default value: {self.defaults[i]}): "))

                                if value >= 0:
                                    self.delay_config[key] = int(value) if is_pixel else value
                                else:
                                    print("Invalid value set - changing back to safe mode")
                                    self.snipe_type = "safe"
                                    break
                            self.snipe_type = "custom"
                            print("Values set - custom mode on\n")
                        elif args not in ["safe", "normal", "quick"]:
                            print(f'Unknown mode: {args}')
                        else:
                            if args == "normal":
                                self.delay_config = self.normal_delay_config
                            elif args == "quick":
                                self.delay_config = self.quick_delay_config
                            self.snipe_type = args
                            print(f"Snipe mode set to: {args}")
                    else:
                        print(f"Current mode: {self.snipe_type}")
                elif command == "infinite":
                    if args:
                        if args == "on":
                            self.infinite = True
                            print("Infinite mode turned on")
                        elif args == "off":
                            self.infinite = False
                            print("Infinite mode turned off")
                        else:
                            print(f"Unknown command: {args}")
                    else:
                        print("Infinite mode is on") if self.infinite else print("Infinite mode is off")
                elif command == "help":
                    print(f'''Commands:
{PINK}"help"{WHITE}              : Self explanatory
{PINK}"start [delay]"{WHITE}     : Starts the bot after entered seconds, or after 5 seconds if no argument is provided
{PINK}"stop"{WHITE}              : Stops the bot if it is running (redundant)
{PINK}"mode [type]"{WHITE}       : Changes mode based on argument, or shows current mode if none are provided
{PINK}"infinite [on/off]"{WHITE} : Switches the infinite mode based on argument, or shows current state if none are provided
{PINK}"exit/close/quit"{WHITE}   : Terminates the program
Additionally, if the FH5 text shows as {GREEN}green {WHITE}instead of {PINK}pink{WHITE}, debug mode is turned on''')
                elif command in ("exit", "close", "quit"):
                    print("Goodbye")
                    self.cli_running = False
                else:
                    print("Unknown command")
    def ui_message(self, text, timed):
        if self.cli_running:
            print(text)
        else:
            self.dispatcher.message.emit(text, timed)
    def ui_finish_snipe(self):
        self.dispatcher.finish_snipe.emit()
    def ui_update_button_state(self):
        self.dispatcher.update_buttons.emit()

if __name__ == "__main__":
    Logic()