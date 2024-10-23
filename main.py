import sys
from timed_import import timed_import

import asyncio 
import pprint
import signal
import win32api
import win32con

from auth import load_session, restore_or_authenticate
from cache import load_selected_team
from database import get_user_teams
from ocr import initialize_paddleocr
from overlay import OverlayWindow
from detect_screen_type import detect_screen_type
from priority import set_highest_priority, set_normal_priority
from screens.player_performance import process_player_performance_screen
from screens.match_facts import process_match_facts
from screens.player_performance_extended import process_player_performance_extended
from screens.pre_match import load_pre_match_data, process_pre_match
from screens.sim_match_performance import process_sim_match_performance
from screenshot import take_screenshot
from screens.sim_match_facts import process_sim_match_facts
from select_team import select_team

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

running = True  # Global flag to control the main process

async def start_main_process(selected_team, overlay, ocr):
    global running

    print(f"Monitoring screenshots for team: {selected_team['teamName']}")

    # Load previous pre-match data if any exists (status: ongoing)
    pre_match_data = load_pre_match_data()

    while running:
        try:
            f5_pressed = (win32api.GetAsyncKeyState(win32con.VK_F5) & 0x8000) != 0
            f12_pressed = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0

            if f12_pressed:
                set_highest_priority() # Set high priority for the process
                print("F12 pressed. Taking screenshot...")
                overlay.show("Screenshotting..", duration=3)
    
                screenshot_path = take_screenshot()
                screen_type = await detect_screen_type(screenshot_path, ocr)

                print("Debug: Screen type:", screen_type)

                if screen_type == "pre_match":
                    overlay.show("Pre-match screen detected.\nProcessing...", duration=5)
                    pre_match_data = await process_pre_match(screenshot_path, ocr)

                elif screen_type == "match_facts":
                    overlay.show("Match facts detected. Processing...", duration=5)
                    match_facts = await process_match_facts(screenshot_path, ocr)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None 

                elif screen_type == "sim_match_facts":
                    overlay.show("Sim match facts detected. Processing...", duration=5)
                    sim_match_facts = await process_sim_match_facts(screenshot_path, ocr, selected_team)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None

                elif screen_type == "sim_match_performance":
                    overlay.show("Sim match performance screen detected. Processing...", duration=5)
                    sim_match_performance = await process_sim_match_performance(screenshot_path, ocr, selected_team)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None

                elif screen_type == "player_performance":
                    overlay.show("Player performance screen detected. Processing...", duration=5)
                    player_performance = await process_player_performance_screen(screenshot_path, ocr)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None  

                    pprint.pprint(player_performance)
                elif screen_type == "player_performance_extended":
                    overlay.show("Player performance extended screen detected. Processing...", duration=5)
                    player_performance_extended = await process_player_performance_extended(screenshot_path, ocr)
                else:
                    overlay.show("Unexpected screen detected. Please take the correct screenshot.", duration=5)
                set_normal_priority()  # Reset the priority to normal

             # Detect F5 press to trigger refresh
            if f5_pressed:
                print("F5 pressed. Refreshing user teams...")
                teams = get_user_teams(selected_team['userId']) 

                if not teams:
                    print("No teams found. Create a team in FCORE before starting this program.")
                    return

                # Let user select team again
                selected_team = select_team(selected_team['userId'], teams)
                print("Selected team: ", selected_team)

                await start_main_process(selected_team, overlay, ocr)  


            esc_pressed = (win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0
            if esc_pressed and pre_match_data:
                overlay.show("Match aborted.", duration=5)
                pre_match_data = None  # Abort the ongoing match

            await asyncio.sleep(0.1)  

        except KeyboardInterrupt:
            print("Gracefully shutting down...")
            running = False
            overlay.close()
            break

    print("Exited main process.")

def signal_handler(sig, frame):
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False

async def main():
    global running

    overlay = OverlayWindow()  # Initialize overlay
    ocr_startup_task = asyncio.create_task(initialize_paddleocr())

    try:
        # Step 1: Load session from file
        session = load_session()

        # Step 2: Check if session contains a userId and load cached team
        cache_team = None
        if session and "localId" in session:
            cache_team = load_selected_team(session["localId"])  # Load team based on userId

        # Step 3: Start authentication in the background
        auth_task = asyncio.create_task(restore_or_authenticate(session))

        # Step 4: Proceed optimistically with the cached team if available
        if cache_team:
            main_process_task = asyncio.create_task(start_main_process(cache_team, overlay, ocr_startup_task))
        else:
            print("No cached team available, waiting for authentication to proceed.")
            main_process_task = None  # Will wait for team selection after auth

        # Step 5: Wait for authentication to finish in parallel
        user = await auth_task
        userId = user.get('localId') or user.get('userId')

        # Step 6: If authentication fails, exit
        if not user or not userId:
            print("Failed to authenticate user. Exiting...")
            if main_process_task:
                running = False  # Stop the ongoing main process
            return

        # Step 7: If authentication succeeds but no cached team, continue normally
        if not cache_team:
            # Load teams from Firestore after authentication succeeds
            teams = get_user_teams(userId)
            print("Teams: ", teams)

            if not teams:
                print("No teams found. Create a team in FCORE before starting this program.")
                return

            # Select the team after getting the list of teams
            selected_team = select_team(userId, teams)
            print("Selected team: ", selected_team)

            # Start the main process with the selected team
            await start_main_process(selected_team, overlay, ocr_startup_task)
        else:
            # If authentication succeeds but we already started the main process, continue
            await main_process_task  # Wait for the optimistic process to finish

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting gracefully (manually handled on Windows)...")
        running = False

    finally:
        print("Cleaning up resources...")
        overlay.close()



if __name__ == "__main__":
    asyncio.run(main())
