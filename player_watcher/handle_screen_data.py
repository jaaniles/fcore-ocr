from screens.screen_types import SQUAD_ATTRIBUTES, SQUAD_FINANCIAL, SQUAD_STATS
from screens.squad_attributes import process_squad_attributes
from screens.squad_financial import process_squad_financial
from screens.squad_stats import process_squad_stats

async def handle_screen_data(screen_type, screenshot_path):
    """
    Process the screenshot data based on the detected screen type.
    Uses OCR to extract information and returns the processed data.
    """
    if screen_type == SQUAD_FINANCIAL:
        return await process_squad_financial(screenshot_path)

    elif screen_type == SQUAD_ATTRIBUTES:
        return await process_squad_attributes(screenshot_path)
    
    elif screen_type == SQUAD_STATS:
        return await process_squad_stats(screenshot_path)

    else:
        raise ValueError(f"Unknown screen type: {screen_type}")