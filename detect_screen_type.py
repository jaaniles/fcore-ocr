import difflib
import os
import re

from ocr import extract_text_from_image, paddleocr


def fuzzy_match(ocr_output, keyword, cutoff=0.8):
    """
    Check if a keyword is present in the OCR output using fuzzy matching.
    
    Parameters:
        ocr_output (str): The OCR output text.
        keyword (str): The keyword to search for.
        cutoff (float): The matching accuracy threshold (0 to 1).
        
    Returns:
        bool: True if the keyword is found with sufficient similarity, False otherwise.
    """
    return difflib.get_close_matches(keyword, ocr_output.split(), cutoff=cutoff)

def is_match_facts_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Match Facts' screen.
    """
    all_keywords = ["Match Facts"]
    any_keywords = ["Shots", "Passes Attempted", "Pass Accuracy %", "Tackles", "Possession"]
    failable_keywords = ["Fitness", "Ratings", "Stats", "Gameplan"]

    # Step 1: Check if any of the failable keywords are present, return False if found
    for word in failable_keywords:
        if fuzzy_match(ocr_output, word):
            return False

    # Step 2: Check if all the mandatory keywords are present, return False if any are missing
    for word in all_keywords:
        if not fuzzy_match(ocr_output, word):
            return False

    # Step 3: Check if any of the optional keywords are present, return True if found
    for word in any_keywords:
        if fuzzy_match(ocr_output, word):
            return True

    # If no matches found for optional keywords, return False
    return False

def is_performance_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Performance' screen.
    Looks for player ratings (e.g., '6.1', '7.5') or player positions (e.g., 'RB', 'LCM').
    """
    failable_keywords = ["Fitness", "Ratings", "Stats", "Gameplan", "Overall Position", "Summary"]
    
    for word in failable_keywords:
        if fuzzy_match(ocr_output, word):
            return False

    rating_pattern = r'\b\d\.\d\b'  # Regular expression to find ratings like '6.1', '7.5'
    ratings_found = re.findall(rating_pattern, ocr_output)
    
    positions = ["RB", "LCM", "RM", "CB", "RW", "LW", "ST", "CM", "GK"]
    positions_found = False
    for position in positions:
        if fuzzy_match(ocr_output, position):
            positions_found = True

    return bool(ratings_found) and positions_found

def is_performance_extended_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of an 'Extended Performance' screen.
    """

    # Keywords that must be present
    all_keywords = ["Player Performance", "Summary", "OVERALL POSITION"]
    # Keywords that will fail the ckec
    failableKeywords = ["Fitness", "Ratings", "Stats", "Gameplan"]
    for word in failableKeywords:
        if word in ocr_output:
            return False

    # Check if all the mandatory keywords are present, return False if any are missing
    for word in all_keywords:
        if word not in ocr_output:
            return False
        
    return True

def is_sim_match_facts_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Sim Match Facts' screen.
    """

    # All of these words need to be present    
    keywords = ["Fitness", "Ratings", "Stats", "Gameplan", "Possession", "Shots", "Chances"]
    # Convert the OCR output to a single string for easy search

    # Check if each keyword from the combined list is in the OCR text
    for word in keywords:
        if word not in ocr_output:
            return False

    return True


def is_sim_match_performance_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Sim Match Player Performance' screen.
    """
    # All of these words need to be present    
    keywords = ["Fitness", "Ratings", "Stats", "Gameplan", "Starting 11", "Bench"]

    # Check if each keyword from the combined list is in the OCR text
    for word in keywords:
        if word not in ocr_output:
            return False

    return True

def is_pre_match_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Pre-Match' screen.
    Add specific terms or indicators that appear in the pre-match screen.
    """
    # Placeholder check: Replace with actual indicators specific to pre-match
    if "Play Match" and "Tactical View" and "Play Highlights" and "Customise" in ocr_output:
        return True
    return False


def detect_screen_type(image_path):
    """
    Detects the type of screen in the screenshot.
    Returns the detected screen type as a string or 'unknown'.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} does not exist.")

    ocr_output = extract_text_from_image(image_path)

    print(ocr_output)

    if is_match_facts_screen(ocr_output):
        return "match_facts"
    elif is_performance_screen(ocr_output):
        return "player_performance"
    elif is_sim_match_facts_screen(ocr_output):
        return "sim_match_facts"
    elif is_sim_match_performance_screen(ocr_output):
        return "sim_match_performance"
    elif is_pre_match_screen(ocr_output):
        return "pre_match"
    elif is_performance_extended_screen(ocr_output):
        return "player_performance_extended"
    else:
        return "unknown"
