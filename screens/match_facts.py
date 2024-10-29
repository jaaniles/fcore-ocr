import difflib
import os
import pprint
import re
import cv2

from crop import crop_image, crop_region
from image_processing import upscale_image
from ocr import extract_number_value, paddleocr, parse_ocr
from save_image import save_image

DEBUG = True
FOLDER = './images/match_facts'
os.makedirs(FOLDER, exist_ok=True)

async def process_match_facts(screenshot_path, our_team):
    our_team_name = our_team['teamName']
    image = cv2.imread(screenshot_path)

    # Coordinates for cropping the stats
    match_score_coords = (1900, 80, 3440 - 400, 1440 - 1270)  
    possession_stats_coords = (1950, 375, 3400 - 880, 1440 - 880) 
    shots_stats_coords = (1550, 715, 3440 - 500, 1440 - 620)
    passes_stats_coords = (1550, 800, 3440 - 500, 920)
    accuracy_stats_coords = (1550, 900, 3440 - 500, 1020)
    tackles_stats_coords = (1550, 1000, 3440 - 500, 1100)

    # Crop the relevant areas
    cropped_match_score = crop_image(image, match_score_coords)
    cropped_possession = crop_image(image, possession_stats_coords)
    cropped_shots = crop_image(image, shots_stats_coords)
    cropped_passes = crop_image(image, passes_stats_coords)
    cropped_accuracy = crop_image(image, accuracy_stats_coords)
    cropped_tackles = crop_image(image, tackles_stats_coords)

    if DEBUG:
        save_image(cropped_match_score, FOLDER, "match_score.png")
        save_image(cropped_possession, FOLDER, "possession_stats.png")
        save_image(cropped_shots, FOLDER, "shots_stats.png")
        save_image(cropped_passes, FOLDER, "passes_stats.png")
        save_image(cropped_accuracy, FOLDER, "accuracy_stats.png")
        save_image(cropped_tackles, FOLDER, "tackles_stats.png")

    # Perform OCR on each cropped section
    possession_stats_result = await paddleocr(cropped_possession)
    shots_result = await paddleocr(cropped_shots)
    passes_result = await paddleocr(cropped_passes)
    accuracy_result = await paddleocr(cropped_accuracy)
    tackles_result = await paddleocr(cropped_tackles)

    # Extract match facts
    home, away = await process_match_score(cropped_match_score)
    home_possession, away_possession = process_possession_stats(possession_stats_result)
    home_shots, away_shots = await extract_value(shots_result, "Shots", cropped_shots)
    home_passes, away_passes = await extract_value(passes_result, "Passes", cropped_passes)
    home_accuracy, away_accuracy = await extract_value(accuracy_result, "Accuracy", cropped_accuracy)
    home_tackles, away_tackles = await extract_value(tackles_result, "Tackles", cropped_tackles)

    # Determine which team is ours
    home_team = home['team_name']
    away_team = away['team_name']
    home_score = home['score']
    away_score = away['score']
    
    our_team, their_team = determine_our_team(home_team, away_team, our_team_name)
    is_home_team = our_team == home_team

    match_facts = {
        'our_team': {
            'name': our_team,
            'score': home_score if is_home_team else away_score,
            'possession': home_possession if is_home_team else away_possession,
            'shots': home_shots if is_home_team else away_shots,
            'passes': home_passes if is_home_team else away_passes,
            'accuracy': home_accuracy if is_home_team else away_accuracy,
            'tackles': home_tackles if is_home_team else away_tackles,
        },
        'their_team': {
            'name': their_team,
            'score': away_score if is_home_team else home_score,
            'possession': away_possession if is_home_team else home_possession,
            'shots': away_shots if is_home_team else home_shots,
            'passes': away_passes if is_home_team else home_passes,
            'accuracy': away_accuracy if is_home_team else home_accuracy,
            'tackles': away_tackles if is_home_team else home_tackles,
        }
    }

    pprint.pprint(match_facts)

    return match_facts

# Helper function to calculate the center of a bounding box
def calculate_center(bounding_box):
    x_coords = [point[0] for point in bounding_box]
    y_coords = [point[1] for point in bounding_box]
    center_x = int(sum(x_coords) / len(x_coords))
    center_y = int(sum(y_coords) / len(y_coords))
    return center_x, center_y

# Main function to extract values
async def extract_value(ocr_result, keyword, image):
    TRAVERSE = 505
    CROP_WIDTH = 175
    CROP_HEIGHT = 70

    # Loop through and find keyword
    for detection_group in ocr_result:
        for detection in detection_group:
            if len(detection) >= 2 and isinstance(detection[1], tuple):
                bounding_box, (text_data, confidence) = detection[0], detection[1]

                # Check if the keyword is present in the detected text
                if keyword.lower() in text_data.lower():
                    # Steps to extract the home and away values
                    # 1. Calculate the center of the keyword's bounding box
                    # 2. Traverse to the left and right of the keyword center
                    # 3. Crop the regions and apply OCR to extract the numbers
                    # 4. Return the extracted home and away values

                    # Calculate the center of the keyword's bounding box
                    center_x, center_y = calculate_center(bounding_box)

                    # Traverse to the left of the keyword center
                    left_x = center_x - TRAVERSE
                    cropped_left = upscale_image(crop_region(image, left_x, center_y, width=CROP_WIDTH, height=CROP_HEIGHT), 6)
                    right_x = center_x + TRAVERSE
                    cropped_right = upscale_image(crop_region(image, right_x, center_y, width=CROP_WIDTH, height=CROP_HEIGHT), 6)

                    if DEBUG:
                        # Save cropped image for debugging
                        left_image_path = os.path.join(FOLDER, f"home_{keyword}.png")
                        cv2.imwrite(left_image_path, cropped_left)
                        right_image_path = os.path.join(FOLDER, f"away_{keyword}.png")
                        cv2.imwrite(right_image_path, cropped_right)

                    left_ocr_result = await paddleocr(cropped_left) 
                    if not left_ocr_result or left_ocr_result == [None] or len(left_ocr_result) == 0:
                        left_ocr_result = []
                    right_ocr_result = await paddleocr(cropped_right)
                    if not right_ocr_result or right_ocr_result == [None] or len(right_ocr_result) == 0:
                        right_ocr_result = []
                    
                    home = extract_number_value(left_ocr_result)
                    away = extract_number_value(right_ocr_result)

                    return home, away

    return None, None

async def process_match_score(image):
    ocr_result = await paddleocr(image)
    home_team, away_team = extract_team_names(ocr_result)

    cropped_score = crop_image(image, (520, 0, 680, 100))
    save_image(cropped_score, FOLDER, "debug_crop_score.png")
    score_ocr_result = await paddleocr(cropped_score)

    print("OCR RESULT?", score_ocr_result)

    home_score, away_score = extract_scores_from_ocr(score_ocr_result)

    home = {
        'team_name': home_team,
        'score': home_score
    }

    away = {
        'team_name': away_team,
        'score': away_score
    }

    return home, away


def extract_scores_from_ocr(ocr_output):
    """
    Extracts home and away scores from OCR output.
    
    Parameters:
        ocr_output (list): The structured OCR output.
    
    Returns:
        tuple: Home and away scores as integers, or None if not found.
    """
    # Initialize home and away scores
    home_score, away_score = None, None

    # Regex to match common OCR patterns for scores (e.g., '1-1', '1 -1', '1 - 1')
    score_pattern = re.compile(r'(\d)\s*-\s*(\d)')

    # Check each OCR text line for the score pattern
    for item in ocr_output[0]:
        text = item[1][0]  # Extract the text part of the OCR item
        
        # Try to match the score pattern directly
        match = score_pattern.search(text)
        if match:
            home_score, away_score = int(match.group(1)), int(match.group(2))
            break

        # If no direct match, handle split scores (e.g., "1" in one item and "1" in another)
        text_parts = re.findall(r'\d', text)
        if len(text_parts) == 2:
            home_score, away_score = int(text_parts[0]), int(text_parts[1])
            break

    return home_score, away_score

def extract_team_names(ocr_output, confidence_threshold=0.7):
    """
    Extracts home and away team names from OCR output, filtering out scores and time formats.
    
    Parameters:
        ocr_output (list): The structured OCR output.
        confidence_threshold (float): Minimum confidence to consider a valid text.
    
    Returns:
        tuple: Home and away team names as strings, or None if not found.
    """
    left_team_name, right_team_name = None, None
    left_max_x, right_min_x = float('inf'), float('-inf')

    score_pattern = re.compile(r'^\d\s*-\s*\d$')
    time_pattern = re.compile(r'^\d{1,2}:\d{2}$')
    
    for bbox, text, confidence in parse_ocr(ocr_output):
        # Ignore entries with low confidence, score pattern, or time format
        if confidence < confidence_threshold or score_pattern.match(text) or time_pattern.match(text):
            continue

        # Determine if the text belongs to the left or right team based on bbox x-coordinates
        if bbox[0][0] < left_max_x:
            left_team_name = text
            left_max_x = bbox[0][0]
        elif bbox[0][0] > right_min_x:
            right_team_name = text
            right_min_x = bbox[0][0]

    return left_team_name, right_team_name

def process_home_away_stats(ocr_output, stat_name):
    if not ocr_output:
        return {f'{stat_name}_home': None, f'{stat_name}_away': None}

    items = ocr_output[0]
    text_items = []

    if not items:
        return {f'{stat_name}_home': None, f'{stat_name}_away': None}

    for item in items:
        coords = item[0]
        text, confidence = item[1]
        x_coords = [p[0] for p in coords]
        avg_x = sum(x_coords) / len(x_coords)
        text_items.append({'x': avg_x, 'text': text})

    numbers = []
    for item in text_items:
        text = item['text']
        nums = re.findall(r'\d+\.?\d*', text)
        if nums:
            for num in nums:
                try:
                    num_value = float(num)
                    if num_value.is_integer():
                        num_value = int(num_value)
                    numbers.append((item['x'], num_value))
                except ValueError:
                    continue
    numbers.sort(key=lambda x: x[0])
    
    if len(numbers) >= 2:
        home_value = numbers[0][1]
        away_value = numbers[-1][1]
    else:
        home_value = None
        away_value = None
    
    return {
        f'{stat_name}_home': home_value,
        f'{stat_name}_away': away_value
    }

def process_possession_stats(ocr_output):
    stats = process_home_away_stats(ocr_output, 'possession')
    home = stats['possession_home']
    away = stats['possession_away']

    return home, away

def determine_our_team(home_team, away_team, our_team):
    """
    Uses fuzzy matching to determine which team is ours.
    """
    home_match = difflib.get_close_matches(our_team, [home_team], n=1, cutoff=0.6)
    away_match = difflib.get_close_matches(our_team, [away_team], n=1, cutoff=0.6)

    if home_match:
        return home_team, away_team
    elif away_match:
        return away_team, home_team
    else:
        raise ValueError(f"Our team '{our_team}' could not be matched to either '{home_team}' or '{away_team}'.")
    