from reports.submit_report import submit_match_report, submit_player_report, submit_sim_match_report  
from screens.screen_types import (
    PLAYER_PERFORMANCE_EXTENDED,
    PRE_MATCH,
    MATCH_FACTS,
    PLAYER_PERFORMANCE,
    SIM_MATCH_FACTS,
    SIM_MATCH_PERFORMANCE,
    SIM_MATCH_PERFORMANCE_BENCH,
    SIM_PRE_MATCH,
    SQUAD_ATTRIBUTES,
    SQUAD_FINANCIAL,
    SQUAD_STATS
)

MATCH_REPORT = "match_report"
SIM_MATCH_REPORT = "sim_match_report"
PLAYER_REPORT = "player_report"

REPORT_TYPES = {
    MATCH_REPORT: {
        "initial_screen": PRE_MATCH,
        "required_screens": [MATCH_FACTS, PLAYER_PERFORMANCE],
        "optional_screens": [PLAYER_PERFORMANCE_EXTENDED],
        "multi_capture_screens": [],
        "submit_function": submit_match_report,
    },
    SIM_MATCH_REPORT: {
        "initial_screen": SIM_PRE_MATCH,
        "required_screens": [SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH],
        "optional_screens": [],
        "multi_capture_screens": [],
        "submit_function": submit_sim_match_report,
    },
    PLAYER_REPORT: {
        "initial_screen": SQUAD_STATS,
        "required_screens": [SQUAD_FINANCIAL, SQUAD_ATTRIBUTES],
        "optional_screens": [],
        "multi_capture_screens": [],
        "submit_function": submit_player_report,
    }
}