import ctypes
import ctypes.wintypes
import win32gui
import win32con
import win32api
import threading
from time import time

# Load user32.dll for SetTimer and KillTimer
user32 = ctypes.windll.user32

# Constants for window style
WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOPMOST = 0x00000008
HWND_TOPMOST = -1

# Colors and transparency
TRANSPARENT_COLOR = 0x000000  # Fully transparent color
BACKGROUND_COLOR = win32api.RGB(0, 0, 0)  # Black semi-transparent background
TRANSPARENCY_LEVEL = 180  # Background transparency (0-255)

# Padding around text
PADDING = 10

# Define the RECT structure used in the overlay
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

# Define the callback function for EnumDisplayMonitors
MonitorEnumProc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.wintypes.HMONITOR, ctypes.wintypes.HDC, ctypes.POINTER(RECT), ctypes.wintypes.LPARAM)

def get_monitor_positions():
    """Get the positions of all monitors"""
    monitor_positions = []

    def monitor_enum_proc(hMonitor, hdcMonitor, lprcMonitor, dwData):
        rct = lprcMonitor.contents
        monitor_positions.append((rct.left, rct.top, rct.right, rct.bottom))
        return 1  # Continue enumeration

    # Call EnumDisplayMonitors using ctypes
    user32.EnumDisplayMonitors(None, None, MonitorEnumProc(monitor_enum_proc), 0)
    return monitor_positions

def get_secondary_monitor_position():
    """Get the position of the second monitor"""
    monitors = get_monitor_positions()
    if len(monitors) > 1:
        return monitors[1][0], monitors[1][1]  # Get the second monitor position
    else:
        print("Only one monitor detected. Positioning on primary screen.")
        return monitors[0][0], monitors[0][1]  # Default to the first monitor if only one is available

def position_overlay_on_second_screen(hwnd):
    """Position the overlay on the second monitor (or primary if only one exists)."""
    x, y = get_secondary_monitor_position()
    win32gui.SetWindowPos(hwnd, win32con.HWND_TOPMOST, x, y, 300, 100, win32con.SWP_SHOWWINDOW)

# OverlayWindow class
class OverlayWindow:
    def __init__(self):
        self.hwnd = None
        self.text = "Overlay Text"
        self.duration = None
        self.start_time = None

        # Variables to synchronize between threads
        self._text_lock = threading.Lock()
        self._update_text = False

        # Start the thread that runs the window
        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()

    def run(self):
        # Create and register window class in this thread
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.lpszClassName = 'OverlayWindowClass'
        wc.hInstance = win32api.GetModuleHandle(None)
        win32gui.RegisterClass(wc)

        # Create the window
        self.width = 300
        self.height = 100
        self.hwnd = win32gui.CreateWindowEx(
            WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOPMOST,
            wc.lpszClassName,
            "Overlay",
            win32con.WS_POPUP,
            10, 10, self.width, self.height,
            None, None, wc.hInstance, None
        )

        # Set window transparency
        win32gui.SetLayeredWindowAttributes(self.hwnd, TRANSPARENT_COLOR, TRANSPARENCY_LEVEL, win32con.LWA_ALPHA)
        # Force window to stay on top
        win32gui.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        # Run the message loop
        win32gui.PumpMessages()

    def show(self, text, duration=None):
        """Show the overlay with the given text and auto-hide after duration."""
        with self._text_lock:
            self.text = text
            self.duration = duration
            self.start_time = time() if duration else None
            self._update_text = True

        position_overlay_on_second_screen(self.hwnd)

        # Post a custom message to update the window
        win32gui.PostMessage(self.hwnd, win32con.WM_USER + 1, 0, 0)

        # Show the window
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)

        if self.duration:
            # Set a timer using ctypes (Windows API)
            user32.SetTimer(self.hwnd, 1, int(self.duration * 1000), None)
        else:
            # Kill any existing timer
            user32.KillTimer(self.hwnd, 1)

    def hide(self):
        """Hide the overlay window."""
        win32gui.ShowWindow(self.hwnd, win32con.SW_HIDE)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_PAINT:
            self.on_paint(hwnd)
            return 0
        elif msg == win32con.WM_TIMER:
            # Hide the window when the timer fires
            self.hide()
            user32.KillTimer(self.hwnd, 1)  # Kill the timer
            return 0
        elif msg == win32con.WM_USER + 1:
            # Custom message to update text
            win32gui.InvalidateRect(self.hwnd, None, True)
            return 0
        elif msg == win32con.WM_DESTROY:
            win32gui.PostQuitMessage(0)
            return 0
        else:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def on_paint(self, hwnd):
        hdc, ps = win32gui.BeginPaint(hwnd)

        with self._text_lock:
            text = self.text

        # Define RECT structure for measurement
        rect = RECT()
        rect.left = PADDING
        rect.top = PADDING
        rect.right = rect.left + 300  # Initial width
        rect.bottom = rect.top + 100  # Initial height

        # Set the format flags for text layout
        format_flags = win32con.DT_LEFT | win32con.DT_WORDBREAK | win32con.DT_CALCRECT

        # Measure the text rectangle (this updates rect)
        DrawTextW = ctypes.windll.user32.DrawTextW
        DrawTextW.argtypes = [
            ctypes.wintypes.HDC,
            ctypes.c_wchar_p,
            ctypes.c_int,
            ctypes.POINTER(RECT),
            ctypes.c_uint
        ]
        DrawTextW.restype = ctypes.c_int

        DrawTextW(hdc, text, -1, ctypes.byref(rect), format_flags)

        # Adjust the window size based on the measured rectangle
        self.width = rect.right - rect.left + PADDING * 2
        self.height = rect.bottom - rect.top + PADDING * 2
        win32gui.SetWindowPos(self.hwnd, HWND_TOPMOST, 10, 10, self.width, self.height, win32con.SWP_NOZORDER)

        # Draw the semi-transparent background behind the text
        background_rect = (0, 0, self.width, self.height)
        brush = win32gui.CreateSolidBrush(BACKGROUND_COLOR)
        win32gui.FillRect(hdc, background_rect, brush)
        win32gui.DeleteObject(brush)

        # Prepare RECT for drawing text
        rect_draw = RECT()
        rect_draw.left = PADDING
        rect_draw.top = PADDING
        rect_draw.right = self.width - PADDING
        rect_draw.bottom = self.height - PADDING

        # Draw the text
        format_flags = win32con.DT_LEFT | win32con.DT_WORDBREAK
        DrawTextW(hdc, text, -1, ctypes.byref(rect_draw), format_flags)

        win32gui.EndPaint(hwnd, ps)

    def close(self):
        """Close the overlay window."""
        win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        self.thread.join()
