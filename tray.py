from pystray import Icon, Menu, MenuItem
from PIL import Image
import os
import subprocess

# Function to start logger service
def start_service(icon, item):
    subprocess.Popen(['python', 'onloq_service.py', 'start'])

# Function to stop logger service
def stop_service(icon, item):
    subprocess.Popen(['python', 'onloq_service.py', 'stop'])

# Function to exit
def exit_action(icon, item):
    icon.stop()

# Create menu
menu = Menu(
    MenuItem('Start Service', start_service),
    MenuItem('Stop Service', stop_service),
    MenuItem('Exit', exit_action)
)

# Load an icon image
icon_image = Image.open("icon.png")

# Create system tray icon
icon = Icon("Onloq Logger", icon_image, "Onloq Logger", menu)

icon.run()
