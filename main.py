import logging
import time
import threading
import win32api
import win32con
from paddleocr import PaddleOCR
from match_facts import process_match_facts
from overlay import OverlayWindow
from detect_screen_type import detect_screen_type 
from player_performance import process_player_performance_screen
from screenshot import take_screenshot

# Initialize the OCR engine
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)

# Disable PaddleOCR debug logs
logging.getLogger('ppocr').setLevel(logging.WARNING)  # Disables all logs below WARNING level
logging.getLogger('paddle').setLevel(logging.WARNING)  # Disable debug/info logs from paddle as well

# Global variables
overlay = None
report_type = None  # The deduced report type from the first screenshot
required_screens = []  # List of required screens for the current report type
captured_screenshots = {}  # Dictionary to store captured screenshots
waiting_for_submission = False
first_screenshot_taken = False

# Define report types and their required screens based on the first screenshot type
report_types = {
    "match_facts": {
        "report_type": "match_report",
        "required_screens": ["player_performance"],
    },
    "simulated_match_facts": {
        "report_type": "simulated_match_report",
        "required_screens": ["simulated_player_performance"],
    },
}

def process_first_screenshot():
    """Process the first screenshot, determine report type, and identify required screens."""
    global overlay, report_type, required_screens, captured_screenshots, first_screenshot_taken

    # Display "Processing..." while screenshot is being taken and processed
    overlay.show("Processing...", duration=5)

    screenshot_path = take_screenshot()
    screen_type = detect_screen_type(screenshot_path)  # Implement this function
    print(f"First screenshot type: {screen_type}")

    if screen_type in report_types:
        # Deduce report type and required screens
        report_info = report_types[screen_type]
        report_type = report_info["report_type"]
        required_screens = report_info["required_screens"]
        captured_screenshots[screen_type] = screenshot_path  # Save the first screenshot
        first_screenshot_taken = True

        # If data extraction is required for the first screenshot, process it
        if screen_type == 'player_performance':
            threading.Thread(target=process_player_performance_screen_with_ocr_display, args=(screenshot_path, ocr)).start()
        elif screen_type == 'match_facts':
            threading.Thread(target=process_match_facts, args=(screenshot_path, ocr)).start()

        # Inform the user
        remaining_screens = [screen for screen in required_screens if screen not in captured_screenshots]
        if remaining_screens:
            overlay.show(f"First screenshot '{screen_type}' received.\nPlease take screenshots of: {', '.join(remaining_screens)}.\nPress F12 to capture, ESC to abort.", duration=None)
        else:
            # All required screenshots captured
            waiting_for_submission = True
            overlay.show("All required screenshots captured.\nPress Enter to submit, ESC to abort.", duration=None)
    else:
        overlay.show(f"Unrecognized first screenshot '{screen_type}'.\nProcess aborted.", duration=5)
        print(f"Unrecognized first screenshot '{screen_type}'.")
        reset_process()

def process_player_performance_screen_with_ocr_display(screenshot_path, ocr):
    """Process the player performance screen, extract OCR data, and display it as a table."""
    global overlay
    # Display "Processing..." in the overlay
    overlay.show("Processing player performance...", duration=5)

    # Process the screenshot, run OCR, and extract player data
    player_data = process_player_performance_screen(screenshot_path, ocr)

    # Display the extracted player data in a table format using the overlay
    if player_data:
        formatted_data = [{'player': p['fullName'], 'rating': p['matchRating']} for p in player_data]
        overlay.show(formatted_data)  # Use the tabular display from the overlay
    else:
        overlay.show("No valid player data extracted. Please try again.", duration=5)

def process_additional_screenshot():
    """Process additional screenshots after the first one."""
    global overlay, required_screens, captured_screenshots, waiting_for_submission

    # Display "Processing..." while screenshot is being taken and processed
    overlay.show("Processing...", duration=5)

    screenshot_path = take_screenshot()
    screen_type = detect_screen_type(screenshot_path)  # Implement this function
    print(f"Captured screenshot type: {screen_type}")

    # Check if the captured screen is one of the required screens and hasn't been captured yet
    if screen_type in required_screens and screen_type not in captured_screenshots:
        captured_screenshots[screen_type] = screenshot_path
        print(f"Screenshot '{screen_type}' captured.")

        # If data extraction is required for this screen_type, process it
        if screen_type == 'player_performance':
            threading.Thread(target=process_player_performance_screen_with_ocr_display, args=(screenshot_path, ocr)).start()

        remaining_screens = [screen for screen in required_screens if screen not in captured_screenshots]
        if remaining_screens:
            overlay.show(f"Screenshot '{screen_type}' received.\nPlease capture: {', '.join(remaining_screens)}.\nPress F12 to continue, ESC to abort.", duration=None)
        else:
            # All required screenshots have been captured
            waiting_for_submission = True
            overlay.show("All required screenshots captured.\nPress Enter to submit, ESC to abort.", duration=None)
    elif screen_type in captured_screenshots:
        overlay.show(f"Screenshot '{screen_type}' already captured.\nPlease capture remaining: {', '.join([screen for screen in required_screens if screen not in captured_screenshots])}.", duration=5)
        print(f"Screenshot '{screen_type}' already captured.")
    else:
        overlay.show(f"Unexpected screenshot '{screen_type}'.\nPlease capture the required screenshots.", duration=5)
        print(f"Unexpected screenshot '{screen_type}'.")

def handle_submission():
    """Handle submission of the report."""
    global overlay, waiting_for_submission
    if waiting_for_submission:
        overlay.show("Submitting report...", duration=3)
        print("Submitting...")
        # Access captured_screenshots dictionary
        # You can add code here to process or upload the data
        reset_process()

def handle_abort():
    """Handle aborting the report process."""
    global overlay, waiting_for_submission
    overlay.show("Report aborted. Waiting for new reports.", duration=3)
    print("Aborted. Waiting for new reports.")
    reset_process()

def reset_process():
    """Reset variables to start a new report process."""
    global report_type, required_screens, captured_screenshots, waiting_for_submission, first_screenshot_taken
    report_type = None
    required_screens = []
    captured_screenshots = {}
    waiting_for_submission = False
    first_screenshot_taken = False

def main():
    global overlay
    overlay = OverlayWindow()  # Initialize the overlay window

    print("Program ready. Press F12 to start capturing screenshots.")

    # Initialize previous key states
    last_f12_pressed = False
    last_esc_pressed = False
    last_enter_pressed = False

    try:
        while True:
            # Check F12 key
            f12_pressed = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0
            if f12_pressed and not last_f12_pressed:
                # F12 key was just pressed
                if not first_screenshot_taken:
                    threading.Thread(target=process_first_screenshot).start()
                elif not waiting_for_submission:
                    threading.Thread(target=process_additional_screenshot).start()
                last_f12_pressed = True
            elif not f12_pressed:
                last_f12_pressed = False

            # Check ESC key
            esc_pressed = (win32api.GetAsyncKeyState(win32con.VK_ESCAPE) & 0x8000) != 0
            if esc_pressed and not last_esc_pressed:
                # ESC key was just pressed
                if waiting_for_submission or captured_screenshots:
                    threading.Thread(target=handle_abort).start()
                last_esc_pressed = True
            elif not esc_pressed:
                last_esc_pressed = False

            # Check Enter key
            enter_pressed = (win32api.GetAsyncKeyState(win32con.VK_RETURN) & 0x8000) != 0
            if enter_pressed and not last_enter_pressed:
                # Enter key was just pressed
                if waiting_for_submission:
                    threading.Thread(target=handle_submission).start()
                last_enter_pressed = True
            elif not enter_pressed:
                last_enter_pressed = False

            time.sleep(0.1)  # Sleep to prevent high CPU usage
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
