
from select_team import refresh_teams

async def handle_refresh(action_refresh, user_id, selected_team, overlay):
    """Refreshes user teams if F5 is pressed"""
    from main import start_main_process


    if action_refresh:
        print("F5 pressed. Refreshing user teams...")
        selected_team = refresh_teams(user_id)
        if selected_team:
            await start_main_process(user_id, selected_team, overlay)