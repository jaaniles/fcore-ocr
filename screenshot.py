import os
import time
from PIL import ImageGrab

def take_screenshot():
    """Takes a screenshot and returns the file path."""
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = os.path.join('screenshots', f'screenshot_{timestamp}.png')

    screenshot = ImageGrab.grab()  # Full-screen screenshot
    screenshot.save(filename)

    return filename
