import os
import cv2
import numpy as np
from crop import crop_area, crop_image
from image_processing import grayscale_image, preprocess_image, upscale_image
from PIL import Image

from ocr import annotate_ocr_results, paddleocr, parse_ocr
from player_name import clean_player_name, is_valid_player_name
from save_image import save_image

# Allow saving images for debugging purposes
DEBUG = True
FOLDER = './images/player_performance'
os.makedirs(FOLDER, exist_ok=True)

def process_player_performance_screen(screenshot_path):
    """Process the player performance screen to extract data."""
    image = cv2.imread(screenshot_path)

    # Crop the image
    cropped_image = crop_player_performance(image)
    upscaled_image = upscale_image(cropped_image, 4)
    processed_image = grayscale_image(upscaled_image)
    
    result = paddleocr(processed_image)

    if DEBUG:
        save_image(processed_image, FOLDER, "player_performance_processed.png")
        annotate_ocr_results(processed_image, FOLDER, result)

    player_data = extract_player_data(result, upscaled_image)

    return player_data


def extract_player_data(ocr_data, image):
    """
    Extract player names, match ratings, and check for MVP from the OCR results.
    
    Parameters:
        ocr_data (list): The OCR result containing players and match ratings.
        image (np.array): The full image to check for the MVP icon.
    
    Returns:
        list: A list of dictionaries containing player info (full_name, match_rating, is_mvp).
    """
    y_threshold = 50
    x_threshold = 30
    processed_names = set()
    mvp_found = False  # To track if we've already marked a player as MVP

    # Helper functions for extracting last name and match rating
    def find_last_name(current_index, first_name_bbox):
        for j in range(current_index + 1, len(ocr_iterator)):
            next_bbox, next_text, _ = ocr_iterator[j]
            next_cleaned_text = clean_player_name(next_text)

            if is_valid_player_name(next_cleaned_text) and \
               abs(next_bbox[0][1] - first_name_bbox[2][1]) <= y_threshold and \
               abs(next_bbox[0][0] - first_name_bbox[0][0]) <= x_threshold:
                return next_cleaned_text, next_bbox
        return None, None

    def find_match_rating(current_index, first_name_bbox):
        for j in range(current_index + 1, len(ocr_iterator)):
            bbox_right, text_right, _ = ocr_iterator[j]
            try:
                rating = float(text_right)
                if bbox_right[0][0] > first_name_bbox[2][0]:  # Ensure it's to the right
                    return rating
            except ValueError:
                continue
        return None

    # Main processing function
    def process_player(i):
        nonlocal mvp_found  # Inform Python to use the outer scope variable
        
        bbox, text, _ = ocr_iterator[i]
        cleaned_text = clean_player_name(text)

        if is_valid_player_name(cleaned_text):
            first_name = cleaned_text
            first_name_bbox = bbox

            last_name, last_name_bbox = find_last_name(i, first_name_bbox)
            full_name = first_name if not last_name else f"{first_name} {last_name}"

            if full_name not in processed_names:
                match_rating = find_match_rating(i, first_name_bbox)

                if match_rating is not None:
                    # Check for MVP only if not already found
                    is_mvp = False
                    if not mvp_found and last_name_bbox:
                        is_mvp = check_for_mvp(image, last_name_bbox, full_name)
                        if is_mvp:
                            mvp_found = True  # Stop checking further once found

                    processed_names.add(full_name)
                    processed_names.add(first_name)
                    if last_name:
                        processed_names.add(last_name)
                    return {
                        'full_name': full_name,
                        'match_rating': match_rating,
                        'is_mvp': is_mvp
                    }
        return None

    # Iterate over OCR data and collect players
    ocr_iterator = list(parse_ocr(ocr_data))
    player_data = [player for i in range(len(ocr_iterator)) if (player := process_player(i))]

    return player_data

def check_for_mvp(image, last_name_bbox, player_name):
    """
    Check if the player has the MVP icon based on color detection.
    
    Parameters:
        image (np.array): The original image containing the player data.
        last_name_bbox (list): The bounding box of the player's last name.
    
    Returns:
        bool: True if the player is the MVP, False otherwise.
    """
    # Get the coordinates for the last name's bounding box
    x_min, y_min = last_name_bbox[0]  # Top-left corner of the last name
    x_max, y_max = last_name_bbox[2]  # Bottom-right corner of the last name

    # Calculate the midpoint for Y and a leftward X value to search for the icon
    y_mid = (y_min + y_max) // 2
    search_x = x_min - 190 

    # Crop a small 30x30 pixel area for analysis
    cropped_area = crop_area(image, search_x, y_mid - 15, 30, 30)

    # Ensure the cropped area is valid (not empty)
    if cropped_area is None or cropped_area.size == 0:
        print(f"Error: Cropped area for {player_name} is empty or invalid.")
        return False
    
    if DEBUG:
        save_image(cropped_area, FOLDER, f"mvp_{player_name}.png")

    # Convert the cropped area to HSV
    try:
        hsv_cropped = cv2.cvtColor(cropped_area, cv2.COLOR_BGR2HSV)
    except cv2.error as e:
        print(f"OpenCV error when converting cropped area to HSV for {player_name}: {e}")
        return False

    # Define HSV color range for detecting gold/yellow color
    lower_gold = (20, 100, 100)
    upper_gold = (30, 255, 255)

    # Create a mask to detect yellow/gold pixels
    mask = cv2.inRange(hsv_cropped, lower_gold, upper_gold)

    # Calculate the percentage of yellow pixels
    yellow_percentage = (cv2.countNonZero(mask) / mask.size) * 100

    return yellow_percentage > 75  # Return True if more than 75% of the area is yellow/gold

def crop_player_performance(image):
    """Crop the image to focus on the relevant area with player names and ratings."""
    cropped_image = crop_image(image, (1900, 200, 2800, 1250))

    if DEBUG:
        save_image(cropped_image, FOLDER, "player_performance_cropped.png")
    
    return cropped_image