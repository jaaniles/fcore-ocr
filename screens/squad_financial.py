import difflib
import os
import pprint
import re

import cv2

from crop import crop_image
from ocr import annotate_ocr_results, paddleocr, parse_ocr
from save_image import save_image


DEBUG = True

FOLDER = './images/squad_financial'
os.makedirs(FOLDER, exist_ok=True)

# Initialize a manager to handle multiple sequential screenshots

async def process_squad_financial(screenshot_path):
    # Load the screenshot
    image = cv2.imread(screenshot_path)

    cropped_image = crop_image(image, (1700, 570, 2550, 1200))
    save_image(cropped_image, FOLDER, "cropped_image.png")
    ocr_ext = await paddleocr(cropped_image)
    print(ocr_ext)

    if DEBUG:
        annotate_ocr_results(cropped_image, FOLDER, ocr_ext)

    player_data = extract_player_data(ocr_ext)
    pprint.pprint(player_data)

    return player_data

def sort_ocr_data(ocr_data):
    """
    Sorts OCR data by Y and X coordinates to structure it as rows.
    """
    # Use parse_ocr to get a cleaned list of (bbox, text, confidence)
    parsed_entries = list(parse_ocr(ocr_data))
    # Sort by Y, then by X
    return sorted(parsed_entries, key=lambda x: (x[0][0][1], x[0][0][0]))

def process_row(row, data_labels, contract_length_pattern):
    """
    Processes a single row to extract label-value pairs for relevant fields.
    """
    for i in range(len(row)):
        text = row[i][1]
        lower_text = text.lower()
        
        if "squad role" in lower_text:
            if i + 1 < len(row):
                data_labels["squad_role"] = row[i + 1][1]
        
        elif "wage" in lower_text:
            if i + 1 < len(row):
                wage_text = re.sub(r"[^\d]", "", row[i + 1][1])  # Remove non-numeric characters
                data_labels["wage"] = int(wage_text) if wage_text.isdigit() else None
        
        elif "market value" in lower_text:
            if i + 1 < len(row):
                market_value_text = row[i + 1][1]
                
                # Remove commas or periods used as thousands separators, then parse as integer
                value_match = re.search(r"(\d[\d,\.]*)", market_value_text)
                if value_match:
                    cleaned_value = value_match.group(1).replace(",", "").replace(".", "")
                    data_labels["market_value"] = int(cleaned_value) if cleaned_value.isdigit() else None

                # Check if there's a change percentage and set market_value_change
                change_match = re.search(r"(\d+%)", market_value_text)
                data_labels["market_value_change"] = change_match.group(1) if change_match else "0%"
        
        elif "contract length" in lower_text:
            if i + 1 < len(row):
                contract_length_string = row[i + 1][1]
                cleaned_length = re.sub(r"(\d)([A-Za-z])", r"\1 \2", contract_length_string)
                if contract_length_pattern.search(cleaned_length):
                    data_labels["contract_length_string"] = cleaned_length
                    data_labels["contract_length_months"] = convert_contract_length_to_months(cleaned_length)

def extract_player_data(ocr_data):
    """
    Extracts player data in a structured format by processing sorted OCR data rows.
    """
    # Initialize data labels with None values
    data_labels = {
        "squad_role": None,
        "wage": None,
        "market_value": None,
        "market_value_change": None,
        "contract_length_string": None,
        "contract_length_months": None
    }
    
    # Contract length pattern
    contract_length_pattern = re.compile(r"\b\d+\s*(year[s]?|month[s]?)\b", re.IGNORECASE)
    
    # Sort OCR data to structure as rows
    sorted_data = sort_ocr_data(ocr_data)
    
    # Process sorted data row-by-row
    current_row_y = None
    row_entries = []

    for entry in sorted_data:
        bbox, text, confidence = entry
        y_coord = bbox[0][1]
        
        # If y-coord changes, we consider it a new row
        if current_row_y is None or abs(y_coord - current_row_y) > 10:  # Allow for minor variations in y
            if row_entries:
                # Sort current row by X coordinate and process it
                row_entries.sort(key=lambda x: x[0][0][0])
                process_row(row_entries, data_labels, contract_length_pattern)
                row_entries = []
            current_row_y = y_coord

        row_entries.append(entry)
    
    # Process the last row if there are any remaining entries
    if row_entries:
        row_entries.sort(key=lambda x: x[0][0][0])
        process_row(row_entries, data_labels, contract_length_pattern)
    
    print(data_labels)
    return data_labels

def convert_contract_length_to_months(contract_length_string):
    """
    Convert a contract length string (e.g., "2 Year(s)" or "6 Month(s)") to the equivalent number of months.
    """
    match = re.match(r"(\d+)\s*(year[s]?|month[s]?)", contract_length_string, re.IGNORECASE)
    if match:
        number = int(match.group(1))
        unit = match.group(2).lower()
        if "year" in unit:
            return number * 12
        elif "month" in unit:
            return number
    return None