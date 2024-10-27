import cv2
import os
import numpy as np

# Paths to the playstyle templates
REGULAR_PLAYSTYLE_PATH = "assets/playstyles/regular"
GOLDEN_PLAYSTYLE_PATH = "assets/playstyles/golden"
GK_PLAYSTYLE_PATH = "assets/playstyles/goalkeeper"
GK_GOLDEN_PLAYSTYLE_PATH = "assets/playstyles/goalkeeper_golden"

THRESHOLD = 0.5  # Confidence threshold for a successful match

def load_templates(path):
    """Load all playstyle templates from the specified directory in grayscale."""
    templates = {}
    for filename in os.listdir(path):
        if filename.endswith(".png"):
            template_name = os.path.splitext(filename)[0]
            template_image = cv2.imread(os.path.join(path, filename), cv2.IMREAD_GRAYSCALE)
            templates[template_name] = template_image
    return templates

# Load templates once for each type of playstyle
REGULAR_TEMPLATES = load_templates(REGULAR_PLAYSTYLE_PATH)
GOLDEN_TEMPLATES = load_templates(GOLDEN_PLAYSTYLE_PATH)
GK_TEMPLATES = load_templates(GK_PLAYSTYLE_PATH)
GK_GOLDEN_TEMPLATES = load_templates(GK_GOLDEN_PLAYSTYLE_PATH)

def match_playstyle(cropped_image, is_gk=False):
    """
    Matches the cropped playstyle icon against stored templates based on the icon type (regular, golden, goalkeeper).
    
    Parameters:
        cropped_image (numpy.ndarray): The cropped playstyle icon from the player screen.
        is_gk (bool): True if the player is a goalkeeper, else False.

    Returns:
        best_match (str): The name of the best-matching template, or "none" if no match meets the threshold.
        best_confidence (float): The confidence score of the best match.
    """
    # Standard size for comparison
    TARGET_SIZE = (70, 70)

    # Resize cropped image to target size
    cropped_resized = cv2.resize(cropped_image, TARGET_SIZE, interpolation=cv2.INTER_AREA)

    # Determine if the playstyle is golden
    golden_playstyle = is_golden_playstyle(cropped_resized)
    
    # Choose the correct template set
    if is_gk and golden_playstyle:
        templates = GK_GOLDEN_TEMPLATES
    elif is_gk:
        templates = GK_TEMPLATES
    elif golden_playstyle:
        templates = GOLDEN_TEMPLATES
    else:
        templates = REGULAR_TEMPLATES

    # Convert to grayscale if not already
    if len(cropped_resized.shape) == 3 and cropped_resized.shape[2] == 3:
        cropped_gray = cv2.cvtColor(cropped_resized, cv2.COLOR_BGR2GRAY)
    else:
        cropped_gray = cropped_resized

    # Check average brightness to detect empty slots
    avg_brightness = np.mean(cropped_gray)
    
    if avg_brightness < 60:
        return "none", None

    best_match = "none"
    best_confidence = 0.0

    # Loop through each template and perform template matching
    for template_name, template_image in templates.items():
        # Resize template to target size for consistent matching
        resized_template = cv2.resize(template_image, TARGET_SIZE, interpolation=cv2.INTER_AREA)

        # Perform template matching
        result = cv2.matchTemplate(cropped_gray, resized_template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)

        # Track the best match if the new confidence score is higher
        if max_val > best_confidence:
            best_confidence = max_val
            best_match = template_name if max_val >= THRESHOLD else "none"

    return best_match, best_confidence

def is_golden_playstyle(cropped_image):
    """
    Detects if the given playstyle icon is golden or regular by analyzing shape and color.
    
    Parameters:
        cropped_image (numpy.ndarray): The cropped playstyle icon from the player screen.
    
    Returns:
        bool: True if the icon is golden, False if it is regular.
    """
    # Step 1: Check Color in HSV Space for Golden Hue
    hsv_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2HSV)
    
    # Define range for golden color (this range may need fine-tuning)
    lower_gold = np.array([15, 100, 100])  # Adjust hue range for golden color
    upper_gold = np.array([35, 255, 255])

    # Create mask to isolate golden color
    mask = cv2.inRange(hsv_image, lower_gold, upper_gold)
    golden_pixels = cv2.countNonZero(mask)

    # If there's a significant amount of golden color, we classify as golden
    if golden_pixels > 50:  # Threshold might need adjustment based on icon size
        return True

    # Step 2: Shape Analysis for Gem-like Structure
    # Convert to grayscale and find contours
    gray_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        # Approximate the contour to reduce number of points
        epsilon = 0.04 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Golden icon has more sides than the diamond, e.g., 5 or 6 sides vs 4 for diamond
        if len(approx) >= 5:
            return True

    return False
