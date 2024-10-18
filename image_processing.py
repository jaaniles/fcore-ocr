# image_processing.py

import os
from PIL import Image
import cv2
import numpy as np


def preprocess_image(image):
    """Preprocess the image to improve OCR accuracy."""
    # Upscale the image slightly to enhance OCR accuracy
    upscaled_image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    # Convert to grayscale
    gray = cv2.cvtColor(upscaled_image, cv2.COLOR_BGR2GRAY)

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

def preprocess_image2(image):
    """Preprocess the image to improve OCR accuracy, including edge detection."""
    # Upscale the image slightly to enhance OCR accuracy
    upscaled_image = cv2.resize(image, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    # Convert to grayscale
    gray = cv2.cvtColor(upscaled_image, cv2.COLOR_BGR2GRAY)

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