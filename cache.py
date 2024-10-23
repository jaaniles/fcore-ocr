import json
import os

CACHE_FOLDER = 'local_cache'

# Ensure the cache folder exists
if not os.path.exists(CACHE_FOLDER):
    os.makedirs(CACHE_FOLDER)

def get_user_cache(user_id: str) -> str:
    return os.path.join(CACHE_FOLDER, f'user_{user_id}.json')

# Load the selected team from the cache
def load_selected_team(user_id: str):
    file_path = get_user_cache(user_id)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return None

# Store the selected team in the cache
def store_selected_team(user_id: str, selected_team: dict):
    file_path = get_user_cache(user_id)
    with open(file_path, 'w') as f:
        json.dump(selected_team, f)