def extract_number_value(ocr_result):
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
                    print(f"Extracted number: {text_data}")
                    return text_data  # Return the first detected number

    # If no number is found, return None
    print("No numerical value found in OCR result")
    return None