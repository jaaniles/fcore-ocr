import json
import os

import inquirer
from reports.report_manager import CACHE_DIR

def load_incomplete_reports(overlay=None):
    """Prompt the user to choose between multiple incomplete reports and notify them."""
    cache_files = [f for f in os.listdir(CACHE_DIR) if not f.endswith("_submitted.json")]

    incomplete_reports = []
    for cache_file in cache_files:
        with open(os.path.join(CACHE_DIR, cache_file), 'r') as file:
            report = json.load(file)
            if report.get("status") == "in_progress":
                incomplete_reports.append((cache_file, report))

    if len(incomplete_reports) == 0:
        print("No incomplete reports found.")
        return None

    # If more than one incomplete report is found, let the user choose
    if len(incomplete_reports) > 1:
        choices = [
            f"{idx + 1}. Report ID: {report['reportId']} (Incomplete)"
            for idx, (_, report) in enumerate(incomplete_reports)
        ]
        
        questions = [
            inquirer.List('report_choice',
                          message="Multiple incomplete reports found. Choose one to continue:",
                          choices=choices)
        ]
        selected = inquirer.prompt(questions)
        selected_idx = int(selected['report_choice'].split('.')[0]) - 1

        selected_report = incomplete_reports[selected_idx][1]
    else:
        # Load the only incomplete report
        selected_report = incomplete_reports[0][1]

    # Notify the user about the loaded incomplete report
    report_id = selected_report["reportId"]
    report_type = selected_report["report_type"]
    status = selected_report.get("status", "in_progress")

    # Show the status via overlay (optional)
    if overlay:
        overlay.show(f"Loaded Report: {report_type} (ID: {report_id}) - Status: {status}", duration=5)

    return selected_report