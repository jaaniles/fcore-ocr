import pprint
import signal
import time
import win32api # type: ignore
import win32con # type: ignore

from inquirer import list_input # type: ignore
from auth import fetch_teams, load_credentials, login_to_firebase
from overlay import OverlayWindow
from detect_screen_type import detect_screen_type
from screens.player_performance import process_player_performance_screen
from screens.match_facts import process_match_facts
from screens.player_performance_extended import process_player_performance_extended
from screens.pre_match import load_pre_match_data, process_pre_match
from screens.sim_match_performance import process_sim_match_performance
from screenshot import take_screenshot
from screens.sim_match_facts import process_sim_match_facts

running = True  # Global flag to control the main process

# Function to handle team selection via Inquirer
def select_team(teams):
    team_names = [team["team_name"] for team in teams]
    selected_team_name = list_input("Select your team", choices=team_names)
    selected_team = next(team for team in teams if team["team_name"] == selected_team_name)
    print(f"Selected team: {selected_team['team_name']}")
    return selected_team

def start_main_process(selected_team, overlay):
    global running

    print(f"Monitoring screenshots for team: {selected_team['team_name']}")

    # Load previous pre-match data if any exists (status: ongoing)
    pre_match_data = load_pre_match_data()

    while running:
        try:
            f12_pressed = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0
            if f12_pressed:
                screenshot_path = take_screenshot()
                screen_type = detect_screen_type(screenshot_path)

                print("Debug: Screen type:", screen_type)

                if screen_type == "pre_match":
                    overlay.show("Pre-match screen detected.\nProcessing...", duration=5)
                    
                    pre_match_data = process_pre_match(screenshot_path)
                    #print (pre_match_data)
                    #save_pre_match_data(pre_match_data)
                    #overlay.show(f"Pre-match captured for {pre_match_data['home_team']} vs {pre_match_data['away_team']}", duration=5)

                elif screen_type == "match_facts":
                    overlay.show("Match facts detected. Processing...", duration=5)
                    match_facts = process_match_facts(screenshot_path)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None 

                elif screen_type == "sim_match_facts":
                    overlay.show("Sim match facts detected. Processing...", duration=5)
                    sim_match_facts = process_sim_match_facts(screenshot_path)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None

                elif screen_type == "sim_match_performance":
                    overlay.show("Sim match performance screen detected. Processing...", duration=5)
                    sim_match_performance = process_sim_match_performance(screenshot_path)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None

                elif screen_type == "player_performance":
                    overlay.show("Player performance screen detected. Processing...", duration=5)
                    player_performance = process_player_performance_screen(screenshot_path)
                    overlay.show("Match report generated. Match complete.", duration=5)
                    pre_match_data = None  

                    pprint.pprint(player_performance)
                elif screen_type == "player_performance_extended":
                    overlay.show("Player performance extended screen detected. Processing...", duration=5)
                    player_performance_extended = process_player_performance_extended(screenshot_path)


                else:
                    overlay.show("Unexpected screen detected. Please take the correct screenshot.", duration=5)

            esc_pressed = (win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0
            if esc_pressed and pre_match_data:
                overlay.show("Match aborted.", duration=5)
                pre_match_data = None  # Abort the ongoing match

            time.sleep(0.1)  

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
        print("Program interrupted. Exiting...")
    finally:
        print("Cleaning up resources...")
        overlay.close()  

if __name__ == "__main__":
    main()
