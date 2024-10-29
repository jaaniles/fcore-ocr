
from database import save_to_collection


def submit_match_report(report):
    print("SUBMIT!", report["report_handle"])
    print(report)

def submit_sim_match_report(report):
    print("SUBMIT SIM!", report["report_handle"])
    print(report)

def submit_player_report(report):
    saved_report_id = save_to_collection('player_reports', report)

    if saved_report_id:
        print(f"Report successfully saved with ID: {saved_report_id}")
    else:
        print("Failed to save the report.")

def submit_squad_financial_report(report):
    print("SUBMIT SQUAD!", report["report_handle"])
    print(report)

def submit_squad_attributes_report(report):
    print("SUBMIT SQUAD ATTRIBUTES!", report["report_handle"])
    print(report)

def submit_squad_stats_report(report):
    print("SUBMIT SQUAD STATS!", report["report_handle"])
    print(report)