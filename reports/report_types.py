from reports.submit_report import submit_match_report, submit_sim_match_report, submit_squad_report  
from screens.screen_types import (
    PLAYER_PERFORMANCE_EXTENDED,
    PRE_MATCH,
    MATCH_FACTS,
    PLAYER_PERFORMANCE,
    SIM_MATCH_FACTS,
    SIM_MATCH_PERFORMANCE,
    SIM_MATCH_PERFORMANCE_BENCH,
    SIM_PRE_MATCH,
    SQUAD_FINANCIAL,
)

MATCH_REPORT = "match_report"
SIM_MATCH_REPORT = "sim_match_report"
SQUAD_REPORT = "squad_report"

REPORT_TYPES = {
    MATCH_REPORT: {
        "initial_screen": PRE_MATCH,
        "required_screens": [MATCH_FACTS, PLAYER_PERFORMANCE],
        "optional_screens": [PLAYER_PERFORMANCE_EXTENDED],
        "submit_function": submit_match_report,
    },
    SIM_MATCH_REPORT: {
        "initial_screen": SIM_PRE_MATCH,
        "required_screens": [SIM_MATCH_FACTS, SIM_MATCH_PERFORMANCE, SIM_MATCH_PERFORMANCE_BENCH],
        "optional_screens": [],
        "submit_function": submit_sim_match_report,
    },
    SQUAD_REPORT: {
        "initial_screen": SQUAD_FINANCIAL,
        "required_screens": [],
        "optional_screens": [],
        "submit_function": submit_squad_report,
    }
}