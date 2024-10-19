# image_processing.py

import os
from PIL import Image
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

def upscale_image(image): 
    """Preprocess the image to improve OCR accuracy."""
    # Upscale the image slightly to enhance OCR accuracy
    upscaled_image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    return upscaled_image

def preprocess_number_image(image, upscale=True):
    """
    Preprocess the player form image for better OCR results.
    Steps:
    - Convert the image to grayscale
    - Apply adaptive or binary thresholding to improve contrast
    - Use morphological operations (dilate/erode) to clean up noise
    """
    # Upscale the image slightly to enhance OCR accuracy
    if upscale:
        image = cv2.resize(image, None, fx=3, fy=3, interpolation=cv2.INTER_LINEAR)
    else:
        image = image

    # Step 1: Convert to grayscale
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply a mild Gaussian Blur to reduce noise
    blurred = cv2.GaussianBlur(gray_image, (9, 9), 0)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # Step 2: Apply binary thresholding to improve contrast
    # This will make the number stand out clearly from the background
    _, threshold_image = cv2.threshold(enhanced, 90, 255, cv2.THRESH_BINARY)

    # Optional: Apply additional blur to further enhance the 'haloing' effect
    final_blur = cv2.GaussianBlur(dilated_image, (3, 3), 0)

    # Return the preprocessed image
    return final_blur

def preprocess_image2(image, upscale=True):
    """Preprocess the image to improve OCR accuracy, including edge detection."""
    # Upscale the image slightly to enhance OCR accuracy
    #upscaled_image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    if upscale:
        image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)
    else:
        image = image

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise while keeping edges
    filtered_image = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)

    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(16, 16))
    enhanced = clahe.apply(filtered_image)

    # Apply adaptive thresholding instead of Otsu's thresholding
    adaptive_thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    # Apply morphological closing to fill gaps in text and reduce noise
    kernel = np.ones((2, 2), np.uint8)
    morph_image = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)

    # Apply Canny edge detection to further enhance text boundaries
    edges = cv2.Canny(morph_image, 100, 200)

    # Convert back to BGR for PaddleOCR
    processed_image = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    return processed_image