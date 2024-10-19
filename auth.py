# Mock Firebase login function (replace with real Firebase logic)
import json
import time

from inquirer import list_input


def login_to_firebase(email, password):
    print(f"Logging in with {email}")
    return {"status": "success", "user_id": "mock_user_id"}

# Mock team fetching function (replace with real Firebase logic)
def fetch_teams(user_id):
    return [
        {"team_id": "team_1", "team_name": "Team A", "players": []},
        {"team_id": "team_2", "team_name": "Team B", "players": []}
    ]

# Load credentials from JSON file
def load_credentials():
    with open("credentials.json", "r") as f:
        return json.load(f)


# Function to handle team selection via Inquirer
def select_team(teams):
    team_names = [team["team_name"] for team in teams]
    selected_team_name = list_input("Select your team", choices=team_names)
    selected_team = next(team for team in teams if team["team_name"] == selected_team_name)
    print(f"Selected team: {selected_team['team_name']}")
    return selected_team
