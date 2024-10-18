# data_extraction.py

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

    # List to hold player data
    player_data = []
    # Threshold for considering items in the same line
    Y_THRESHOLD = 80  # Adjust as needed based on OCR results

    # Process each item that is a match rating (i.e., text can be converted to float)
    for item in items:
        text = item['text']
        try:
            # Try to convert text to float (for match rating)
            float(text)
            matchRating = text
            rating_Y = item['Y']
            rating_X = item['X']
            # Collect names to the left of the rating and within Y_THRESHOLD
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
            # Not a match rating, skip
            continue

    return player_data
