import os
import pprint

import cv2
from crop import crop_image
from ocr import annotate_ocr_results, paddleocr, parse_ocr
from save_image import save_image
from squad.squad_stats_data_manager import SquadStatsDataManager


DEBUG = True

FOLDER = './images/squad_stats'
os.makedirs(FOLDER, exist_ok=True)

# Initialize a manager to handle multiple sequential screenshots
manager = SquadStatsDataManager()

async def process_squad_stats(screenshot_path):
    # Load the screenshot
    image = cv2.imread(screenshot_path)

    # Crop main stats area
    cropped_stats_screen = crop_image(image, (1700, 500, 2550, 1300))
    image_height, image_width = cropped_stats_screen.shape[:2]
    stats_screen_ocr = await paddleocr(cropped_stats_screen)
    
    # Get bbox for "Totals"
    totals_coordinates = get_totals_bbox(stats_screen_ocr)
    if totals_coordinates is None:
        print("Totals not found in the OCR data.")
        return None

    # Define padding
    x_padding = 30
    y_padding = 30

    # Calculate crop coordinates based on "Totals" bbox
    left_x = max(int(totals_coordinates[0][0]) - x_padding, 0)
    top_y = max(int(totals_coordinates[0][1]) - y_padding, 0)
    bottom_y = min(int(totals_coordinates[3][1]) + y_padding, image_height)
    right_x = image_width  # End at the right edge of the original image

    # Use crop_image helper to crop around "Totals"
    cropped_totals = crop_image(cropped_stats_screen, (left_x, top_y, right_x, bottom_y))
    save_image(cropped_totals, FOLDER, "cropped_totals.png")

    # Perform OCR on cropped totals area
    ocr_ext = await paddleocr(cropped_totals)
    print(ocr_ext)

    if DEBUG:
        annotate_ocr_results(cropped_totals, FOLDER, ocr_ext)

    # Extract stats from OCR output
    stats = extract_stats(ocr_ext)
    pprint.pprint(stats)

    return stats

def extract_stats(ocr_data):
    """
    Extracts stat values from OCR data after sorting by the X-coordinate.
    """
    # Parse OCR data using the helper function
    parsed_entries = list(parse_ocr(ocr_data))

    # Sort entries by the X-coordinate of the first point in the bounding box
    entries_sorted = sorted(parsed_entries, key=lambda x: x[0][0][0])

    # Define the labels we expect in the specific order after "Totals"
    stat_labels = [
        "appearances", "goals", "assists", "clean_sheets",
        "yellow_cards", "red_cards", "rating_avg"
    ]

    # Initialize an empty dictionary to store the results
    stats = {}

    # Find the index of the "Totals" label in the sorted data
    for i, (_, label_text, _) in enumerate(entries_sorted):
        if label_text == "Totals":
            # Start reading the stats after the "Totals" label
            for j, stat_label in enumerate(stat_labels, start=i+1):
                if j < len(entries_sorted):  # Check bounds
                    _, stat_text, _ = entries_sorted[j]
                    stats[stat_label] = stat_text
            break

    return stats

def get_totals_bbox(ocr_data):
    """
    Extracts the bounding box (bbox) of the text "Totals" from OCR output.
    
    Parameters:
        ocr_data (list): The OCR data in the format [[bbox, (text, confidence)], ...].

    Returns:
        tuple or None: The bbox coordinates of "Totals" if found, else None.
    """

    for bbox, text, _ in parse_ocr(ocr_data):
        # Check if text is exactly "Totals" (case-sensitive)
            if text.strip() == "Totals":
                return bbox  # Return the bbox as soon as "Totals" is found

    # Return None if "Totals" is not found in the OCR data
    return None