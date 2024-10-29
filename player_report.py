# player_report_watcher.py

from PIL import ImageGrab
import os
import asyncio
import signal
import time
import win32api
import win32con

from auth import load_session, restore_or_authenticate
from cache import load_selected_team
from database import get_user_teams
from player_watcher.process_screenshots import process_screenshots
from priority import set_highest_priority
from select_team import select_team

SCREENSHOT_DIR = "./local_player_data" 
os.makedirs(SCREENSHOT_DIR, exist_ok=True)
running = True  

def take_screenshot():
    """Takes a screenshot and returns the file path."""
    if not os.path.exists('screenshots'):
        os.makedirs('screenshots')

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(SCREENSHOT_DIR, f'screenshot_{timestamp}.png')

    screenshot = ImageGrab.grab() 
    screenshot.save(filename)

    return filename

async def watch_for_screenshots(user_id):
    """
    Continuously monitor the screenshot directory for new images.
    Print "Screenshotted" each time a new screenshot is detected or taken with F12.
    """
    print("Starting Watch Mode: Monitoring for new screenshots...")

    # Track existing files in the directory
    seen_files = set(os.listdir(SCREENSHOT_DIR))

    while running:
        action_screenshot = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0
        action_process = (win32api.GetAsyncKeyState(win32con.VK_F10) & 0x8000) != 0

        if action_screenshot:
            print("Taking screenshot..")
            screenshot_file = take_screenshot()
            seen_files.add(os.path.basename(screenshot_file))  

        if action_process:
            set_highest_priority()
            print("\nProcess Mode Activated. Listing all screenshots taken during Watch Mode:")
            await process_screenshots(user_id)

        # Check for new files in the directory
        current_files = set(os.listdir(SCREENSHOT_DIR))
        new_files = current_files - seen_files

        if new_files:
            for file in new_files:
                print("Screenshotted:", file)  
            seen_files.update(new_files)

        # Wait briefly before checking again
        await asyncio.sleep(0.1)


async def main():
    global running

    try:
        # Step 1: Load session from file
        session = load_session()

        # Step 2: Check if session contains a userId and load cached team
        cache_team = None
        if session and "userId" in session:
            cache_team = load_selected_team(session["userId"])  # Load team based on userId

        # Step 3: Start authentication in the background
        auth_task = asyncio.create_task(restore_or_authenticate(session))

        # Step 4: Proceed optimistically with the cached team if available
        if cache_team:
            user_id = cache_team.get('userId')
            print(f"Using cached team: {cache_team['teamName']}")
        else:
            print("No cached team available, waiting for authentication to proceed.")
            user_id = None  # Will wait for team selection after auth

        # Step 5: Wait for authentication to finish in parallel
        user = await auth_task
        user_id = user.get('localId') or user.get('userId')

        # Step 6: If authentication fails, exit
        if not user or not user_id:
            print("Failed to authenticate user. Exiting...")
            running = False
            return

        # Step 7: If authentication succeeds but no cached team, continue normally
        if not cache_team:
            # Load teams from the database after authentication succeeds
            teams = get_user_teams(user_id)
            if not teams:
                print("No teams found. Create a team in FCORE before starting this program.")
                return

            # Select the team after getting the list of teams
            selected_team = select_team(user_id, teams)
            print(f"Selected team: {selected_team['teamName']}")
        else:
            # Use the cached team if available
            selected_team = cache_team

        # Step 8: Start the screenshot watcher
        print(f"Monitoring screenshots for team: {selected_team['teamName']}")
        await watch_for_screenshots(user_id)

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting gracefully.")
        running = False

    finally:
        print("Cleaning up resources...")

# Graceful shutdown handling
def signal_handler(sig, frame):
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False

# Register signal handler for graceful exit
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    asyncio.run(main())
