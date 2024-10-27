# Allow saving images for debugging purposes
import os
import pprint
import re
import cv2

from crop import crop_image
from image_processing import upscale_image
from ocr import annotate_ocr_results, paddleocr
from save_image import save_image
from squad.squad_financial_data_manager import SquadFinancialDataManager

DEBUG = True

FOLDER = './images/squad_financial'
os.makedirs(FOLDER, exist_ok=True)

# Initialize a manager to handle multiple sequential screenshots
manager = SquadFinancialDataManager()

POSITION = 'position'
NAME = 'name'
AGE = 'age'
VALUE = 'value'
WAGE = 'wage'
CONTRACT_LENGTH = 'contract_length'

async def process_squad_financial(screenshot_path):
    """
    Process the squad financial screen.
    """
    # Load the screenshot
    image = cv2.imread(screenshot_path)

    cropped_image = crop_image(image, (400, 300, 1750, 1300))
    save_image(cropped_image, FOLDER, "cropped_image.png")

    upscaled_image = upscale_image(cropped_image)

    ocr_results = await paddleocr(upscaled_image)
    print(ocr_results)
    if DEBUG:
        annotate_ocr_results(upscaled_image, FOLDER, ocr_results)
    new_players = []

    players = extract_player_data(ocr_results)
    # Loop through OCR results to process each player
    for player in players:
        # Generate a unique player_id by combining player name and value
        player_name = player['name']
        player_value = player['value']
        player_id = f"{player_name}_{player_value}"
        
        # Check if player is already processed
        if not manager.is_player_processed(player_id):
            # Create structured player data with separate keys for each stat
            player_data = {
                "player_id": player_id,
                "position": player['position'],
                "name": player_name,
                "age": player['age'],
                "market_value": player_value,
                "wage": player['wage'],
                "contract_length_months": convert_contract_length(player['contract_length']),
                "contract_length_string": player['contract_length'],
            }
            
            # Add new player to manager with full data
            manager.add_player(player_id, player_data)
            
            # Append structured player data to the new_players list
            new_players.append(player_data)

    # Retrieve all processed players with full data
    all_players = manager.get_all_players()

    pprint.pprint(all_players)

    return {
        "players": all_players,
    }

def extract_player_data(ocr_data):
    # Extract the data from the OCR output
    data = ocr_data[0]
    entries = []
    for item in data:
        bbox = item[0]  # The bounding box
        text_conf = item[1]
        text = text_conf[0]
        conf = text_conf[1]
        x_center = sum([point[0] for point in bbox]) / 4.0
        y_center = sum([point[1] for point in bbox]) / 4.0
        entries.append({
            'bbox': bbox,
            'text': text,
            'conf': conf,
            'x_center': x_center,
            'y_center': y_center
        })

    # Sort entries by y_center (vertical position)
    entries.sort(key=lambda x: x['y_center'])

    # Group entries into rows based on y_center proximity
    rows = []
    current_row = []
    current_y = None
    threshold = 30  # Adjust as needed based on the data

    for entry in entries:
        y = entry['y_center']
        if current_y is None:
            current_y = y
            current_row = [entry]
        elif abs(y - current_y) < threshold:
            current_row.append(entry)
        else:
            rows.append(current_row)
            current_row = [entry]
            current_y = y

    if current_row:
        rows.append(current_row)

    # Define column boundaries based on x_center (horizontal position)
    columns = [
        (POSITION, 300, 450),
        (NAME, 500, 850),
        (AGE, 1000, 1200),
        (VALUE, 1200, 1400),
        (WAGE, 1400, 1600),
        (CONTRACT_LENGTH, 1600, 1800)
    ]

    def get_column(x_center):
        for column_name, x_min, x_max in columns:
            if x_min <= x_center <= x_max:
                return column_name
        return None

    # Assign columns to each entry based on x_center
    for entry in entries:
        entry['column'] = get_column(entry['x_center'])

    # Extract data for each player
    players = []

    for row in rows:
        # Sort entries in row by x_center
        row.sort(key=lambda x: x['x_center'])
        columns_in_row = {}
        for entry in row:
            column_name = entry['column']
            if column_name:
                columns_in_row.setdefault(column_name, []).append(entry)

        # Initialize player data
        player = {}
        captain = False

        for column_name in [POSITION, NAME, AGE, VALUE, WAGE, CONTRACT_LENGTH]:
            entries_in_column = columns_in_row.get(column_name, [])
            if entries_in_column:
                if column_name == NAME:
                    texts = [e['text'] for e in entries_in_column]
                    # Check for captain marker 'c'
                    if 'c' in texts:
                        captain = True
                        texts.remove('c')
                    player_name = ' '.join(texts)
                    player[NAME] = player_name
                else:
                    # Choose the text with the highest confidence
                    best_entry = max(entries_in_column, key=lambda e: e['conf'])
                    field_value = best_entry['text']

                    # Apply converters to relevant columns
                    if column_name == VALUE:
                        player[column_name] = convert_market_value(field_value)
                    elif column_name == WAGE:
                        player[column_name] = convert_wage(field_value)
                    else:
                        player[column_name] = field_value
            else:
                player[column_name] = None  # Handle missing data

        player['is_captain'] = captain
        players.append(player)

    return players

def convert_market_value(value_str):
    """
    Convert a market value string like '800K' or '1.0M' into an integer.
    
    Args:
        value_str (str): Market value string with suffix 'K' for thousand or 'M' for million.
        
    Returns:
        int: The market value as an integer.
    """
    value_str = value_str.strip().upper()  # Standardize to uppercase
    if 'M' in value_str:
        # Convert millions to integer
        return int(float(value_str.replace('M', '')) * 1_000_000)
    elif 'K' in value_str:
        # Convert thousands to integer
        return int(float(value_str.replace('K', '')) * 1_000)
    else:
        return int(value_str)  # In case there's no suffix

def convert_wage(wage_str):
    """
    Convert a wage string like '3K', '19K', 'E3K', or '1000' into an integer (in thousands).
    """
    wage_str = wage_str.strip().upper().replace('E', '').replace('$', '')  # Remove currency symbols

    if 'K' in wage_str:
        return int(float(wage_str.replace('K', '')) * 1_000)
    elif 'M' in wage_str:
        return int(float(wage_str.replace('M', '')) * 1_000_000)
    else:
        # If no 'K' or 'M', assume it's already in whole units (like '1000' -> 1000)
        return int(wage_str)

def convert_contract_length(contract_str):
    """
    Convert contract length from a string format like '1y 7m' or '7m' to a total month count.
    
    Args:
        contract_str (str): The contract length string (e.g., '1y 7m', '7m').
    
    Returns:
        int: The total number of months for the contract.
    """
    years = 0
    months = 0
    
    # Match patterns like "1y 7m" or "7m"
    year_match = re.search(r"(\d+)\s*y", contract_str)
    month_match = re.search(r"(\d+)\s*m", contract_str)
    
    # Extract years if present
    if year_match:
        years = int(year_match.group(1))
    
    # Extract months if present
    if month_match:
        months = int(month_match.group(1))
    
    # Convert years to months and add additional months
    total_months = (years * 12) + months
    return total_months