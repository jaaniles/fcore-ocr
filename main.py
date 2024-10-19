import json
import logging
import threading
import time
import win32api
import win32con
from inquirer import list_input
from auth import fetch_teams, load_credentials, login_to_firebase, select_team
from overlay import OverlayWindow
from detect_screen_type import detect_screen_type
from player_performance import process_player_performance_screen
from match_facts import process_match_facts
from pre_match import extract_pre_match_data, load_pre_match_data, save_pre_match_data
from screenshot import take_screenshot


# Function to start the main process after login and team selection
def start_main_process(selected_team, overlay):
    print(f"Monitoring screenshots for team: {selected_team['team_name']}")

    # Load previous pre-match data if any exists (status: ongoing)
    pre_match_data = load_pre_match_data()

    while True:
        # Detect screenshots using existing logic
        f12_pressed = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0
        if f12_pressed:
            screenshot_path = take_screenshot()
            screen_type = detect_screen_type(screenshot_path)

            if pre_match_data and screen_type == "pre_match_screen":
                # Inform the user that a pre-match is already ongoing and ask if they want to abort or replace
                overlay.show("Another pre-match screen was detected.\nPress F10 to abort previous match or ESC to accept new match.", duration=None)
                # Handle user decision here (mock for now)
                pre_match_data = None  # This is where you handle aborting/replacing the old pre-match

            elif not pre_match_data and screen_type == "pre_match_screen":
                # Handle pre-match screen detection
                overlay.show("Pre-match screen detected.\nProcessing...", duration=5)
                pre_match_data = extract_pre_match_data(screenshot_path)
                save_pre_match_data(pre_match_data)
                overlay.show(f"Pre-match captured for {pre_match_data['home_team']} vs {pre_match_data['away_team']}", duration=5)

            elif pre_match_data and screen_type == "match_facts":
                # Handle match facts screen and pairing with pre-match
                overlay.show("Match facts detected. Processing...", duration=5)
                process_match_facts(screenshot_path, overlay, on_data_extracted=lambda data: None)
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

# Main entry point
def main():
    overlay = OverlayWindow()  # Initialize overlay

    # Load credentials and login
    credentials = load_credentials()
    firebase_response = login_to_firebase(credentials["email"], credentials["password"])

    if firebase_response["status"] != "success":
        print("Failed to log in.")
        return

    # Fetch and select team
    user_id = firebase_response["user_id"]
    teams = fetch_teams(user_id)
    selected_team = select_team(teams)

    # Start the main process
    start_main_process(selected_team, overlay)

if __name__ == "__main__":
    main()
