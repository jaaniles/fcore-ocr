import os
import cv2


def save_image(image, folder, filename):
    path = os.path.join(folder, filename)
    cv2.imwrite(path, image)