# Mock function to extract data from the pre-match screen (for now)
import json
import time

def extract_pre_match_data(screenshot_path):
    return {
        "match_id": "mock_match_001",
        "home_team": "Mock Home Team",
        "away_team": "Mock Away Team",
        "timestamp": time.time(),
        "status": "ongoing"
    }

# Save pre-match data into a JSON file
def save_pre_match_data(match_data):
    with open("pre_match_data.json", "w") as f:
        json.dump(match_data, f, indent=4)

# Load pre-match data from JSON
def load_pre_match_data():
    try:
        with open("pre_match_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None