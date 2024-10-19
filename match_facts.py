import re
import cv2

from crop import crop_image

def preprocess_image(image):
    # Step 1: Convert the image to Grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Step 2: Apply Gaussian blur to reduce background noise
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)

    # Step 3: Apply Morphological Transformation to preserve text structure
    # We use a morphological "close" operation to maintain text integrity
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    morph_image = cv2.morphologyEx(blurred_image, cv2.MORPH_CLOSE, kernel)
    
    # Step 4: Apply light thresholding to make text stand out (use a moderate threshold)
    _, thresh_image = cv2.threshold(morph_image, 160, 255, cv2.THRESH_BINARY_INV)

    return thresh_image

def process_match_facts(screenshot_path, ocr):
    # Load the screenshot
    image = cv2.imread(screenshot_path)

    # Define the coordinates for cropping the relevant data sections
    # Adjust these coordinates according to the regions you want to extract
    match_score_coords = (1900, 80, 3440 - 400, 1440 - 1270)  # Top-right corner (Team names and score)
    possession_stats_coords = (1950, 375, 3400 - 880, 1440 - 880)  # Center-right for possession stats
    shots_stats_coords = (1550, 710, 3440 - 500, 1440 - 600)  # Center-right for shots stats
    passes_stats_coords = (1550, 800, 3440 - 500, 920)  # Center-right for passes stats
    accuracy_stats_coords = (1550, 900, 3440 - 500, 1020)  # Center-right for pass accuracy stats
    tackles_stats_coords = (1550, 1000, 3440 - 500, 1100)  # Center-right for tackles stats

    # Crop and process each region
    cropped_match_score = crop_image(image, match_score_coords)
    cropped_possession_stats = crop_image(image, possession_stats_coords)
    cropped_shots_stats = crop_image(image, shots_stats_coords)
    cropped_passes_stats = crop_image(image, passes_stats_coords)
    cropped_accuracy_stats = crop_image(image, accuracy_stats_coords)
    cropped_tackles_stats = crop_image(image, tackles_stats_coords)

    # Preprocess the images before OCR
    processed_match_score = preprocess_image(cropped_match_score)
    processed_possession_stats = preprocess_image(cropped_possession_stats)
    processed_shots_stats = preprocess_image(cropped_shots_stats)
    processed_passes_stats = preprocess_image(cropped_passes_stats)
    processed_accuracy_stats = preprocess_image(cropped_accuracy_stats)
    processed_tackles_stats = preprocess_image(cropped_tackles_stats)

    # Run OCR on each processed image
    match_score_result = ocr.ocr(processed_match_score)
    possession_stats_result = ocr.ocr(processed_possession_stats)
    shots_stats_result = ocr.ocr(processed_shots_stats)
    passes_stats_result = ocr.ocr(processed_passes_stats)
    accuracy_stats_result = ocr.ocr(processed_accuracy_stats)
    tackles_stats_result = ocr.ocr(processed_tackles_stats)

    # Process the OCR results to extract match data
    score = process_match_score(match_score_result)
    possession_stats = process_possession_stats(possession_stats_result)
    shots_stats = process_shots_stats(shots_stats_result)
    passes_stats = process_passes_attempted_stats(passes_stats_result)
    accuracy_stats = process_pass_accuracy_stats(accuracy_stats_result)
    tackles_stats = process_tackles_stats(tackles_stats_result)

    # Combine all data into a single dictionary
    match_facts_data = {}
    match_facts_data.update(score)
    match_facts_data.update(possession_stats)
    match_facts_data.update(shots_stats)
    match_facts_data.update(passes_stats)
    match_facts_data.update(accuracy_stats)
    match_facts_data.update(tackles_stats)

    # Print the extracted data
    print("Extracted Match Facts Data:")
    for key, value in match_facts_data.items():
        print(f"{key}: {value}")


# Function to process match score
def process_match_score(ocr_output):
    items = ocr_output[0]
    text_items = []
    for item in items:
        coords = item[0]
        text, confidence = item[1]
        x_coords = [p[0] for p in coords]
        avg_x = sum(x_coords) / len(x_coords)
        text_items.append({'x': avg_x, 'text': text})
    text_items.sort(key=lambda x: x['x'])

    time = None
    home_team = None
    away_team = None
    home_score = None
    away_score = None

    for item in text_items:
        text = item['text']
        if re.match(r'\d{1,2}:\d{2}', text):
            time = text
        elif re.search(r'[-:]', text):
            score_text = text.replace(' ', '')
            match = re.match(r'(\d+)[-:](\d+)', score_text)
            if match:
                home_score = int(match.group(1))
                away_score = int(match.group(2))
        elif len(text) > 3:
            if home_team is None:
                home_team = text
            else:
                away_team = text
    
    return {
        'time': time,
        'home_team': home_team,
        'away_team': away_team,
        'home_score': home_score,
        'away_score': away_score
    }

# Generic function to process home/away stats
def process_home_away_stats(ocr_output, stat_name):
    items = ocr_output[0]
    text_items = []
    for item in items:
        coords = item[0]
        text, confidence = item[1]
        x_coords = [p[0] for p in coords]
        avg_x = sum(x_coords) / len(x_coords)
        text_items.append({'x': avg_x, 'text': text})

    numbers = []
    for item in text_items:
        text = item['text']
        nums = re.findall(r'\d+\.?\d*', text)
        if nums:
            for num in nums:
                try:
                    num_value = float(num)
                    if num_value.is_integer():
                        num_value = int(num_value)
                    numbers.append((item['x'], num_value))
                except ValueError:
                    continue
    numbers.sort(key=lambda x: x[0])
    
    if len(numbers) >= 2:
        home_value = numbers[0][1]
        away_value = numbers[-1][1]
    else:
        home_value = None
        away_value = None
    
    return {
        f'{stat_name}_home': home_value,
        f'{stat_name}_away': away_value
    }

# Function to process possession stats
def process_possession_stats(ocr_output):
    return process_home_away_stats(ocr_output, 'possession')

# Function to process shots stats
def process_shots_stats(ocr_output):
    return process_home_away_stats(ocr_output, 'shots')

# Function to process passes attempted stats
def process_passes_attempted_stats(ocr_output):
    return process_home_away_stats(ocr_output, 'passes_attempted')

# Function to process pass accuracy stats
def process_pass_accuracy_stats(ocr_output):
    return process_home_away_stats(ocr_output, 'pass_accuracy')

# Function to process tackles stats
def process_tackles_stats(ocr_output):
    return process_home_away_stats(ocr_output, 'tackles')

