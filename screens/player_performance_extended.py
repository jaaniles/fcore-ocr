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

async def process_player_performance_extended(screenshot_path, ocr):
    """Process the player performance extended screen to extract data."""
    image = cv2.imread(screenshot_path)
    cropped_image = crop_performance_area(image)
    grayscale = grayscale_image(cropped_image)

    result = await paddleocr(grayscale, ocr)
    annotate_ocr_results(grayscale, FOLDER, result)
    print(result)

    player_data = extract_player_data(result, cropped_image)
    pprint.pprint(player_data)

def extract_player_data(ocr_results, image):
    ocr_results_sorted = sorted(ocr_results, key=lambda x: (x[0][0][1], x[0][0][0]))

    # Variables to store x-coordinates of the MR, G, and AST columns
    mr_x, g_x, ast_x = None, None, None

    # List to store the extracted player data
    player_data = []
    mvp_found = False

    # Step 1: Find the x-coordinates of MR, G, AST labels
    for bbox, text, confidence in parse_ocr(ocr_results_sorted):
        if text == "MR":
            mr_x = bbox[0][0]  # Store the x-coordinate of the "MR" column
        elif text == "G":
            g_x = bbox[0][0]  # Store the x-coordinate of the "G" (Goals) column
        elif text == "AST":
            ast_x = bbox[0][0]  # Store the x-coordinate of the "AST" (Assists) column

        # Break early once we've found all the labels
        if mr_x and g_x and ast_x:
            break

    # Variables to temporarily hold data for each player
    current_player = None

    # Step 2: Process player data based on the x-coordinates of MR, G, and AST
    for bbox, text, confidence in parse_ocr(ocr_results_sorted):
        if confidence < 0.75:
            continue

        # Check for positions (start of a player block)
        if text in ['LS', 'RS', 'LM', 'RM', 'LB', 'LCB', 'RCB', 'RB', "CDM", 'GK', 'CAM', 'RCM', 'LCM', "SUB"]:
            # Save the previous player's data before starting a new player block
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
                is_mvp = check_for_mvp(image, bbox, current_player["name"])
                if is_mvp:
                    current_player["mvp"] = True
                    mvp_found = True

        # Numbers (rating, goals, assists) follow after the name
        elif current_player:
            try:
                # Convert the text into a number (either float for rating or int for goals/assists)
                num = float(text) if '.' in text else int(text)

                # Use the x-coordinate of the number to assign it to the correct stat
                stat_x = bbox[0][0]  # Get the x-coordinate of the current stat

                # Compare x-coordinate to MR, G, and AST columns
                if abs(stat_x - mr_x) < abs(stat_x - g_x) and abs(stat_x - mr_x) < abs(stat_x - ast_x):
                    current_player["rating"] = num  # It's the rating (MR)
                elif abs(stat_x - g_x) < abs(stat_x - ast_x):
                    current_player["goals"] = num  # It's the goals (G)
                else:
                    current_player["assists"] = num  # It's the assists (AST)

            except ValueError:
                pass  # If it's not a number, ignore

    # Append the last player's data
    if current_player:
        player_data.append(current_player)

    return player_data

def is_nearby(value_bbox, label_bbox, tolerance=50):
    """
    Check if the value is close enough to a label (such as 'G' or 'AST') based on their bounding boxes.
    
    Parameters:
        value_bbox (list): Bounding box of the value (number).
        label_bbox (list): Bounding box of the label (such as 'G' or 'AST').
        tolerance (int): The maximum allowed distance between the value and the label.
    
    Returns:
        bool: True if the value is close to the label, False otherwise.
    """
    # Compare the x-coordinates of the value and label bounding boxes
    value_x_min = value_bbox[0][0]
    label_x_min = label_bbox[0][0]
    
    return abs(value_x_min - label_x_min) <= tolerance

def crop_performance_area(image):
    """Crop the image to focus on the relevant area with player names and ratings and stats."""
    cropped_image = crop_image(image, (420, 400, 1380, 1300))

    if DEBUG:
        save_image(cropped_image, FOLDER, "cropped.png")
    
    return cropped_image