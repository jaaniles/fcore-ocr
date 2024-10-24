from reports.report_manager import is_report_complete
from reports.report_types import REPORT_TYPES

def handle_optional_screens(report, report_type, overlay):
    """Handles optional screen capture after required screens are completed"""
    report_config = REPORT_TYPES[report_type]

    if is_report_complete(report):
        missing_optional_screens = [
            screen for screen in report_config["optional_screens"]
            if screen not in report["screens_data"]
        ]
        if missing_optional_screens:
            overlay.show(f"Required screens captured. Press F10 to submit or capture optional screens.")
        else:
            return True  # All screens captured, can proceed to submission

    return False  # Still waiting for optional screens or user confirmation to submit