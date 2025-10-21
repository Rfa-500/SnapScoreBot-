import sys
import platform
import os
import time
import json
import threading
import random
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox

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
from colorama import Fore, init

# Initialize colorama for console fallbacks
init(autoreset=True, convert=True)

# ==================== SETTINGS ====================
TUTORIAL_VIDEO = "Soon"
VERSION = "3.0.0"
CREDITS = "Eddie-500 - Educational Purpose Only"
CONFIG_FILE = "config.json"

# ==================== HELPER FUNCTIONS ====================
def title(text):
    """Sets the console window title when available"""
    if sys.platform.startswith('win'):
        import ctypes
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(text)
        except Exception:
            pass


def nice_print(text, status="-", color=Fore.WHITE):
    """Formatted print with status icon (console fallback)"""
    print(f"{Fore.WHITE}[{Fore.RED}{status}{Fore.WHITE}] {color}{text}")

# ==================== CONFIGURATION CLASS ====================
class Config:
    def __init__(self):
        self.loop_delay = 5
        self.click_delay = 1.2
        self.position_delay = 0.5
        self.random_delay = False
        self.random_delay_min = 3
        self.random_delay_max = 8
        self.auto_stop_enabled = False
        self.auto_stop_after = 100
        self.schedule_delay_enabled = False
        self.schedule_delay_seconds = 0
        self.pre_snap_delay = 1.0
        self.cooldown_enabled = False
        self.cooldown_after = 25
        self.cooldown_duration = 30
        self.anti_detection_jitter = False
        self.anti_detection_range = 12
        self.session_alerts = True
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
                nice_print("Configuration loaded", "✓", Fore.GREEN)
            except:
                pass
    
    def save_config(self):
        """Saves configuration to JSON file"""
        data = {
            'loop_delay': self.loop_delay,
            'click_delay': self.click_delay,
            'position_delay': self.position_delay,
            'random_delay': self.random_delay,
            'random_delay_min': self.random_delay_min,
            'random_delay_max': self.random_delay_max,
            'auto_stop_enabled': self.auto_stop_enabled,
            'auto_stop_after': self.auto_stop_after,
            'schedule_delay_enabled': self.schedule_delay_enabled,
            'schedule_delay_seconds': self.schedule_delay_seconds,
            'pre_snap_delay': self.pre_snap_delay,
            'cooldown_enabled': self.cooldown_enabled,
            'cooldown_after': self.cooldown_after,
            'cooldown_duration': self.cooldown_duration,
            'anti_detection_jitter': self.anti_detection_jitter,
            'anti_detection_range': self.anti_detection_range,
            'session_alerts': self.session_alerts
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=4)
        nice_print("Configuration saved", "✓", Fore.GREEN)

# ==================== STATISTICS CLASS ====================
class Statistics:
    def __init__(self):
        self.total_snaps_sent = 0
        self.session_snaps = 0
        self.start_time = None
        self.errors_count = 0
        self.stats_file = "stats.json"
        self.longest_streak = 0
        self.current_streak = 0
        self.last_session = None
        self.load_stats()
    
    def load_stats(self):
        """Loads previous statistics"""
        if Path(self.stats_file).exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_snaps_sent = data.get('total_snaps_sent', 0)
                    self.longest_streak = data.get('longest_streak', 0)
                    self.last_session = data.get('last_session')
            except:
                pass
    
    def save_stats(self):
        """Saves statistics"""
        data = {
            'total_snaps_sent': self.total_snaps_sent,
            'last_session': datetime.now().isoformat(),
            'last_session_snaps': self.session_snaps,
            'longest_streak': self.longest_streak
        }
        with open(self.stats_file, 'w') as f:
            json.dump(data, f, indent=4)
        self.last_session = data['last_session']

    def get_elapsed_time(self):
        """Gets formatted elapsed time"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = int(elapsed % 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"

    def reset_session(self):
        self.session_snaps = 0
        self.errors_count = 0
        self.current_streak = 0
        self.start_time = None

# ==================== SNAP BOT CORE ====================
class AdvancedSnapBot:
    def __init__(self, config, stats, log_callback=None, status_callback=None, session_callback=None):
        self.config = config
        self.stats = stats
        self.positions = {}
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.session_callback = session_callback
        self.thread = None
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.shortcut_user_count = 0
        self.first_try = True

    def log(self, message, level="info"):
        if self.log_callback:
            self.log_callback(message, level)
        else:
            color = Fore.WHITE
            if level == "success":
                color = Fore.GREEN
            elif level == "warning":
                color = Fore.YELLOW
            elif level == "error":
                color = Fore.RED
            nice_print(message, "!", color)

    def update_status(self, message):
        if self.status_callback:
            self.status_callback(message)

    def notify_session_update(self):
        if self.session_callback:
            self.session_callback()

    def get_positions(self):
        """Captures mouse positions"""
        positions_needed = [
            ('camera', 'Camera button'),
            ('send_to', 'Send to button'),
            ('shortcut', 'Shortcut button'),
            ('select_all', 'Select All button')
        ]

        self.log("Position capture started. Press Esc to cancel.", "warning")

        for key, description in positions_needed:
            prompt = f"Move the mouse to the {description} and press F"
            self.update_status(prompt)
            self.log(prompt, "info")

            while True:
                if keyboard.is_pressed("f"):
                    self.positions[key] = pyautogui.position()
                    self.log(f"Position saved for {description}: {self.positions[key]}", "success")
                    time.sleep(self.config.position_delay)
                    break
                if keyboard.is_pressed("escape"):
                    self.log("Position capture canceled", "error")
                    self.update_status("Position capture canceled")
                    return False
                time.sleep(0.05)

        self.save_positions()
        self.update_status("All positions captured")
        return True
    
    def save_positions(self):
        """Saves positions to a JSON file"""
        positions_data = {k: {'x': v.x, 'y': v.y} for k, v in self.positions.items()}
        with open('positions.json', 'w') as f:
            json.dump(positions_data, f)
        self.log("Positions saved", "success")

    def load_positions(self):
        """Loads previously saved positions"""
        if Path('positions.json').exists():
            try:
                with open('positions.json', 'r') as f:
                    data = json.load(f)
                    for key, coords in data.items():
                        self.positions[key] = pyautogui.Point(coords['x'], coords['y'])
                self.log("Positions loaded", "success")
                return True
            except:
                pass
        return False
    
    def jitter_point(self, point):
        if not self.config.anti_detection_jitter:
            return point

        jitter_range = max(1, int(self.config.anti_detection_range))
        offset_x = random.randint(-jitter_range, jitter_range)
        offset_y = random.randint(-jitter_range, jitter_range)
        return pyautogui.Point(point.x + offset_x, point.y + offset_y)

    def send_snap(self):
        """Sends a snap sequence"""
        try:
            if self.config.pre_snap_delay > 0:
                time.sleep(self.config.pre_snap_delay)

            pyautogui.moveTo(self.jitter_point(self.positions['camera']))
            if self.first_try:
                pyautogui.click()
                self.first_try = False
            time.sleep(self.get_delay())

            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.jitter_point(self.positions['send_to']))
            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.jitter_point(self.positions['shortcut']))
            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.jitter_point(self.positions['select_all']))
            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.jitter_point(self.positions['send_to']))
            pyautogui.click()

            return True

        except Exception as e:
            self.stats.errors_count += 1
            self.log(f"Error sending snap: {e}", "error")
            return False
    
    def get_delay(self):
        """Returns a random or fixed delay"""
        if self.config.random_delay:
            return random.uniform(self.config.random_delay_min, self.config.random_delay_max)
        return self.config.click_delay

    def get_loop_delay(self):
        if self.config.random_delay:
            return random.uniform(self.config.random_delay_min, self.config.random_delay_max)
        return self.config.loop_delay

    def start(self, shortcut_user_count):
        if self.thread and self.thread.is_alive():
            self.log("Bot is already running", "warning")
            return False

        if not self.positions:
            if not self.load_positions():
                self.log("No saved positions found. Please capture positions first.", "error")
                return False

        self.shortcut_user_count = shortcut_user_count
        self.stop_event.clear()
        self.pause_event.clear()
        self.stats.reset_session()
        self.stats.start_time = time.time()
        self.first_try = True
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        return True

    def run(self):
        self.log("Automation thread started", "info")
        title(f"SnapScoreBot v{VERSION} - Running")

        if self.config.schedule_delay_enabled and self.config.schedule_delay_seconds > 0:
            seconds = int(self.config.schedule_delay_seconds)
            for remaining in range(seconds, 0, -1):
                if self.stop_event.is_set():
                    self.log("Start countdown cancelled", "warning")
                    self.update_status("Start cancelled")
                    return
                self.update_status(f"Starting in {remaining}s")
                time.sleep(1)

        cooldown_counter = 0
        self.update_status("Running automation")
        self.notify_session_update()

        while not self.stop_event.is_set():
            if self.pause_event.is_set():
                self.update_status("Paused")
                time.sleep(0.2)
                continue

            if self.config.cooldown_enabled and cooldown_counter >= self.config.cooldown_after:
                self.update_status("Cooling down")
                self.log(
                    f"Cooldown engaged for {self.config.cooldown_duration}s after {self.config.cooldown_after} snaps",
                    "warning"
                )
                for _ in range(int(self.config.cooldown_duration)):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                cooldown_counter = 0
                self.update_status("Resuming automation")

            success = self.send_snap()

            if success:
                cooldown_counter += 1
                self.stats.session_snaps += 1
                self.stats.total_snaps_sent += self.shortcut_user_count
                self.stats.current_streak += 1
                self.stats.longest_streak = max(self.stats.longest_streak, self.stats.current_streak)
                self.notify_session_update()
                self.log(
                    f"Snap dispatched to {self.shortcut_user_count} recipients (session total: {self.stats.session_snaps})",
                    "success"
                )
            else:
                self.stats.current_streak = 0
                self.notify_session_update()

            if self.config.auto_stop_enabled and self.stats.session_snaps >= self.config.auto_stop_after:
                self.log("Auto-stop threshold reached", "warning")
                break

            loop_delay = self.get_loop_delay()
            self.update_status(f"Waiting {loop_delay:.1f}s before next snap")

            for _ in range(int(max(loop_delay * 10, 1))):
                if self.stop_event.is_set() or self.pause_event.is_set():
                    break
                time.sleep(0.1)

        self.stop_event.set()
        self.update_status("Idle")
        self.log("Bot stopped", "info")
        self.stats.save_stats()
        self.notify_session_update()

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.log("Stopping bot", "warning")
            self.stop_event.set()
            self.pause_event.clear()
            self.thread.join(timeout=5)
            self.thread = None
            self.update_status("Idle")

    def toggle_pause(self):
        if not self.thread or not self.thread.is_alive():
            return False
        if self.pause_event.is_set():
            self.pause_event.clear()
            self.update_status("Running automation")
            self.log("Automation resumed", "info")
        else:
            self.pause_event.set()
            self.update_status("Paused")
            self.log("Automation paused", "warning")
        return True

    def is_running(self):
        return self.thread is not None and self.thread.is_alive()
# ==================== VERSION CHECK ====================
def check_version():
    """Checks for new versions available"""
    try:
        r = requests.get(
            "https://raw.githubusercontent.com/useragents/Snapchat-Snapscore-Botter/refs/heads/main/version.txt",
            timeout=3
        )
        latest_version = r.text.strip()
        if latest_version and latest_version != VERSION:
            return latest_version
    except Exception:
        return None


class SnapScoreBotApp:
    """Graphical control panel for the SnapScore automation"""

    BG_BASE = "#0d0d0d"
    BG_PANEL = "#161616"
    BG_NAV = "#121212"
    ACCENT = "#FFFC00"
    TEXT_PRIMARY = "#f7f7f7"
    TEXT_SECONDARY = "#b5b5b5"

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"SnapScoreBot v{VERSION}")
        self.root.geometry("1180x700")
        self.root.configure(bg=self.BG_BASE)
        self.root.minsize(1050, 640)

        self.version_info = check_version()

        self.config = Config()
        self.stats = Statistics()
        self.status_var = tk.StringVar(value="Idle")
        self.total_sent_var = tk.StringVar(value="0")
        self.session_sent_var = tk.StringVar(value="0")
        self.elapsed_var = tk.StringVar(value="00:00:00")
        self.error_var = tk.StringVar(value="0")
        self.streak_var = tk.StringVar(value="0")

        self.shortcut_count_var = tk.IntVar(value=1)
        self.random_delay_var = tk.BooleanVar(value=self.config.random_delay)
        self.auto_stop_var = tk.BooleanVar(value=self.config.auto_stop_enabled)
        self.schedule_delay_var = tk.BooleanVar(value=self.config.schedule_delay_enabled)
        self.cooldown_enabled_var = tk.BooleanVar(value=self.config.cooldown_enabled)
        self.jitter_var = tk.BooleanVar(value=self.config.anti_detection_jitter)
        self.session_alerts_var = tk.BooleanVar(value=self.config.session_alerts)

        self.loop_delay_var = tk.DoubleVar(value=self.config.loop_delay)
        self.click_delay_var = tk.DoubleVar(value=self.config.click_delay)
        self.random_min_var = tk.DoubleVar(value=self.config.random_delay_min)
        self.random_max_var = tk.DoubleVar(value=self.config.random_delay_max)
        self.auto_stop_after_var = tk.IntVar(value=self.config.auto_stop_after)
        self.schedule_delay_seconds_var = tk.IntVar(value=self.config.schedule_delay_seconds)
        self.pre_snap_delay_var = tk.DoubleVar(value=self.config.pre_snap_delay)
        self.cooldown_after_var = tk.IntVar(value=self.config.cooldown_after)
        self.cooldown_duration_var = tk.IntVar(value=self.config.cooldown_duration)
        self.jitter_range_var = tk.IntVar(value=self.config.anti_detection_range)

        self.bot = AdvancedSnapBot(
            self.config,
            self.stats,
            log_callback=self.log_message,
            status_callback=self.set_status,
            session_callback=self.refresh_statistics
        )

        self.create_styles()
        self.create_layout()
        self.refresh_statistics()
        self.root.after(1000, self.tick)

    # -------------------- UI BUILDERS --------------------
    def create_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('LeftNav.TButton',
                        background=self.BG_NAV,
                        foreground=self.TEXT_SECONDARY,
                        padding=12,
                        anchor='w',
                        font=('Segoe UI', 11))
        style.map('LeftNav.TButton',
                  background=[('active', '#1f1f1f'), ('selected', '#1f1f1f')],
                  foreground=[('selected', self.ACCENT), ('active', self.TEXT_PRIMARY)])

        style.configure('Accent.TButton',
                        background=self.ACCENT,
                        foreground='#111111',
                        padding=10,
                        font=('Segoe UI Semibold', 11))
        style.map('Accent.TButton', background=[('active', '#ffe600')])

        style.configure('Danger.TButton',
                        background='#ff5252',
                        foreground='#ffffff',
                        padding=10,
                        font=('Segoe UI Semibold', 11))
        style.map('Danger.TButton', background=[('active', '#ff6b6b')])

        style.configure('Toggle.TCheckbutton',
                        background=self.BG_PANEL,
                        foreground=self.TEXT_PRIMARY,
                        font=('Segoe UI', 10))
        style.map('Toggle.TCheckbutton',
                  background=[('selected', self.BG_PANEL)],
                  foreground=[('active', self.TEXT_PRIMARY)])

        style.configure('Card.TFrame', background=self.BG_PANEL, relief='flat')
        style.configure('CardHeader.TLabel',
                        background=self.BG_PANEL,
                        foreground=self.TEXT_SECONDARY,
                        font=('Segoe UI', 10))
        style.configure('CardValue.TLabel',
                        background=self.BG_PANEL,
                        foreground=self.TEXT_PRIMARY,
                        font=('Segoe UI Semibold', 20))

    def create_layout(self):
        self.nav_frame = tk.Frame(self.root, bg=self.BG_NAV, width=230)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.nav_frame.pack_propagate(False)

        brand = tk.Label(self.nav_frame,
                         text="SnapScoreBot",
                         font=('Segoe UI Black', 18),
                         bg=self.BG_NAV,
                         fg=self.ACCENT)
        brand.pack(pady=(24, 4), padx=24, anchor='w')

        subtitle = tk.Label(self.nav_frame,
                            text="Automation Hub",
                            font=('Segoe UI', 11),
                            bg=self.BG_NAV,
                            fg=self.TEXT_SECONDARY)
        subtitle.pack(pady=(0, 30), padx=24, anchor='w')

        self.nav_buttons = {}
        nav_items = [
            ("Dashboard", self.show_dashboard),
            ("Automation", self.show_automation),
            ("Statistics", self.show_statistics),
            ("Positions", self.show_positions),
            ("Help & Safety", self.show_help)
        ]

        for name, command in nav_items:
            btn = ttk.Button(self.nav_frame,
                             text=name,
                             style='LeftNav.TButton',
                             command=lambda n=name: self.show_page(n))
            btn.pack(fill='x', padx=18, pady=6)
            self.nav_buttons[name] = btn

        version_text = f"v{VERSION}"
        if self.version_info and self.version_info != VERSION:
            version_text += f"  •  Update {self.version_info} available"

        version_label = tk.Label(self.nav_frame,
                                 text=version_text,
                                 font=('Segoe UI', 9),
                                 bg=self.BG_NAV,
                                 fg=self.TEXT_SECONDARY,
                                 wraplength=160,
                                 justify='left')
        version_label.pack(side='bottom', padx=18, pady=18, anchor='w')

        self.content_frame = tk.Frame(self.root, bg=self.BG_BASE)
        self.content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.pages = {}
        self.create_dashboard_page()
        self.create_automation_page()
        self.create_statistics_page()
        self.create_positions_page()
        self.create_help_page()

        self.show_page("Dashboard")

    # -------------------- PAGE CREATION --------------------
    def create_page_container(self, name):
        frame = tk.Frame(self.content_frame, bg=self.BG_BASE)
        self.pages[name] = frame
        return frame

    def create_dashboard_page(self):
        frame = self.create_page_container("Dashboard")

        header = tk.Label(frame,
                          text="Automation Control Center",
                          font=('Segoe UI Semibold', 20),
                          bg=self.BG_BASE,
                          fg=self.TEXT_PRIMARY)
        header.pack(anchor='w', padx=28, pady=(28, 6))

        sub = tk.Label(frame,
                       text="Monitor your snap sessions and manage live automations.",
                       font=('Segoe UI', 11),
                       bg=self.BG_BASE,
                       fg=self.TEXT_SECONDARY)
        sub.pack(anchor='w', padx=28, pady=(0, 20))

        cards_frame = tk.Frame(frame, bg=self.BG_BASE)
        cards_frame.pack(fill='x', padx=24)

        for idx, (title, var) in enumerate([
            ("Total snaps dispatched", self.total_sent_var),
            ("Session snaps", self.session_sent_var),
            ("Active streak", self.streak_var),
            ("Session errors", self.error_var)
        ]):
            card = ttk.Frame(cards_frame, style='Card.TFrame')
            card.grid(row=0, column=idx, padx=10, pady=4, sticky='nsew')
            cards_frame.grid_columnconfigure(idx, weight=1)

            ttk.Label(card, text=title, style='CardHeader.TLabel').pack(anchor='w', padx=18, pady=(16, 4))
            ttk.Label(card, textvariable=var, style='CardValue.TLabel').pack(anchor='w', padx=18, pady=(0, 16))

        status_panel = tk.Frame(frame, bg=self.BG_PANEL)
        status_panel.pack(fill='x', padx=24, pady=(20, 12))

        tk.Label(status_panel,
                 text="Session status",
                 font=('Segoe UI', 11),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).grid(row=0, column=0, sticky='w', padx=20, pady=(18, 0))

        tk.Label(status_panel,
                 textvariable=self.status_var,
                 font=('Segoe UI Semibold', 18),
                 bg=self.BG_PANEL,
                 fg=self.ACCENT).grid(row=1, column=0, sticky='w', padx=20, pady=(0, 18))

        tk.Label(status_panel,
                 text="Elapsed time",
                 font=('Segoe UI', 11),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).grid(row=0, column=1, sticky='w', padx=20, pady=(18, 0))

        tk.Label(status_panel,
                 textvariable=self.elapsed_var,
                 font=('Segoe UI Semibold', 18),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_PRIMARY).grid(row=1, column=1, sticky='w', padx=20, pady=(0, 18))

        controls = tk.Frame(frame, bg=self.BG_BASE)
        controls.pack(fill='x', padx=24, pady=(10, 24))

        shortcut_box = tk.Frame(controls, bg=self.BG_PANEL)
        shortcut_box.pack(side='left', padx=(0, 20))
        tk.Label(shortcut_box,
                 text="Shortcut recipients",
                 font=('Segoe UI', 10),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).pack(anchor='w', padx=18, pady=(16, 4))
        spin = ttk.Spinbox(shortcut_box,
                           from_=1,
                           to=500,
                           width=8,
                           textvariable=self.shortcut_count_var,
                           font=('Segoe UI', 12))
        spin.pack(padx=18, pady=(0, 16))

        button_box = tk.Frame(controls, bg=self.BG_BASE)
        button_box.pack(side='left', padx=8)

        self.start_button = ttk.Button(button_box,
                                       text="Start automation",
                                       style='Accent.TButton',
                                       command=self.handle_start)
        self.start_button.grid(row=0, column=0, padx=8, pady=6)

        self.pause_button = ttk.Button(button_box,
                                       text="Pause",
                                       style='LeftNav.TButton',
                                       command=self.handle_pause,
                                       state='disabled')
        self.pause_button.grid(row=0, column=1, padx=8, pady=6)

        self.stop_button = ttk.Button(button_box,
                                      text="Stop",
                                      style='Danger.TButton',
                                      command=self.handle_stop,
                                      state='disabled')
        self.stop_button.grid(row=0, column=2, padx=8, pady=6)

        session_details = tk.Frame(frame, bg=self.BG_PANEL)
        session_details.pack(fill='x', padx=24)

        detail_text = (
            "Snapchat automation uses your recorded mouse positions to send snaps to a shortcut. "
            "Ensure Snapchat Web is in focus when you start the bot."
        )
        tk.Label(session_details,
                 text=detail_text,
                 wraplength=760,
                 justify='left',
                 font=('Segoe UI', 10),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).pack(anchor='w', padx=20, pady=18)

    def create_automation_page(self):
        frame = self.create_page_container("Automation")

        header = tk.Label(frame,
                          text="Automation Settings",
                          font=('Segoe UI Semibold', 20),
                          bg=self.BG_BASE,
                          fg=self.TEXT_PRIMARY)
        header.pack(anchor='w', padx=28, pady=(28, 6))

        sub = tk.Label(frame,
                       text="Fine-tune delays, safety pauses, and detection countermeasures.",
                       font=('Segoe UI', 11),
                       bg=self.BG_BASE,
                       fg=self.TEXT_SECONDARY)
        sub.pack(anchor='w', padx=28, pady=(0, 20))

        grid = tk.Frame(frame, bg=self.BG_BASE)
        grid.pack(fill='both', expand=True, padx=24, pady=(0, 24))
        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        primary_card = ttk.Frame(grid, style='Card.TFrame')
        primary_card.grid(row=0, column=0, padx=12, pady=12, sticky='nsew')

        self.create_spin_setting(primary_card, "Loop delay (s)", self.loop_delay_var, 0.5, 120, 0.5)
        self.create_spin_setting(primary_card, "Click delay (s)", self.click_delay_var, 0.1, 10, 0.1)
        self.create_spin_setting(primary_card, "Pre-snap delay (s)", self.pre_snap_delay_var, 0.0, 5.0, 0.1)

        ttk.Separator(primary_card, orient='horizontal').pack(fill='x', padx=18, pady=12)

        random_toggle = ttk.Checkbutton(primary_card,
                                        text="Enable dynamic delays",
                                        variable=self.random_delay_var,
                                        style='Toggle.TCheckbutton',
                                        command=self.toggle_random_delay)
        random_toggle.pack(anchor='w', padx=18, pady=(6, 0))

        self.random_frame = tk.Frame(primary_card, bg=self.BG_PANEL)
        self.random_frame.pack(fill='x', padx=18, pady=(6, 12))
        self.create_spin_setting(self.random_frame, "Minimum delay (s)", self.random_min_var, 0.1, 30, 0.1)
        self.create_spin_setting(self.random_frame, "Maximum delay (s)", self.random_max_var, 0.2, 60, 0.1)

        ttk.Separator(primary_card, orient='horizontal').pack(fill='x', padx=18, pady=12)

        auto_stop_toggle = ttk.Checkbutton(primary_card,
                                           text="Auto-stop after X snaps",
                                           variable=self.auto_stop_var,
                                           style='Toggle.TCheckbutton',
                                           command=self.toggle_auto_stop)
        auto_stop_toggle.pack(anchor='w', padx=18, pady=(6, 0))

        self.auto_stop_frame = tk.Frame(primary_card, bg=self.BG_PANEL)
        self.auto_stop_frame.pack(fill='x', padx=18, pady=(6, 12))
        self.create_spin_setting(self.auto_stop_frame, "Snaps limit", self.auto_stop_after_var, 5, 2000, 5)

        safety_card = ttk.Frame(grid, style='Card.TFrame')
        safety_card.grid(row=0, column=1, padx=12, pady=12, sticky='nsew')

        schedule_toggle = ttk.Checkbutton(safety_card,
                                          text="Schedule start after delay",
                                          variable=self.schedule_delay_var,
                                          style='Toggle.TCheckbutton',
                                          command=self.toggle_schedule)
        schedule_toggle.pack(anchor='w', padx=18, pady=(18, 0))

        self.schedule_frame = tk.Frame(safety_card, bg=self.BG_PANEL)
        self.schedule_frame.pack(fill='x', padx=18, pady=(6, 12))
        self.create_spin_setting(self.schedule_frame, "Delay (seconds)", self.schedule_delay_seconds_var, 5, 900, 5)

        cooldown_toggle = ttk.Checkbutton(safety_card,
                                          text="Enable cooldown pauses",
                                          variable=self.cooldown_enabled_var,
                                          style='Toggle.TCheckbutton',
                                          command=self.toggle_cooldown)
        cooldown_toggle.pack(anchor='w', padx=18, pady=(6, 0))

        self.cooldown_frame = tk.Frame(safety_card, bg=self.BG_PANEL)
        self.cooldown_frame.pack(fill='x', padx=18, pady=(6, 12))
        self.create_spin_setting(self.cooldown_frame, "Snaps before cooldown", self.cooldown_after_var, 5, 500, 1)
        self.create_spin_setting(self.cooldown_frame, "Cooldown duration (s)", self.cooldown_duration_var, 5, 600, 5)

        jitter_toggle = ttk.Checkbutton(safety_card,
                                        text="Anti-detection mouse jitter",
                                        variable=self.jitter_var,
                                        style='Toggle.TCheckbutton',
                                        command=self.toggle_jitter)
        jitter_toggle.pack(anchor='w', padx=18, pady=(6, 0))

        self.jitter_frame = tk.Frame(safety_card, bg=self.BG_PANEL)
        self.jitter_frame.pack(fill='x', padx=18, pady=(6, 12))
        self.create_spin_setting(self.jitter_frame, "Jitter range (px)", self.jitter_range_var, 2, 60, 1)

        ttk.Separator(safety_card, orient='horizontal').pack(fill='x', padx=18, pady=12)

        alerts_toggle = ttk.Checkbutton(safety_card,
                                        text="Desktop alerts while running",
                                        variable=self.session_alerts_var,
                                        style='Toggle.TCheckbutton')
        alerts_toggle.pack(anchor='w', padx=18, pady=(0, 12))

        save_button = ttk.Button(frame,
                                 text="Save configuration",
                                 style='Accent.TButton',
                                 command=self.handle_save_config)
        save_button.pack(anchor='e', padx=36, pady=(0, 20))

        self.toggle_random_delay()
        self.toggle_auto_stop()
        self.toggle_schedule()
        self.toggle_cooldown()
        self.toggle_jitter()

    def create_statistics_page(self):
        frame = self.create_page_container("Statistics")

        header = tk.Label(frame,
                          text="Session Insights",
                          font=('Segoe UI Semibold', 20),
                          bg=self.BG_BASE,
                          fg=self.TEXT_PRIMARY)
        header.pack(anchor='w', padx=28, pady=(28, 6))

        sub = tk.Label(frame,
                       text="Track global totals, streaks, and review live logs.",
                       font=('Segoe UI', 11),
                       bg=self.BG_BASE,
                       fg=self.TEXT_SECONDARY)
        sub.pack(anchor='w', padx=28, pady=(0, 20))

        top = tk.Frame(frame, bg=self.BG_BASE)
        top.pack(fill='x', padx=24)

        info_card = ttk.Frame(top, style='Card.TFrame')
        info_card.pack(side='left', padx=12, pady=12, fill='both', expand=True)

        tk.Label(info_card,
                 text="Lifetime totals",
                 font=('Segoe UI Semibold', 13),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_PRIMARY).pack(anchor='w', padx=18, pady=(18, 6))

        self.lifetime_label = tk.Label(info_card,
                                       text="",
                                       justify='left',
                                       font=('Segoe UI', 11),
                                       bg=self.BG_PANEL,
                                       fg=self.TEXT_SECONDARY)
        self.lifetime_label.pack(anchor='w', padx=18, pady=(0, 16))

        reset_btn = ttk.Button(info_card,
                               text="Reset statistics",
                               style='Danger.TButton',
                               command=self.handle_reset_stats)
        reset_btn.pack(anchor='w', padx=18, pady=(0, 18))

        log_card = ttk.Frame(top, style='Card.TFrame')
        log_card.pack(side='left', padx=12, pady=12, fill='both', expand=True)

        tk.Label(log_card,
                 text="Live activity log",
                 font=('Segoe UI Semibold', 13),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_PRIMARY).pack(anchor='w', padx=18, pady=(18, 6))

        self.log_list = tk.Listbox(log_card,
                                   bg='#1f1f1f',
                                   fg=self.TEXT_PRIMARY,
                                   activestyle='none',
                                   highlightthickness=0,
                                   bd=0,
                                   font=('Consolas', 10))
        self.log_list.pack(fill='both', expand=True, padx=18, pady=(0, 18))

    def create_positions_page(self):
        frame = self.create_page_container("Positions")

        header = tk.Label(frame,
                          text="Button Mapping",
                          font=('Segoe UI Semibold', 20),
                          bg=self.BG_BASE,
                          fg=self.TEXT_PRIMARY)
        header.pack(anchor='w', padx=28, pady=(28, 6))

        sub = tk.Label(frame,
                       text="Capture or adjust the coordinates SnapScoreBot will click during automation.",
                       font=('Segoe UI', 11),
                       bg=self.BG_BASE,
                       fg=self.TEXT_SECONDARY)
        sub.pack(anchor='w', padx=28, pady=(0, 20))

        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='x', padx=24, pady=12)

        instructions = (
            "1. Open Snapchat Web and make sure the browser window is visible.\n"
            "2. Click \"Capture buttons\" and follow the prompts. Press F to record and Esc to cancel.\n"
            "3. Keep the pointer steady when pressing F to avoid inaccurate clicks."
        )

        tk.Label(card,
                 text=instructions,
                 justify='left',
                 font=('Segoe UI', 11),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).pack(anchor='w', padx=20, pady=(18, 12))

        btn_frame = tk.Frame(card, bg=self.BG_PANEL)
        btn_frame.pack(anchor='w', padx=20, pady=(0, 18))

        ttk.Button(btn_frame,
                   text="Capture buttons",
                   style='Accent.TButton',
                   command=self.handle_capture_positions).grid(row=0, column=0, padx=6, pady=6)

        ttk.Button(btn_frame,
                   text="Load saved",
                   style='LeftNav.TButton',
                   command=self.handle_load_positions).grid(row=0, column=1, padx=6, pady=6)

        ttk.Button(btn_frame,
                   text="Clear saved",
                   style='Danger.TButton',
                   command=self.handle_clear_positions).grid(row=0, column=2, padx=6, pady=6)

    def create_help_page(self):
        frame = self.create_page_container("Help & Safety")

        header = tk.Label(frame,
                          text="Safety & Best Practices",
                          font=('Segoe UI Semibold', 20),
                          bg=self.BG_BASE,
                          fg=self.TEXT_PRIMARY)
        header.pack(anchor='w', padx=28, pady=(28, 6))

        sub = tk.Label(frame,
                       text="Review important information before running automations.",
                       font=('Segoe UI', 11),
                       bg=self.BG_BASE,
                       fg=self.TEXT_SECONDARY)
        sub.pack(anchor='w', padx=28, pady=(0, 20))

        card = ttk.Frame(frame, style='Card.TFrame')
        card.pack(fill='x', padx=24, pady=12)

        disclaimer = (
            "• This toolkit is for educational use only.\n"
            "• Automating Snapchat violates their Terms of Service and can result in permanent account bans.\n"
            "• Run the bot on disposable accounts and avoid excessive send rates.\n"
            "• Keep automation windows in focus to prevent misclicks."
        )

        tk.Label(card,
                 text=disclaimer,
                 justify='left',
                 font=('Segoe UI', 11),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).pack(anchor='w', padx=20, pady=(18, 18))

        tutorial_card = ttk.Frame(frame, style='Card.TFrame')
        tutorial_card.pack(fill='x', padx=24, pady=12)

        tk.Label(tutorial_card,
                 text="Video tutorial",
                 font=('Segoe UI Semibold', 13),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_PRIMARY).pack(anchor='w', padx=20, pady=(18, 6))

        tk.Label(tutorial_card,
                 text=TUTORIAL_VIDEO,
                 font=('Segoe UI', 11),
                 bg=self.BG_PANEL,
                 fg=self.ACCENT).pack(anchor='w', padx=20, pady=(0, 18))

    # -------------------- UI HELPERS --------------------
    def create_spin_setting(self, parent, label, variable, minimum, maximum, increment):
        wrapper = tk.Frame(parent, bg=self.BG_PANEL)
        wrapper.pack(fill='x', padx=18, pady=4)
        tk.Label(wrapper,
                 text=label,
                 font=('Segoe UI', 10),
                 bg=self.BG_PANEL,
                 fg=self.TEXT_SECONDARY).pack(anchor='w')
        spin = ttk.Spinbox(wrapper,
                           from_=minimum,
                           to=maximum,
                           increment=increment,
                           textvariable=variable,
                           width=8,
                           font=('Segoe UI', 11),
                           command=self.apply_config_changes)
        spin.pack(anchor='w', pady=(2, 6))
        spin.bind('<FocusOut>', lambda _e: self.apply_config_changes())

    def show_page(self, name):
        for frame in self.pages.values():
            frame.pack_forget()
        frame = self.pages.get(name)
        if frame:
            frame.pack(fill='both', expand=True)

        for btn_name, button in self.nav_buttons.items():
            if btn_name == name:
                button.state(['selected'])
            else:
                button.state(['!selected'])

    def show_dashboard(self):
        self.show_page("Dashboard")

    def show_automation(self):
        self.show_page("Automation")

    def show_statistics(self):
        self.show_page("Statistics")

    def show_positions(self):
        self.show_page("Positions")

    def show_help(self):
        self.show_page("Help & Safety")

    # -------------------- EVENT HANDLERS --------------------
    def handle_start(self):
        if self.bot.is_running():
            messagebox.showinfo("Automation active", "SnapScoreBot is already running.")
            return

        try:
            count = int(self.shortcut_count_var.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid value", "Enter how many friends are inside your Snapchat shortcut.")
            return

        if self.bot.start(count):
            self.set_status("Running automation")
            self.start_button.state(['disabled'])
            self.pause_button.state(['!disabled'])
            self.stop_button.state(['!disabled'])
            self.pause_button.config(text="Pause")
            self.log_message("Automation started", "info")
        else:
            messagebox.showwarning(
                "Positions required",
                "Capture the Snapchat buttons (Camera, Send To, Shortcut, Select All) before starting."
            )

    def handle_stop(self):
        self.bot.stop()
        self.start_button.state(['!disabled'])
        self.pause_button.state(['disabled'])
        self.stop_button.state(['disabled'])
        self.pause_button.config(text="Pause")
        self.log_message("Automation stopped", "warning")

    def handle_pause(self):
        if self.bot.toggle_pause():
            if self.pause_button.cget('text') == "Pause":
                self.pause_button.config(text="Resume")
            else:
                self.pause_button.config(text="Pause")

    def handle_save_config(self):
        self.apply_config_changes()
        self.config.save_config()
        messagebox.showinfo("Configuration saved", "Settings persisted to config.json")

    def handle_reset_stats(self):
        if messagebox.askyesno("Reset statistics", "This will clear your lifetime totals. Continue?"):
            self.stats.total_snaps_sent = 0
            self.stats.longest_streak = 0
            self.stats.save_stats()
            self.refresh_statistics()
            self.log_message("Statistics reset", "warning")

    def handle_capture_positions(self):
        if self.bot.is_running():
            messagebox.showwarning("Automation running", "Stop the automation before capturing positions.")
            return

        threading.Thread(target=self._capture_positions_async, daemon=True).start()

    def _capture_positions_async(self):
        if self.bot.get_positions():
            self.log_message("New positions recorded", "success")
        else:
            self.log_message("Position capture canceled", "warning")

    def handle_load_positions(self):
        if self.bot.load_positions():
            messagebox.showinfo("Positions loaded", "Saved coordinates applied successfully.")
        else:
            messagebox.showerror("No saved positions", "positions.json was not found or is invalid.")

    def handle_clear_positions(self):
        path = Path('positions.json')
        if path.exists():
            path.unlink()
            self.bot.positions.clear()
            messagebox.showinfo("Positions cleared", "Saved coordinates removed.")
        else:
            messagebox.showwarning("No saved file", "There are no saved positions to delete.")

    # -------------------- STATE MANAGEMENT --------------------
    def apply_config_changes(self):
        try:
            self.config.loop_delay = float(self.loop_delay_var.get())
            self.config.click_delay = float(self.click_delay_var.get())
            self.config.pre_snap_delay = float(self.pre_snap_delay_var.get())
            self.config.random_delay = bool(self.random_delay_var.get())
            self.config.random_delay_min = float(self.random_min_var.get())
            self.config.random_delay_max = float(self.random_max_var.get())
            self.config.auto_stop_enabled = bool(self.auto_stop_var.get())
            self.config.auto_stop_after = int(self.auto_stop_after_var.get())
            self.config.schedule_delay_enabled = bool(self.schedule_delay_var.get())
            self.config.schedule_delay_seconds = int(self.schedule_delay_seconds_var.get())
            self.config.cooldown_enabled = bool(self.cooldown_enabled_var.get())
            self.config.cooldown_after = int(self.cooldown_after_var.get())
            self.config.cooldown_duration = int(self.cooldown_duration_var.get())
            self.config.anti_detection_jitter = bool(self.jitter_var.get())
            self.config.anti_detection_range = int(self.jitter_range_var.get())
            self.config.session_alerts = bool(self.session_alerts_var.get())
            if self.config.random_delay_min > self.config.random_delay_max:
                self.config.random_delay_max = self.config.random_delay_min
                self.random_max_var.set(self.config.random_delay_max)
        except ValueError:
            messagebox.showerror("Invalid value", "Please verify that all numeric fields contain valid numbers.")

    def toggle_random_delay(self):
        state = 'normal' if self.random_delay_var.get() else 'disabled'
        self.set_children_state(self.random_frame, state)
        self.apply_config_changes()

    def toggle_auto_stop(self):
        state = 'normal' if self.auto_stop_var.get() else 'disabled'
        self.set_children_state(self.auto_stop_frame, state)
        self.apply_config_changes()

    def toggle_schedule(self):
        state = 'normal' if self.schedule_delay_var.get() else 'disabled'
        self.set_children_state(self.schedule_frame, state)
        self.apply_config_changes()

    def toggle_cooldown(self):
        state = 'normal' if self.cooldown_enabled_var.get() else 'disabled'
        self.set_children_state(self.cooldown_frame, state)
        self.apply_config_changes()

    def toggle_jitter(self):
        state = 'normal' if self.jitter_var.get() else 'disabled'
        self.set_children_state(self.jitter_frame, state)
        self.apply_config_changes()

    def set_children_state(self, widget, state):
        for child in widget.winfo_children():
            try:
                child.configure(state=state)
            except tk.TclError:
                pass
            self.set_children_state(child, state)

    # -------------------- CALLBACKS --------------------
    def log_message(self, message, level="info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {
            'info': 'ℹ️',
            'success': '✅',
            'warning': '⚠️',
            'error': '❌'
        }.get(level, '•')
        text = f"[{timestamp}] {icon} {message}"

        def append():
            if hasattr(self, 'log_list'):
                self.log_list.insert('end', text)
                self.log_list.yview_moveto(1)

        self.root.after(0, append)

    def set_status(self, status):
        self.root.after(0, lambda: self.status_var.set(status))

    def refresh_statistics(self):
        self.total_sent_var.set(f"{self.stats.total_snaps_sent:,}")
        self.session_sent_var.set(str(self.stats.session_snaps))
        self.error_var.set(str(self.stats.errors_count))
        self.streak_var.set(str(self.stats.current_streak))
        self.elapsed_var.set(self.stats.get_elapsed_time())

        lifetime = [
            f"Total snaps: {self.stats.total_snaps_sent:,}",
            f"Longest streak: {self.stats.longest_streak}",
        ]
        if self.stats.last_session:
            lifetime.append(f"Last session: {self.stats.last_session}")
        self.lifetime_label.config(text="\n".join(lifetime))

    def tick(self):
        if self.bot.is_running():
            self.refresh_statistics()
        self.root.after(1000, self.tick)

    def run(self):
        self.root.mainloop()


# ==================== PROGRAM ENTRY ====================
if __name__ == "__main__":
    app = SnapScoreBotApp()
    app.run()
