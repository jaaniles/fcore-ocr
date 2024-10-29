import os
import re
import cv2
from image_processing import upscale_image
from ocr import annotate_ocr_results, extract_text_from_image
from positions import is_position_found
from screens.screen_types import (
    MATCH_FACTS, PLAYER_PERFORMANCE, PLAYER_PERFORMANCE_EXTENDED, PRE_MATCH,
    SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH,
    SIM_PRE_MATCH
)

DEBUG = True

# Keyword configuration for each screen type
SCREEN_KEYWORDS = {
    MATCH_FACTS: {
        "required": {"performance", "highlighter"},
        "optional": {"shots", "passes", "attempted", "accuracy", "tackles", "possession"},
        "failable": {"fitness", "ratings", "stats", "gameplan"},
    },
    PLAYER_PERFORMANCE: {
        "failable": {"fitness", "ratings", "stats", "gameplan", "overall", "summary"},
        "pattern": r'\b\d\.\d\b'  # Regex for player ratings like "6.1" or "7.5"
    },
    PLAYER_PERFORMANCE_EXTENDED: {
        "required": {"player", "performance", "summary", "overall", "position"},
        "failable": {"fitness", "ratings", "stats", "gameplan"},
    },
    SIM_MATCH_FACTS: {
        "required": {"fitness", "ratings", "stats", "gameplan", "possession", "shots", "chances"},
    },
    SIM_MATCH_PERFORMANCE: {
        "required": {"fitness", "ratings", "stats", "gameplan", "starting", "bench"},
    },
    SIM_MATCH_PERFORMANCE_BENCH: {
        "required": {"fitness", "ratings", "stats", "gameplan", "bench"},
    },
    PRE_MATCH: {
        "required": {"play", "match", "tactical", "view", "highlights", "customise"},
    },
    SIM_PRE_MATCH: {
        "required": {"play", "match", "tactical", "view", "highlights", "customise"},
        "optional": {"simulate"},  # Assuming "simulate" would be present in SIM_PRE_MATCH
    }
}

def preprocess_ocr_output(ocr_output):
    return set(ocr_output.lower().split())

async def detect_screen_type(screenshot_path):
    if not os.path.exists(screenshot_path):
        raise FileNotFoundError(f"{screenshot_path} does not exist.")

    # Extract OCR data from the image
    ocr_output, ocr_result = await extract_text_from_image(screenshot_path)
    
    if DEBUG:
        image = cv2.imread(screenshot_path)
        annotate_ocr_results(image, "./images/debug", ocr_result)

    # Preprocess OCR output to a set of lowercased words
    ocr_output_words = preprocess_ocr_output(ocr_output)

    # Check each screen type's configuration for a match
    for screen_type, keywords in SCREEN_KEYWORDS.items():
        if is_screen_type(ocr_output_words, screen_type, keywords):
            return screen_type

    # If no match found, return 'unknown'
    return "unknown"

def is_screen_type(ocr_output_words, screen_type, keywords):
    """Checks if OCR output matches the specified screen type based on keywords."""
    required = keywords.get("required", set())
    optional = keywords.get("optional", set())
    failable = keywords.get("failable", set())
    pattern = keywords.get("pattern")

    # If any failable keyword is present, this is not a match
    if failable and failable.intersection(ocr_output_words):
        return False

    # Ensure all required keywords are present
    if required and not required.issubset(ocr_output_words):
        return False

    # Check for an optional pattern match (like player rating)
    if pattern and not re.search(pattern, " ".join(ocr_output_words)):
        return False

    # Optional keywords enhance confidence but are not necessary
    return True