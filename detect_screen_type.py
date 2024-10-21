from paddleocr import PaddleOCR
import os
import re

# Initialize PaddleOCR globally
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)

def extract_text_from_image(image_path):
    """
    Extracts text from the given image using PaddleOCR.
    """
    result = ocr.ocr(image_path, cls=True)

    if result is None:
        return []
    elif len(result) == 0:
        return []

    ocr_output = []
    for line in result:
        if len(line) == 0:
            continue

        for text_line in line:
            ocr_output.append(text_line[1][0])
    return " ".join(ocr_output)

def is_match_facts_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Match Facts' screen.
    Looks for terms like 'Possession %', 'Shots', or 'Pass Accuracy %'.
    """
    if "Possession %" in ocr_output or "Shots" in ocr_output or "Pass Accuracy %" in ocr_output:
        return True
    return False

def is_performance_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Performance' screen.
    Looks for player ratings (e.g., '6.1', '7.5') or player positions (e.g., 'RB', 'LCM').
    """
    rating_pattern = r'\b\d\.\d\b'  # Regular expression to find ratings like '6.1', '7.5'
    ratings_found = re.findall(rating_pattern, ocr_output)
    #if ratings_found:
    #    return True
    
    positions = ["RB", "LCM", "RM", "CB", "RW", "LW", "ST", "CM", "GK"]  # Player positions
    positions_found = False
    for position in positions:
        if position in ocr_output:
            positions_found = True

    return ratings_found and positions_found

def is_sim_match_facts_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Sim Match Facts' screen.
    Add specific terms or indicators that appear in the simulated match facts screen.
    """
    # Placeholder check: Replace with actual indicators specific to sim match facts
    if "Sim Possession %" in ocr_output or "Sim Shots" in ocr_output:
        return True
    return False

def is_sim_performance_screen(ocr_output):
    """
    Checks if the screenshot contains indicators of a 'Sim Performance' screen.
    Add specific terms or indicators that appear in the simulated performance screen.
    """
    # Placeholder check: Replace with actual indicators specific to sim performance
    sim_rating_pattern = r'\bSim\d\.\d\b'  # Simulated ratings, just as an example
    sim_ratings_found = re.findall(sim_rating_pattern, ocr_output)
    
    positions = ["RB", "LCM", "RM", "CB", "RW", "LW", "ST", "CM", "GK"]  # Player positions
    if sim_ratings_found or any(position in ocr_output for position in positions):
        return True
    
    return False

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
    Supports detection of:
    - match_facts
    - performance
    - sim_match_facts
    - sim_performance

    Returns the detected screen type as a string or 'unknown'.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"{image_path} does not exist.")

    ocr_output = extract_text_from_image(image_path)

    if is_match_facts_screen(ocr_output):
        return "match_facts"
    elif is_performance_screen(ocr_output):
        return "player_performance"
    elif is_sim_match_facts_screen(ocr_output):
        return "sim_match_facts"
    elif is_sim_performance_screen(ocr_output):
        return "sim_player_performance"
    elif is_pre_match_screen(ocr_output):
        return "pre_match"
    else:
        return "unknown"
