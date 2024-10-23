import os
import sys
from watchfiles import run_process

def restart_program():
    """Restarts the program when changes are detected."""
    print("Python code changes detected. Restarting the program...")
    os.execv(sys.executable, [sys.executable] + ['main.py'])  # Restart the main.py script

def watch_filter(change, path):
    """Only watch .py files."""
    # Ensure that `path` is a .py file and return True only for .py files
    return path.endswith('.py')

if __name__ == "__main__":
    # Monitor the current directory, but only restart on .py file changes
    run_process('.', target=restart_program, watch_filter=watch_filter, recursive=True)