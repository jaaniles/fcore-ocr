import asyncio
from player_watcher.detect_squad_screen_type import detect_squad_screen_type
from screens.screen_types import SQUAD_ATTRIBUTES, SQUAD_FINANCIAL, SQUAD_STATS

ACCEPTED_SCREEN_TYPES = [SQUAD_FINANCIAL, SQUAD_STATS, SQUAD_ATTRIBUTES]

async def filter_screenshots(screenshot_paths):
    """Filter screenshots to keep only valid screen types using concurrent processing."""
    
    # Schedule concurrent detection tasks for each screenshot
    tasks = [detect_squad_screen_type(path) for path in screenshot_paths]
    
    # Run all detection tasks concurrently
    screen_types = await asyncio.gather(*tasks)
    
    # Filter for valid screenshots based on screen type
    valid_screenshots = [
        (path, screen_type) 
        for path, screen_type in zip(screenshot_paths, screen_types) 
        if screen_type in ACCEPTED_SCREEN_TYPES
    ]

    return valid_screenshots
