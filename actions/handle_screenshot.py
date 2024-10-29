from reports.report_manager import add_screen_data, create_report, set_screen_data, show_expected_screens
from reports.report_types import REPORT_TYPES
from screens.extract_data_from_screen import extract_data_from_screen
from screens.detect_match_screen_type import detect_match_screen_type
from show_missing_screens import show_missing_screens

async def handle_screenshot(screenshot_path, report, report_type, user_id, team, overlay):
    """
    Handles the screenshot action, determines the report type and screen type,
    and manages the report data collection based on detected screen information.
    """
    screen_type = await detect_match_screen_type(screenshot_path)
    print(f"Detected screen: {screen_type}")

    # Initialize report if necessary
    report_type, report = initialize_report(report, report_type, user_id, screen_type, overlay)

    # Perform data extraction if report_type is set and screen is allowed
    if report_type:
        await extract_and_process_screen_data(screenshot_path, report, report_type, team, screen_type, overlay)

    return report, report_type


def initialize_report(report, report_type, user_id, screen_type, overlay):
    """
    Initializes report and report_type if this is the first screen capture,
    based on screen type and configuration.
    """
    # Return existing report and type if already initialized
    if report_type:
        return report_type, report

    # Identify report type based on initial screen type and initialize report if necessary
    for r_type, config in REPORT_TYPES.items():
        if screen_type == config["initial_screen"]:
            report_type = r_type
            report = create_report(r_type, user_id)
            show_expected_screens(report_type, overlay)
            return report_type, report

    # If no valid initial screen, log and return unmodified
    print(f"Unrecognized initial screen: {screen_type}")
    return report_type, report


async def extract_and_process_screen_data(screenshot_path, report, report_type, team, screen_type, overlay):
    """
    Extracts data from screens and updates the report based on the screen type
    and multi or single capture configuration.
    """
    report_config = REPORT_TYPES[report_type]
    multi_capture = screen_type in report_config["multi_capture_screens"]
    allowed_screens = (
        [report_config["initial_screen"]]
        + report_config["required_screens"]
        + report_config["optional_screens"]
        + report_config["multi_capture_screens"]
    )

    if screen_type in allowed_screens:
        screen_data = await extract_data_from_screen(screen_type, screenshot_path, team)
        handle_screen_data(report, screen_type, screen_data, multi_capture)
        show_missing_screens(report, report_type, overlay)
        handle_submission_status(report_config, report, overlay, multi_capture)


def handle_screen_data(report, screen_type, screen_data, multi_capture):
    """
    Adds data to the report if multi_capture is enabled; otherwise, sets data.
    """
    if multi_capture:
        add_screen_data(report, screen_type, screen_data)
    else:
        set_screen_data(report, screen_type, screen_data)


def handle_submission_status(config, report, overlay, multi_capture):
    """
    Manages submission prompts based on the capture type and report status.
    """
    if multi_capture:
        overlay.show("Ready for another screenshot. You can press F10 to submit.", duration=5)
    elif not config["required_screens"]:
        report["status"] = "complete"
        overlay.show("Report ready to submit. Press F10 to submit.", duration=5)
