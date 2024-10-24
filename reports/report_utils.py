# Helper function to show the user which screens are missing
from reports.report_types import REPORT_TYPES

def show_missing_screens(report, report_type, overlay):
    report_config = REPORT_TYPES[report_type]
    
    # Get the list of screens that are still missing
    captured_screens = report["screens_data"].keys()
    required_screens = set(report_config["required_screens"])
    missing_screens = required_screens - set(captured_screens)
    
    if missing_screens:
        overlay_text = f"Screens missing: {', '.join(missing_screens)}"
    else:
        overlay_text = "All required screens captured. Ready to submit."

    print(overlay_text)
    
    # Show the overlay with the missing screen information
    overlay.show(overlay_text, duration=5)