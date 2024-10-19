def crop_image(image, coordinates):
    """Crop the image based on coordinates (x1, y1, x2, y2)."""
    return image[coordinates[1]:coordinates[3], coordinates[0]:coordinates[2]]