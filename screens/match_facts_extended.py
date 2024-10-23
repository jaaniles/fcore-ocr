import os
import cv2

from image_processing import grayscale_image
from ocr import annotate_ocr_results, paddleocr


DEBUG = True
FOLDER = './images/match_facts_extended'
os.makedirs(FOLDER, exist_ok=True)

async def process_match_facts_extended(screenshot_path):
    """Process the player performance extended screen to extract data."""
    image = cv2.imread(screenshot_path)
    grayscale = grayscale_image(image)

    result = await paddleocr(grayscale)

    annotate_ocr_results(grayscale, FOLDER, result)  