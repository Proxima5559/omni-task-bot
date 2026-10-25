import logging

from app.config import settings


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)