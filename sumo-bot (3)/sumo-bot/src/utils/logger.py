"""
Logger Setup — mit optionalem colorlog
"""
import logging
import os
from logging.handlers import RotatingFileHandler

try:
    import colorlog
    _HAS_COLORLOG = True
except ImportError:
    _HAS_COLORLOG = False


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    # Console Handler
    if _HAS_COLORLOG:
        console = colorlog.StreamHandler()
        console.setFormatter(colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)-8s%(reset)s | %(name)s | %(message)s",
            datefmt=date_fmt,
            log_colors={
                "DEBUG":    "cyan",
                "INFO":     "green",
                "WARNING":  "yellow",
                "ERROR":    "red",
                "CRITICAL": "bold_red",
            },
        ))
    else:
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    console.setLevel(logging.INFO)
    logger.addHandler(console)

    # File Handler
    os.makedirs("logs", exist_ok=True)
    file_handler = RotatingFileHandler("logs/sumo.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    return logger
