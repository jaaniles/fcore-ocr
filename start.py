# auto_reload.py

import sys
import subprocess
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

class ReloadHandler(PatternMatchingEventHandler):
    patterns = ["*.py"]

    def __init__(self, process):
        super().__init__()
        self.process = process

    def on_modified(self, event):
        print(f"{event.src_path} has been modified. Reloading...")
        self.process.kill()
        self.process = subprocess.Popen([sys.executable, 'run.py'])

def start_watcher():
    process = subprocess.Popen([sys.executable, 'run.py'])

    event_handler = ReloadHandler(process)
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping watcher.")
        observer.stop()
        process.kill()
    observer.join()

if __name__ == "__main__":
    start_watcher()