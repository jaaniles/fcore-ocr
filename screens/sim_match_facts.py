import difflib
import os
import re

import cv2

from image_processing import grayscale_image
from ocr import annotate_ocr_results, easyocr_number, extract_number_value, paddleocr, parse_ocr
from save_image import save_image

DEBUG = True
FOLDER = './images/sim_match_facts'
os.makedirs(FOLDER, exist_ok=True)

async def process_sim_match_facts(screenshot_path, ocr, team):
    """
    Main function that processes match facts, returning relevant data.
    """
    our_team_name = team['teamName']

    image = cv2.imread(screenshot_path)
    result = await paddleocr(image, ocr)

    # Step 1: Process penalties
    penalties = process_penalties(result)

    # Step 2: Annotate OCR results for debugging purposes
    annotate_ocr_results(image.copy(), FOLDER, result)

    # Step 3: Extract score and team information
    score, score_bbox = extract_score(result)
    home_team, away_team = extract_teams(result)

    # Step 4: Determine our team and relevant stats
    our_team, their_team = determine_our_team(home_team, away_team, our_team_name)
    stats = await extract_stats(result, score_bbox, image, ocr)

    # Step 5: Determine match result, including penalties
    winner, home_score, away_score, is_draw, penalties = determine_match_result(score, penalties)

    # Step 6: Prepare final data output
    summary = format_match_summary(our_team, their_team, home_team, home_score, away_score, stats, winner, is_draw, penalties)

    print(summary)
    return summary

def format_match_summary(our_team, their_team, home_team, home_score, away_score, stats, winner, is_draw, penalties):
    """
    Prepares the final data output by identifying relevant stats and score details.
    """
    if our_team == home_team:
        our_score = home_score
        their_score = away_score
        our_possession = stats['home'].get('Possession %', None)
        their_possession = stats['away'].get('Possession %', None)
        our_shots = stats['home'].get('Shots', None)
        their_shots = stats['away'].get('Shots', None)
        our_chances = stats['home'].get('Chances', None)
        their_chances = stats['away'].get('Chances', None)

    else:
        our_score = away_score
        their_score = home_score
        our_possession = stats['away'].get('Possession %', None)
        their_possession = stats['home'].get('Possession %', None)
        our_shots = stats['away'].get('Shots', None)
        their_shots = stats['home'].get('Shots', None)
        our_chances = stats['away'].get('Chances', None)
        their_chances = stats['home'].get('Chances', None)

    if penalties:
        if our_team == home_team:
            penalties_score = {
                'our_penalty_score': penalties['home_penalty_score'],
                'their_penalty_score': penalties['away_penaltyscore']
            }
        else:
            penalties_score = {
                'our_penalty_score': penalties['away_penalty_score'],
                'their_penalty_score': penalties['home_penalty_score']
            }
    else:
        penalties_score = None


    # Return the formatted data
    return {
        'winner': winner,
        'our_score': our_score,
        'their_score': their_score,
        'our_team_name': our_team,
        'their_team_name': their_team,
        'is_draw': is_draw,
        'penalties': penalties_score,
        'stats': {
            'our_possession': our_possession,
            'their_possession': their_possession,
            'our_shots': our_shots,
            'their_shots': their_shots,
            'our_chances': our_chances,
            'their_chances': their_chances
        }
    }

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

async def extract_stats(ocr_data, score_bbox, image, ocr):
    """
    Extract statistics values for keywords like 'Possession %', 'Shots', and 'Chances' from an OCR-processed image.
    
    This function scans for the keyword in the OCR output, determines if it belongs to the home or away team based on 
    its position relative to the score bounding box, and then crops the relevant area to extract the value below the keyword.
    
    Parameters:
        ocr_data (list): The OCR result containing bounding boxes and text.
        score_bbox (list): The bounding box of the score (used to determine home/away sides).
        image (np.array): The image on which the OCR was run.
    
    Returns:
        dict: A dictionary containing two dictionaries:
              {'home': {'Possession %': value, 'Shots': value, 'Chances': value},
               'away': {'Possession %': value, 'Shots': value, 'Chances': value}}
    """
    
    # Define the keywords we want to search for
    keywords = ["Possession %", "Shots", "Chances"]
    
    # Define the size of the area to crop below the keyword's bounding box
    crop_width = 400
    crop_height = 290
    
    # Define Y-offset to make the cropped area vertically centered below the keyword
    y_offset = -25  # This value can be adjusted for better centering

    # Calculate the X-center of the score_bbox (optional, if needed for home/away logic)
    score_x_center = (score_bbox[0][0] + score_bbox[2][0]) / 2
    
    # Initialize dictionaries to store home and away stats
    home_stats = {"Possession %": None, "Shots": None, "Chances": None}
    away_stats = {"Possession %": None, "Shots": None, "Chances": None}

    # Step 1: Loop through the keywords
    for keyword in keywords:
        # Step 2: Loop through the OCR data to find matching keywords
        for bbox, text, _ in parse_ocr(ocr_data):
            # Check if this text matches the current keyword (case-insensitive)
            if keyword.lower() in text.lower():
                # Step 3: Calculate the X-center of the keyword's bounding box
                keyword_x_center = (bbox[0][0] + bbox[2][0]) / 2
                
                # Step 4: Determine if this is home or away based on comparison with the score X-center
                if keyword_x_center < score_x_center:
                    team_side = "home"
                    target_stats = home_stats
                else:
                    team_side = "away"
                    target_stats = away_stats

                # Step 5: Extract the bounding box details and calculate the cropping area
                y_min = int(bbox[2][1] + y_offset)  # Add vertical offset for better centering
                
                # Adjust x_min and x_max to center the crop area horizontally around the keyword
                x_min = int(keyword_x_center - crop_width / 2)
                x_max = int(keyword_x_center + crop_width / 2)
                y_max = y_min + crop_height

                # Step 6: Crop the area below the keyword in the image
                cropped_area = image[y_min:y_max, x_min:x_max]

                # Step 7: Run OCR on the cropped image to extract the value (start with paddleOCR)
                ocr_result = await paddleocr(cropped_area, ocr)
                value = extract_number_value(ocr_result)

                # Step 8: If no value is found, try easyOCR
                if not value:
                    value = easyocr_number(cropped_area)

                # Step 9: If still no value, apply grayscale processing and retry with paddleOCR
                if not value:
                    processed_cropped_area = grayscale_image(cropped_area)
                    result = await paddleocr(processed_cropped_area)
                    value = extract_number_value(result)

                # Step 10: Try easyOCR again on the grayscale image
                if not value:
                    value = easyocr_number(processed_cropped_area)

                # Step 11: If no value is found after all attempts, set it to 0
                if not value:
                    value = 0

                # Step 12: Store the extracted value in the correct team dictionary under the appropriate keyword
                target_stats[keyword] = value
                # Step 13: Optionally save the cropped area for visual debugging
                if DEBUG:
                    save_image(cropped_area, FOLDER, f"{team_side}_{keyword}.png")

    # Return the extracted statistics as dictionaries for home and away
    return {'home': home_stats, 'away': away_stats}

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

def process_penalties(ocr_data):
    """
    Check if penalties occurred in the match and determine the winner if applicable.
    
    Parameters:
        ocr_data (list): The OCR output from the image.
        
    Returns:
        dict: Contains the result of the penalty check and the winner if applicable.
              Example: {"penalties": True, "winner": "home", "home_score": X, "away_score": Y}
    """
    # Define the regex pattern for penalty shootout scenarios
    penalty_pattern = re.compile(r'(\d*)\s*PEN\s*(\d*)', re.IGNORECASE)

    home_penalty_score, away_penalty_score = None, None
    penalties_detected = False
    pen_bbox = None
    
    # Step 1: Find the "PEN" text and any potential numbers near it
    for bbox, text, _ in parse_ocr(ocr_data):
        match = re.search(penalty_pattern, text)
        if match:
            penalties_detected = True
            pen_bbox = bbox

            # Extract penalty scores from the PEN text, if available
            if match.group(1):  # Number before 'PEN'
                home_penalty_score = int(match.group(1))
            if match.group(2):  # Number after 'PEN'
                away_penalty_score = int(match.group(2))
            break

    # Step 2: If penalties were detected, search for missing scores near the "PEN" bbox
    if penalties_detected and (home_penalty_score is None or away_penalty_score is None):
        y_threshold = 200  # Threshold for proximity to the "PEN" bbox (vertical)
        pen_y_center = (pen_bbox[0][1] + pen_bbox[2][1]) / 2  # Y-center of the "PEN" bbox
        pen_top_y = pen_bbox[0][1]  # Top Y of the PEN bounding box
        pen_x_center = (pen_bbox[0][0] + pen_bbox[2][0]) / 2  # X-center of the "PEN" bbox

        # Search for penalty scores near the "PEN" bbox
        for bbox, text, _ in parse_ocr(ocr_data):
            try:
                number = int(text.strip())
            except ValueError:
                continue  # Skip non-numeric text

            current_y_center = (bbox[0][1] + bbox[2][1]) / 2
            current_bottom_y = bbox[2][1]  # Bottom Y-coordinate of the bbox

            # Check if the current number is close to the PEN text and below/aligned with it
            if (abs(current_y_center - pen_y_center) <= y_threshold) and (current_bottom_y >= pen_top_y):
                current_x_center = (bbox[0][0] + bbox[2][0]) / 2  # X-center of the number bbox

                # Assign the number to the home or away team based on its X-position relative to the PEN text
                if current_x_center < pen_x_center and home_penalty_score is None:
                    home_penalty_score = number
                elif current_x_center > pen_x_center and away_penalty_score is None:
                    away_penalty_score = number

    # Step 3: Determine the winner based on penalty scores
    if penalties_detected:
        if home_penalty_score is not None and away_penalty_score is not None:
            if home_penalty_score > away_penalty_score:
                return {"penalties": True, "winner": "home", "home_score": home_penalty_score, "away_score": away_penalty_score}
            elif away_penalty_score > home_penalty_score:
                return {"penalties": True, "winner": "away", "home_score": home_penalty_score, "away_score": away_penalty_score}
            else:
                return {"penalties": True, "winner": "draw", "home_score": home_penalty_score, "away_score": away_penalty_score}

    # If no penalties or scores are missing, return penalties as false or indeterminate result
    return {"penalties": penalties_detected, "winner": None}

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

        away_team = max(same_row_items, key=lambda x: x[0][0][0])  # Find largest X-coordinate
        away_team_name = away_team[1][0].strip()
    else:
        home_team_name = None
        away_team_name = None

    return home_team_name, away_team_name

def determine_match_result(score_str, penalties=None):
    """
    Determines the match result based on score and penalties.

    Parameters:
        score_str (str): The match score string in the format 'X : Y', allowing for whitespaces.
        penalties (dict): A dictionary containing penalty shootout information, if available.
                          Example: {'penalties': True, 'winner': 'away', 'home_score': 1, 'away_score': 3}

    Returns:
        tuple: (winner, home_score, away_score, is_draw, penalties)
               - winner (str): 'home', 'away', or 'is_draw'
               - home_score (int): Actual home team score (excluding penalties)
               - away_score (int): Actual away team score (excluding penalties)
               - is_draw (bool): True if the match was a draw, False otherwise
               - penalties (dict or None): Penalty scores or None if no penalties were played
    """

    # Extract home and away scores from the score string
    home_score, away_score = extract_match_score_values(score_str)

    # Handle penalties if they were played
    if penalties and penalties.get('penalties'):
        # Penalty winner exists, return the penalty result
        penalty_winner = penalties['winner']
        home_penalty_score = penalties['home_score']
        away_penalty_score = penalties['away_score']
        
        return penalty_winner, home_score, away_score, False, {'home_penalty_score': home_penalty_score, 'away_penalty_score': away_penalty_score}

    # Determine the winner based on regular match score (no penalties)
    if home_score > away_score:
        return 'home', home_score, away_score, False, None
    elif away_score > home_score:
        return 'away', home_score, away_score, False, None
    else:
        return 'is_draw', home_score, away_score, True, None
    

def extract_match_score_values(score_str):
    """Extracts the home and away score from the score string."""
    score_pattern = re.compile(r"(\d+)\s*:\s*(\d+)")
    match = re.search(score_pattern, score_str)

    if not match:
        raise ValueError(f"Invalid score format: '{score_str}'")
    
    return int(match.group(1)), int(match.group(2))
