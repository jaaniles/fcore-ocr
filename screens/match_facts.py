import os
import re
import cv2

from crop import crop_image, crop_region
from image_processing import upscale_image
from ocr import extract_number_value, paddleocr

DEBUG = True
FOLDER = './images/match_facts'
os.makedirs(FOLDER, exist_ok=True)

async def process_match_facts(screenshot_path, ocr):
    image = cv2.imread(screenshot_path)

    # Co-ordinates for cropping the stats
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
    
    # Apply OCR to each cropped area
    match_score_result = await paddleocr(cropped_match_score, ocr)
    possession_stats_result = await paddleocr(cropped_possession, ocr)
    shots_result = await paddleocr(cropped_shots, ocr)
    passes_result = await paddleocr(cropped_passes, ocr)
    accuracy_result = await paddleocr(cropped_accuracy, ocr)
    tackles_result = await paddleocr(cropped_tackles, ocr)

    home, away = process_match_score(match_score_result)
    home_possession, away_possession = process_possession_stats(possession_stats_result)
    home_shots, away_shots = await extract_value(shots_result, "Shots", cropped_shots, ocr)
    home_passes, away_passes = await extract_value(passes_result, "Passes", cropped_passes, ocr)
    home_accuracy, away_accuracy = await extract_value(accuracy_result, "Accuracy", cropped_accuracy, ocr)
    home_tackles, away_tackles = await extract_value(tackles_result, "Tackles", cropped_tackles, ocr)
    home_team = home['team_name']
    away_team = away['team_name']
    home_score = home['score']
    away_score = away['score']

    print("Match Score:")
    print(home_team + " - " + away_team)
    print(str(home_score) + " - " + str(away_score))

    print("Possession Stats:")
    print(home_possession, away_possession)

    print("Shots:")
    print(home_shots, away_shots)

    print("Passes:")
    print(home_passes, away_passes)

    print("Accuracy:")
    print(home_accuracy, away_accuracy)

    print("Tackles:")
    print(home_tackles, away_tackles)

    return {
        'home_team': home_team,
        'away_team': away_team,
        'home_score': home_score,
        'away_score': away_score,
        'home_possession': home_possession,
        'away_possession': away_possession,
        'home_shots': home_shots,
        'away_shots': away_shots,
        'home_passes': home_passes,
        'away_passes': away_passes,
        'home_accuracy': home_accuracy,
        'away_accuracy': away_accuracy,
        'home_tackles': home_tackles,
        'away_tackles': away_tackles
    }

# Helper function to calculate the center of a bounding box
def calculate_center(bounding_box):
    x_coords = [point[0] for point in bounding_box]
    y_coords = [point[1] for point in bounding_box]
    center_x = int(sum(x_coords) / len(x_coords))
    center_y = int(sum(y_coords) / len(y_coords))
    return center_x, center_y

# Main function to extract values
async def extract_value(ocr_result, keyword, image, ocr):
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

                    left_ocr_result = await paddleocr(cropped_left, ocr) 
                    if not left_ocr_result or left_ocr_result == [None] or len(left_ocr_result) == 0:
                        left_ocr_result = []
                    right_ocr_result = await paddleocr(cropped_right, ocr)
                    if not right_ocr_result or right_ocr_result == [None] or len(right_ocr_result) == 0:
                        right_ocr_result = []
                    
                    home = extract_number_value(left_ocr_result)
                    away = extract_number_value(right_ocr_result)

                    return home, away

    return None, None

def process_match_score(ocr_output):
    if not ocr_output:
        return {'home_team': None, 'away_team': None, 'home_score': None, 'away_score': None}
    
    items = ocr_output[0]
    text_items = []

    if not items:
        return {'home_team': None, 'away_team': None, 'home_score': None, 'away_score': None}

    for item in items:
        coords = item[0]
        text, confidence = item[1]
        x_coords = [p[0] for p in coords]
        avg_x = sum(x_coords) / len(x_coords)
        text_items.append({'x': avg_x, 'text': text})
    text_items.sort(key=lambda x: x['x'])

    home_team = None
    away_team = None
    home_score = None
    away_score = None

    for item in text_items:
        text = item['text']
        if re.search(r'[-:]', text):
            score_text = text.replace(' ', '')
            match = re.match(r'(\d+)[-:](\d+)', score_text)
            if match:
                home_score = int(match.group(1))
                away_score = int(match.group(2))
        elif len(text) > 3:
            if home_team is None:
                home_team = text
            else:
                away_team = text
    
    home = {
        'team_name': home_team,
        'score': home_score
    }

    away = {
        'team_name': away_team,
        'score': away_score
    }

    return home, away

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
