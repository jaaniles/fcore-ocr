import os
import re

import cv2
import easyocr

from image_processing import grayscale_image, preprocess
from ocr import annotate_ocr_results, easyocr_number, extract_number_value, paddleocr, parse_ocr

DEBUG = True
FOLDER = './images/sim_match_facts'
os.makedirs(FOLDER, exist_ok=True)

def process_sim_match_facts(screenshot_path):
    image = cv2.imread(screenshot_path)
    result = paddleocr(image)

    annotate = image.copy()
    annotate_ocr_results(annotate, FOLDER, result)

    score, score_bbox = extract_score(result)

    teams = extract_teams(result)
    print(teams)
    print(score)

    extract_stats(result, score_bbox, image)
    #home_stats, away_stats = extract_stats_whole(result, score_bbox, image, ocr)
    #print(home_stats, away_stats)

    return True

def extract_stats(ocr_data, score_bbox, image):
    # Define the keywords we want to search for
    keywords = ["Possession %", "Shots", "Chances"]
    
    # Define the size of the area to crop below the keyword's bounding box
    crop_width = 400
    crop_height = 290
    
    # Define Y-offset to make the cropped area vertically centered below the keyword
    y_offset = -25  # This value can be adjusted for better centering
    
    # Calculate the X-center of the score_bbox (optional, if needed for home/away logic)
    score_x_center = (score_bbox[0][0] + score_bbox[2][0]) / 2

    # Step 1: Loop through the keywords
    for keyword in keywords:
        for bbox, text, _ in parse_ocr(ocr_data):
            # Step 2: Check if this text matches the current keyword
            if keyword.lower() in text.lower():
                # Calculate Y-center and X-center of the keyword's bounding box
                keyword_x_center = (bbox[0][0] + bbox[2][0]) / 2
                
                # Step 3: Determine if this is home or away based on comparison with the score X-center
                if keyword_x_center < score_x_center:
                    team_side = "home"
                else:
                    team_side = "away"

                # Step 4: Extract the bounding box details and center X
                y_min = int(bbox[2][1] + y_offset)  # Add vertical offset for better centering
                
                # Adjust x_min and x_max to center the crop area
                x_min = int(keyword_x_center - crop_width / 2)
                x_max = int(keyword_x_center + crop_width / 2)
                y_max = y_min + crop_height
                
                # Step 5: Crop the area below the keyword in the image
                cropped_area = image[y_min:y_max, x_min:x_max]
                # Step 6: Run OCR on the cropped image
                ocr_result = paddleocr(cropped_area)
                value = extract_number_value(ocr_result)

                # No value, trying easyocr
                if not value:
                    value = easyocr_number(cropped_area)

                # Still no value. Try grayscale image and run OCR again
                if not value:
                    processed_cropped_area = grayscale_image(cropped_area)
                    result = paddleocr(processed_cropped_area)
                    value = extract_number_value(result)

                # Try grayscale with easyocr
                if not value:
                    value = easyocr_number(processed_cropped_area)

                # Give up and set to 0
                if not value:
                    value = 0

                print(f"{team_side} {keyword}: {value}")

                # Optionally save the cropped area for visual debugging
                cropped_filename = os.path.join(FOLDER, f"{team_side}_{keyword}.png")
                cv2.imwrite(cropped_filename, cropped_area)
                    
                    


def extract_stats_whole(ocr_data, score_bbox):
    # Define the keywords we want to search for
    keywords = ["Possession %", "Shots", "Chances"]
    
    # Define thresholds for Y and X distance
    y_threshold = 200  # Allowable Y-variance below the keyword
    x_threshold = 300  # Allowable X-variance to ensure it's in the same "column"
    
    # Calculate the X-center of the score_bbox
    score_x_center = (score_bbox[0][0] + score_bbox[2][0]) / 2

    # Initialize dictionaries to store the home and away stats
    home_stats = {"Possession %": None, "Shots": None, "Chances": None}
    away_stats = {"Possession %": None, "Shots": None, "Chances": None}
    
    # Loop through the keywords
    # When a keyword is detected we grab the value below it
    # We then determine if the value belongs to the home or away team
    # by comparing the X-center of the keyword with the X-center of the score
    for keyword in keywords:
        for bbox, text, _ in parse_ocr(ocr_data):
            # Step 2: Check if this text matches the current keyword
            if keyword.lower() in text.lower():
                # Calculate Y-center and X-center of the keyword's bounding box
                keyword_y_center = (bbox[0][1] + bbox[2][1]) / 2
                keyword_x_center = (bbox[0][0] + bbox[2][0]) / 2
                
                # Step 3: Determine if this is home or away based on comparison with the score X-center
                if keyword_x_center < score_x_center:
                    team_side = "home"
                else:
                    team_side = "away"
                
                # Step 4: Loop through the items again to find the value below the keyword
                for group_below in ocr_data:
                    for item_below in group_below:
                        if isinstance(item_below, list) and len(item_below) == 2 and isinstance(item_below[1], tuple):
                            bbox_below, (value_text, _) = item_below
                            
                            # Calculate Y-center and X-center of the potential value's bounding box
                            value_y_center = (bbox_below[0][1] + bbox_below[2][1]) / 2
                            value_x_center = (bbox_below[0][0] + bbox_below[2][0]) / 2
                            
                            # Step 5: Check if the value is below the keyword (Y-axis) and within the same column (X-axis)
                            if (value_y_center > keyword_y_center and
                                abs(value_y_center - keyword_y_center) < y_threshold and
                                abs(value_x_center - keyword_x_center) < x_threshold):

                                try:
                                    value_text = int(value_text.strip())
                                except ValueError:
                                    break
                                
                                # Step 6: Store the value in the correct team's stats dictionary
                                if team_side == "home":
                                    home_stats[keyword] = value_text
                                else:
                                    away_stats[keyword] = value_text
                                break                 

    return home_stats, away_stats

def extract_teams(ocr_data):
    # Find the match score value and it's location
    score_value, score_bbox = extract_score(ocr_data)

    if not score_bbox or not score_value:
        print("Score not found, abort")
        return

    home_team_name, away_team_name = extract_team_names(ocr_data, score_bbox)

    return home_team_name, away_team_name

def extract_score(ocr_data):
    for bbox, text, _ in parse_ocr(ocr_data):
        # Use regex to find the score in the text
        if isinstance(text, str):
            score_pattern = re.compile(r"\d+\s*:\s*\d+")
            if re.search(score_pattern, text):
                score_value = text.strip()  
                score_bbox = bbox  # Store the score bounding box
                return score_value, score_bbox

                
def extract_team_names(ocr_data, score_bbox):
    y_threshold = 30  # Y-variance allowed for items to be considered in the same row

    # Use score location as anchor for team names
    # Team names are on the same row as the score.
    score_y_center = (score_bbox[0][1] + score_bbox[2][1]) / 2
    
    # Find all items in the same Y row based on threshold
    same_row_items = []
    for group in ocr_data:
        for item in group:
            if isinstance(item, list) and len(item) == 2 and isinstance(item[1], tuple):
                bbox, (text, _) = item
                item_y_center = (bbox[0][1] + bbox[2][1]) / 2
                if abs(item_y_center - score_y_center) < y_threshold:  # Check if Y is within threshold
                    same_row_items.append(item)
    
    # Grab the home and away team names
    # They are most likely located on the far-left and far-right
    if same_row_items:
        home_team = min(same_row_items, key=lambda x: x[0][0][0])  # Find smallest X-coordinate
        home_team_name = home_team[1][0].strip()  # Extract the home team name
        print(f"Home team name: {home_team_name}")

        away_team = max(same_row_items, key=lambda x: x[0][0][0])  # Find largest X-coordinate
        away_team_name = away_team[1][0].strip()
        print(f"Away team name: {away_team_name}")
    else:
        home_team_name = None
        away_team_name = None

    return home_team_name, away_team_name