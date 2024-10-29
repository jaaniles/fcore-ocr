import os
import shutil
import asyncio
import time

from player_watcher.filter_screenshots import filter_screenshots
from reports.report_manager import create_report, save_to_cache, submit_report
from screens.screen_types import SQUAD_FINANCIAL, SQUAD_STATS, SQUAD_ATTRIBUTES
from screens.squad_attributes import process_squad_attributes
from screens.squad_financial import process_squad_financial
from screens.squad_stats import process_squad_stats
from player_watcher.detect_player_from_screen import detect_player_from_screen

SCREENSHOT_DIR = "./local_player_data"
ARCHIVE_DIR = os.path.join(SCREENSHOT_DIR, "archive")
os.makedirs(ARCHIVE_DIR, exist_ok=True)

async def process_screenshots(user_id):
    """Process valid screenshots by filtering, grouping by player, and saving all players in a single report."""
    start_time = time.time()  # Start timing the process

    screenshot_paths = [os.path.join(SCREENSHOT_DIR, f) for f in os.listdir(SCREENSHOT_DIR) if os.path.isfile(os.path.join(SCREENSHOT_DIR, f))]
    print("Filtering screenshots...")
    valid_screenshots = await filter_screenshots(screenshot_paths)

    total_images = len(valid_screenshots)
    if not valid_screenshots:
        print("\nNo valid screenshots found.")
        clean_up_non_valid_screenshots(screenshot_paths, valid_screenshots)
        return

    print(f"\nTotal images to process: {total_images}")
    player_report = create_report("player_report", user_id)
    player_report["screens_data"] = {"players": []}  # Initialize as a list of player dictionaries

    # Schedule all processing tasks concurrently
    processing_tasks = [
        process_single_screenshot(path, screen_type, player_report["screens_data"]["players"], i + 1, total_images) 
        for i, (path, screen_type) in enumerate(valid_screenshots)
    ]

    # Run all tasks concurrently
    await asyncio.gather(*processing_tasks)

    # Save the complete player report
    save_to_cache(player_report)

    # Clean up non-valid screenshots
    clean_up_non_valid_screenshots(screenshot_paths, valid_screenshots)

    submit_report(player_report)

    end_time = time.time()  # End timing the process
    print(f"Saved player report for all players: {player_report['report_handle']}")
    print(f"Total processing time: {end_time - start_time:.2f} seconds")

async def process_single_screenshot(path, screen_type, players_data, current_index, total_images):
    """Process a single screenshot, including player detection and data extraction."""
    player_name = await detect_player_from_screen(path)
    
    if not player_name:
        print(f"Could not detect player name for screenshot: {path}")
        return

    # Find existing player entry or create a new one
    player_entry = next((player for player in players_data if player["name"] == player_name), None)
    if not player_entry:
        player_entry = {"name": player_name, "financial": None, "stats": None, "attributes": None}
        players_data.append(player_entry)

    # Await async processing functions and populate the appropriate field
    if screen_type == SQUAD_FINANCIAL:
        player_entry["financial"] = await process_squad_financial(path)
    elif screen_type == SQUAD_STATS:
        player_entry["stats"] = await process_squad_stats(path)
    elif screen_type == SQUAD_ATTRIBUTES:
        player_entry["attributes"] = await process_squad_attributes(path)

    # Inform the user of progress
    print(f"Processed image {current_index}/{total_images}: {os.path.basename(path)}")

def archive_screenshot(screenshot_path):
    filename = os.path.basename(screenshot_path)
    archive_path = os.path.join(ARCHIVE_DIR, filename)
    shutil.move(screenshot_path, archive_path)
    print(f"Archived screenshot: {filename}")

def clean_up_non_valid_screenshots(all_screenshots, valid_screenshots):
    valid_paths = {path for path, _ in valid_screenshots}
    non_valid_screenshots = set(all_screenshots) - valid_paths

    for path in non_valid_screenshots:
        os.remove(path)
        print(f"Deleted non-valid screenshot: {os.path.basename(path)}")
