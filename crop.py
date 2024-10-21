def crop_image(image, coordinates):
    """Crop the image based on coordinates (x1, y1, x2, y2)."""
    return image[coordinates[1]:coordinates[3], coordinates[0]:coordinates[2]]

def crop_area(image, x, y, w, h):
    """Helper function to crop the area based on coordinates and ensure indices are integers."""
    x, y, w, h = int(x), int(y), int(w), int(h)  # Ensure all coordinates are integers
    return image[y:y+h, x:x+w]

def crop_region(image, center_x, center_y, width=100, height=100):
    x_start = max(center_x - width // 2, 0)
    y_start = max(center_y - height // 2, 0)
    x_end = x_start + width
    y_end = y_start + height
    cropped_image = image[y_start:y_end, x_start:x_end]
    return cropped_image