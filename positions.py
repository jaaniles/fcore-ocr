import re

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