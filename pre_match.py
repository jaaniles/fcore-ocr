from datetime import datetime
import os
import json
import pprint
import re
import cv2
import numpy as np
from crop import crop_area, crop_image
from image_processing import upscale_image

# Allow saving images for debugging purposes
DEBUG = True

PRE_MATCH_FOLDER = './screenshots/pre_match'
os.makedirs(PRE_MATCH_FOLDER, exist_ok=True)

def process_pre_match(screenshot_path, ocr):
    # Load the screenshot
    image = cv2.imread(screenshot_path)
    upscaled_image = upscale_image(image)

    # Define crop coordinates for match date and starting 11
    match_date_coords = (1840, 475, 3240, 620)
    starting_11_coords = (1720, 590, 3500, 1650)

    # Step 1: Crop relevant sections
    cropped_match_date = crop_image(upscaled_image, match_date_coords)
    cropped_starting_11 = crop_image(upscaled_image, starting_11_coords)
    processed_starting_11 = preprocess_starting_11_image(cropped_starting_11)

    # Cover a portion of the image where know irrelevant text will be
    # This will remove unnecessary text from the OCR results
    block_coords = (0, 1000, 375, 870)
    processed_starting_11 = cv2.rectangle(processed_starting_11, (block_coords[0], block_coords[1]), 
                                          (block_coords[2], block_coords[3]), (255, 255, 0), thickness=-1)

    # Step 3: Perform OCR on each cropped section
    match_date_result = ocr.ocr(cropped_match_date)
    starting_11_result = ocr.ocr(processed_starting_11)

    # Save cropped images for debugging
    if DEBUG:
        match_date_path = os.path.join(PRE_MATCH_FOLDER, "cropped_match_date.png")
        starting_11_path = os.path.join(PRE_MATCH_FOLDER, "cropped_starting_11.png")
        cv2.imwrite(match_date_path, cropped_match_date)
        cv2.imwrite(starting_11_path, processed_starting_11)
        annotate_ocr_results(processed_starting_11, starting_11_result)


    match_date = extract_match_date(match_date_result)
    starting_11 = extract_starting_11(starting_11_result, cropped_starting_11, ocr)
    pprint.pprint(starting_11)

    return {
        "match_date": match_date,
        "starting_11": starting_11,
    }

def annotate_ocr_results(image, ocr_results):
    """
    Annotate the image with bounding boxes around OCR results and save the annotated image.
    """
    # Step 4: Annotate the image with bounding boxes around recognized text
    for result in ocr_results:
        for line in result:
            bbox = line[0]  # Get bounding box coordinates
            # Draw a red bounding box around each OCR result
            cv2.rectangle(image, 
                          (int(bbox[0][0]), int(bbox[0][1])), 
                          (int(bbox[2][0]), int(bbox[2][1])), 
                          (0, 0, 255), 2)  # Red bounding box

    # Save the annotated image
    cv2.imwrite(os.path.join(PRE_MATCH_FOLDER, f"annotated_pre_match.png"), image)

def extract_starting_11(ocr_results, image, ocr):
    """
    Process the OCR results to extract player names and crop mood and player form symbols based on bounding boxes.
    """
    CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence level for valid OCR results
    players_info = [] 

    for result in ocr_results:
        for line in result:
            text = line[1][0]  # Extract recognized text (e.g., player name)
            confidence = line[1][1]
            bbox = line[0]  # Extract the bounding box (x, y) coordinates

            name = is_valid_player_name(text)
            if not name:
                continue
            elif confidence < CONFIDENCE_THRESHOLD:
                continue

            # Check if text contains a player name, and add 'is_captain' flag if the name starts with "c"
            player_name = name
            is_captain = False

            # Check for captain tag 
            # Case 1: "c " prefix ex. "c Ruibal"
            if player_name.startswith('c '):
                player_name = player_name[2:] # Remove the "c " prefix
                is_captain = True
            # Case 2: "c" prefix ex. "cRuibal"
            elif player_name[0] == 'c' and player_name[1].isupper():
                player_name = player_name[1:] # Remove the "c" prefix
                is_captain = True

            # Calculate the absolute center of the player name bounding box
            x1, y1 = int(bbox[0][0]), int(bbox[0][1])  # Top-left corner of the bounding box
            x2, y2 = int(bbox[2][0]), int(bbox[2][1])  # Bottom-right corner of the bounding box
            name_center_x = (x1 + x2) // 2
            name_center_y = (y1 + y2) // 2

            # Adjust the center X for captains to compensate for the "C" tag width
            CAPTAIN_OFFSET = -43
            if is_captain:
                name_center_x -= CAPTAIN_OFFSET // 2 

            # Crop mood
            mood_area = crop_area(image, name_center_x - 101, name_center_y - 128, 42, 42)
            # Detect mood color
            mood = detect_mood(mood_area)

            # Adjust name_center_x for short names
            player_form_area_offset = name_center_x + 40
            if len(player_name) < 5:   
                player_form_area_offset += 20

            # Crop player form
            player_form_area = crop_area(image, player_form_area_offset, name_center_y - 121, 75, 40)
            # Preprocess for better OCR results
            processed_player_form, isPositive = preprocess_player_form_image(player_form_area)
            # Perform OCR 
            player_form_result = ocr.ocr(processed_player_form)  # Perform OCR on the form area

            print(player_name, player_form_result)
            

            player_form_value = process_player_form_value(player_form_result, isPositive)

            if DEBUG:   
                # Save image for debugging
                player_form_path = os.path.join(PRE_MATCH_FOLDER, f"form_{player_name}.png")
                cv2.imwrite(player_form_path, processed_player_form)
                mood_path = os.path.join(PRE_MATCH_FOLDER, f"mood_{player_name}.png")
                cv2.imwrite(mood_path, mood_area)

            # Append player info with relevant data
            player_info = {
                "name": player_name,
                "mood": mood,  
                "form": player_form_value  
            }
            if is_captain:
                player_info["is_captain"] = True

            players_info.append(player_info)

    return players_info


def extract_match_date(ocr_output):
    """
    Extract the match date from OCR output and convert it to datetime format.
    """
    if not isinstance(ocr_output, list):
        return None

    # Flatten the OCR results list
    flat_ocr = [item[1][0] for line in ocr_output for item in line if item and item[1]]

    # Search for the line containing "Referee" and extract the date part
    for text in flat_ocr:
        if "Referee" in text:
            date_text = text.split('Referee')[0]

            # Find the date pattern in the form of "22 August 2026"
            match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_text)
            if match:
                day, month, year = match.groups()

                try:
                    # Convert month name to number and construct date
                    month_number = datetime.strptime(month, "%B").month
                    match_date = datetime(int(year), int(month_number), int(day))

                    # Return the formatted date
                    return match_date.strftime('%d.%m.%Y')
                except ValueError:
                    return None

    return None  # No date found

def is_form_value_positive(image):
    """
    Analyze the color information to determine if the form is positive (green) or negative (red).
    """
    # Convert image to HSV for better color detection
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Define color ranges for green and red in HSV space
    green_lower = (35, 50, 50)
    green_upper = (85, 255, 255)

    # Red has two ranges in the HSV space (because hue wraps around)
    red_lower1 = (0, 50, 50)
    red_upper1 = (10, 255, 255)
    red_lower2 = (170, 50, 50)
    red_upper2 = (180, 255, 255)

    # Create masks for the green and red colors
    green_mask = cv2.inRange(hsv_image, green_lower, green_upper)
    red_mask1 = cv2.inRange(hsv_image, red_lower1, red_upper1)
    red_mask2 = cv2.inRange(hsv_image, red_lower2, red_upper2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # Count the number of green and red pixels
    green_pixels = cv2.countNonZero(green_mask)
    red_pixels = cv2.countNonZero(red_mask)

    # If there are more red pixels than green, it's negative; otherwise, it's positive
    if red_pixels > green_pixels:
        return False  # Negative
    elif green_pixels > red_pixels:
        return True  # Positive

    # If neither color is detected, return None
    return None

def process_player_form_value(ocr_result, isPositive):
    """
    Clean the OCR result for the form value, ensuring it's a valid number.
    Combine the OCR result with whether the form value is positive.
    Return the value as a string with either '+' or '-' sign.
    """
    if ocr_result and ocr_result[0]:
        # Extract the OCR-detected text
        raw_text_list = [item[1][0] for item in ocr_result[0]]  # Extract all texts from OCR output
        raw_text = ''.join(raw_text_list).strip()  # Join all texts and strip spaces
        
        # Strip non-digit characters
        cleaned_text = ''.join(filter(str.isdigit, raw_text))
        
        # Ensure that the cleaned text contains a valid number
        if cleaned_text:
            try:
                player_form_value = int(cleaned_text)
                # Return the value as a string with the appropriate sign
                if not isPositive:
                    return f"-{player_form_value}"
                return f"+{player_form_value}"
            except ValueError:
                return None  # If OCR result is not a valid number, return None
    return None

def detect_mood(mood_image):
    """
    Analyze the mood image to determine the mood color.
    This function uses color detection to identify the mood (green, cyan, yellow, red).
    """
    if mood_image is None or mood_image.size == 0:
        print("Empty mood image detected. Skipping color detection.")
        return None

    hsv_image = cv2.cvtColor(mood_image, cv2.COLOR_BGR2HSV)
    
    # Define color ranges in HSV space for different moods
    excited_green_lower = (40, 50, 50)  # Green (Excited)
    excited_green_upper = (75, 255, 255)
    happy_cyan_lower = (85, 50, 50)  # Cyan-Blue (Happy)
    happy_cyan_upper = (105, 255, 255)
    neutral_yellow_lower = (20, 50, 50)  # Yellow (Neutral)
    neutral_yellow_upper = (30, 255, 255)
    bad_red_lower1 = (0, 50, 50)  # Red (Bad) - lower range
    bad_red_upper1 = (10, 255, 255)
    bad_red_lower2 = (170, 50, 50)  # Red (Bad) - upper range
    bad_red_upper2 = (180, 255, 255)
    
    # Create masks for different colors
    green_mask = cv2.inRange(hsv_image, excited_green_lower, excited_green_upper)
    cyan_mask = cv2.inRange(hsv_image, happy_cyan_lower, happy_cyan_upper)
    yellow_mask = cv2.inRange(hsv_image, neutral_yellow_lower, neutral_yellow_upper)
    red_mask1 = cv2.inRange(hsv_image, bad_red_lower1, bad_red_upper1)
    red_mask2 = cv2.inRange(hsv_image, bad_red_lower2, bad_red_upper2)
    red_mask = cv2.bitwise_or(red_mask1, red_mask2)

    # Check for color presence and return mood
    if cv2.countNonZero(green_mask) > 0:
        return "excited"
    elif cv2.countNonZero(cyan_mask) > 0:
        return "happy"
    elif cv2.countNonZero(yellow_mask) > 0:
        return "neutral"
    elif cv2.countNonZero(red_mask) > 0:
        return "bad"
    
    return "unknown"

def is_valid_player_name(text):
    print("Is it valid?", text)

    """Check if the detected text is a valid player name."""
    # Strip leading and trailing whitespaces
    text = text.strip()

    # Exclude names that are digits or contain only symbols/numbers
    if text.isdigit() or any(char in text for char in '+0123456789'):
        return False

    # Require that the name has at least two characters
    if len(text) < 2:
        return False

    # Define allowed non-alphabetic characters in names
    allowed_chars = {"'", "-", "."}

    # Check that each character is either alphabetic, a space, or in the allowed set
    if not all(char.isalpha() or char.isspace() or char in allowed_chars for char in text):
        return False

    # Ensure no two special characters are next to each other (e.g., `O'-Connor` or `Dr..`)
    if any(text[i] in allowed_chars and text[i + 1] in allowed_chars for i in range(len(text) - 1)):
        return False

    return text  # Return the cleaned player name if valid

def preprocess_player_form_image(image):

    """
    Preprocess the player form image for better OCR results by sharpening,
    enhancing edges, and ensuring the numbers are solid white on a black background with a black outline.
    """
    # Step 1: Use color information to determine the form sign
    is_positive = is_form_value_positive(image)

    # Step 2: Upscale the image to enhance OCR accuracy
    image = cv2.resize(image, None, fx=6, fy=6, interpolation=cv2.INTER_LINEAR)

    # Step 3: Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


    # Sharpening the image after blurring
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])  # Simple sharpening kernel
    sharpened = cv2.filter2D(gray_image, -1, kernel)

    # Apply CLAHE (more aggressive contrast enhancement)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(10, 10))
    enhanced = clahe.apply(sharpened)

    return enhanced, is_positive


# Custom preprocessing for starting_11
# This produces the best results
def preprocess_starting_11_image(image):
    adjust_contrast = cv2.convertScaleAbs(image, alpha=1.1, beta=10)

    return adjust_contrast


# Save pre-match data into a JSON file
def save_pre_match_data(match_data):
    with open("pre_match_data.json", "w") as f:
        json.dump(match_data, f, indent=4)

# Load pre-match data from JSON
def load_pre_match_data():
    try:
        with open("pre_match_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    