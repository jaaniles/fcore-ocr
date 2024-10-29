
from database import save_to_collection


def submit_match_report(report):
    saved_report_id = save_to_collection('matchReport', report)

    if saved_report_id:
        print(f"Report successfully saved with ID: {saved_report_id}")
    else:
        print("Failed to save the report.")

def submit_sim_match_report(report):
    saved_report_id = save_to_collection('matchReport', report)

    if saved_report_id:
        print(f"Report successfully saved with ID: {saved_report_id}")
    else:
        print("Failed to save the report.")

def submit_player_report(report):
    saved_report_id = save_to_collection('playerReport', report)

    if saved_report_id:
        print(f"Report successfully saved with ID: {saved_report_id}")
    else:
        print("Failed to save the report.")

