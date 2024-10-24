import os
from reports.report_manager import get_cache_path

def abort_report(report):
    """Abort the current report and delete or mark the cached report as aborted."""
    cache_path = get_cache_path(report["reportId"], report["report_type"])
    if os.path.exists(cache_path):
        os.remove(cache_path)  # Delete the cached report
        print(f"Report {report['reportId']} aborted and removed from cache.")