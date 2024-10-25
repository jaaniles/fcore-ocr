from functools import partial
import asyncio
from timed_import import timed_import

ocr_initialization_task = None
PaddleOCR = timed_import('paddleocr', 'PaddleOCR')

async def initialize_paddleocr():
    """Initialize PaddleOCR asynchronously"""
    print("Initializing PaddleOCR...")
    loop = asyncio.get_event_loop()
    ocr_partial = partial(PaddleOCR, use_angle_cls=True, lang='en', use_gpu=True)
    ocr_instance = await loop.run_in_executor(None, ocr_partial)
    print("PaddleOCR initialized.")
    return ocr_instance

async def get_ocr_instance():
    """Returns the initialized PaddleOCR instance, awaiting initialization if needed."""
    global ocr_initialization_task
    if ocr_initialization_task is None:
        ocr_initialization_task = asyncio.create_task(initialize_paddleocr())
    else:
        if not ocr_initialization_task.done():
            print("Waiting for OCR to be initialized...")

    ocr_instance = await ocr_initialization_task
    return ocr_instance