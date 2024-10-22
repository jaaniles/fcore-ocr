import logging
import os
import cv2
import easyocr
from paddleocr import PaddleOCR

reader = easyocr.Reader(['en'], gpu=True)
ocr = PaddleOCR(use_angle_cls=True, lang='en', use_gpu=True)

logging.getLogger("ppocr").setLevel(logging.ERROR)

def extract_number_value(ocr_result):
    for bbox, text, _ in parse_ocr(ocr_result):
        if text.isdigit() or text.replace('.', '', 1).isdigit():
            return text

def extract_number_value2(ocr_result):
    if ocr_result is None or len(ocr_result) == 0:
        print("No OCR result available to extract number.")
        return None
    
    # Traverse through the OCR result
    for detection_group in ocr_result:
        for detection in detection_group:
            if len(detection) >= 2 and isinstance(detection[1], tuple):
                text_data = detection[1][0]  # The detected text
                
                # Check if the text is a digit or a valid number
                if text_data.isdigit() or text_data.replace('.', '', 1).isdigit():
                    return text_data  

    return None

def annotate_ocr_results(image, folder, ocr_results):
    """
    Annotate the image with bounding boxes around OCR results and save the annotated image.
    """
    # Step 4: Annotate the image with bounding boxes around recognized text
    for result in ocr_results:
        for line in result:
            bbox = line[0]  # Get bounding box coordinates
            # Draw a red bounding box around each OCR result
            cv2.rectangle(image, 
                          (int(bbox[0][0]), int(bbox[0][1])), 
                          (int(bbox[2][0]), int(bbox[2][1])), 
                          (0, 0, 255), 2)  # Red bounding box

    # Save the annotated image
    cv2.imwrite(os.path.join(folder, f"annotated_image.png"), image)

def paddleocr(image):
    ocr_result = ocr.ocr(image)
    return ocr_result

def easyocr_number(image):
    """
    This function parses EasyOCR results and extracts the number or letter 'O'.
    
    Args:
        ocr_results (list): OCR output in the form of a list of bounding box, text, and confidence score.
    
    Returns:
        str: The extracted number or the letter 'O' from the OCR output. 
        Returns None if no valid number or 'O' is found.
    """
    ocr_result = reader.readtext(image)

    for result in ocr_result:
        # Each result consists of [bounding box, text, confidence]
        _, text, confidence = result

        # Clean the text by removing any surrounding whitespaces
        text = text.strip()
        
        # Check if the text is a valid number or 'O'
        if text.isdigit():  # Check if it's a number
            return text
        elif text.upper() == 'O':  # Check if it's the letter 'O' (case insensitive)
            return 0
    
    # If no number or 'O' is found, return None
    return None

def parse_ocr(ocr_data):
    """
    A helper function to iterate through OCR data, yielding bounding box and text.
    
    Parameters:
        ocr_data (list): The OCR result containing groups of OCR items.
    
    Yields:
        tuple: A tuple containing (bbox, text, confidence) for each OCR item.
    """
    if not ocr_data:
        return None

    for group in ocr_data:
        # Check if the group itself is valid and iterable
        if not group or group is None:
            continue  # Skip invalid or empty groups

        for item in group:
            # Check if the item is valid and contains a tuple with (bbox, (text, confidence))
            if not item or not isinstance(item, list) or len(item) != 2 or not isinstance(item[1], tuple):
                continue  # Skip invalid or malformed items

            try:
                bbox, (text, confidence) = item
                yield bbox, text, confidence
            except (ValueError, TypeError):
                continue