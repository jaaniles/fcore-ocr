import os
import cv2

from crop import crop_image
from ocr import paddleocr
from save_image import save_image

DEBUG = True

FOLDER = './images/player_report/'
os.makedirs(FOLDER, exist_ok=True)

async def detect_player_from_screen(screenshot_path):
    image = cv2.imread(screenshot_path)
    cropped_image = crop_image(image, (1700, 300, 2550, 960))
    save_image(cropped_image, FOLDER, "cropped_image.png")

    cropped_name = crop_image(cropped_image, (50, 60, 700, 160))
    processed_name = cv2.rectangle(cropped_name, (0, 50), 
                                                (80, 100), (255, 255, 0), thickness=-1)
    
    save_image(processed_name, FOLDER, "cropped_name.png")

    ocr_name = await paddleocr(processed_name)
    full_name = extract_full_name(ocr_name)

    print(full_name)

    return full_name
    
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