import json
import os
from pathlib import Path
import uuid

import numpy as np
from reports.report_types import REPORT_TYPES

# Define a directory for local cache
CACHE_DIR = Path("local_cache")
CACHE_DIR.mkdir(exist_ok=True)  # Ensure the cache directory exists

# Utility function to get the cache path for a specific report
def get_cache_path(report_id, report_type, is_submitted=False):
    suffix = "_submitted" if is_submitted else ""
    return CACHE_DIR / f"{report_type}_{report_id}{suffix}.json"

# Initialize a new report
def create_report(report_type, user_id):
    """Create a new report with a shortened UUID and save it to cache."""
    report_id = str(uuid.uuid4())[:8]  # Shorten the UUID to 8 characters
    report = {
        "report_handle": report_id,
        "userId": user_id,
        "report_type": report_type,
        "screens_data": {},
        "status": "in_progress"
    }

    # Save the report with the new naming convention
    cache_path = os.path.join(CACHE_DIR, f"{report_type}_{report_id}.json")
    with open(cache_path, 'w') as cache_file:
        json.dump(report, cache_file)

    return report

def show_expected_screens(report_type, overlay):
    """
    Show the expected required and optional screens for the current report type.
    """
    report_config = REPORT_TYPES[report_type]
    required_screens = ', '.join(report_config['required_screens'])
    optional_screens = ', '.join(report_config['optional_screens'])

    overlay_text = f"Expected Screens:\nRequired: {required_screens}\nOptional: {optional_screens}"
    overlay.show(overlay_text, duration=5)

def custom_json_serializer(obj):
    """ Custom serializer for types that are not serializable by default. """
    if isinstance(obj, np.bool_):  # Handle numpy bool
        return bool(obj)
    elif isinstance(obj, np.integer):  # Handle numpy integer types
        return int(obj)
    elif isinstance(obj, np.floating):  # Handle numpy float types
        return float(obj)
    elif isinstance(obj, np.ndarray):  # Handle numpy arrays
        return obj.tolist()
    else:
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

# Save report to cache
def save_to_cache(report):
    is_submitted = report["status"] == "complete"

    cache_path = get_cache_path(report["report_handle"], report["report_type"], is_submitted)
    with open(cache_path, "w") as cache_file:
        json.dump(report, cache_file, default=custom_json_serializer)

# Add screen data to the report
def set_screen_data(report, screen_type, screen_data):
    report["screens_data"][screen_type] = screen_data

    save_to_cache(report)

def add_screen_data(report, screen_type, screen_data):
    if screen_type not in report["screens_data"]:
        report["screens_data"][screen_type] = []
    report["screens_data"][screen_type].append(screen_data)

    save_to_cache(report)

# Check if the report is complete (all required screens are captured)
def is_report_complete(report):
    required_screens = REPORT_TYPES[report["report_type"]]["required_screens"]
    return all(screen in report["screens_data"] for screen in required_screens)

# Finalize and submit the report
def submit_report(report):
    # Ensure the report isn't already submitted
    if report["status"] == "complete":
        print(f"Report {report['report_handle']} is already submitted.")
        return
    
    # Mark the report as complete
    report["status"] = "complete"
    save_to_cache(report)

    submit_function = REPORT_TYPES[report["report_type"]]["submit_function"]
    submit_function(report)  # Directly call the function to submit the report

    # Rename the file after submission
    old_path = get_cache_path(report["report_handle"], report["report_type"])
    new_path = old_path.with_name(f"{report['report_type']}_{report['report_handle']}_submitted.json")
    
    # Handle conflict if submitted file already exists
    if os.path.exists(new_path):
        os.remove(new_path)  # Remove existing submitted file (if needed)
    
    os.rename(old_path, new_path)  # Rename the file to mark it as submitted
