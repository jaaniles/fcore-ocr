from reports.report_manager import add_screen_data, create_report, show_expected_screens
from reports.report_types import REPORT_TYPES
from reports.report_utils import show_missing_screens
from screens.extract_data_from_screen import extract_data_from_screen
from screens.detect_screen_type import detect_screen_type

async def handle_screenshot(screenshot_path, ocr, report, report_type, user_id, team, overlay):
    """Handles the screenshot action and adds the screen data to the report"""
    screen_type = await detect_screen_type(screenshot_path, ocr)

    # No report type yet, determine report from initial screen
    if not report_type:
        for r_type, config in REPORT_TYPES.items():
            if screen_type == config["initial_screen"]:
                report_type = r_type
                report = create_report(r_type, user_id)  # Create new report if it's the initial screen
                show_expected_screens(report_type, overlay)  # Inform user what screens to capture
                
                # Add initial screen data to report
                initial_screen_data = await extract_data_from_screen(screen_type, screenshot_path, team, ocr)
                add_screen_data(report, screen_type, initial_screen_data)
                return report, report_type

        # If no matching initial screen, return with no changes
        print(f"Unrecognized initial screen: {screen_type}")
        return report, report_type
    
    # If report_type is already determined, proceed with handling the report
    report_config = REPORT_TYPES[report_type]
    allowed_screens = report_config["required_screens"] + report_config["optional_screens"]
    
    if screen_type in allowed_screens:
        screen_data = await extract_data_from_screen(screen_type, screenshot_path, team, ocr)
        add_screen_data(report, screen_type, screen_data)

        # Show which screens are still missing
        show_missing_screens(report, report_type, overlay)
    
    return report, report_type

