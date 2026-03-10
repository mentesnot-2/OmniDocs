"""Structured logging for OmniDocs API."""


import logging
import sys


def setup_logging(level:str="INFO")->logging.Logger:
    """Configure and return the application logger."""

    logger = logging.getLogger("omnidocs")
    logger.setLevel(level)


    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        logger.addHandler(handler)
        return logger


logger = setup_logging()