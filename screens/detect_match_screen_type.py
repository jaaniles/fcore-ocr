import os
import re
import cv2
from crop import crop_image
from ocr import find_text_in_ocr, paddleocr
from positions import find_position_from_ocr
from save_image import save_image
from screens.check_is_regular_match import check_is_regular_match
from screens.screen_types import (
    MATCH_FACTS, PLAYER_PERFORMANCE, PLAYER_PERFORMANCE_EXTENDED, PRE_MATCH,
    SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH,
    SIM_PRE_MATCH
)

DEBUG = True

async def detect_match_screen_type(screenshot_path):
    if not os.path.exists(screenshot_path):
        raise FileNotFoundError(f"{screenshot_path} does not exist.")
    
    image = cv2.imread(screenshot_path)

    # Attempt each screen detection function and return the first detected type
    screen_type = await is_pre_match_screen(image)
    if screen_type:
        return screen_type

    screen_type = await is_match_facts_screen(image)
    if screen_type:
        return screen_type

    screen_type = await is_performance_screen(image)
    if screen_type:
        return screen_type

    screen_type = await is_performance_extended_screen(image)
    if screen_type:
        return screen_type

    screen_type = await is_sim_match_facts_screen(image)
    if screen_type:
        return screen_type

    screen_type = await is_sim_match_performance_screen(image)
    if screen_type:
        return screen_type

    return "unknown"

async def is_pre_match_screen(image):
    cropped_image = crop_image(image, (470, 1170, 1150, 1350))

    if DEBUG:
        save_image(cropped_image, "./images/debug/", "pre_match.png")

    ocr_result = await paddleocr(cropped_image)
    is_pre_match, _, _ = find_text_in_ocr(ocr_result, "play match")

    if not is_pre_match:
        return False
    
    is_regular_pre_match = await check_is_regular_match(cropped_image)
    if is_regular_pre_match:
        return PRE_MATCH
    
    return SIM_PRE_MATCH
    
async def is_match_facts_screen(image):
    cropped_image = crop_image(image, (1859, 420, 2500, 520))

    if DEBUG:
        save_image(cropped_image, "./images/debug/", "match_facts.png")

    ocr_result = await paddleocr(cropped_image)
    is_match_facts, _, _ = find_text_in_ocr(ocr_result, "possession %")

    if not is_match_facts:
        return False
    
    return MATCH_FACTS

async def is_performance_screen(image):
    cropped_image = crop_image(image, (1740, 300, 1840, 400))

    if DEBUG:
        save_image(cropped_image, "./images/debug/", "performance.png")

    ocr_result = await paddleocr(cropped_image)
    is_performance_screen = find_position_from_ocr(ocr_result)

    if not is_performance_screen:
        return False
    
    return PLAYER_PERFORMANCE

async def is_performance_extended_screen(image):
    cropped_image = crop_image(image, (400, 50, 1000, 200))

    if DEBUG:
        save_image(cropped_image, "./images/debug/", "performance_extended.png")

    ocr_result = await paddleocr(cropped_image)
    is_performance_extended_screen, _, _ = find_text_in_ocr(ocr_result, "player performance")

    if not is_performance_extended_screen:
        return False
    
    return PLAYER_PERFORMANCE_EXTENDED

async def is_sim_match_facts_screen(image):
    cropped_image = crop_image(image, (700, 380, 930, 440))

    if DEBUG:
        save_image(cropped_image, "./images/debug/", "sim_match_facts.png")

    ocr_result = await paddleocr(cropped_image)
    is_sim_match_facts_screen, _, _ = find_text_in_ocr(ocr_result, "possession %")

    if not is_sim_match_facts_screen:
        return False
    
    return SIM_MATCH_FACTS

async def is_sim_match_performance_screen(image):
    cropped_image = crop_image(image, (650, 380, 1000, 440))

    if DEBUG:
        save_image(cropped_image, "./images/debug/", "sim_match_performance.png")

    ocr_result = await paddleocr(cropped_image)
    is_sim_match_performance_screen, _, _ = find_text_in_ocr(ocr_result, "bench")

    if not is_sim_match_performance_screen:
        return False
    
    is_bench_view, _, _ = find_text_in_ocr(ocr_result, "n/a")

    if is_bench_view:
        return SIM_MATCH_PERFORMANCE_BENCH
    
    return SIM_MATCH_PERFORMANCE
