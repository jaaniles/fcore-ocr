from screens.match_facts import process_match_facts
from screens.player_performance import process_player_performance_screen
from screens.player_performance_extended import process_player_performance_extended
from screens.pre_match import process_pre_match
from screens.screen_types import MATCH_FACTS, PLAYER_PERFORMANCE, PLAYER_PERFORMANCE_EXTENDED, PRE_MATCH, SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH, SIM_PRE_MATCH, SQUAD_ATTRIBUTES, SQUAD_FINANCIAL, SQUAD_STATS
from screens.sim_match_facts import process_sim_match_facts
from screens.sim_match_performance import process_sim_match_performance
from screens.squad_attributes import process_squad_attributes
from screens.squad_financial import process_squad_financial
from screens.squad_stats import process_squad_stats

async def extract_data_from_screen(screen_type, screenshot_path, team):
    """
    Process the screenshot data based on the detected screen type.
    Uses OCR to extract information and returns the processed data.
    """
    if screen_type == PRE_MATCH:
        return await process_pre_match(screenshot_path)
    
    elif screen_type == SIM_PRE_MATCH:
        return await process_pre_match(screenshot_path)
    
    elif screen_type == MATCH_FACTS:
        return await process_match_facts(screenshot_path, team)
    
    elif screen_type == PLAYER_PERFORMANCE:
        return await process_player_performance_screen(screenshot_path)
    
    elif screen_type == PLAYER_PERFORMANCE_EXTENDED:
        return await process_player_performance_extended(screenshot_path)
    
    elif screen_type == SIM_MATCH_FACTS:
        return await process_sim_match_facts(screenshot_path, team)
    
    elif screen_type == SIM_MATCH_PERFORMANCE:
        return await process_sim_match_performance(screenshot_path, team)
    
    elif screen_type == SIM_MATCH_PERFORMANCE_BENCH:
        return await process_sim_match_performance(screenshot_path, team)

    elif screen_type == SQUAD_FINANCIAL:
        return await process_squad_financial(screenshot_path)

    elif screen_type == SQUAD_ATTRIBUTES:
        return await process_squad_attributes(screenshot_path)
    
    elif screen_type == SQUAD_STATS:
        return await process_squad_stats(screenshot_path)

    else:
        raise ValueError(f"Unknown screen type: {screen_type}")