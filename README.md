# 🟣 SnapBot CLI v2.0.0

**SnapBot CLI** is a fully interactive console-based automation tool built with **Python** that simulates Snapchat activity for **testing and educational purposes**.  
It automates Snap sending cycles through mouse control, configurable timing, and live session tracking — all from a lightweight, color-coded command-line interface.

---

## 🧰 Requirements

### 🖥️ System
- Windows, macOS, or Linux  
- Python **3.8+**

### 📦 Libraries
Install dependencies using:
```
pip install colorama pyautogui keyboard requests
Alternatively, on Windows, simply double-click:

Install_Requirements.bat
```
**📂 Project Structure**
SnapScoreBot.py          → Main application (CLI version)
config.json              → Auto-saved configuration file
positions.json           → Saved mouse coordinates for Snap buttons (You can choose if use saved coordinates or make new ones. To avoid mistakes make new ones)
Install_Requirements.bat → Batch installer for dependencies

**⚙️ Configuration**
All settings are managed inside the program and stored automatically in config.json.
You can also edit them manually if needed:

```
json
{
  "loop_delay": 5,
  "click_delay": 1.2,
  "position_delay": 0.5,
  "random_delay": false,
  "random_delay_min": 3,
  "random_delay_max": 8,
  "auto_stop_enabled": false,
  "auto_stop_after": 100
}
```

**🚀 How to Run**
Clone the repository:
```
git clone https://github.com/Eddie-500/SnapScoreBot
cd SnapScoreBot
Doble click Install_Requirements.bat
```

Run the bot:
The main menu will appear:
```
[1] Start Bot
[2] Configuration
[3] Statistics
[4] Help & Instructions
[5] Disclaimer
[0] Exit
```
🧭 Quick Start Instructions
On your Snapchat mobile app, create a Shortcut with the friends you want to send Snaps to.
(You can use bots or alternate accounts.)

On your computer, open Snapchat Web and log in.

Allow camera and microphone permissions.  
If you don’t have a webcam, use **OBS Studio** with a virtual camera.

Run the program and select option **[1] Start Bot**.

The bot will guide you through capturing your screen positions:

- Move your mouse over each button and press **F** to record its location.  
- Press **ESC** to cancel the setup.  
- Once all positions are set it will begin sending Snaps automatically.

You can control the bot anytime using your keyboard:

- **P** → Pause / Resume  
- **Q** → Stop the bot  
- **F** → Start from ready mode  

---

## 🧮 Stats & Logs

- **Total Snaps Sent:** Saved in `stats.json`  
- **Session Snaps:** Reset at each new run  
- **Errors:** Counted per session  
- **Auto-stop:** Optional — stops automatically after a chosen number of snaps  

You can view or reset all stats at any time from the **Statistics Menu**.

---

## ⚙️ Configuration Menu Options
```
[1] Loop delay (seconds)
[2] Click delay (seconds)
[3] Random delay (on/off + min/max)
[4] Auto-stop (on/off + snap count)
[5] Save configuration
[0] Return to main menu
```
All settings are automatically saved in `config.json`.
---

## 🎥 Video Tutorial

Video tutorial — *Coming soon!*  
📺 Stay tuned for updates

---

## 🧑‍💻 Development Notes

- Built with **Colorama** for colored console output  
- **PyAutoGUI** handles mouse automation  
- **Keyboard** module enables live hotkey control  
- Automatically checks for missing modules on startup  
- Auto-saves progress, statistics, and configuration files  
- Clean ASCII interface with real-time session feedback  

---

## ⚠️ Disclaimer

> This project is intended **for educational and research purposes only**.  
> It is **not affiliated with Snapchat Inc.**, and using automation on Snapchat may violate its **Terms of Service**.  
> The developer is **not responsible** for any misuse, account bans, or data loss.  
> Use at your own risk.

---

## 🪪 License

This project is released under the **MIT License**.  
© 2025 **SnapScoreBot CLI** — *Educational use only.*
