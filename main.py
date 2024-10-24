import asyncio 
import win32api
import win32con
import inquirer

from actions.handle_screenshot import handle_screenshot
from actions.handle_refresh import handle_refresh
from actions.handle_optional_screens import handle_optional_screens
from auth import load_session, restore_or_authenticate
from cache import load_selected_team
from database import get_user_teams
from ocr import initialize_paddleocr
from overlay import OverlayWindow
from priority import set_highest_priority, set_normal_priority
from reports.handle_report_submission import handle_report_submission
from reports.load_incomplete_reports import load_incomplete_reports
from reports.abort_report import abort_report
from reports.report_utils import show_missing_screens
from screenshot import take_screenshot
from select_team import select_team

running = True  # Global flag to control the main process

async def start_main_process(user_id, selected_team, overlay, ocr):
    global running

    print(f"Monitoring screenshots for team: {selected_team['teamName']}")

    # Load incomplete reports if any exist
    report = load_incomplete_reports(overlay)
    report_type = None

    # Incomplete report loaded from cache
    if report:
        report_type = report["report_type"]
        # Inform the user about the status of the cached report
        print(f"Loaded cached report: {report['reportId']}, status: {report['status']}")
        # Show which screens are still missing
        show_missing_screens(report, report_type, overlay)

    while running:
        try:
            # Detect keypress actions
            action_refresh = (win32api.GetAsyncKeyState(win32con.VK_F5) & 0x8000) != 0
            action_screenshot = (win32api.GetAsyncKeyState(win32con.VK_F12) & 0x8000) != 0
            action_submit = (win32api.GetAsyncKeyState(win32con.VK_F10) & 0x8000) != 0
            action_abort = (win32api.GetAsyncKeyState(win32con.VK_F3) & 0x8000) != 0  # Abort report with F3

            # Handle screenshot action
            if action_screenshot:
                set_highest_priority()
                overlay.show("Screenshotting..", duration=3)

                screenshot_path = take_screenshot()
                report, report_type = await handle_screenshot(screenshot_path, ocr, report, report_type, user_id, selected_team, overlay)

                # Handle optional screens logic
                if report_type and handle_optional_screens(report, report_type, overlay):
                    report_type = None  # Reset after submission

                set_normal_priority()

            if action_submit:
                handle_report_submission(report, report_type, overlay)
                report_type = None  # Reset after submission

            if action_refresh:
                # Handle refresh action (F5)
                await handle_refresh(action_refresh, user_id, selected_team, overlay, ocr)

            if action_abort and report:
                # Handle abort action (F3) and delete the selected report
                abort_report(report)
                report = None
                report_type = None
                overlay.show("Report aborted and deleted.", duration=3)
                print("Report aborted and deleted.")

            await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            print("Gracefully shutting down...")
            running = False
            overlay.close()
            break

    print("Exited main process.")

def signal_handler(sig, frame):
    global running
    print("\nCtrl+C detected. Exiting gracefully...")
    running = False

async def main():
    global running

    overlay = OverlayWindow()  # Initialize overlay
    ocr_startup_task = asyncio.create_task(initialize_paddleocr())

    try:
        # Step 1: Load session from file
        session = load_session()

        # Step 2: Check if session contains a userId and load cached team
        cache_team = None
        if session and "userId" in session:
            cache_team = load_selected_team(session["userId"])  # Load team based on userId

        # Step 3: Start authentication in the background
        auth_task = asyncio.create_task(restore_or_authenticate(session))

        # Step 4: Proceed optimistically with the cached team if available
        if cache_team:
            user_id = cache_team.get('userId')
            main_process_task = asyncio.create_task(start_main_process(user_id, cache_team, overlay, ocr_startup_task))
        else:
            print("No cached team available, waiting for authentication to proceed.")
            main_process_task = None  # Will wait for team selection after auth

        # Step 5: Wait for authentication to finish in parallel
        user = await auth_task
        user_id = user.get('localId') or user.get('userId')

        # Step 6: If authentication fails, exit
        if not user or not user_id:
            print("Failed to authenticate user. Exiting...")
            if main_process_task:
                running = False  # Stop the ongoing main process
            return

        # Step 7: If authentication succeeds but no cached team, continue normally
        if not cache_team:
            # Load teams from Firestore after authentication succeeds
            teams = get_user_teams(user_id)
            if not teams:
                print("No teams found. Create a team in FCORE before starting this program.")
                return

            # Select the team after getting the list of teams
            selected_team = select_team(user_id, teams)
            print("Selected team: ", selected_team)

            # Start the main process with the selected team
            await start_main_process(user_id, selected_team, overlay, ocr_startup_task)
        else:
            # If authentication succeeds but we already started the main process, continue
            await main_process_task  # Wait for the optimistic process to finish

    except KeyboardInterrupt:
        print("\nCtrl+C detected. Exiting gracefully.")
        running = False

    finally:
        print("Cleaning up resources...")
        overlay.close()


if __name__ == "__main__":
    asyncio.run(main())
