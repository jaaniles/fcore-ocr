import os
import cv2
import numpy as np
from data_extraction import extract_player_data
from image_processing import preprocess_image
from PIL import Image

def process_player_performance_screen(screenshot_path, ocr):
    """Process the player performance screen to extract data."""
    # Crop the image
    cropped_image_path = crop_player_performance(screenshot_path)
    
    # Read the image using OpenCV
    image = cv2.imread(cropped_image_path)
    
    # Preprocess the image
    processed_image = preprocess_image(image)
    
    # Run OCR
    result = ocr.ocr(processed_image, cls=True)
    
    # Extract player data from OCR result
    player_data = extract_player_data(result)

    # Return player data so it can be used in main.py
    return player_data

def crop_player_performance(image_path):
    """Crop the image to focus on the relevant area with player names and ratings."""
    image = Image.open(image_path)
    cropped_image = image.crop((1900, 200, 2800, 1250))  # Adjust coordinates for your use case
    cropped_image_path = os.path.join(os.path.dirname(image_path), "cropped_" + os.path.basename(image_path))
    cropped_image.save(cropped_image_path)
    print(f"Cropped screenshot saved to {cropped_image_path}")
    return cropped_image_path
