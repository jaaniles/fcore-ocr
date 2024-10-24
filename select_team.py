import inquirer

from cache import store_selected_team
from database import get_user_teams

# Function to select a team from the user's teams
def select_team(userId, user_teams):
    # If there's only one team, auto-pick that one
    if len(user_teams) == 1:
        print(f"Only one team available: {user_teams[0]['teamName']}. Auto-selecting it.")
        return user_teams[0]

    # Prepare a list of choices for inquirer
    choices = [(team['teamName'], team['id']) for team in user_teams]

    # Use inquirer to prompt the user to choose a team
    questions = [
        inquirer.List(
            'team',
            message="Select a team",
            choices=choices,
        )
    ]
    
    # Get the selected team
    answer = inquirer.prompt(questions)
    
    # Find and return the selected team by matching the ID
    selected_team = next(team for team in user_teams if team['id'] == answer['team'])
    store_selected_team(userId, selected_team)

    print(f"Selected team: {selected_team['teamName']}")
    return selected_team

def refresh_teams(user_id):
    print("Refreshing teams...")
    teams = get_user_teams(user_id)
    if not teams:
        print("No teams found.")
        return None
    selected_team = select_team(user_id, teams)
    print(f"Selected team: {selected_team}")
    return selected_team