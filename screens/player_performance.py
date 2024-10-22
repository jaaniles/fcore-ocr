import os
import cv2
from image_processing import preprocess_image
from PIL import Image

from ocr import paddleocr

# Allow saving images for debugging purposes
DEBUG = True
FOLDER = './images/player_performance'
os.makedirs(FOLDER, exist_ok=True)

def process_player_performance_screen(screenshot_path):
    """Process the player performance screen to extract data."""
    # Crop the image
    cropped_image_path = crop_player_performance(screenshot_path)
    
    image = cv2.imread(cropped_image_path)
    
    processed_image = preprocess_image(image)
    
    result = paddleocr(processed_image)
    
    player_data = extract_player_data(result)

    return player_data


def extract_player_data(ocr_output):
    """Extract players' names and ratings from the OCR results."""
    items = []
    for line in ocr_output:
        for text_line in line:
            bbox = text_line[0]
            text = text_line[1][0]
            confidence = text_line[1][1]

            X_avg = sum([pt[0] for pt in bbox]) / 4
            Y_avg = sum([pt[1] for pt in bbox]) / 4

            items.append({'text': text, 'X': X_avg, 'Y': Y_avg, 'confidence': confidence})

    player_data = []
    # Threshold for considering which items are on the same line
    Y_THRESHOLD = 80  

    # Iterate over items and convert them to float
    # is float -> it's a match rating
    for item in items:
        text = item['text']
        try:
            # Float conversion
            float(text)
            matchRating = text

            # Grab coordinates. We will use these to find the player name
            rating_Y = item['Y']
            rating_X = item['X']
            name_items = []
            for name_item in items:
                if name_item == item:
                    continue
                if abs(name_item['Y'] - rating_Y) <= Y_THRESHOLD and name_item['X'] < rating_X:
                    name_items.append(name_item)
            # Sort name_items by X
            name_items.sort(key=lambda x: x['X'])
            # Combine names into fullName
            fullName = ' '.join([ni['text'] for ni in name_items])

            # Optionally, split fullName into firstName and lastName
            name_parts = fullName.strip().split()
            if len(name_parts) >= 2:
                firstName = name_parts[0]
                lastName = ' '.join(name_parts[1:])
            elif len(name_parts) == 1:
                firstName = name_parts[0]
                lastName = ''
            else:
                firstName = ''
                lastName = ''
            player = {
                'firstName': firstName,
                'lastName': lastName,
                'fullName': fullName,
                'matchRating': matchRating
            }
            player_data.append(player)
        except ValueError:
            continue

    return player_data


def crop_player_performance(image_path):
    """Crop the image to focus on the relevant area with player names and ratings."""
    image = Image.open(image_path)
    cropped_image = image.crop((1900, 200, 2800, 1250)) 
    cropped_image_path = os.path.join(FOLDER, "cropped_" + os.path.basename(image_path))

    if DEBUG:
        cropped_image.save(cropped_image_path)
    
    return cropped_image_path
