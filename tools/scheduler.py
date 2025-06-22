from pystray import Icon, Menu, MenuItem
from PIL import Image, ImageDraw
import threading
import time

running = False

def start_task():
    global running
    if not running:
        running = True
        print("Task started.")
        threading.Thread(target=run_loop, daemon=True).start()
    else:
        print("Task already running.")

def stop_task():
    global running
    if running:
        running = False
        print("Task stopped.")
    else:
        print("Task already stopped.")

def run_loop():
    while running:
        print("Running scheduled task...")
        time.sleep(10)

def create_icon():
    # Create a simple red dot icon
    image = Image.new("RGB", (64, 64), "white")
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 16, 48, 48), fill="red")
    return image

icon = Icon(
    "MyScheduler",
    create_icon(),
    menu=Menu(
        MenuItem("Start", lambda icon, item: start_task()),
        MenuItem("Stop", lambda icon, item: stop_task()),
        Menu.SEPARATOR,
        MenuItem("Quit", lambda icon, item: icon.stop()),
    )
)

icon.run()