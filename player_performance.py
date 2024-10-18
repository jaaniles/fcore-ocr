# player_performance.py

import os
import cv2
import numpy as np
from data_extraction import extract_player_data
from image_processing import preprocess_image
from PIL import Image

def process_player_performance_screen(screenshot_path, ocr, overlay, on_data_extracted):
    """Process the player performance screen to extract data."""
    # Crop the image
    cropped_image_path = crop_player_performance(screenshot_path)
    # Read the image using OpenCV
    image = cv2.imread(cropped_image_path)
    # Preprocess the image
    processed_image = preprocess_image(image)
    # Run OCR
    result = ocr.ocr(processed_image, cls=True)
    # Draw bounding boxes (for debugging)
    for line in result:
        for text_line in line:
            box = np.array(text_line[0]).astype(int)  # Extract the bounding box coordinates
            # Draw the rectangle using OpenCV (in red color, thickness of 2)
            cv2.rectangle(processed_image, tuple(box[0]), tuple(box[2]), (0, 0, 255), 2)
    # Save the image with bounding boxes
    annotated_image_path = os.path.join('screenshots', 'annotated_' + os.path.basename(cropped_image_path))
    cv2.imwrite(annotated_image_path, processed_image)
    print(f"Annotated image with bounding boxes saved to {annotated_image_path}")
    # Extract player data
    player_data = extract_player_data(result)
    # Print or process the player data
    print("Extracted Player Data:")
    for player in player_data:
        print(player)
    # Call the callback function with the extracted data
    on_data_extracted(player_data)

def crop_player_performance(image_path):
    """Crop the image to focus on the relevant area with player names and ratings."""
    image = Image.open(image_path)
    # Adjust crop coordinates based on your screen resolution
    cropped_image = image.crop((1900, 200, 2800, 1250))  # Adjusted to exclude player positions
    cropped_image_path = os.path.join(os.path.dirname(image_path), "cropped_" + os.path.basename(image_path))
    cropped_image.save(cropped_image_path)
    print(f"Cropped screenshot saved to {cropped_image_path}")
    return cropped_image_path
