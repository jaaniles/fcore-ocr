from reports.report_manager import is_report_complete, submit_report

def handle_report_submission(report, report_type, overlay):
    """Submits the report if user presses F10"""
    if report and is_report_complete(report):
        submit_report(report)
        overlay.show(f"{report_type} submitted successfully!", duration=3)
        return True
    
    return False