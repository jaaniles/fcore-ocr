from reports.submit_report import submit_match_report, submit_sim_match_report  
from screens.screen_types import (
    PRE_MATCH,
    MATCH_FACTS,
    MATCH_FACTS_EXTENDED,
    PLAYER_PERFORMANCE,
    SIM_MATCH_FACTS,
    SIM_MATCH_PERFORMANCE,
    SIM_MATCH_PERFORMANCE_BENCH,
    SIM_PRE_MATCH,
)

MATCH_REPORT = "match_report"
SIM_MATCH_REPORT = "sim_match_report"

REPORT_TYPES = {
    MATCH_REPORT: {
        "initial_screen": PRE_MATCH,
        "required_screens": [MATCH_FACTS, PLAYER_PERFORMANCE],
        "optional_screens": [MATCH_FACTS_EXTENDED],
        "submit_function": submit_match_report,
    },
    SIM_MATCH_REPORT: {
        "initial_screen": SIM_PRE_MATCH,
        "required_screens": [SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH],
        "optional_screens": [],
        "submit_function": submit_sim_match_report,
    }
}