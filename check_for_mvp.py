import cv2

from crop import crop_area
from save_image import save_image

DEBUG = True

def check_for_mvp(image, last_name_bbox, player_name, search_x_offset=50, folder="./images"):
    """
    Check if the player has the MVP icon based on color detection.
    
    Parameters:
        image (np.array): The original image containing the player data.
        last_name_bbox (list): The bounding box of the player's last name.
        player_name (str): Name of the player being checked for MVP.
        search_x_offset (int): Distance to move left from the last name's x_min to search for the MVP icon.
        save (bool): Whether to save the cropped area for debugging.
    
    Returns:
        bool: True if the player is the MVP, False otherwise.
    """
    # Get the coordinates for the last name's bounding box
    x_min, y_min = last_name_bbox[0]  # Top-left corner of the last name
    x_max, y_max = last_name_bbox[2]  # Bottom-right corner of the last name

    # Calculate the midpoint for Y and a leftward X value to search for the icon
    y_mid = (y_min + y_max) // 2
    search_x = x_min - search_x_offset  # Use the provided offset for searching leftwards

    # Crop a small 30x30 pixel area for analysis
    cropped_area = crop_area(image, search_x, y_mid - 15, 30, 30)

    # Ensure the cropped area is valid (not empty)
    if cropped_area is None or cropped_area.size == 0:
        print(f"Error: Cropped area for {player_name} is empty or invalid.")
        return False
    
    # Optionally save the cropped image for debugging
    if DEBUG:
        save_image(cropped_area, folder, f"mvp.png")

    # Convert the cropped area to HSV
    try:
        hsv_cropped = cv2.cvtColor(cropped_area, cv2.COLOR_BGR2HSV)
    except cv2.error as e:
        print(f"OpenCV error when converting cropped area to HSV for {player_name}: {e}")
        return False

    # Define HSV color range for detecting gold/yellow color
    lower_gold = (20, 100, 100)
    upper_gold = (30, 255, 255)

    # Create a mask to detect yellow/gold pixels
    mask = cv2.inRange(hsv_cropped, lower_gold, upper_gold)

    # Calculate the percentage of yellow pixels
    yellow_percentage = (cv2.countNonZero(mask) / mask.size) * 100

    return yellow_percentage > 50  # Return True if more than 75% of the area is yellow/gold