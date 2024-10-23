import psutil
import os

def set_highest_priority():
    # Get the current process
    p = psutil.Process(os.getpid())
    
    # Set the priority to "highest" (for Windows)
    p.nice(psutil.REALTIME_PRIORITY_CLASS)

def set_high_priority():
    # Get the current process
    p = psutil.Process(os.getpid())
    
    # Set the priority to "high" (for Windows)
    p.nice(psutil.HIGH_PRIORITY_CLASS)

def set_normal_priority():
    """Resets the process priority to normal."""
    p = psutil.Process(os.getpid())
    p.nice(psutil.NORMAL_PRIORITY_CLASS)