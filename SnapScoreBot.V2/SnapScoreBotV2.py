import sys
import platform
import os
import time
import json
import threading
import random
from pathlib import Path
from datetime import datetime

# ==================== MODULE CHECK ====================
required_modules = {
    'colorama': 'colorama',
    'pyautogui': 'pyautogui',
    'keyboard': 'keyboard',
    'requests': 'requests'
}

missing_modules = []
for module in required_modules.values():
    try:
        __import__(module)
    except ImportError:
        missing_modules.append(module)

if missing_modules:
    print("Error: Missing required modules detected")
    print("Please run 'Install_Requirements.bat' first")
    print("\nMissing modules:")
    for mod in missing_modules:
        print(f" - {mod}")
    input("\nPress ENTER to exit...")
    sys.exit(1)

# Now import the modules
import pyautogui
import keyboard
import requests
from colorama import Fore, init, Style
import tkinter as tk
from tkinter import messagebox

# Initialize colorama
init(autoreset=True, convert=True)

# ==================== SETTINGS ====================
TUTORIAL_VIDEO = "Soon"
VERSION = "2.0.0"
CREDITS = "Eddie-500 - Educational Purpose Only"
CONFIG_FILE = "config.json"
ACCENT_COLOR = Fore.YELLOW

# ==================== LOGGING HELPERS ====================
LOG_LISTENERS = []


def register_log_listener(callback):
    """Registers a callback to receive log events"""
    if callback not in LOG_LISTENERS:
        LOG_LISTENERS.append(callback)


def unregister_log_listener(callback):
    """Removes a log callback"""
    if callback in LOG_LISTENERS:
        LOG_LISTENERS.remove(callback)


def clear():
    """Clears the console"""
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def title(text):
    """Sets the console window title"""
    if sys.platform.startswith('win'):
        import ctypes
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(text)
        except Exception:
            pass


def nice_print(text, status="-", color=Fore.WHITE):
    """Formatted print with status icon"""
    formatted = f"{Fore.WHITE}[{ACCENT_COLOR if status == '✓' else Fore.RED if status == '✗' else Fore.CYAN}{status}{Fore.WHITE}] {color}{text}{Style.RESET_ALL}"
    print(formatted)
    for callback in LOG_LISTENERS:
        try:
            callback(text=text, status=status, color=color)
        except Exception:
            continue


def print_banner():
    """Prints the program banner"""
    banner = rf"""
{ACCENT_COLOR}
    ┏━┓┏┓╻┏━┓┏━┓┏━┓┏━╸┏━┓┏━┓┏━╸┏┓ ┏━┓╺┳╸
    ┗━┓┃┗┫┣━┫┣━┛┗━┓┃  ┃ ┃┣┳┛┣╸ ┣┻┓┃ ┃ ┃
    ┗━┛╹ ╹╹ ╹╹  ┗━┛┗━╸┗━┛╹┗╸┗━╸┗━┛┗━┛ ╹

{Fore.YELLOW}             Version {VERSION}
{Fore.CYAN}Educational Purpose Only - By: Eddie-500 GITHUB
{Fore.WHITE}═════════════════════════════════════════════════════
"""
    print(banner)


# ==================== CONFIGURATION CLASS ====================
class Config:
    DEFAULTS = {
        'loop_delay': 5.0,
        'click_delay': 1.2,
        'position_delay': 0.5,
        'random_delay': False,
        'random_delay_min': 3.0,
        'random_delay_max': 8.0,
        'auto_stop_enabled': False,
        'auto_stop_after': 100,
        'schedule_delay_minutes': 0,
        'ramp_up_enabled': False,
        'ramp_up_minutes': 0,
        'safe_mode': True,
        'session_duration_minutes': 0
    }

    def __init__(self):
        for key, value in self.DEFAULTS.items():
            setattr(self, key, value)
        self.load_config()

    def load_config(self):
        """Loads configuration from JSON file"""
        if Path(CONFIG_FILE).exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                nice_print("Configuration loaded", "✓", ACCENT_COLOR)
            except Exception:
                nice_print("Failed to load configuration, using defaults", "!", Fore.YELLOW)

    def save_config(self):
        """Saves configuration to JSON file"""
        data = {key: getattr(self, key) for key in self.DEFAULTS}
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        nice_print("Configuration saved", "✓", ACCENT_COLOR)

    def reset_defaults(self):
        """Resets configuration to default values"""
        for key, value in self.DEFAULTS.items():
            setattr(self, key, value)
        self.save_config()


# ==================== STATISTICS CLASS ====================
class Statistics:
    def __init__(self):
        self.total_snaps_sent = 0
        self.session_snaps = 0
        self.start_time = None
        self.errors_count = 0
        self.last_session_snaps = 0
        self.last_session_time = None
        self.last_session_duration = 0
        self.stats_file = "stats.json"
        self.load_stats()

    def load_stats(self):
        """Loads previous statistics"""
        if Path(self.stats_file).exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_snaps_sent = data.get('total_snaps_sent', 0)
                    self.last_session_snaps = data.get('last_session_snaps', 0)
                    self.last_session_time = data.get('last_session', None)
                    self.last_session_duration = data.get('last_session_duration', 0)
            except Exception:
                nice_print("Failed to load statistics", "!", Fore.YELLOW)

    def save_stats(self):
        """Saves statistics"""
        data = {
            'total_snaps_sent': self.total_snaps_sent,
            'last_session': self.last_session_time,
            'last_session_snaps': self.last_session_snaps,
            'last_session_duration': self.last_session_duration
        }
        with open(self.stats_file, 'w') as f:
            json.dump(data, f, indent=4)

    def start_session(self):
        """Initializes tracking for a new session"""
        self.session_snaps = 0
        self.errors_count = 0
        self.start_time = time.time()

    def end_session(self):
        """Persists statistics at the end of a session"""
        if self.start_time:
            self.last_session_duration = time.time() - self.start_time
        else:
            self.last_session_duration = 0
        self.last_session_snaps = self.session_snaps
        self.last_session_time = datetime.now().isoformat()
        self.start_time = None
        self.save_stats()

    def reset_statistics(self):
        """Resets cumulative statistics"""
        self.total_snaps_sent = 0
        self.session_snaps = 0
        self.errors_count = 0
        self.last_session_snaps = 0
        self.last_session_duration = 0
        self.last_session_time = None
        self.save_stats()

    def get_elapsed_time(self):
        """Gets formatted elapsed time"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
# ==================== SNAP BOT CORE ====================
class AdvancedSnapBot:
    def __init__(self, config, stats):
        self.config = config
        self.stats = stats
        self.positions = {}
        self.is_running = False
        self.first_try = True
        self.pause_bot = False
        self.stop_event = threading.Event()
        self._pause_lock = threading.Lock()

    def get_positions(self):
        """Captures mouse positions"""
        positions_needed = [
            ('camera', 'Camera button'),
            ('send_to', 'Send to button'),
            ('shortcut', 'Shortcut button'),
            ('select_all', 'Select All button')
        ]

        for key, description in positions_needed:
            nice_print(f"Move the mouse to the {description} and press F", "→", Fore.YELLOW)

            while True:
                if keyboard.is_pressed("f"):
                    self.positions[key] = pyautogui.position()
                    nice_print(f"Position saved: {self.positions[key]}", "✓", ACCENT_COLOR)
                    time.sleep(self.config.position_delay)
                    break
                if keyboard.is_pressed("escape"):
                    return False

        self.save_positions()
        return True

    def save_positions(self):
        """Saves positions to a JSON file"""
        positions_data = {k: {'x': v.x, 'y': v.y} for k, v in self.positions.items()}
        with open('positions.json', 'w') as f:
            json.dump(positions_data, f)
        nice_print("Positions saved to file", "✓", ACCENT_COLOR)

    def load_positions(self):
        """Loads previously saved positions"""
        if Path('positions.json').exists():
            try:
                with open('positions.json', 'r') as f:
                    data = json.load(f)
                    for key, coords in data.items():
                        self.positions[key] = pyautogui.Point(coords['x'], coords['y'])
                nice_print("Positions loaded from file", "✓", ACCENT_COLOR)
                return True
            except Exception:
                nice_print("Failed to load saved positions", "✗", Fore.RED)
        return False

    def clear_positions(self):
        """Removes stored mouse positions"""
        self.positions = {}
        try:
            Path('positions.json').unlink(missing_ok=True)
        except Exception:
            pass
        nice_print("Stored positions cleared", "!", Fore.YELLOW)

    def wait(self, seconds):
        """Wait helper that respects pause and stop events"""
        if seconds <= 0:
            return True
        end_time = time.time() + seconds
        while time.time() < end_time:
            if self.stop_event.is_set():
                return False
            if self.pause_bot:
                pause_start = time.time()
                while self.pause_bot and not self.stop_event.is_set():
                    time.sleep(0.1)
                if self.stop_event.is_set():
                    return False
                pause_duration = time.time() - pause_start
                end_time += pause_duration
            time.sleep(min(0.1, end_time - time.time()))
        return True

    def get_click_delay(self):
        """Returns a random or fixed click delay"""
        delay = self.config.click_delay
        if self.config.random_delay:
            delay = random.uniform(self.config.random_delay_min, self.config.random_delay_max)
        if self.config.safe_mode:
            delay *= 1.2
        return delay

    def get_loop_delay(self):
        """Returns the loop delay with safety adjustments"""
        delay = self.config.loop_delay
        if self.config.safe_mode:
            delay *= 1.4
        return delay

    def send_snap(self, shortcut_user_count):
        """Sends a snap sequence"""
        try:
            pyautogui.moveTo(self.positions['camera'])
            if self.first_try:
                pyautogui.click()
                self.first_try = False
                if not self.wait(self.config.position_delay):
                    return False

            pyautogui.click()
            if not self.wait(self.get_click_delay()):
                return False

            pyautogui.moveTo(self.positions['send_to'])
            pyautogui.click()
            if not self.wait(self.get_click_delay()):
                return False

            pyautogui.moveTo(self.positions['shortcut'])
            pyautogui.click()
            if not self.wait(self.get_click_delay()):
                return False

            pyautogui.moveTo(self.positions['select_all'])
            pyautogui.click()
            if not self.wait(self.get_click_delay()):
                return False

            pyautogui.moveTo(self.positions['send_to'])
            pyautogui.click()
            if not self.wait(self.get_click_delay()):
                return False

            self.stats.session_snaps += 1
            self.stats.total_snaps_sent += shortcut_user_count
            nice_print(f"Snap batch sent to {shortcut_user_count} recipients", "✓", ACCENT_COLOR)
            return True

        except Exception as e:
            self.stats.errors_count += 1
            nice_print(f"Error sending snap: {e}", "✗", Fore.RED)
            return False

    def run_bot(self, shortcut_user_count, schedule_delay=0):
        """Runs the main bot loop"""
        if not self.positions:
            nice_print("No button positions configured. Capture them before starting.", "✗", Fore.RED)
            return

        if self.is_running:
            return

        self.stop_event.clear()
        self.pause_bot = False
        self.is_running = True
        self.first_try = True
        self.stats.start_session()
        nice_print("Preparing automation workflow...", "!", Fore.CYAN)

        if schedule_delay > 0:
            nice_print(f"Scheduled start in {int(schedule_delay)} seconds", "⏳", Fore.YELLOW)
            if not self.wait(schedule_delay):
                self.cleanup_after_stop()
                return

        if self.config.ramp_up_enabled and self.config.ramp_up_minutes > 0:
            ramp_seconds = int(self.config.ramp_up_minutes * 60)
            nice_print(f"Ramp-up delay active for {self.config.ramp_up_minutes} minute(s)", "⏳", Fore.YELLOW)
            if not self.wait(ramp_seconds):
                self.cleanup_after_stop()
                return

        nice_print("Automation started. Use the control panel to manage the session.", "▶", Fore.CYAN)

        while not self.stop_event.is_set():
            if self.pause_bot:
                time.sleep(0.1)
                continue

            if not self.send_snap(shortcut_user_count):
                if self.stop_event.is_set():
                    break

            if self.config.auto_stop_enabled and self.stats.session_snaps >= self.config.auto_stop_after:
                nice_print(f"Auto stop threshold reached ({self.config.auto_stop_after} snaps)", "!", Fore.YELLOW)
                break

            if self.config.session_duration_minutes:
                max_duration = self.config.session_duration_minutes * 60
                if self.stats.start_time and (time.time() - self.stats.start_time) >= max_duration:
                    nice_print("Configured session duration reached", "!", Fore.YELLOW)
                    break

            loop_delay = self.get_loop_delay()
            if not self.wait(loop_delay):
                break

        self.cleanup_after_stop()

    def cleanup_after_stop(self):
        """Handles cleanup once the bot stops"""
        self.stop_event.clear()
        running_before = self.is_running
        self.is_running = False
        self.pause_bot = False
        self.stats.end_session()
        if running_before:
            nice_print("Automation stopped", "✓", ACCENT_COLOR)

    def stop(self):
        """Signals the bot to stop"""
        self.stop_event.set()
        self.pause_bot = False

    def pause(self):
        """Pauses the bot"""
        if self.is_running:
            self.pause_bot = True
            nice_print("Automation paused", "||", Fore.YELLOW)

    def resume(self):
        """Resumes the bot if paused"""
        if self.is_running and self.pause_bot:
            self.pause_bot = False
            nice_print("Automation resumed", "▶", Fore.CYAN)


# ==================== UI COMPONENTS ====================
class SnapBotApp(tk.Tk):
    BG_MAIN = "#0f0f12"
    BG_CARD = "#16161a"
    BG_NAV = "#111115"
    BG_ACCENT = "#fffc00"
    FG_TEXT = "#f9f9f9"
    FG_MUTED = "#9a9a9f"

    def __init__(self):
        super().__init__()
        self.title(f"SnapScoreBot v{VERSION} – Automation Studio")
        self.geometry("1200x720")
        self.minsize(1080, 640)
        self.configure(bg=self.BG_MAIN)

        self.config_obj = Config()
        self.stats = Statistics()
        self.bot = AdvancedSnapBot(self.config_obj, self.stats)
        self.bot_thread = None

        register_log_listener(self._on_log_event)

        self.shortcut_count_var = tk.IntVar(value=1)
        self.schedule_delay_var = tk.IntVar(value=int(self.config_obj.schedule_delay_minutes))
        self.ramp_up_var = tk.IntVar(value=int(self.config_obj.ramp_up_minutes))
        self.safe_mode_var = tk.BooleanVar(value=self.config_obj.safe_mode)
        self.random_delay_var = tk.BooleanVar(value=self.config_obj.random_delay)
        self.auto_stop_var = tk.BooleanVar(value=self.config_obj.auto_stop_enabled)
        self.session_duration_var = tk.IntVar(value=int(self.config_obj.session_duration_minutes))

        self.loop_delay_var = tk.DoubleVar(value=self.config_obj.loop_delay)
        self.click_delay_var = tk.DoubleVar(value=self.config_obj.click_delay)
        self.random_min_var = tk.DoubleVar(value=self.config_obj.random_delay_min)
        self.random_max_var = tk.DoubleVar(value=self.config_obj.random_delay_max)
        self.auto_stop_after_var = tk.IntVar(value=self.config_obj.auto_stop_after)

        self._active_view = None
        self._nav_buttons = {}

        self._build_layout()
        self._show_view("dashboard")
        self.after(500, self._refresh_dashboard)

    # -------------- Layout Builders --------------
    def _build_layout(self):
        self.nav_frame = tk.Frame(self, bg=self.BG_NAV, width=220)
        self.nav_frame.pack(side="left", fill="y")

        logo_frame = tk.Frame(self.nav_frame, bg=self.BG_NAV)
        logo_frame.pack(fill="x", pady=(24, 32))
        tk.Label(logo_frame, text="Snap Automator", font=("Helvetica", 18, "bold"), fg=self.BG_ACCENT, bg=self.BG_NAV).pack(anchor="w", padx=24)
        tk.Label(logo_frame, text="by Eddie-500", font=("Helvetica", 10), fg=self.FG_MUTED, bg=self.BG_NAV).pack(anchor="w", padx=24, pady=(4, 0))

        self._add_nav_button("dashboard", "Dashboard")
        self._add_nav_button("control", "Automation Control")
        self._add_nav_button("settings", "Automation Settings")
        self._add_nav_button("statistics", "Statistics")
        self._add_nav_button("help", "Help & Safety")

        footer = tk.Frame(self.nav_frame, bg=self.BG_NAV)
        footer.pack(side="bottom", fill="x", pady=24)
        tk.Label(footer, text=f"Version {VERSION}", fg=self.FG_MUTED, bg=self.BG_NAV, font=("Helvetica", 9)).pack(anchor="w", padx=24)
        tk.Label(footer, text=CREDITS, fg=self.FG_MUTED, bg=self.BG_NAV, font=("Helvetica", 8)).pack(anchor="w", padx=24, pady=(6, 0))

        self.content_frame = tk.Frame(self, bg=self.BG_MAIN)
        self.content_frame.pack(side="left", fill="both", expand=True)

        self.content_wrapper = tk.Frame(self.content_frame, bg=self.BG_MAIN)
        self.content_wrapper.pack(fill="both", expand=True)

        log_frame = tk.Frame(self.content_frame, bg=self.BG_MAIN)
        log_frame.pack(fill="x", padx=24, pady=(0, 24))

        tk.Label(log_frame, text="Session Log", fg=self.FG_MUTED, bg=self.BG_MAIN, font=("Helvetica", 10, "bold")).pack(anchor="w")
        self.log_text = tk.Text(log_frame, height=8, bg=self.BG_CARD, fg=self.FG_TEXT, relief="flat", wrap="word")
        self.log_text.pack(fill="both", expand=True, pady=(8, 0))
        self.log_text.configure(state=tk.DISABLED)

    def _add_nav_button(self, key, label):
        btn = tk.Button(
            self.nav_frame,
            text=label,
            anchor="w",
            command=lambda k=key: self._show_view(k),
            font=("Helvetica", 12),
            bg=self.BG_NAV,
            fg=self.FG_TEXT,
            activebackground=self.BG_NAV,
            activeforeground=self.BG_ACCENT,
            relief="flat",
            padx=24,
            pady=12
        )
        btn.pack(fill="x")
        self._nav_buttons[key] = btn

    def _show_view(self, key):
        if self._active_view == key:
            return

        if self._active_view:
            self._nav_buttons[self._active_view].configure(bg=self.BG_NAV, fg=self.FG_TEXT)

        for widget in self.content_wrapper.winfo_children():
            widget.destroy()

        builder = {
            "dashboard": self._build_dashboard,
            "control": self._build_control,
            "settings": self._build_settings,
            "statistics": self._build_statistics,
            "help": self._build_help
        }.get(key)

        if builder:
            builder()
            self._nav_buttons[key].configure(bg=self.BG_ACCENT, fg="black")
            self._active_view = key

    # -------------- View Builders --------------
    def _build_dashboard(self):
        frame = tk.Frame(self.content_wrapper, bg=self.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        header = tk.Frame(frame, bg=self.BG_MAIN)
        header.pack(fill="x")
        tk.Label(header, text="Automation Overview", font=("Helvetica", 22, "bold"), fg=self.FG_TEXT, bg=self.BG_MAIN).pack(anchor="w")
        tk.Label(header, text="Monitor your Snapchat automation performance in real time.", font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_MAIN).pack(anchor="w", pady=(6, 18))

        cards = tk.Frame(frame, bg=self.BG_MAIN)
        cards.pack(fill="x")

        self.total_snaps_var = tk.StringVar()
        self.session_snaps_var = tk.StringVar()
        self.errors_var = tk.StringVar()
        self.elapsed_var = tk.StringVar()

        self._create_stat_card(cards, "Total Snaps Sent", self.total_snaps_var)
        self._create_stat_card(cards, "Snaps This Session", self.session_snaps_var)
        self._create_stat_card(cards, "Session Errors", self.errors_var)
        self._create_stat_card(cards, "Elapsed Time", self.elapsed_var)

        lower = tk.Frame(frame, bg=self.BG_MAIN)
        lower.pack(fill="both", expand=True, pady=(24, 0))

        left = tk.Frame(lower, bg=self.BG_CARD)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))
        left.configure(padx=24, pady=24)

        tk.Label(left, text="Current Configuration", font=("Helvetica", 14, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(anchor="w")
        tk.Label(left, text="Key automation parameters", font=("Helvetica", 10), fg=self.FG_MUTED, bg=self.BG_CARD).pack(anchor="w", pady=(4, 12))

        config_items = [
            ("Loop Delay", lambda: f"{self.config_obj.loop_delay:.1f}s"),
            ("Click Delay", lambda: f"{self.config_obj.click_delay:.1f}s"),
            ("Random Delay", lambda: "Enabled" if self.config_obj.random_delay else "Disabled"),
            ("Auto Stop", lambda: f"{self.config_obj.auto_stop_after} snaps" if self.config_obj.auto_stop_enabled else "Disabled"),
            ("Safe Mode", lambda: "On" if self.config_obj.safe_mode else "Off"),
            ("Scheduled Start", lambda: f"{self.config_obj.schedule_delay_minutes} min" if self.config_obj.schedule_delay_minutes else "Immediate"),
            ("Session Duration", lambda: f"{self.config_obj.session_duration_minutes} min" if self.config_obj.session_duration_minutes else "Unlimited")
        ]

        for label_text, value_func in config_items:
            row = tk.Frame(left, bg=self.BG_CARD)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label_text, font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_CARD).pack(side="left")
            value_lbl = tk.Label(row, text=value_func(), font=("Helvetica", 11, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD)
            value_lbl.pack(side="right")

        right = tk.Frame(lower, bg=self.BG_CARD)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))
        right.configure(padx=24, pady=24)

        tk.Label(right, text="Last Session", font=("Helvetica", 14, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(anchor="w")
        tk.Label(right, text="Historical context for your automations", font=("Helvetica", 10), fg=self.FG_MUTED, bg=self.BG_CARD).pack(anchor="w", pady=(4, 12))

        last_session_text = tk.Text(right, height=6, bg=self.BG_CARD, fg=self.FG_TEXT, relief="flat", wrap="word")
        last_session_text.pack(fill="both", expand=True)
        last_session_text.insert("1.0", self._format_last_session())
        last_session_text.configure(state=tk.DISABLED)

    def _create_stat_card(self, parent, title, variable):
        card = tk.Frame(parent, bg=self.BG_CARD, padx=24, pady=24)
        card.pack(side="left", expand=True, fill="both", padx=6)
        tk.Label(card, text=title, fg=self.FG_MUTED, bg=self.BG_CARD, font=("Helvetica", 10, "bold")).pack(anchor="w")
        tk.Label(card, textvariable=variable, fg=self.FG_TEXT, bg=self.BG_CARD, font=("Helvetica", 24, "bold")).pack(anchor="w", pady=(12, 0))

    def _build_control(self):
        frame = tk.Frame(self.content_wrapper, bg=self.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(frame, text="Automation Control Center", font=("Helvetica", 22, "bold"), fg=self.FG_TEXT, bg=self.BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="Configure positions, scheduling, and live controls for your automation session.", font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_MAIN).pack(anchor="w", pady=(6, 18))

        sections = tk.Frame(frame, bg=self.BG_MAIN)
        sections.pack(fill="both", expand=True)

        left = tk.Frame(sections, bg=self.BG_CARD, padx=24, pady=24)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(left, text="Button Mapping", font=("Helvetica", 14, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(anchor="w")
        tk.Label(left, text="Capture or manage the screen locations required for automation.", font=("Helvetica", 10), fg=self.FG_MUTED, bg=self.BG_CARD).pack(anchor="w", pady=(4, 12))

        status_text = "Ready" if self.bot.positions else "Not configured"
        self.position_status_var = tk.StringVar(value=status_text)
        status_row = tk.Frame(left, bg=self.BG_CARD)
        status_row.pack(fill="x", pady=(0, 16))
        tk.Label(status_row, text="Status:", font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_CARD).pack(side="left")
        tk.Label(status_row, textvariable=self.position_status_var, font=("Helvetica", 11, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(side="left", padx=(8, 0))

        btn_frame = tk.Frame(left, bg=self.BG_CARD)
        btn_frame.pack(fill="x")
        self._primary_button(btn_frame, "Capture Positions", self._capture_positions).pack(fill="x", pady=(0, 8))
        self._secondary_button(btn_frame, "Load Saved Positions", self._load_positions).pack(fill="x", pady=4)
        self._secondary_button(btn_frame, "Clear Stored Positions", self._clear_positions).pack(fill="x", pady=4)

        right = tk.Frame(sections, bg=self.BG_CARD, padx=24, pady=24)
        right.pack(side="left", fill="both", expand=True, padx=(12, 0))

        tk.Label(right, text="Session Parameters", font=("Helvetica", 14, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(anchor="w")
        tk.Label(right, text="Fine tune timing and scheduling for this run.", font=("Helvetica", 10), fg=self.FG_MUTED, bg=self.BG_CARD).pack(anchor="w", pady=(4, 12))

        self._build_spinbox(right, "Recipients in shortcut", self.shortcut_count_var, 1, 500)
        self._build_slider(right, "Scheduled start (minutes)", self.schedule_delay_var, 0, 30, self._on_schedule_change)
        ramp_row = self._build_slider(right, "Ramp-up time (minutes)", self.ramp_up_var, 0, 15, self._on_ramp_change)
        self._build_slider(right, "Session duration limit (minutes)", self.session_duration_var, 0, 180, self._on_session_duration_change, note="0 = unlimited")

        safe_check = tk.Checkbutton(right, text="Safe mode (adds subtle human-like delays)", variable=self.safe_mode_var,
                                    command=self._toggle_safe_mode, bg=self.BG_CARD, fg=self.FG_TEXT, selectcolor=self.BG_CARD,
                                    activebackground=self.BG_CARD, font=("Helvetica", 10))
        safe_check.pack(anchor="w", pady=(18, 4))

        random_check = tk.Checkbutton(right, text="Randomize click delays", variable=self.random_delay_var,
                                      command=self._toggle_random_delay, bg=self.BG_CARD, fg=self.FG_TEXT, selectcolor=self.BG_CARD,
                                      activebackground=self.BG_CARD, font=("Helvetica", 10))
        random_check.pack(anchor="w", pady=4)

        auto_stop_check = tk.Checkbutton(right, text="Auto stop after X snaps", variable=self.auto_stop_var,
                                         command=self._toggle_auto_stop, bg=self.BG_CARD, fg=self.FG_TEXT, selectcolor=self.BG_CARD,
                                         activebackground=self.BG_CARD, font=("Helvetica", 10))
        auto_stop_check.pack(anchor="w", pady=4)

        control_panel = tk.Frame(frame, bg=self.BG_MAIN)
        control_panel.pack(fill="x", pady=(18, 0))

        self.start_button = self._primary_button(control_panel, "Start Automation", self._start_bot)
        self.start_button.pack(side="left", padx=(0, 12))

        self.pause_button = self._secondary_button(control_panel, "Pause", self._toggle_pause)
        self.pause_button.pack(side="left", padx=12)

        self.stop_button = self._secondary_button(control_panel, "Stop", self._stop_bot)
        self.stop_button.pack(side="left", padx=12)

        self._update_control_states()

    def _build_settings(self):
        frame = tk.Frame(self.content_wrapper, bg=self.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(frame, text="Automation Settings", font=("Helvetica", 22, "bold"), fg=self.FG_TEXT, bg=self.BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="Adjust timing parameters and persistence for your automation workflow.", font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_MAIN).pack(anchor="w", pady=(6, 18))

        settings_card = tk.Frame(frame, bg=self.BG_CARD, padx=24, pady=24)
        settings_card.pack(fill="both", expand=True)

        self._build_spinbox(settings_card, "Loop delay (seconds)", self.loop_delay_var, 0.5, 60, increment=0.5)
        self._build_spinbox(settings_card, "Click delay (seconds)", self.click_delay_var, 0.1, 10, increment=0.1)
        self.random_min_spin = self._build_spinbox(settings_card, "Random delay minimum (seconds)", self.random_min_var, 0.1, 10, increment=0.1)
        self.random_max_spin = self._build_spinbox(settings_card, "Random delay maximum (seconds)", self.random_max_var, 0.2, 15, increment=0.1)
        self.auto_stop_spin = self._build_spinbox(settings_card, "Auto stop after snaps", self.auto_stop_after_var, 10, 1000, increment=5)

        btn_row = tk.Frame(settings_card, bg=self.BG_CARD)
        btn_row.pack(fill="x", pady=(24, 0))
        self._primary_button(btn_row, "Save Settings", self._save_settings).pack(side="left")
        self._secondary_button(btn_row, "Restore Defaults", self._reset_settings).pack(side="left", padx=12)

        self._toggle_random_delay()
        self._toggle_auto_stop()

    def _build_statistics(self):
        frame = tk.Frame(self.content_wrapper, bg=self.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(frame, text="Statistics", font=("Helvetica", 22, "bold"), fg=self.FG_TEXT, bg=self.BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="Review performance and historical activity.", font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_MAIN).pack(anchor="w", pady=(6, 18))

        stats_card = tk.Frame(frame, bg=self.BG_CARD, padx=24, pady=24)
        stats_card.pack(fill="both", expand=True)

        info = tk.Text(stats_card, height=12, bg=self.BG_CARD, fg=self.FG_TEXT, relief="flat", wrap="word")
        info.pack(fill="both", expand=True)
        info.insert("1.0", self._compose_statistics())
        info.configure(state=tk.DISABLED)

        self._secondary_button(stats_card, "Reset Statistics", self._reset_statistics).pack(anchor="e", pady=(18, 0))

    def _build_help(self):
        frame = tk.Frame(self.content_wrapper, bg=self.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=24, pady=24)

        tk.Label(frame, text="Help & Safety", font=("Helvetica", 22, "bold"), fg=self.FG_TEXT, bg=self.BG_MAIN).pack(anchor="w")
        tk.Label(frame, text="Important guidelines for running Snapchat automations responsibly.", font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_MAIN).pack(anchor="w", pady=(6, 18))

        help_card = tk.Frame(frame, bg=self.BG_CARD, padx=24, pady=24)
        help_card.pack(fill="both", expand=True)

        instructions = (
            "1. Prepare a Snapchat shortcut with the friends you want to send snaps to.\n"
            "2. Open Snapchat Web, log in, and allow camera and microphone permissions.\n"
            "3. Use the button mapping wizard to capture the camera, send, shortcut, and select-all buttons.\n"
            "4. Configure delays, schedule, and safety preferences inside the control center.\n"
            "5. Start the automation and monitor the live log to ensure everything behaves as expected."
        )

        safety = (
            "• This tool is for educational purposes only and is not affiliated with Snapchat Inc.\n"
            "• Automating Snapchat interactions violates the Snapchat Terms of Service.\n"
            "• Excessive usage or aggressive timing may result in permanent account bans.\n"
            "• Use safe mode, randomization, and human-like delays to reduce detection risk.\n"
            "• The developer is not responsible for misuse—run automations at your own risk."
        )

        tk.Label(help_card, text="Quick Start", font=("Helvetica", 14, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(anchor="w")
        quick_text = tk.Text(help_card, height=8, bg=self.BG_CARD, fg=self.FG_TEXT, relief="flat", wrap="word")
        quick_text.pack(fill="x", pady=(8, 18))
        quick_text.insert("1.0", instructions)
        quick_text.configure(state=tk.DISABLED)

        tk.Label(help_card, text="Safety Reminder", font=("Helvetica", 14, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD).pack(anchor="w")
        safety_text = tk.Text(help_card, height=8, bg=self.BG_CARD, fg=self.FG_TEXT, relief="flat", wrap="word")
        safety_text.pack(fill="both", expand=True, pady=(8, 0))
        safety_text.insert("1.0", safety)
        safety_text.configure(state=tk.DISABLED)

    # -------------- UI Helpers --------------
    def _primary_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, font=("Helvetica", 11, "bold"),
                         bg=self.BG_ACCENT, fg="black", relief="flat", padx=16, pady=10, activebackground="#fff76a")

    def _secondary_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, font=("Helvetica", 11),
                         bg="#1f1f25", fg=self.FG_TEXT, relief="flat", padx=16, pady=10, activebackground="#2a2a30")

    def _build_spinbox(self, parent, label, variable, minimum, maximum, increment=1):
        row = tk.Frame(parent, bg=self.BG_CARD)
        row.pack(fill="x", pady=6)
        tk.Label(row, text=label, font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_CARD).pack(anchor="w")
        spin = tk.Spinbox(row, from_=minimum, to=maximum, increment=increment, textvariable=variable,
                          font=("Helvetica", 11), width=8, bg="#1d1d22", fg=self.FG_TEXT, relief="flat")
        spin.pack(anchor="w", pady=(6, 0))
        variable.trace_add("write", lambda *args, attr=label: self._on_variable_change(variable))
        return spin

    def _build_slider(self, parent, label, variable, minimum, maximum, callback=None, note=None):
        row = tk.Frame(parent, bg=self.BG_CARD)
        row.pack(fill="x", pady=6)
        header = tk.Frame(row, bg=self.BG_CARD)
        header.pack(fill="x")
        tk.Label(header, text=label, font=("Helvetica", 11), fg=self.FG_MUTED, bg=self.BG_CARD).pack(side="left")
        value_label = tk.Label(header, text=f"{variable.get()}", font=("Helvetica", 11, "bold"), fg=self.FG_TEXT, bg=self.BG_CARD)
        value_label.pack(side="right")

        slider = tk.Scale(row, from_=minimum, to=maximum, orient="horizontal", showvalue=False,
                          resolution=1, variable=variable, length=320,
                          bg=self.BG_CARD, fg=self.FG_TEXT, highlightthickness=0,
                          troughcolor="#1f1f25", sliderrelief="flat", sliderlength=18)
        slider.pack(fill="x", pady=(6, 0))

        if note:
            tk.Label(row, text=note, font=("Helvetica", 9), fg=self.FG_MUTED, bg=self.BG_CARD).pack(anchor="w", pady=(4, 0))

        def on_change(*_):
            value_label.configure(text=f"{variable.get()}")
            if callback:
                callback()

        variable.trace_add("write", on_change)
        return row

    def _on_variable_change(self, variable):
        try:
            self.config_obj.loop_delay = float(self.loop_delay_var.get())
            self.config_obj.click_delay = float(self.click_delay_var.get())
            self.config_obj.random_delay_min = float(self.random_min_var.get())
            self.config_obj.random_delay_max = float(self.random_max_var.get())
            self.config_obj.auto_stop_after = int(self.auto_stop_after_var.get())
            if self.config_obj.random_delay_min > self.config_obj.random_delay_max:
                self.config_obj.random_delay_max = self.config_obj.random_delay_min
                self.random_max_var.set(self.config_obj.random_delay_max)
        except (tk.TclError, ValueError):
            pass

    def _on_schedule_change(self):
        self.config_obj.schedule_delay_minutes = int(self.schedule_delay_var.get())

    def _on_ramp_change(self):
        self.config_obj.ramp_up_minutes = int(self.ramp_up_var.get())

    def _on_session_duration_change(self):
        self.config_obj.session_duration_minutes = int(self.session_duration_var.get())

    def _toggle_safe_mode(self):
        self.config_obj.safe_mode = bool(self.safe_mode_var.get())
        nice_print(f"Safe mode {'enabled' if self.config_obj.safe_mode else 'disabled'}", "!", Fore.CYAN)

    def _toggle_random_delay(self):
        enabled = bool(self.random_delay_var.get())
        self.config_obj.random_delay = enabled
        state = tk.NORMAL if enabled else tk.DISABLED
        for widget in (self.random_min_spin, self.random_max_spin):
            widget.configure(state=state)
        nice_print(f"Random delay {'enabled' if enabled else 'disabled'}", "!", Fore.CYAN)

    def _toggle_auto_stop(self):
        enabled = bool(self.auto_stop_var.get())
        self.config_obj.auto_stop_enabled = enabled
        self.auto_stop_spin.configure(state=tk.NORMAL if enabled else tk.DISABLED)
        nice_print(f"Auto stop {'enabled' if enabled else 'disabled'}", "!", Fore.CYAN)

    def _capture_positions(self):
        def worker():
            success = self.bot.get_positions()
            self.after(0, lambda: self._on_positions_updated(success))

        threading.Thread(target=worker, daemon=True).start()

    def _on_positions_updated(self, success):
        if success:
            self.position_status_var.set("Ready")
            messagebox.showinfo("Positions Saved", "Button coordinates saved successfully.")
        else:
            messagebox.showwarning("Operation Cancelled", "Position capture cancelled.")

    def _load_positions(self):
        if self.bot.load_positions():
            self.position_status_var.set("Ready")
        else:
            messagebox.showerror("Not Found", "No saved positions were found.")

    def _clear_positions(self):
        self.bot.clear_positions()
        self.position_status_var.set("Not configured")

    def _start_bot(self):
        if self.bot_thread and self.bot_thread.is_alive():
            return

        if not self.bot.positions:
            if not self.bot.load_positions():
                messagebox.showwarning("Positions Required", "Capture or load button positions before starting.")
                return
            self.position_status_var.set("Ready")

        shortcut_count = max(1, int(self.shortcut_count_var.get() or 1))
        self.shortcut_count_var.set(shortcut_count)

        schedule_seconds = int(self.config_obj.schedule_delay_minutes * 60)

        def runner():
            try:
                self.bot.run_bot(shortcut_count, schedule_delay=schedule_seconds)
            finally:
                self.after(0, self._on_bot_stopped)

        self.bot_thread = threading.Thread(target=runner, daemon=True)
        self.bot_thread.start()
        nice_print("Automation thread launched", "!", Fore.CYAN)
        self._update_control_states()

    def _toggle_pause(self):
        if not self.bot.is_running:
            return
        if self.bot.pause_bot:
            self.bot.resume()
            self.pause_button.configure(text="Pause")
        else:
            self.bot.pause()
            self.pause_button.configure(text="Resume")

    def _stop_bot(self):
        if self.bot.is_running:
            self.bot.stop()
        self._update_control_states()

    def _on_bot_stopped(self):
        self.pause_button.configure(text="Pause")
        self._update_control_states()

    def _update_control_states(self):
        running = self.bot.is_running or (self.bot_thread and self.bot_thread.is_alive())
        self.start_button.configure(state=tk.DISABLED if running else tk.NORMAL)
        self.pause_button.configure(state=tk.NORMAL if running else tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL if running else tk.DISABLED)

    def _save_settings(self):
        self.config_obj.save_config()
        messagebox.showinfo("Settings Saved", "Configuration saved successfully.")

    def _reset_settings(self):
        self.config_obj.reset_defaults()
        self._sync_from_config()
        messagebox.showinfo("Defaults Restored", "Configuration reset to defaults.")

    def _sync_from_config(self):
        self.loop_delay_var.set(self.config_obj.loop_delay)
        self.click_delay_var.set(self.config_obj.click_delay)
        self.random_min_var.set(self.config_obj.random_delay_min)
        self.random_max_var.set(self.config_obj.random_delay_max)
        self.auto_stop_after_var.set(self.config_obj.auto_stop_after)
        self.schedule_delay_var.set(int(self.config_obj.schedule_delay_minutes))
        self.ramp_up_var.set(int(self.config_obj.ramp_up_minutes))
        self.safe_mode_var.set(self.config_obj.safe_mode)
        self.random_delay_var.set(self.config_obj.random_delay)
        self.auto_stop_var.set(self.config_obj.auto_stop_enabled)
        self.session_duration_var.set(int(self.config_obj.session_duration_minutes))
        self._toggle_random_delay()
        self._toggle_auto_stop()
        self._toggle_safe_mode()

    def _reset_statistics(self):
        if messagebox.askyesno("Reset Statistics", "Are you sure you want to clear all statistics?"):
            self.stats.reset_statistics()
            messagebox.showinfo("Statistics Reset", "All statistics have been cleared.")
            self._show_view("statistics")

    def _compose_statistics(self):
        last_session_time = self.stats.last_session_time
        if last_session_time:
            try:
                last_session = datetime.fromisoformat(last_session_time)
                last_session_str = last_session.strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                last_session_str = last_session_time
        else:
            last_session_str = "Never"

        return (
            f"Total snaps sent historically: {self.stats.total_snaps_sent}\n"
            f"Snaps sent in current session: {self.stats.session_snaps}\n"
            f"Errors detected in current session: {self.stats.errors_count}\n"
            f"Last session snaps: {self.stats.last_session_snaps}\n"
            f"Last session duration: {int(self.stats.last_session_duration // 60)}m {int(self.stats.last_session_duration % 60)}s\n"
            f"Last session run: {last_session_str}\n"
        )

    def _format_last_session(self):
        if not self.stats.last_session_time:
            return "No historical data available yet."
        try:
            last_run = datetime.fromisoformat(self.stats.last_session_time)
            timestamp = last_run.strftime("%B %d, %Y at %H:%M:%S")
        except Exception:
            timestamp = self.stats.last_session_time
        duration_minutes = int(self.stats.last_session_duration // 60)
        duration_seconds = int(self.stats.last_session_duration % 60)
        return (
            f"Last run on {timestamp}.\n"
            f"Snaps sent: {self.stats.last_session_snaps}\n"
            f"Duration: {duration_minutes} minute(s) and {duration_seconds} second(s).\n"
            f"Total historical snaps: {self.stats.total_snaps_sent}."
        )

    def _refresh_dashboard(self):
        self.total_snaps_var.set(f"{self.stats.total_snaps_sent:,}")
        self.session_snaps_var.set(f"{self.stats.session_snaps:,}")
        self.errors_var.set(f"{self.stats.errors_count:,}")
        self.elapsed_var.set(self.stats.get_elapsed_time())
        if self._active_view == "dashboard":
            for widget in self.content_wrapper.winfo_children():
                if isinstance(widget, tk.Frame):
                    break
        self.after(500, self._refresh_dashboard)

    def _on_log_event(self, text, status, color):
        self.log_text.configure(state=tk.NORMAL)
        color_tag = {
            ACCENT_COLOR: "accent",
            Fore.RED: "error",
            Fore.CYAN: "info",
            Fore.YELLOW: "warning"
        }.get(color, "info")

        if not self.log_text.tag_ranges(color_tag):
            self.log_text.tag_configure("accent", foreground="#ffd600")
            self.log_text.tag_configure("error", foreground="#ff7070")
            self.log_text.tag_configure("info", foreground="#9ad0ff")
            self.log_text.tag_configure("warning", foreground="#ffe066")

        message = f"[{status}] {text}\n"
        self.log_text.insert(tk.END, message, color_tag)
        self.log_text.see(tk.END)
        self.log_text.configure(state=tk.DISABLED)

    def destroy(self):
        unregister_log_listener(self._on_log_event)
        super().destroy()


# ==================== VERSION CHECK ====================
def check_version():
    """Checks for new versions available"""
    try:
        r = requests.get("https://raw.githubusercontent.com/useragents/Snapchat-Snapscore-Botter/refs/heads/main/version.txt", timeout=3)
        latest_version = r.text.strip()
        if latest_version != VERSION:
            nice_print(f"New version available: {latest_version}", "!", Fore.YELLOW)
            nice_print(f"Your version: {VERSION}", "!", Fore.YELLOW)
    except Exception:
        nice_print("Unable to verify latest version", "!", Fore.YELLOW)


# ==================== MAIN FUNCTION ====================
def main():
    """Main program entry point"""
    check_version()

    app = SnapBotApp()
    app.mainloop()


# ==================== PROGRAM ENTRY ====================
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        nice_print("Program interrupted by user", "!", Fore.YELLOW)
        sys.exit(0)
    except Exception as e:
        nice_print(f"Critical error: {e}", "✗", Fore.RED)
        input("Press ENTER to exit...")
        sys.exit(1)
