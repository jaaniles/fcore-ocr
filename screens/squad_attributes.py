from difflib import get_close_matches
from multiprocessing import process
import os
import pprint
import re

import cv2
from crop import crop_image
from image_processing import grayscale_image
from ocr import paddleocr, parse_ocr
from playstyles import is_golden_playstyle, match_playstyle
from positions import positions
from save_image import save_image
from squad.squad_attributes_data_manager import SquadAttributesDataManager

DEBUG = True

FOLDER = './images/squad_attributes'
os.makedirs(FOLDER, exist_ok=True)

# Initialize a manager to handle multiple sequential screenshots
manager = SquadAttributesDataManager()

async def process_squad_attributes(screenshot_path):
    """
    Process the squad attributes screen
    Extracts the attributes of one player at a time
    At the end compiles a list of all processed players for mass submitting
    """
    # Load the screenshot
    image = cv2.imread(screenshot_path)
    cropped_image = crop_image(image, (1700, 300, 2550, 960))
    save_image(cropped_image, FOLDER, "cropped_image.png")

    # Extract player data
    player_data = await extract_player_info(cropped_image)
    pprint.pprint(player_data)

    # Generate and store unique player ID
    player_id = f"{player_data.get('name', 'Unknown')}_{player_data.get('overall_rating', 'N/A')}"
    if not manager.is_player_processed(player_id):
        manager.add_player(player_id, player_data)

    # Return all players processed so far
    return manager.get_all_players()

async def extract_player_info(image):
    player = {}

    # Crop specific areas for OCR
    cropped_overall = crop_image(image, (70, 0, 180, 60))
    cropped_position = crop_image(image, (180, 0, 600, 60))

    cropped_name = crop_image(image, (50, 60, 700, 160))
    # Cover flag from the image so OCR does not get confused
    processed_name = cv2.rectangle(cropped_name, (0, 50), 
                                          (80, 100), (255, 255, 0), thickness=-1)

    cropped_info = crop_image(image, (70, 160, 800, 260))
    cropped_skills = crop_image(image, (70, 300, 460, 800))

    if DEBUG:
        save_image(cropped_overall, FOLDER, "cropped_overall.png")
        save_image(cropped_position, FOLDER, "cropped_position.png")
        save_image(processed_name, FOLDER, "cropped_name.png")
        save_image(cropped_info, FOLDER, "cropped_info.png")
        save_image(cropped_skills, FOLDER, "cropped_skills.png")

    ocr_overall = await paddleocr(cropped_overall)
    ocr_position = await paddleocr(cropped_position)
    ocr_name = await paddleocr(processed_name)
    ocr_info = await paddleocr(cropped_info)
    ocr_skills = await paddleocr(cropped_skills)

    player['overall_rating'] = extract_overall_rating(ocr_overall)
    player['position'] = extract_position(ocr_position)
    player['name'] = extract_full_name(ocr_name)
    player['info'] = extract_basic_info(ocr_info)

    is_gk = 'gk' in player['position']
    player['skills'] = extract_skills(ocr_skills, is_gk)

    top_row = crop_playstyles(image, 475, 521, amount=4)
    bottom_row = crop_playstyles(image, 506, 575, amount=3)

    playstyle_images = top_row + bottom_row
    playstyles = []

    for playstyle_image in playstyle_images:
        playstyle, _ = match_playstyle(playstyle_image, is_gk=is_gk)
        playstyles.append((playstyle))

    player['playstyles'] = playstyles

    return player


def crop_playstyles(image, start_x=475, start_y=521, width=55, height=55, amount=4):
    gap = 9

    """
    Crops the top row of playstyle icons (four in total) from the player screen.

    Parameters:
        image (numpy.ndarray): The original image from which to crop playstyles.
        start_x (int): Starting x-coordinate for the first playstyle.
        start_y (int): Starting y-coordinate for the first playstyle.
        width (int): Width of each playstyle icon.
        height (int): Height of each playstyle icon.
        amount (int): Number of playstyles to crop.
        
    Returns:
        list of numpy.ndarray: A list containing the cropped playstyle images.
    """
    cropped_playstyles = []
    
    for i in range(amount):
        # Calculate coordinates for each playstyle in the top row
        x1 = start_x + i * (width + gap)
        y1 = start_y
        x2 = x1 + width
        y2 = y1 + height
        # Use the crop_image helper function to crop each playstyle
        cropped_playstyle = crop_image(image, (x1, y1, x2, y2))
        
        if DEBUG:
            save_image(cropped_playstyle, FOLDER, f"cropped_playstyle_{i}.png")

        cropped_playstyles.append(cropped_playstyle)

    return cropped_playstyles


def extract_basic_info(info_ocr):
    """
    Extracts basic player information: age, height in feet and cm, weight in lbs and kg, and preferred foot from OCR data.
    
    Args:
        info_ocr (list): OCR data containing the basic info of a player.
        
    Returns:
        dict: Dictionary with extracted fields: age, height_feet, height_cm, weight_lbs, weight_kg, pref_foot.
    """
    # Initialize result dictionary with default None values
    info = {
        'age': None,
        'height_feet': None,
        'height_cm': None,
        'weight_lbs': None,
        'weight_kg': None,
        'pref_foot': None
    }

    # Define regex patterns for each field
    age_pattern = re.compile(r'Age\s*(\d{1,2})')
    height_pattern = re.compile(r'Height\s*(\d{1,2})\'(\d{1,2})?"?')
    weight_pattern = re.compile(r'Weight\s*(\d{1,3})\s*[lI1][bB][sS]', re.IGNORECASE)
    pref_foot_pattern = re.compile(r'Pref\.\s*Foot\s*([LR])', re.IGNORECASE)

    # Use parse_ocr to extract text and combine it into a single string
    text_parts = [text.strip() for _, text, _ in parse_ocr(info_ocr) if isinstance(text, str)]
    combined_text = ' '.join(text_parts).strip()

    # Find and parse age
    age_match = age_pattern.search(combined_text)
    if age_match:
        try:
            info['age'] = int(age_match.group(1))
        except ValueError:
            pass  # Skip if conversion fails

    # Find and parse height
    height_match = height_pattern.search(combined_text)
    if height_match:
        feet = int(height_match.group(1))
        inches = int(height_match.group(2)) if height_match.group(2) else 0
        info['height_feet'] = f"{feet}'{inches}\""
        info['height_cm'] = convert_height_to_cm(feet, inches)

    # Find and parse weight
    weight_match = weight_pattern.search(combined_text)
    if weight_match:
        lbs = int(weight_match.group(1))
        info['weight_lbs'] = lbs
        info['weight_kg'] = convert_weight_to_kg(lbs)

    # Find and parse preferred foot
    pref_foot_match = pref_foot_pattern.search(combined_text)
    if pref_foot_match:
        info['pref_foot'] = pref_foot_match.group(1).upper()

    return info


def extract_skills(ocr_skills, is_goalkeeper=False):
    """
    Extracts skills for a player by matching OCR labels and values in sequence.
    
    Args:
        ocr_skills (list): OCR data for skills.
        is_goalkeeper (bool): True if extracting goalkeeper skills, False for field player skills.

    Returns:
        dict: Dictionary of skills with extracted values.
    """
    # Define the expected skills in the correct order based on the player role
    expected_skills = (
        ['diving', 'handling', 'kicking', 'reflexes', 'speed', 'positioning']
        if is_goalkeeper else
        ['pace', 'shooting', 'passing', 'dribbling', 'defending', 'physical']
    )

    # Initialize skills dictionary with expected labels set to None
    skills = {skill: None for skill in expected_skills}
    
    # Extract text-only entries from OCR data using parse_ocr
    extracted_texts = [text.strip() for _, text, _ in parse_ocr(ocr_skills)]

    # Track the current index in extracted_texts
    i = 0
    for skill in expected_skills:
        # Use a while loop to find the skill label followed by a numeric value
        while i < len(extracted_texts) - 1:
            label = extracted_texts[i]
            value = extracted_texts[i + 1]
            
            # Use fuzzy matching to allow for OCR inconsistencies
            if get_close_matches(skill, [label], cutoff=0.7):
                if value.isdigit():  # Confirm that the next item is a number
                    skills[skill] = int(value)
                    i += 2  # Move past this pair
                    break  # Move to next skill
            else:
                i += 1  # Move to the next item if pair is invalid to prevent infinite loop
                print(f"Skipped: Label '{label}' did not match")  # Debug: Skipped item
    
    return skills


def extract_overall_rating(ocr_data):
    """
    Extracts and validates the overall rating from OCR data.
    """
    try:
        rating_text = ocr_data[0][0][1][0]
        rating = int(rating_text)
        if 1 <= rating <= 99:
            return rating
    except (IndexError, ValueError, TypeError):
        print("Failed to extract overall rating")  # Debug rating extraction failure
    
    return None

def extract_position(ocr_position_data):
    """
    Extracts valid positions from OCR data, handling combined strings without whitespace.
    """
    texts = []
    for item in ocr_position_data[0][0]:
        if isinstance(item, tuple):
            texts.append(item[0])

    combined_text = ''.join(texts).upper()

    extracted_positions = []
    i = 0
    while i < len(combined_text):
        match_found = False
        for pos in sorted(positions, key=len, reverse=True):
            if combined_text[i:i+len(pos)] == pos:
                extracted_positions.append(pos.lower())
                i += len(pos)
                match_found = True
                break
        if not match_found:
            i += 1
    return extracted_positions

def extract_full_name(name_ocr):
    """
    Extracts and combines parts of the name from OCR data.
    """
    name_parts = []

    def extract_text(data):
        if isinstance(data, list):
            for item in data:
                extract_text(item)
        elif isinstance(data, tuple) and isinstance(data[0], str):
            name_parts.append(data[0].strip())
    
    extract_text(name_ocr)
    full_name = " ".join(name_parts)
    return full_name.strip()

def convert_height_to_cm(feet, inches=0):
    """
    Converts height from feet and inches to centimeters.
    
    Args:
        feet (int): The height in feet.
        inches (int): The additional height in inches.
        
    Returns:
        float: The height in centimeters.
    """
    return round((feet * 30.48) + (inches * 2.54), 2)


def convert_weight_to_kg(lbs):
    """
    Converts weight from pounds to kilograms.
    
    Args:
        lbs (int): The weight in pounds.
        
    Returns:
        float: The weight in kilograms.
    """
    return round(lbs * 0.453592, 2)