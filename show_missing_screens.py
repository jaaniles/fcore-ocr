# Helper function to show the user which screens are missing
from reports.report_types import REPORT_TYPES

def show_missing_screens(report, report_type, overlay):
    report_config = REPORT_TYPES[report_type]
    
    # Get the list of captured screens
    captured_screens = report["screens_data"].keys()
    
    # Get the required and optional screens from the report configuration
    required_screens = set(report_config["required_screens"])
    optional_screens = set(report_config["optional_screens"])
    
    # Calculate missing required and optional screens
    missing_required_screens = required_screens - set(captured_screens)
    missing_optional_screens = optional_screens - set(captured_screens)
    
    # Construct the combined overlay text
    if missing_required_screens:
        overlay_text = f"Required screens missing: {', '.join(missing_required_screens)}"
    else:
        overlay_text = "All required screens captured."
    
    if missing_optional_screens:
        overlay_text += f"\nOptional screens available: {', '.join(missing_optional_screens)}"
    else:
        overlay_text += "\nNo optional screens available."

    # Print the combined message to the console for debugging purposes
    print(overlay_text)
    
    # Show the overlay with the combined message
    overlay.show(overlay_text, duration=5)