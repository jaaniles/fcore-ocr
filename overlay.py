import ctypes
import ctypes.wintypes
import win32gui
import win32con
import win32api
import threading
from time import time

user32 = ctypes.windll.user32

WS_EX_LAYERED = 0x80000
WS_EX_TRANSPARENT = 0x20
WS_EX_TOPMOST = 0x00000008
HWND_TOPMOST = -1

# Colors and transparency
TRANSPARENT_COLOR = 0x000000  # Fully transparent color
BACKGROUND_COLOR = win32api.RGB(0, 0, 0)  # Black semi-transparent background
TRANSPARENCY_LEVEL = 180  # Background transparency (0-255)

PADDING = 20
FONT_SIZE = 24 
WINDOW_WIDTH = 600  
WINDOW_HEIGHT = 300 

# Define the RECT structure used in the overlay
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]

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
        self.width = WINDOW_WIDTH
        self.height = WINDOW_HEIGHT
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
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 0, 0, 0, 0, win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)

        # Run the message loop
        win32gui.PumpMessages()

    def show(self, text, duration=None):
        """Show the overlay with the given text and auto-hide after duration."""
        with self._text_lock:
            # Determine if text is a string or a list of dicts for table formatting
            if isinstance(text, list):
                self.text = self.format_text_as_table(text)  # Format text into a table
            else:
                self.text = text  # Display the simple string text directly

            self.duration = duration
            self.start_time = time() if duration else None
            self._update_text = True

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

    def format_text_as_table(self, data):
        """Format the given text (list of dicts) into a table-like structure."""
        table = ""
        headers = "Player Name".ljust(30) + "Rating".rjust(10) + "\n"
        table += headers
        table += "-" * len(headers) + "\n"

        # Simulate table structure
        for row in data:
            player = row.get("player", "").ljust(30)
            rating = str(row.get("rating", "")).rjust(10)
            table += f"{player}{rating}\n"
        return table

    def on_paint(self, hwnd):
        hdc, ps = win32gui.BeginPaint(hwnd)

        with self._text_lock:
            text = self.text

        # Define RECT structure for measurement
        rect = RECT()
        rect.left = PADDING
        rect.top = PADDING
        rect.right = rect.left + WINDOW_WIDTH  # Set width
        rect.bottom = rect.top + WINDOW_HEIGHT  # Set height

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
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, 10, 10, self.width, self.height, win32con.SWP_NOZORDER)

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

        # Draw the text with increased font size
        format_flags = win32con.DT_LEFT | win32con.DT_WORDBREAK
        DrawTextW(hdc, text, -1, ctypes.byref(rect_draw), format_flags)

        win32gui.EndPaint(hwnd, ps)

    def close(self):
        """Close the overlay window."""
        win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)
        self.thread.join()
