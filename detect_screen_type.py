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
    extracted_text = []
    for line in result:
        for text_line in line:
            extracted_text.append(text_line[1][0])
    return " ".join(extracted_text)

def is_match_facts_screen(extracted_text):
    """
    Checks if the screenshot contains indicators of a 'Match Facts' screen.
    Looks for terms like 'Possession %', 'Shots', or 'Pass Accuracy %'.
    """
    if "Possession %" in extracted_text or "Shots" in extracted_text or "Pass Accuracy %" in extracted_text:
        return True
    return False

def is_performance_screen(extracted_text):
    """
    Checks if the screenshot contains indicators of a 'Performance' screen.
    Looks for player ratings (e.g., '6.1', '7.5') or player positions (e.g., 'RB', 'LCM').
    """
    rating_pattern = r'\b\d\.\d\b'  # Regular expression to find ratings like '6.1', '7.5'
    
    ratings_found = re.findall(rating_pattern, extracted_text)
    if ratings_found:
        return True
    
    positions = ["RB", "LCM", "RM", "CB", "RW", "LW", "ST", "CM", "GK"]  # Player positions
    for position in positions:
        if position in extracted_text:
            return True

    return False

def is_sim_match_facts_screen(extracted_text):
    """
    Checks if the screenshot contains indicators of a 'Sim Match Facts' screen.
    Add specific terms or indicators that appear in the simulated match facts screen.
    """
    # Placeholder check: Replace with actual indicators specific to sim match facts
    if "Sim Possession %" in extracted_text or "Sim Shots" in extracted_text:
        return True
    return False

def is_sim_performance_screen(extracted_text):
    """
    Checks if the screenshot contains indicators of a 'Sim Performance' screen.
    Add specific terms or indicators that appear in the simulated performance screen.
    """
    # Placeholder check: Replace with actual indicators specific to sim performance
    sim_rating_pattern = r'\bSim\d\.\d\b'  # Simulated ratings, just as an example
    sim_ratings_found = re.findall(sim_rating_pattern, extracted_text)
    
    positions = ["RB", "LCM", "RM", "CB", "RW", "LW", "ST", "CM", "GK"]  # Player positions
    if sim_ratings_found or any(position in extracted_text for position in positions):
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

    extracted_text = extract_text_from_image(image_path)

    if is_match_facts_screen(extracted_text):
        return "match_facts"
    elif is_performance_screen(extracted_text):
        return "player_performance"
    elif is_sim_match_facts_screen(extracted_text):
        return "sim_match_facts"
    elif is_sim_performance_screen(extracted_text):
        return "sim_player_performance"
    else:
        return "unknown"
