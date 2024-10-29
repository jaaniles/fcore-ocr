import cv2
import numpy as np
from ocr import find_text_in_ocr, paddleocr

async def check_is_regular_match(image):
    """
    Checks if match is going to be played as a regular match or simulated
    by checking the "Play Match" text background color.
    If the background is white, the match is regular.
    """
    ocr_result = await paddleocr(image)

    if not ocr_result:
        return False

    bbox, _, _ = find_text_in_ocr(ocr_result, "Play Match")

    if not bbox:
        print("Error: could not find anchor for checking match type.")
        return False
    
    # The bounding box of the "Play Match" text is stored in `anchor`
    x1, y1 = int(bbox[0][0]), int(bbox[0][1])  # Top-left corner
    x2, y2 = int(bbox[2][0]), int(bbox[2][1])  # Bottom-right corner

    # Ensure the bounding box is within the image dimensions
    h, w, _ = image.shape
    if x1 < 0 or y1 < 0 or x2 > w or y2 > h:
        print("Error: Bounding box is out of image bounds.")
        return False

    # Extract the region of interest (ROI) from the image using the bounding box
    roi = image[y1:y2, x1:x2]

    # Convert the image (ROI) to grayscale for color intensity analysis
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Check if the majority of pixels in the ROI are white (value close to 255)
    white_threshold = 200  # Pixel intensity value to consider as "white"
    white_pixels = np.sum(gray_roi >= white_threshold)
    total_pixels = gray_roi.size
    white_ratio = white_pixels / total_pixels

    # If the majority of the pixels are white, consider it as a regular match
    if white_ratio > 0.5:  # Adjust this threshold if needed
        return True  # Regular match (selected)
    else:
        return False  # Simulated match (not selected)