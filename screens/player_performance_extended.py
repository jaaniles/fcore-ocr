# Allow saving images for debugging purposes
import os
import pprint

import cv2

from check_for_mvp import check_for_mvp
from crop import crop_image
from image_processing import grayscale_image
from ocr import annotate_ocr_results, paddleocr, parse_ocr
from save_image import save_image


DEBUG = True
FOLDER = './images/player_performance_extended'
os.makedirs(FOLDER, exist_ok=True)

def process_player_performance_extended(screenshot_path):
    """Process the player performance extended screen to extract data."""
    image = cv2.imread(screenshot_path)
    cropped_image = crop_performance_area(image)
    grayscale = grayscale_image(cropped_image)

    result = paddleocr(grayscale)
    annotate_ocr_results(grayscale, FOLDER, result)
    print(result)

    player_data = extract_player_data(result, cropped_image)
    pprint.pprint(player_data)

def extract_player_data(ocr_results, image):
    ocr_results_sorted = sorted(ocr_results, key=lambda x: (x[0][0][1], x[0][0][0]))

    # List to store the extracted player data
    player_data = []
    mvp_found = False

    # Variables to temporarily hold data for each player
    current_player = None

    # Iterate through the OCR results
    for bbox, text, confidence in parse_ocr(ocr_results_sorted):
        if confidence < 0.75:
            continue

        # Check for positions (start of a player block)
        if text in ['LS', 'RS', 'LM', 'RM', 'LB', 'LCB', 'RCB', 'RB', "CDM", 'GK', 'CAM', 'RCM', 'LCM', "SUB"]:
            # If we're already parsing a player, save the previous player's data
            if current_player:
                player_data.append(current_player)

            # Start a new player entry
            current_player = {
                "position": text,
                "name": "",
                "rating": 0.0,
                "goals": 0,
                "assists": 0,
                "mvp": False
            }

        # Player's name usually follows the position
        elif current_player and current_player["name"] == "":
            current_player["name"] = text

            # Check for MVP if not already found
            if not mvp_found:
                is_mvp = check_for_mvp(image, bbox, current_player["name"], search_x_offset=46, folder=FOLDER)
                if is_mvp:
                    current_player["mvp"] = True
                    mvp_found = True  # Stop looking for MVP once found

        # Match Rating (MR)
        elif current_player and isinstance(current_player["rating"], float) and current_player["rating"] == 0.0:
            try:
                current_player["rating"] = float(text)
            except ValueError:
                current_player["rating"] = None
                pass  # Ignore if the text is not a valid float

        # Goals (G)
        elif current_player and isinstance(current_player["goals"], int) and current_player["goals"] == 0:
            try:
                current_player["goals"] = int(text)
            except ValueError:
                pass  # Ignore if the text is not a valid integer

        # Assists (AST)
        elif current_player and isinstance(current_player["assists"], int) and current_player["assists"] == 0:
            try:
                current_player["assists"] = int(text)
            except ValueError:
                pass  # Ignore if the text is not a valid integer

    # Append the last player data if not added
    if current_player:
        player_data.append(current_player)

    return player_data

def crop_performance_area(image):
    """Crop the image to focus on the relevant area with player names and ratings and stats."""
    cropped_image = crop_image(image, (420, 400, 1380, 1300))

    if DEBUG:
        save_image(cropped_image, FOLDER, "cropped.png")
    
    return cropped_image