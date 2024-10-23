import os
import re
from ocr import extract_text_from_image
from positions import is_position_found, positions

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
    Generalized helper to check if OCR output contains required, optional, and failable keywords.
    
    Parameters:
        ocr_output_words (set): Preprocessed set of words from the OCR output.
        required_keywords (set): Keywords that must be present.
        optional_keywords (set): Optional keywords that, if present, return True.
        failable_keywords (set): Keywords that, if present, fail the check and return False.
        
    Returns:
        bool: True if the screen matches the expected keywords, False otherwise.
    """
    # Check for failable keywords
    if failable_keywords and any(word in ocr_output_words for word in failable_keywords):
        return False

    # Check if all required keywords are present
    if not all(word in ocr_output_words for word in required_keywords):
        return False

    # If optional keywords are present, return True
    if optional_keywords and any(word in ocr_output_words for word in optional_keywords):
        return True

    return True

def is_match_facts_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of a 'Match Facts' screen.
    """
    required_keywords = {"Performance", "Match Facts"}
    optional_keywords = {"shots", "passes", "attempted", "accuracy", "tackles", "possession"}
    failable_keywords = {"fitness", "ratings", "stats", "gameplan"}
    
    positions_found = is_position_found(ocr_output_words)

    if positions_found:
        return False

    return check_keywords(ocr_output_words, required_keywords, optional_keywords, failable_keywords)

def is_performance_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of a 'Performance' screen.
    Looks for player ratings (e.g., '6.1', '7.5') or player positions (e.g., 'RB', 'LCM').
    """
    failable_keywords = {"fitness", "ratings", "stats", "gameplan", "overall", "summary"}
    
    # Check if any failable keyword exists
    if any(word in ocr_output_words for word in failable_keywords):
        return False
    
    print(ocr_output_words)

    # Find ratings using pre-compiled regex
    ratings_found = rating_pattern.findall(" ".join(ocr_output_words))
    
    # Check for player positions
    # Check for player positions
    positions_found = is_position_found(ocr_output_words)

    print(ratings_found, positions_found)

    return bool(ratings_found) and positions_found

def is_performance_extended_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of an 'Extended Performance' screen.
    """
    required_keywords = {"player", "performance", "summary", "overall", "position"}
    failable_keywords = {"fitness", "ratings", "stats", "gameplan"}
    
    return check_keywords(ocr_output_words, required_keywords, failable_keywords=failable_keywords)

def is_sim_match_facts_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of a 'Sim Match Facts' screen.
    """
    print(ocr_output_words)

    required_keywords = {"fitness", "ratings", "stats", "gameplan", "possession", "shots", "chances"}
    
    return check_keywords(ocr_output_words, required_keywords)

def is_sim_match_performance_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of a 'Sim Match Player Performance' screen.
    """
    required_keywords = {"fitness", "ratings", "stats", "gameplan", "starting", "bench"}
    
    return check_keywords(ocr_output_words, required_keywords)

def is_pre_match_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of a 'Pre-Match' screen.
    """
    # Replace with actual indicators specific to the pre-match screen
    required_keywords = {"play", "match", "tactical", "view", "highlights", "customise"}
    
    return check_keywords(ocr_output_words, required_keywords)

def is_match_facts_extended_screen(ocr_output_words):
    """
    Checks if the screenshot contains indicators of an 'Extended Match Facts' screen.
    """
    required_keywords = {"summary", "possession", "shooting", "passing", "defending", "events"}

    return check_keywords(ocr_output_words, required_keywords)

async def detect_screen_type(image_path, ocr):
    """
    Detects the type of screen in the screenshot.
    Returns the detected screen type as a string or 'unknown'.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} does not exist.")

    ocr_output = await extract_text_from_image(image_path, ocr)
    
    # Preprocess OCR output to a set of lowercased words
    ocr_output_words = preprocess_ocr_output(ocr_output)

    if is_match_facts_screen(ocr_output_words):
        return "match_facts"
    elif is_performance_screen(ocr_output_words):
        return "player_performance"
    elif is_sim_match_facts_screen(ocr_output_words):
        return "sim_match_facts"
    elif is_sim_match_performance_screen(ocr_output_words):
        return "sim_match_performance"
    elif is_pre_match_screen(ocr_output_words):
        return "pre_match"
    elif is_performance_extended_screen(ocr_output_words):
        return "player_performance_extended"
    elif is_match_facts_extended_screen(ocr_output_words):
        return "match_facts_extended"
    else:
        return "unknown"
