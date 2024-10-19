from datetime import datetime
import os
import json
import pprint
import re
import cv2
import numpy as np
from crop import crop_image
from image_processing import upscale_image

# Create folder for saving pre-match images
PRE_MATCH_FOLDER = './screenshots/pre_match'
os.makedirs(PRE_MATCH_FOLDER, exist_ok=True)

def preprocess_image(image, upscale=True):
    """Preprocess the image to improve OCR accuracy."""
    if upscale:
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a mild Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Sharpening the image after blurring
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])  # Simple sharpening kernel
    sharpened = cv2.filter2D(blurred, -1, kernel)

    # Apply CLAHE (more aggressive contrast enhancement)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(10, 10))
    enhanced = clahe.apply(sharpened)

    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Convert back to BGR for PaddleOCR
    processed_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    return processed_image

def process_pre_match(screenshot_path, ocr):
    # Load the screenshot
    image = cv2.imread(screenshot_path)

    # Preprocess the image (if required)
    processed_image = upscale_image(image)

    # Define crop coordinates for match date and starting 11
    match_date_coords = (1840, 475, 3440 - 200, 620)
    starting_11_coords = (1720, 590, 3500, 1650)

    # Step 1: Crop relevant sections
    cropped_match_date = crop_image(processed_image, match_date_coords)
    cropped_starting_11 = crop_image(processed_image, starting_11_coords)
    processed_starting_11 = preprocess_image(cropped_starting_11, False)

    # Draw a rectangle over the "Custom" text area
    block_coords = (0, 1000, 375, 870)
    processed_starting_11 = cv2.rectangle(processed_starting_11, (block_coords[0], block_coords[1]), 
                                          (block_coords[2], block_coords[3]), (255, 255, 0), thickness=-1)

    # Step 2: Save cropped images for debugging
    match_date_path = os.path.join(PRE_MATCH_FOLDER, "cropped_match_date.png")
    starting_11_path = os.path.join(PRE_MATCH_FOLDER, "cropped_starting_11.png")
    cv2.imwrite(match_date_path, cropped_match_date)
    cv2.imwrite(starting_11_path, processed_starting_11)

    # Step 3: Perform OCR on each cropped section
    match_date_result = ocr.ocr(cropped_match_date)
    starting_11_result = ocr.ocr(processed_starting_11)

    # Annotate the OCR results on the image
    annotate_ocr_results(processed_starting_11, starting_11_result)

    # Proceed with the rest of your OCR processing logic
    result = process_starting_11(starting_11_result, cropped_starting_11, ocr)
    pprint.pprint(result)

    return {
        "match_date": match_date_result,
        "starting_11": starting_11_result,
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
    cv2.imwrite(os.path.join(PRE_MATCH_FOLDER, f"anno.png"), image)

def process_starting_11(ocr_results, image, ocr):
    """
    Process the OCR results to extract player names and crop emoji and form symbols based on bounding boxes.
    """
    players_info = []
    CAPTAIN_OFFSET = -43  # Adjust this based on estimated width of the captain tag "C "

    for result in ocr_results:
        for line in result:
            text = line[1][0]  # Extract recognized text (e.g., player name)
            confidence = line[1][1]
            bbox = line[0]  # Extract the bounding box (x, y) coordinates

            name = is_valid_player_name(text)
            if confidence < 0.8:
                print(f"Skipping low confidence result: {text} with confidence {confidence:.2f}")
                continue

            # Check if text contains a player name, and add 'is_captain' flag if the name starts with "c"
            if name:
                player_name = name

                is_captain = False

                # Detect if the player is a captain (name starts with "c ")
                if player_name.startswith('c '):
                    player_name = player_name[2:]  # Remove the "c" prefix
                    is_captain = True

                # Detect the case where the name starts with a lowercase "c" followed by an uppercase letter (e.g., "cRuibal")
                elif len(player_name) > 1 and player_name[0] == 'c' and player_name[1].isupper():
                    player_name = player_name[1:]  # Remove the leading lowercase "c"
                    is_captain = True

                # Calculate the absolute center of the player name bounding box
                x1, y1 = int(bbox[0][0]), int(bbox[0][1])  # Top-left corner of the bounding box
                x2, y2 = int(bbox[2][0]), int(bbox[2][1])  # Bottom-right corner of the bounding box
                name_center_x = (x1 + x2) // 2
                name_center_y = (y1 + y2) // 2

                # Adjust the center X for captains to compensate for the "C " tag width
                if is_captain:
                    name_center_x -= CAPTAIN_OFFSET // 2  # Compensate for captain tag width

                # Crop emoji
                emoji_area = crop_area(image, name_center_x - 101, name_center_y - 128, 42, 42)
                # Detect mood from emoji color
                mood = detect_emoji_color(emoji_area)
                # Save image for debugging  
                emoji_path = os.path.join(PRE_MATCH_FOLDER, f"emoji_{player_name}.png")
                cv2.imwrite(emoji_path, emoji_area)

                player_form_area_offset = name_center_x + 40
                if len(player_name) < 5:   
                    player_form_area_offset += 20

                # Crop player form
                player_form_area = crop_area(image, player_form_area_offset, name_center_y - 121, 75, 40)
                # Preprocess for better OCR results
                processed_player_form, sign = preprocess_number_image(player_form_area)
                # Perform OCR 
                player_form_result = ocr.ocr(processed_player_form)  # Perform OCR on the form area
                form_value = process_ocr_result_with_sign(player_form_result, sign)

                # Save image for debugging
                player_form_path = os.path.join(PRE_MATCH_FOLDER, f"form_{player_name}.png")
                cv2.imwrite(player_form_path, processed_player_form)

                # Append player info with relevant data
                player_info = {
                    "name": player_name,
                    "mood": mood,  
                    "form": form_value  
                }
                if is_captain:
                    player_info["is_captain"] = True

                players_info.append(player_info)

    return players_info

def extract_match_date(ocr_output):
    """
    Extract the match date from OCR output and convert it to datetime format.
    """
    # Guard clause for None or empty OCR output
    if not ocr_output or not isinstance(ocr_output, list):
        print("OCR output is either None or not in the expected format.")
        return None

    # Flatten the OCR results list, with a guard clause for non-iterable results
    flat_ocr = []
    try:
        flat_ocr = [item[1][0] for line in ocr_output if line for item in line if item and item[1]]
    except (IndexError, TypeError) as e:
        print(f"Error processing OCR output: {e}")
        return None

    # Iterate through the OCR output to find the string containing "Referee"
    for text in flat_ocr:
        if "Referee" in text:
            # The text containing "Referee" will also have the date before it
            # Split by 'Referee' to isolate the part before it
            date_text = text.split('Referee')[0]

            # Use a regular expression to find the date pattern in the form of "22 August 2026"
            match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_text)
            if match:
                # Extract day, month, and year from the matched text
                day, month, year = match.groups()

                try:
                    # Convert the extracted month to a number using datetime.strptime
                    month_number = datetime.strptime(month, "%B").month  # Convert month name to number

                    # Construct a datetime object from the extracted date
                    match_date = datetime(int(year), int(month_number), int(day))

                    # Return the date in 'DD.MM.YYYY' format
                    return match_date.strftime('%d.%m.%Y')
                except ValueError as ve:
                    print(f"Error converting date: {ve}")
                    return None

    # If no match is found, return None
    print("No date found in the OCR output.")
    return None


def process_form_value(image, ocr):
    """
    Process the form value from an image by detecting the sign using color and extracting the number using OCR.
    """
    # Preprocess the image to isolate the form value
    preprocessed_image, sign = preprocess_number_image(image)

    # Perform OCR on the preprocessed image to get the numeric value
    ocr_result = ocr.ocr(preprocessed_image)

    # Process OCR result with the detected sign
    form_value = process_ocr_result_with_sign(ocr_result, sign)

    return form_value

def determine_form_sign(image):
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
        return "negative"
    elif green_pixels > red_pixels:
        return "positive"

    # If we detect neither color prominently, we return None
    return None

def preprocess_number_image(image, upscale=True):
    """
    Preprocess the player form image for better OCR results. Focus on isolating the numeric value after
    determining the form sign from the color information.
    """
    # Step 1: Use color information to determine the form sign
    sign = determine_form_sign(image)

    # Step 2: Upscale the image to enhance OCR accuracy
    if upscale:
        image = cv2.resize(image, None, fx=6, fy=6, interpolation=cv2.INTER_LINEAR)

    # Step 3: Convert the image to grayscale to remove the color information (+/- symbols)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 4: Apply Gaussian blur to reduce noise (as you found helpful)
    blurred = cv2.GaussianBlur(gray_image, (3, 3), 0)

    # Step 5: Apply binary thresholding to isolate the number from the background
    _, threshold_image = cv2.threshold(blurred, 127, 255, cv2.THRESH_BINARY_INV)

    # Step 6: Return the preprocessed image along with the sign
    return threshold_image, sign

def process_ocr_result_with_sign(ocr_result, sign):
    """
    Clean the OCR result for the form value, ensuring it's a valid number.
    Combine the OCR result with the detected sign from color.
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
                form_value = int(cleaned_text)
                # Return the value as a string with the appropriate sign
                if sign == "negative":
                    return f"-{form_value}"
                return f"+{form_value}"
            except ValueError:
                return None  # If OCR result is not a valid number, return None
    return None

def crop_area(image, x, y, w, h):
    """Helper function to crop the area based on coordinates and ensure indices are integers."""
    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure all coordinates are integers
    return image[y:y+h, x:x+w]

def detect_emoji_color(emoji_image):
    """
    Analyze the emoji image to determine the mood color.
    This function uses color detection to identify the mood (green, cyan, yellow, red).
    """
    if emoji_image is None or emoji_image.size == 0:
        print("Empty emoji image detected. Skipping color detection.")
        return None

    hsv_image = cv2.cvtColor(emoji_image, cv2.COLOR_BGR2HSV)
    
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

def clean_player_form_result(form_text):
    """
    Cleans the OCR result for the form value.
    Extracts and returns a valid positive or negative number, otherwise returns None.
    """
    if form_text:
        # Remove any spaces and ensure the text is in the form of a number like +2 or -2
        form_text = form_text.strip()

    # If it's not a valid number, return None
    return None

def is_valid_player_name(text):
    """Check if the detected text is a valid player name."""
    # Strip leading and trailing whitespaces
    text = text.strip()

    # Exclude names that are digits or contain only symbols/numbers
    if text.isdigit() or any(char in text for char in '+-0123456789'):
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

def process_ocr_result(ocr_output):
    """Extract the most confident text from the OCR result."""
    if ocr_output and ocr_output[0]:
        return ocr_output[0][0][1][0]  # Return the most confident recognized text
    return None

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
