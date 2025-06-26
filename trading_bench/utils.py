import logging
from datetime import datetime


def setup_logging(level=logging.INFO):
    """
    Configure root logger formatting and level.
    """
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=level
    )


def parse_date(date_str: str) -> datetime:
    """
    Parse an ISO-8601 date string into a datetime object.
    """
    return datetime.fromisoformat(date_str)
