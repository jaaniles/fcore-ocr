import os
import re

import cv2
from image_processing import upscale_image
from ocr import annotate_ocr_results, extract_text_from_image
from positions import is_position_found
from screens.check_is_regular_match import check_is_regular_match
from screens.screen_types import MATCH_FACTS, PLAYER_PERFORMANCE, PLAYER_PERFORMANCE_EXTENDED, PRE_MATCH, SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH, SIM_PRE_MATCH, SQUAD_ATTRIBUTES, SQUAD_FINANCIAL, SQUAD_STATS

DEBUG = True
# Pre-compiled regex for rating detection
rating_pattern = re.compile(r'\b\d\.\d\b')

def preprocess_ocr_output(ocr_output):
    """
    Preprocess the OCR output by lowercasing and splitting into words.
    
    Parameters:
        ocr_output (str): The OCR output text.
        
    Returns:
        set: A set of lowercased words from the OCR output.
    """
    return set(ocr_output.lower().split())

def check_keywords(ocr_output_words, required_keywords, optional_keywords=None, failable_keywords=None):
    """
    Checks OCR output against required, optional, and failable keywords, returning matching details.
    
    Parameters:
        ocr_output_words (set): Set of words from OCR output.
        required_keywords (set): Keywords that must be present.
        optional_keywords (set): Keywords that are optional.
        failable_keywords (set): Keywords that should not be present.

    Returns:
        tuple: (is_match, all_found_keywords, all_missing_keywords)
            - found_keywords (set): All required and optional keywords found in the OCR output.
            - missing_keywords (set): All required keywords missing from the OCR output.
            - is_match (bool): True if all required keywords are present, no failable keywords are found, and any optional keywords exist if provided.
    """
    found_keywords = set()
    missing_keywords = set(required_keywords)  # Start with all required keywords as missing

    # Check for failable keywords
    if failable_keywords and any(word in ocr_output_words for word in failable_keywords):
        return set(),missing_keywords, False

    # Find required keywords that are present
    found_keywords.update(word for word in required_keywords if word in ocr_output_words)
    missing_keywords.difference_update(found_keywords)  # Remove found required keywords

    # Check if all required keywords are met
    is_match = not missing_keywords

    # Find optional keywords if required keywords are matched
    if is_match and optional_keywords:
        found_keywords.update(word for word in optional_keywords if word in ocr_output_words)
        # If any optional keyword is found, it confirms a match
        is_match = any(word in ocr_output_words for word in optional_keywords) if optional_keywords else is_match

    return is_match, found_keywords, missing_keywords

def is_match_facts_screen(ocr_output_words):
    required_keywords = {"performance", "highlighter"}
    optional_keywords = {"shots", "passes", "attempted", "accuracy", "tackles", "possession"}
    failable_keywords = {"fitness", "ratings", "stats", "gameplan"}
    
    positions_found = is_position_found(ocr_output_words)

    if positions_found:
        return False
    
    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords, optional_keywords, failable_keywords)

    return is_screen

def is_performance_screen(ocr_output_words):
    """
    Looks for player ratings (e.g., '6.1', '7.5') or player positions (e.g., 'RB', 'LCM').
    """
    failable_keywords = {"fitness", "ratings", "stats", "gameplan", "overall", "summary"}
    
    # Check if any failable keyword exists
    if any(word in ocr_output_words for word in failable_keywords):
        return False
    
    # Find ratings using pre-compiled regex
    ratings_found = rating_pattern.findall(" ".join(ocr_output_words))
    
    # Check for player positions
    # Check for player positions
    positions_found = is_position_found(ocr_output_words)

    return bool(ratings_found) and positions_found

def is_performance_extended_screen(ocr_output_words):
    required_keywords = {"player", "performance", "summary", "overall", "position"}
    failable_keywords = {"fitness", "ratings", "stats", "gameplan"}
    
    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords, failable_keywords)

    return is_screen

def is_sim_match_facts_screen(ocr_output_words):
    required_keywords = {"fitness", "ratings", "stats", "gameplan", "possession", "shots", "chances"}
    
    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)

    return is_screen

def is_sim_match_performance_screen(ocr_output_words):
    required_keywords = {"fitness", "ratings", "stats", "gameplan", "starting", "bench"}
    
    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)

    return is_screen

def is_pre_match_screen(ocr_output_words):
    # Replace with actual indicators specific to the pre-match screen
    required_keywords = {"play", "match", "tactical", "view", "highlights", "customise"}
    
    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)

    return is_screen

def is_match_facts_extended_screen(ocr_output_words):
    required_keywords = {"summary", "possession", "shooting", "passing", "defending", "events"}

    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)

    return is_screen

def is_squad_financial_screen(ocr_output_words):
    required_keywords = {"status", "stats", "attributes", "financial", "market", "value"}

    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)


    return is_screen

def is_squad_attributes_screen(ocr_output_words):
    required_keywords = {"status", "stats", "attributes", "financial", "weak", "foot", "skill", "moves"}

    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)

    return is_screen

def is_squad_stats_screen(ocr_output_words):
    required_keywords = {"status", "stats", "attributes", "financial", "clean", "goals", "competitions"}

    is_screen, _, _ = check_keywords(ocr_output_words, required_keywords)

    return is_screen

async def detect_screen_type(screenshot_path):
    """
    Detects the type of screen in the screenshot.
    Returns the detected screen type as a string or 'unknown'.
    """
    if not os.path.exists(screenshot_path):
        raise FileNotFoundError(f"{screenshot_path} does not exist.")

    ocr_output, ocr_result = await extract_text_from_image(screenshot_path)
    
    if DEBUG:
        image = cv2.imread(screenshot_path)
        annotate_ocr_results(image, "./images/debug", ocr_result)

    # Preprocess OCR output to a set of lowercased words
    ocr_output_words = preprocess_ocr_output(ocr_output)

    if is_match_facts_screen(ocr_output_words):
        return MATCH_FACTS
    
    elif is_performance_screen(ocr_output_words):
        return PLAYER_PERFORMANCE
    
    elif is_sim_match_facts_screen(ocr_output_words):
        return SIM_MATCH_FACTS
    
    elif is_sim_match_performance_screen(ocr_output_words):
        is_bench_view = "n/a" in ocr_output_words

        if is_bench_view:
            return SIM_MATCH_PERFORMANCE_BENCH
        else:
            return SIM_MATCH_PERFORMANCE
    
    # Check if user is intending to play the match regularly or simulate it
    elif is_pre_match_screen(ocr_output_words):
        image = cv2.imread(screenshot_path)
        upscaled_image = upscale_image(image)

        is_regular_match = await check_is_regular_match(upscaled_image)

        if is_regular_match:
            return PRE_MATCH
        else:
            return SIM_PRE_MATCH

    elif is_performance_extended_screen(ocr_output_words):
        return PLAYER_PERFORMANCE_EXTENDED
    
    elif is_squad_financial_screen(ocr_output_words):
        return SQUAD_FINANCIAL
    
    elif is_squad_attributes_screen(ocr_output_words):
        return SQUAD_ATTRIBUTES
    
    elif is_squad_stats_screen(ocr_output_words):
        return SQUAD_STATS

    else:
        return "unknown"
