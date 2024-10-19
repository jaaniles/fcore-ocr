import signal
import json
import logging
import threading
import time
from paddleocr import PaddleOCR
import win32api
import win32con
from inquirer import list_input
from auth import fetch_teams, load_credentials, login_to_firebase
from overlay import OverlayWindow
from detect_screen_type import detect_screen_type
from player_performance import process_player_performance_screen
from match_facts import process_match_facts
from pre_match import load_pre_match_data, process_pre_match
from screenshot import take_screenshot

# Global variable to manage the program exit gracefully
running = True  # This will help us exit threads cleanly

ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)

# Function to handle team selection via Inquirer
def select_team(teams):
    team_names = [team["team_name"] for team in teams]
    selected_team_name = list_input("Select your team", choices=team_names)
    selected_team = next(team for team in teams if team["team_name"] == selected_team_name)
    print(f"Selected team: {selected_team['team_name']}")
    return selected_team

# Function to start the main process after login and team selection
def start_main_process(selected_team, overlay):
    global running

    print(f"Monitoring screenshots for team: {selected_team['team_name']}")

    # Load previous pre-match data if any exists (status: ongoing)
    pre_match_data = load_pre_match_data()

    while running:  # Check if the program is still running
        try:
            # Detect screenshots using existing logic
            f12_pressed = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0
            if f12_pressed:
                screenshot_path = take_screenshot()
                screen_type = detect_screen_type(screenshot_path)

                print("Debug: Screen type:", screen_type)

                if not pre_match_data and screen_type == "pre_match":
                    # Handle pre-match screen detection
                    overlay.show("Pre-match screen detected.\nProcessing...", duration=5)
                    
                    pre_match_data = process_pre_match(screenshot_path, ocr)
                    #print (pre_match_data)
                    #save_pre_match_data(pre_match_data)
                    #overlay.show(f"Pre-match captured for {pre_match_data['home_team']} vs {pre_match_data['away_team']}", duration=5)

                elif pre_match_data and screen_type == "pre_match":
                    # Inform the user that a pre-match is already ongoing and ask if they want to abort or replace
                    overlay.show("Another pre-match screen was detected.\nPress F10 to abort previous match or ESC to accept new match.", duration=None)
                    pre_match_data = None  # This is where you handle aborting/replacing the old pre-match

                elif pre_match_data and screen_type == "match_facts":
                    # Handle match facts screen and pairing with pre-match
                    overlay.show("Match facts detected. Processing...", duration=5)
                    process_match_facts(screenshot_path, ocr)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None  # Clear pre-match data after successful match report

                elif pre_match_data and screen_type == "player_performance":
                    # Handle player performance screen and pairing with pre-match
                    overlay.show("Player performance screen detected. Processing...", duration=5)
                    process_player_performance_screen(screenshot_path, overlay)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None  # Clear pre-match data after successful match report

                else:
                    overlay.show("Unexpected screen detected. Please take the correct screenshot.", duration=5)

            # Handle ESC for aborting ongoing match
            esc_pressed = (win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0
            if esc_pressed and pre_match_data:
                overlay.show("Match aborted.", duration=5)
                pre_match_data = None  # Abort the ongoing match

            time.sleep(0.1)  # Prevent high CPU usage

        except KeyboardInterrupt:
            print("Gracefully shutting down...")
            running = False
            overlay.close()
            break

    print("Exited main process.")

# Function to handle Ctrl+C signal (SIGINT)
def signal_handler(sig, frame):
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False

# Main entry point
def main():
    global running

    # Register the signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    overlay = OverlayWindow()  # Initialize overlay

    try:
        # Load credentials and login
        credentials = load_credentials()
        firebase_response = login_to_firebase(credentials["email"], credentials["password"])

        if firebase_response["status"] != "success":
            print("Failed to log in.")
            return

        # Fetch and select team
        user_id = firebase_response["user_id"]
        teams = fetch_teams(user_id)
        #selected_team = select_team(teams)
        selected_team = {"team_id": "team_1", "team_name": "Team A", "players": []}

        # Start the main process
        start_main_process(selected_team, overlay)

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully in case it wasn't caught by the main process
        print("Program interrupted. Exiting...")
    finally:
        print("Cleaning up resources...")
        overlay.close()  # Close overlay window if still open

if __name__ == "__main__":
    main()
