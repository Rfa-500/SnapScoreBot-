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

# Initialize colorama
init(autoreset=True, convert=True)

# ==================== SETTINGS ====================
TUTORIAL_VIDEO = "Soon"
VERSION = "2.0.0"
CREDITS = "Eddie-500 - Educational Purpose Only"
CONFIG_FILE = "config.json"

# ==================== HELPER FUNCTIONS ====================
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
        except:
            pass

def nice_print(text, status="-", color=Fore.WHITE):
    """Formatted print with status icon"""
    print(f"{Fore.WHITE}[{Fore.RED}{status}{Fore.WHITE}] {color}{text}")

def print_banner():
    """Prints the program banner"""
    banner = rf"""
{Fore.RED}
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
    def __init__(self):
        self.loop_delay = 5
        self.click_delay = 1.2
        self.position_delay = 0.5
        self.random_delay = False
        self.random_delay_min = 3
        self.random_delay_max = 8
        self.auto_stop_enabled = False
        self.auto_stop_after = 100
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
            'auto_stop_after': self.auto_stop_after
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
        self.load_stats()
    
    def load_stats(self):
        """Loads previous statistics"""
        if Path(self.stats_file).exists():
            try:
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                    self.total_snaps_sent = data.get('total_snaps_sent', 0)
            except:
                pass
    
    def save_stats(self):
        """Saves statistics"""
        data = {
            'total_snaps_sent': self.total_snaps_sent,
            'last_session': datetime.now().isoformat(),
            'last_session_snaps': self.session_snaps
        }
        with open(self.stats_file, 'w') as f:
            json.dump(data, f, indent=4)
    
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
                    nice_print(f"Position saved: {self.positions[key]}", "✓", Fore.GREEN)
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
        nice_print("Positions saved to file", "✓", Fore.GREEN)
    
    def load_positions(self):
        """Loads previously saved positions"""
        if Path('positions.json').exists():
            try:
                with open('positions.json', 'r') as f:
                    data = json.load(f)
                    for key, coords in data.items():
                        self.positions[key] = pyautogui.Point(coords['x'], coords['y'])
                nice_print("Positions loaded from file", "✓", Fore.GREEN)
                return True
            except:
                pass
        return False
    
    def send_snap(self, shortcut_user_count):
        """Sends a snap sequence"""
        try:
            pyautogui.moveTo(self.positions['camera'])
            if self.first_try:
                pyautogui.click()
                self.first_try = False
            time.sleep(self.get_delay())

            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.positions['send_to'])
            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.positions['shortcut'])
            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.positions['select_all'])
            pyautogui.click()
            time.sleep(self.get_delay())

            pyautogui.moveTo(self.positions['send_to'])
            pyautogui.click()

            self.stats.session_snaps += 1
            self.stats.total_snaps_sent += shortcut_user_count
            return True
            
        except Exception as e:
            self.stats.errors_count += 1
            nice_print(f"Error sending snap: {e}", "✗", Fore.RED)
            return False
    
    def get_delay(self):
        """Returns a random or fixed delay"""
        if self.config.random_delay:
            return random.uniform(self.config.random_delay_min, self.config.random_delay_max)
        return self.config.click_delay
    
    def run_bot(self, shortcut_user_count):
        """Runs the main bot loop"""
        self.is_running = True
        self.stats.start_time = time.time()
        sent_count = 0
        
        nice_print("Bot started. Press 'Q' to stop, 'P' to pause", "!", Fore.CYAN)
        
        while self.is_running:
            if keyboard.is_pressed('q'):
                nice_print("Stopping bot...", "!", Fore.YELLOW)
                break
            
            if keyboard.is_pressed('p'):
                self.pause_bot = not self.pause_bot
                if self.pause_bot:
                    nice_print("Bot paused. Press 'P' to resume", "||", Fore.YELLOW)
                else:
                    nice_print("Bot resumed", "▶", Fore.GREEN)
                time.sleep(0.5)
            
            if self.pause_bot:
                time.sleep(0.1)
                continue
            
            title(f"SnapScoreBot v{VERSION} | Sent: {self.stats.total_snaps_sent} | Time: {self.stats.get_elapsed_time()}")
            
            success = self.send_snap(shortcut_user_count)
            
            if success:
                sent_count += 1
                clear()
                print_banner()
                nice_print(f"Snaps sent this session: {self.stats.session_snaps}", "📊", Fore.CYAN)
                nice_print(f"Total historical: {self.stats.total_snaps_sent}", "📈", Fore.CYAN)
                nice_print(f"Elapsed time: {self.stats.get_elapsed_time()}", "⏱", Fore.CYAN)
                
                if self.config.auto_stop_enabled and sent_count >= self.config.auto_stop_after:
                    nice_print(f"Auto-stop reached ({self.config.auto_stop_after} snaps)", "!", Fore.YELLOW)
                    break
            
            loop_delay = random.uniform(self.config.random_delay_min, self.config.random_delay_max) if self.config.random_delay else self.config.loop_delay
            time.sleep(loop_delay)
        
        self.is_running = False
        self.stats.save_stats()
        nice_print("Bot stopped", "✓", Fore.GREEN)
# ==================== CONFIGURATION MENU ====================
def configuration_menu(config):
    """Interactive configuration menu"""
    while True:
        clear()
        print_banner()
        print(f"{Fore.CYAN}═══ CONFIGURATION ═══{Fore.WHITE}\n")
        
        print(f"[1] Loop delay: {Fore.YELLOW}{config.loop_delay}s{Fore.WHITE}")
        print(f"[2] Click delay: {Fore.YELLOW}{config.click_delay}s{Fore.WHITE}")
        print(f"[3] Random delay: {Fore.YELLOW}{'Enabled' if config.random_delay else 'Disabled'}{Fore.WHITE}")
        if config.random_delay:
            print(f"    └─ Range: {Fore.YELLOW}{config.random_delay_min}s - {config.random_delay_max}s{Fore.WHITE}")
        print(f"[4] Auto-stop: {Fore.YELLOW}{'Enabled' if config.auto_stop_enabled else 'Disabled'}{Fore.WHITE}")
        if config.auto_stop_enabled:
            print(f"    └─ After: {Fore.YELLOW}{config.auto_stop_after} snaps{Fore.WHITE}")
        print(f"[5] Save configuration")
        print(f"[0] Return to main menu")
        
        try:
            option = input(f"\n{Fore.RED}> {Fore.WHITE}")
            
            if option == "1":
                config.loop_delay = float(input("New loop delay (seconds): "))
            elif option == "2":
                config.click_delay = float(input("New click delay (seconds): "))
            elif option == "3":
                config.random_delay = not config.random_delay
                if config.random_delay:
                    config.random_delay_min = float(input("Minimum delay (seconds): "))
                    config.random_delay_max = float(input("Maximum delay (seconds): "))
            elif option == "4":
                config.auto_stop_enabled = not config.auto_stop_enabled
                if config.auto_stop_enabled:
                    config.auto_stop_after = int(input("Stop after how many snaps: "))
            elif option == "5":
                config.save_config()
                input("Press ENTER to continue...")
            elif option == "0":
                break
        except ValueError:
            nice_print("Invalid value", "✗", Fore.RED)
            input("Press ENTER to continue...")

# ==================== STATISTICS MENU ====================
def statistics_menu(stats):
    """Displays and manages statistics"""
    clear()
    print_banner()
    print(f"{Fore.CYAN}═══ STATISTICS ═══{Fore.WHITE}\n")
    
    print(f"{Fore.YELLOW}📊 Global Statistics:{Fore.WHITE}")
    print(f"   Total snaps sent: {Fore.GREEN}{stats.total_snaps_sent}{Fore.WHITE}")
    print(f"   Snaps this session: {Fore.GREEN}{stats.session_snaps}{Fore.WHITE}")
    print(f"   Errors this session: {Fore.RED}{stats.errors_count}{Fore.WHITE}")
    
    if stats.session_snaps > 0:
        success_rate = (stats.session_snaps / (stats.session_snaps + stats.errors_count)) * 100
        print(f"   Success rate: {Fore.GREEN}{success_rate:.1f}%{Fore.WHITE}")
    
    print(f"\n[1] Reset statistics")
    print(f"[0] Return to main menu")
    
    option = input(f"\n{Fore.RED}> {Fore.WHITE}")
    
    if option == "1":
        confirm = input("Are you sure? (y/n): ")
        if confirm.lower() == 'y':
            stats.total_snaps_sent = 0
            stats.session_snaps = 0
            stats.errors_count = 0
            stats.save_stats()
            nice_print("Statistics reset", "✓", Fore.GREEN)
            input("Press ENTER to continue...")

# ==================== VERSION CHECK ====================
def check_version():
    """Checks for new versions available"""
    try:
        r = requests.get("https://raw.githubusercontent.com/useragents/Snapchat-Snapscore-Botter/refs/heads/main/version.txt", timeout=3)
        latest_version = r.text.strip()
        if latest_version != VERSION:
            nice_print(f"New version available: {latest_version}", "!", Fore.YELLOW)
            nice_print(f"Your version: {VERSION}", "!", Fore.YELLOW)
            input("Press ENTER to continue...")
    except:
        pass

# ==================== MAIN FUNCTION ====================
def main():
    """Main program entry point"""
    check_version()
    
    config = Config()
    stats = Statistics()
    bot = AdvancedSnapBot(config, stats)
    
    while True:
        clear()
        print_banner()
        
        print(f"{Fore.CYAN}═══ SNAP SCORE BOT MAIN MENU ═══{Fore.WHITE}\n")
        print(f"[{Fore.RED}1{Fore.WHITE}] Start Bot")
        print(f"[{Fore.RED}2{Fore.WHITE}] Configuration")
        print(f"[{Fore.RED}3{Fore.WHITE}] Statistics")
        print(f"[{Fore.RED}4{Fore.WHITE}] Help & Instructions")
        print(f"[{Fore.RED}5{Fore.WHITE}] Disclaimer")
        print(f"[{Fore.RED}0{Fore.WHITE}] Exit")
        
        try:
            option = input(f"\n{Fore.RED}> {Fore.WHITE}")
            
            if option == "1":
                try:
                    shortcut_user_count = int(input(f"\nHow many people are in your shortcut? {Fore.RED}> {Fore.WHITE}"))
                    
                    if not bot.positions:
                        load_saved = input("\nLoad saved positions? (y/n): ")
                        if load_saved.lower() == 'y' and bot.load_positions():
                            nice_print("Positions loaded", "✓", Fore.GREEN)
                        else:
                            print("\n")
                            nice_print("Let's configure the positions", "!", Fore.CYAN)
                            if not bot.get_positions():
                                nice_print("Configuration canceled", "✗", Fore.RED)
                                input("Press ENTER to continue...")
                                continue
                    
                    print("\n")
                    nice_print("Positions ready. Press F when you're ready to start", "!", Fore.CYAN)
                    while not keyboard.is_pressed("f"):
                        time.sleep(0.1)
                    
                    clear()
                    print_banner()
                    bot.run_bot(shortcut_user_count)
                    
                    input("\nPress ENTER to return to the menu...")
                    
                except ValueError:
                    nice_print("Invalid number", "✗", Fore.RED)
                    input("Press ENTER to continue...")
                    
            elif option == "2":
                configuration_menu(config)
                
            elif option == "3":
                statistics_menu(stats)
                
            elif option == "4":
                clear()
                print_banner()
                print(f"{Fore.CYAN}═══ HELP & INSTRUCTIONS ═══{Fore.WHITE}\n")
                print(f"{Fore.YELLOW}Instructions:{Fore.WHITE}")
                print("1. On your phone, create a shortcut with people to send snaps to.")
                print("2. Open Snapchat Web on your computer.")
                print("3. Log in and allow camera/microphone permissions.")
                print("4. If you don't have a webcam, use OBS Studio with a virtual camera.")
                print("5. Run this program and select 'Start Bot'.")
                print("6. Configure mouse positions following the on-screen guide.")
                print("7. The bot will automatically start sending snaps.")
                print(f"\n{Fore.YELLOW}Bot Controls:{Fore.WHITE}")
                print("   Q - Stop the bot")
                print("   P - Pause/Resume")
                print(f"\n{Fore.YELLOW}Video Tutorial:{Fore.WHITE} {TUTORIAL_VIDEO}")
                input("\nPress ENTER to return to the menu...")
                
            elif option == "5":
                clear()
                print_banner()
                print(f"{Fore.RED}═══ DISCLAIMER ═══{Fore.WHITE}\n")
                print("⚠️  IMPORTANT WARNING ⚠️\n")
                print("• This script is for EDUCATIONAL PURPOSES ONLY")
                print("• It is NOT affiliated with Snapchat Inc.")
                print("• Using bots violates Snapchat’s Terms of Service")
                print("• Your account may be PERMANENTLY BANNED")
                print("• The developer is NOT responsible for any misuse")
                print("• Use it at your own risk")
                input("\nPress ENTER to return to the menu...")
                
            elif option == "0":
                nice_print("Exiting...", "!", Fore.YELLOW)
                stats.save_stats()
                sys.exit(0)
                
        except KeyboardInterrupt:
            nice_print("\nExiting...", "!", Fore.YELLOW)
            sys.exit(0)
        except Exception as e:
            nice_print(f"Unexpected error: {e}", "✗", Fore.RED)
            input("Press ENTER to continue...")

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
