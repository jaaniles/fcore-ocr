import os
import time

import cv2
from crop import crop_image
from ocr import extract_text_from_image
from save_image import save_image
from screens.screen_types import SQUAD_FINANCIAL, SQUAD_ATTRIBUTES, SQUAD_STATS

# Configuration for squad screen types
SQUAD_SCREEN_KEYWORDS = {
    SQUAD_FINANCIAL: {
        "required": {"value", "wage", "contract"},
    },
    SQUAD_ATTRIBUTES: {
        "required": {"ovr", "form", "plan"},
    },
    SQUAD_STATS: {
        "required": {"goals", "assists", "clean"},
    }
}

def preprocess_ocr_output(ocr_output):
    return set(ocr_output.lower().split())

async def detect_squad_screen_type(screenshot_path):
    """Detects the type of squad screen in the screenshot with optimized checks."""
    if not os.path.exists(screenshot_path):
        raise FileNotFoundError(f"{screenshot_path} does not exist.")
    
    image = cv2.imread(screenshot_path)

    # Crop small section which includes relevant keywords
    cropped_image = crop_image(image, (400, 225, 1750, 350))

    # Perform OCR on the full image
    ocr_output, _ = await extract_text_from_image(cropped_image)
    ocr_output_words = preprocess_ocr_output(ocr_output)

    # Start timing the screen type detection
    start_time = time.time()

    # Batch keyword matching: iterate over screen types and find first match
    for screen_type, keywords in SQUAD_SCREEN_KEYWORDS.items():
        if is_screen_type(ocr_output_words, keywords):
            check_time = time.time() - start_time
            print(f"Time taken for screen type check: {check_time:.4f} seconds")
            return screen_type

    # Measure and print the time taken if no match is found
    check_time = time.time() - start_time
    print(f"Time taken for screen type check (no match found): {check_time:.4f} seconds")
    return "unknown"

def is_screen_type(ocr_output_words, keywords):
    """Checks if OCR output matches a specific squad screen type based on keywords."""
    required = keywords.get("required", set())
    return required.issubset(ocr_output_words)
