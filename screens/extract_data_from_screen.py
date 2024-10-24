from screens.match_facts import process_match_facts
from screens.player_performance import process_player_performance_screen
from screens.pre_match import process_pre_match
from screens.screen_types import MATCH_FACTS, PLAYER_PERFORMANCE, PRE_MATCH, SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH, SIM_PRE_MATCH
from screens.sim_match_facts import process_sim_match_facts
from screens.sim_match_performance import process_sim_match_performance

async def extract_data_from_screen(screen_type, screenshot_path, team, ocr):
    """
    Process the screenshot data based on the detected screen type.
    Uses OCR to extract information and returns the processed data.
    """
    if screen_type == PRE_MATCH:
        return await process_pre_match(screenshot_path, ocr)
    
    elif screen_type == SIM_PRE_MATCH:
        return await process_pre_match(screenshot_path, ocr)
    
    elif screen_type == MATCH_FACTS:
        return await process_match_facts(screenshot_path, ocr)
    
    elif screen_type == PLAYER_PERFORMANCE:
        return await process_player_performance_screen(screenshot_path, ocr)
    
    elif screen_type == SIM_MATCH_FACTS:
        return await process_sim_match_facts(screenshot_path, team, ocr)
    
    elif screen_type == SIM_MATCH_PERFORMANCE:
        return await process_sim_match_performance(screenshot_path, team, ocr)
    
    elif screen_type == SIM_MATCH_PERFORMANCE_BENCH:
        return await process_sim_match_performance(screenshot_path, team, ocr)
    
    # Add more screen types as needed
    else:
        raise ValueError(f"Unknown screen type: {screen_type}")