import cv2
import numpy as np

def preprocess_image(image, upscale=True):
    """Preprocess the image to improve OCR accuracy."""
    # Upscale the image slightly to enhance OCR accuracy
    #upscaled_image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    if upscale:
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    else:
        image = image

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a mild Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # Apply Otsu's thresholding
    _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Convert back to BGR for PaddleOCR
    processed_image = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    return processed_image

def upscale_image(image, amount=1.5): 
    """Preprocess the image to improve OCR accuracy."""
    # Upscale the image slightly to enhance OCR accuracy
    upscaled_image = cv2.resize(image, None, fx=amount, fy=amount, interpolation=cv2.INTER_LINEAR)

    return upscaled_image

def increase_vibrance(image, increase_amount=50):
    """
    Increase the vibrance of an image by manipulating the saturation in HSV color space.
    
    Args:
        image: Input BGR image.
        increase_amount: The amount by which to increase the vibrance (saturation).
        
    Returns:
        Vibrance enhanced image.
    """
    # Convert image to HSV color space
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    # Split into H, S, V channels
    h, s, v = cv2.split(hsv)
    
    # Increase the saturation channel
    s = np.clip(s + increase_amount, 0, 255)
    
    # Merge the channels back
    hsv_enhanced = cv2.merge([h, s, v])
    
    # Convert back to BGR color space
    vibrant_image = cv2.cvtColor(hsv_enhanced, cv2.COLOR_HSV2BGR)
    
    return vibrant_image

# Works very well for dark backgrounds
def preprocess(image):
    # Step 1: Convert the image to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Step 2: Calculate the average brightness of the grayscale image
    avg_brightness = np.mean(gray_image)

    # Step 3: Define brightness thresholds
    dark_threshold = 100
    medium_brightness_threshold = 180

    print("AVG BRIGHTNESS", avg_brightness)

    if avg_brightness < dark_threshold:
        blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
        _, threshold_image = cv2.threshold(blurred_image, 0, 200, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = np.ones((3, 3), np.uint8)
        dilated_image = cv2.dilate(threshold_image, kernel, iterations=1)
        sharpening_kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharpened_image = cv2.filter2D(dilated_image, -1, sharpening_kernel)

        return sharpened_image

    elif avg_brightness > dark_threshold and avg_brightness < medium_brightness_threshold:
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        return gray_image
    else:
        return image
