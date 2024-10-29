import re

from ocr import parse_ocr

positions = [
    "GK", "RB", "RWB", "LB", "LWB", "CB", "RCB", "LCB",
    "CDM", "CM", "LCM", "RCM", "CAM", "RM", "LM", "RW", "LW",
    "ST", "CF", "RS", "LS", "RF", "LF"
]

# Create a regular expression pattern to match the positions, allowing for surrounding characters
position_pattern = re.compile(r'\b(?:' + '|'.join(positions) + r')\b', re.IGNORECASE)

def is_position_found(ocr_output_words):
    """
    Checks if any player position is found in the OCR output using regular expressions.
    
    Parameters:
        ocr_output_words (set): Preprocessed set of words from the OCR output.
        
    Returns:
        bool: True if any position is found, False otherwise.
    """
    # Check each word in the OCR output against the position pattern
    return any(position_pattern.search(word) for word in ocr_output_words)

def find_position_from_ocr(ocr_output):
    """
    Finds the first player position in the OCR output using regex.

    Parameters:
        ocr_output (list): The OCR output from PaddleOCR containing groups of OCR items.
        
    Returns:
        str: The detected position if found, otherwise None.
    """
    # Combine all detected text elements into a single string
    combined_text = " ".join(text for _, text, _ in parse_ocr(ocr_output))

    # Search for the position using regex
    match = position_pattern.search(combined_text)
    
    return match.group(0) if match else None