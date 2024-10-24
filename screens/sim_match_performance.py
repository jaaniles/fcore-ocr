import difflib
import os
import pprint
import re

import cv2
import numpy as np

from crop import crop_area
from ocr import paddleocr, parse_ocr
from player_name import clean_player_name, is_valid_player_name
from save_image import save_image

DEBUG = True
FOLDER = './images/sim_match_performance'
os.makedirs(FOLDER, exist_ok=True)

async def process_sim_match_performance(screenshot_path, team, ocr):
    team_name = team['teamName']

    image = cv2.imread(screenshot_path)
    # Step 1: Perform OCR on the full image using paddleocr
    ocr_data = await paddleocr(image, ocr)

    # Step 2: Detect the team side (home or away)
    _, image_width, _ = image.shape  # Get image dimensions
    team_side = detect_team_side(ocr_data, team_name, image_width)
    if not team_side:
        raise ValueError(f"Team '{team_name}' not found in the OCR output")
    
    # Step 3: Find the horizontal midpoint between 'Starting 11' and 'Bench' on the correct side
    anchor_result = find_anchors(ocr_data, team_side, image_width)
    if anchor_result is None:
        raise ValueError("Could not find 'Starting 11' or 'Bench' on the correct side")

    bench_midpoint_x, bench_y = anchor_result  

    # Step 4: Crop the image based on the team side and bench midpoint
    cropped_image = crop_team_players(image, bench_midpoint_x, bench_y)
    cropped_filename = os.path.join(FOLDER, f"{team_side}.png")
    cv2.imwrite(cropped_filename, cropped_image)

    # Step 5: Re-run OCR on the cropped image to get player data
    cropped_ocr_data = await paddleocr(cropped_image, ocr)

    # Step 6: Extract player information (name, rating, is_sub, scored_goal)
    player_data = extract_player_data(cropped_ocr_data, cropped_image, team_side)

    return player_data

def detect_team_side(ocr_data, team_name, image_width):
    """
    Detect whether our team is on the left (home) or right (away) side based on the OCR output.
    
    Parameters:
        ocr_data (list): The OCR result containing bounding boxes and text.
        team_name (str): The name of our team (e.g., "Arminia Bielefeld").
        image_width (int): The width of the image to dynamically calculate the midpoint.
    
    Returns:
        str: 'home' if the team is on the left side, 'away' if on the right side, or None if not found.
    """
    team_name_lower = team_name.lower()  # Normalize the team name for case-insensitive matching
    image_midpoint = image_width // 2 

    for bbox, text, _ in parse_ocr(ocr_data):
        text_lower = text.lower()

        # Use fuzzy matching to find the team name in the OCR output
        match = difflib.get_close_matches(text_lower, [team_name_lower], cutoff=0.7)
        if match:
            x_min = bbox[0][0]

            # Determine if the team is on the left or right side based on the X-coordinate
            if x_min < image_midpoint:
                return 'home'
            else:
                return 'away'

    # Return None if the team name is not found
    return None

def find_anchors(ocr_data, team_side, image_width):
    """
    Find the bounding boxes for 'Starting 11' and 'Bench' on the correct side of the image and return the horizontal midpoint and bottom Y-coordinate.
    
    Parameters:
        ocr_data (list): The OCR result containing bounding boxes and text.
        team_side (str): Either 'home' or 'away', indicating which side of the image to search for anchors.
        image_width (int): The width of the image to dynamically calculate the midpoint.
    
    Returns:
        tuple: A tuple containing (midpoint_x, bottom_y), where:
               - midpoint_x: The X-coordinate of the midpoint between 'Starting 11' and 'Bench' for cropping.
               - bottom_y: The maximum Y-coordinate (bottom edge) of the 'Starting 11' or 'Bench' bounding box.
        None: If the anchors are not found.
    """
    image_midpoint = image_width // 2 
    
    starting_box = None
    bench_box = None

    # Define possible variations of 'Starting 11' and 'Bench' using fuzzy matching terms
    starting_variants = ['starting 11', 'starting11', 'starting ll', 'starting' 'starting il']
    bench_variants = ['bench', 'bencl', 'bencll', 'benchi', 'benchl', 'bench1', 'benchil']

    for bbox, text, _ in parse_ocr(ocr_data):
        x_min = bbox[0][0] 
        text_lower = text.lower()

        # Fuzzy match the text against possible variants
        match_starting = difflib.get_close_matches(text_lower, starting_variants, n=1, cutoff=0.7)
        match_bench = difflib.get_close_matches(text_lower, bench_variants, n=1, cutoff=0.7)

        # Filter by team side (left for home, right for away)
        if team_side == 'home' and x_min < image_midpoint:
            if match_starting:
                starting_box = bbox
            if match_bench:
                bench_box = bbox
        elif team_side == 'away' and x_min >= image_midpoint:
            if match_starting:
                starting_box = bbox
            if match_bench:
                bench_box = bbox

    # Fallback mechanism if 'Bench' is not found
    if starting_box and not bench_box:
        print("Warning: 'Bench' label not found. Using 'Starting 11' as fallback.")
        starting_right_x = starting_box[1][0]  # Right X-coordinate of 'Starting 11'
        bottom_y = starting_box[2][1]  # Bottom Y-coordinate of 'Starting 11'
        return starting_right_x, bottom_y

    # If both anchors are found, calculate the midpoint X-coordinate and bottom Y-coordinate
    if starting_box and bench_box:
        starting_right_x = starting_box[1][0]  # Right X-coordinate of 'Starting 11'
        bench_left_x = bench_box[0][0]  # Left X-coordinate of 'Bench'
        midpoint_x = (starting_right_x + bench_left_x) // 2

        bottom_y = bench_box[2][1]  # Bottom Y-coordinate of 'Bench' box
        return midpoint_x, bottom_y

    # Return None if neither anchor is found
    print("Error: Could not find 'Starting 11' or 'Bench' labels.")
    return None


def crop_team_players(image, bench_midpoint_x, bench_y):
    """
    Crop the image to include only the relevant team’s players, based on the team side and the horizontal midpoint between 'Starting 11' and 'Bench'.
    
    Parameters:
        image (np.array): The input image containing the full match performance screen.
        bench_midpoint_x (int): The X-coordinate of the midpoint between 'Starting 11' and 'Bench' for cropping.
        bench_y (int): The Y-coordinate of the bottom edge of the 'Bench' bounding box.

    Returns:
        np.array: The cropped image containing only our team's players.
    """

    cropping_height = 775
    cropping_width = 750
    midpoint_x = int(bench_midpoint_x)  # Ensure bench_midpoint_x is an integer
    midpoint_offset = 750 // 2
    y_point = bench_y - 0

    return crop_area(image, midpoint_x - midpoint_offset, y_point, cropping_width, cropping_height)
    
def extract_player_data(ocr_data, image, team_side):
    """
    Extract player names, ratings, and additional info (substitutions, goals, captain) from the OCR data of the cropped image.
    
    Parameters:
        ocr_data (list): The OCR result from the cropped image containing players.
        image (np.array): The cropped image containing only the team's players.
        team_side (str): Either 'home' or 'away', indicating how to interpret the OCR layout.
    
    Returns:
        list: A list of dictionaries containing player info (name, rating, is_sub, scored_goal, is_captain).
    """
    player_data = []
    
    # Step 1: Sort OCR data by Y-coordinate (rows), then by X-coordinate (columns)
    sorted_ocr_data = sorted(parse_ocr(ocr_data), key=lambda x: (x[0][0][1], x[0][0][0]))

    row_data = []
    current_row = []
    current_y = None
    y_threshold = 20  # Y-distance threshold for items to be considered in the same row

    # Step 2: Group OCR data into rows
    for bbox, text, _ in sorted_ocr_data:
        item_y = bbox[0][1]  # Y-coordinate of the top-left corner of the bounding box
        if current_y is None or abs(item_y - current_y) < y_threshold:
            current_row.append((bbox, text))
            current_y = item_y
        else:
            # New row starts
            row_data.append(current_row)
            current_row = [(bbox, text)]
            current_y = item_y

    if current_row:
        row_data.append(current_row)  # Add the last row

    # Step 3: Process each row to extract player name, rating, and other info
    for row in row_data:
        player = {'name': None, 'rating': None, 'scored_goal': False}
        player_box = None

        for bbox, text in row:
            cleaned_text = clean_player_name(text)

            # Detect valid player names (after cleaning)
            if is_valid_player_name(cleaned_text):
                player['name'] = cleaned_text
                player_box = bbox  # Save player bounding box for rating and C tag detection

        # Once we have the player name, extract rating based on team side
        if player['name']:
            for bbox, text in row:
                try:
                    rating = float(text)
                    rating_x_min = bbox[0][0]
                    player_x_min, player_x_max = player_box[0][0], player_box[2][0]

                    # Home side: rating should be to the right of the player
                    if team_side == 'home' and rating_x_min > player_x_max:
                        player['rating'] = rating
                        break  

                    # Away side: rating should be to the left of the player
                    if team_side == 'away' and rating_x_min < player_x_min:
                        player['rating'] = rating
                        break  # Stop after finding the rating
                except ValueError:
                    continue  # Skip non-numeric values

            player['scored_goal'] = check_for_scored_goal(image, player_box, team_side, player['name'])

            is_captain, player['name'] = check_captaincy(player['name'], row, team_side, player_box)
            if is_captain:
                player['is_captain'] = True

            is_sub = check_for_substitution(image, player_box, team_side, player['name'], is_captain)
            if is_sub:
                player['is_sub'] = True


            # Add the player to the list
            player_data.append(player)

    return player_data



def check_for_scored_goal(image, player_box, team_side, player_name):
    """
    Check if the player has scored a goal based on the presence of a white soccer ball icon near the player name.
    
    Parameters:
        image (np.array): The full image in which the player data exists.
        player_box (list): The bounding box of the player name.
        team_side (str): Either 'home' or 'away' indicating where the goal icon would appear.
    
    Returns:
        bool: True if the player has scored a goal (i.e., if the ball icon is detected), False otherwise.
    """
    # Get the coordinates of the player name's bounding box
    _, y_min = player_box[0]  # Top-left corner
    _, _ = player_box[2]  # Bottom-right corner


    # Define crop size and offsets
    crop_size = 30  # Size of the cropping area (width and height)

    _, width, _ = image.shape

    if team_side == 'home':
        x_point = 85
    elif team_side == 'away':
        x_point = width - 98
    else:
        # Invalid team side
        return False

    crop_y = y_min  # Crop area aligned with the player's bounding box vertically

    # Use the crop_area helper function to handle cropping
    cropped_area = crop_area(image, x_point, crop_y - 5, crop_size, crop_size)

    # Save the cropped area for debugging
    if DEBUG:
        if cropped_area is None or cropped_area.size == 0:
            print(f"Error: Cropped area for player {player_name} is empty. Skipping.")
        else:
            save_image(cropped_area, FOLDER, f"goal_{player_name}.png")

    # Analyze the cropped area for the presence of white pixels (ball icon)
    white_threshold = 200  # Threshold to consider a pixel as "white"
    white_pixel_count = np.sum(cropped_area >= white_threshold)

    # Check if a significant portion of the cropped area is white (representing the ball icon)
    total_pixels = cropped_area.size
    white_percentage = (white_pixel_count / total_pixels) * 100

    return white_percentage > 50  # If more than 75% of the area is white, we detect a goal


def check_for_substitution(image, player_box, team_side, player_name, is_captain):
    """
    Check if the player was involved in a substitution based on the presence of green (sub) caret icon
    We don't actually check for an icon, we just count the color pixels in the area where the icon would be.
    
    Parameters:
        image (np.array): The full image in which the player data exists.
        player_box (list): The bounding box of the player name.
        team_side (str): Either 'home' or 'away' indicating where the substitution icon would appear.
        player_name (str): The player's name as detected by OCR.
        is_captain (bool): Whether the player is the captain. Offsets are adjusted based on this.
    
    Returns:
        bool: True if substitution icon was detected, False otherwise
    """
    # Get the coordinates of the player name's bounding box
    x_max, y_min = player_box[2]  # Bottom-right corner of the player name
    x_min, y_max = player_box[0]  # Top-left corner

    # Calculate the Y midpoint of the player name's bounding box
    y_mid = (y_min + y_max) // 2  # Midpoint for Y

    # Define crop size and offsets
    crop_height = 25
    crop_width = 40
    x_offset = 0   # Horizontal offset to move outside the player name bounding box

    if is_captain:
        x_offset += 40
    
    if team_side == 'home':
        # For home side, caret is on the right side of the player name
        crop_x = x_max + x_offset
    elif team_side == 'away':
        # For away side, caret is on the left side of the player name
        crop_x = max(0, x_min - crop_width - x_offset)
    else:
        # Invalid team side
        return False, False

    # Use the Y midpoint to ensure we center the crop vertically on the caret
    crop_y = y_mid - (crop_height // 2)

    # Use the crop_area helper function to handle cropping
    cropped_area = crop_area(image, crop_x, crop_y, crop_width, crop_height)

    # Ensure the cropped area is not empty or invalid before proceeding
    if cropped_area is None or cropped_area.size == 0:
        print(f"Error: Cropped area for player {player_name} is empty. Skipping.")
        return False, False

    # Save the cropped area for debugging
    if DEBUG:
        save_image(cropped_area, FOLDER, f"sub_{player_name}.png")

    # Adjusted green caret color thresholds with higher saturation
    lower_green = np.array([50, 100, 50], dtype=np.uint8)  # Green lower bound
    upper_green = np.array([80, 255, 255], dtype=np.uint8)  # Green upper bound


    # Convert the cropped area to HSV for better color detection
    hsv_cropped_area = cv2.cvtColor(cropped_area, cv2.COLOR_BGR2HSV)

    # Create masks to detect green and red pixels in the HSV space
    green_mask = cv2.inRange(hsv_cropped_area, lower_green, upper_green)

    # Count green and red pixels
    green_pixel_count = np.sum(green_mask > 0)


    # Determine if player is a sub or benched based on the detected colors
    green_threshold = 20  # Adjust this based on tests for the green caret
    
    is_sub = green_pixel_count > green_threshold

    return is_sub

def check_captaincy(player_name, row, team_side, player_box):
    """
    Check if the player is the captain based on either a separate "C" tag near the player name 
    or if the player name starts or ends with 'c', or has 'c' in the middle for some edge cases.
    
    Parameters:
        player_name (str): The player's name as detected by OCR.
        row (list): The list of OCR items in the current row.
        team_side (str): Either 'home' or 'away' indicating which side the player is on.
        player_box (list): The bounding box of the player name.
    
    Returns:
        tuple: (bool, str) A tuple containing whether the player is the captain and the cleaned player name.
    """
    player_x_min, player_x_max = player_box[0][0], player_box[2][0]

    # Case 1: The "C" appears as a separate text element next to the player name
    for bbox, text in row:
        if text.lower() == "c":
            c_x_min = bbox[0][0]
            # Home side: "C" should be to the right of the player name
            if team_side == 'home' and c_x_min > player_x_max:
                return True, player_name
            # Away side: "C" should be to the left of the player name
            elif team_side == 'away' and c_x_min < player_x_min:
                return True, player_name

    # Case 2: The "C" is embedded in the player name text
    # Example: "Koumetio c", "c A. Muller"
    if player_name.lower().endswith(' c'):
        # Strip the trailing ' c' and mark as captain
        return True, player_name[:-2].strip()
    
    if player_name.lower().startswith('c ') or player_name.lower().startswith('c.'):
        # Strip the leading 'c ' or 'c.' and mark as captain
        return True, player_name[2:].strip()

    # Case 3: The "C" is embedded in a name like "cRuibal" (lowercase 'c' followed by uppercase)
    if player_name[0] == 'c' and len(player_name) > 1 and player_name[1].isupper():
        # Strip the initial 'c' from the name and mark as captain
        return True, player_name[1:]

    # No captaincy found
    return False, player_name