import sys
import os
from datetime import datetime
from pathlib import Path
from loguru import logger as loguru_logger
from dotenv import load_dotenv

load_dotenv()

DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_SIZE_LIMIT = os.getenv("LOG_SIZE_LIMIT", "10 MB")
SERVICE_NAME = os.getenv("SERVICE_NAME", "chatbot-service")

loguru_logger.remove()

LOG_DIR = Path("./logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_filename = f"{SERVICE_NAME}-{datetime.now().strftime('%Y%m%d')}.log"
LOG_FILE = LOG_DIR / log_filename

LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

loguru_logger.configure(
    handlers=[
        {
            "sink": sys.stdout,
            "level": LOG_LEVEL,
            "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        },
        {
            "sink": LOG_FILE,
            "level": LOG_LEVEL,
            "rotation": LOG_SIZE_LIMIT,
            "retention": "30 days",
            "compression": "zip",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            "serialize": True,
            "backtrace": True,
            "diagnose": True,
        },
        {
            "sink": str(LOG_DIR / f"{SERVICE_NAME}-daily.log"),
            "level": LOG_LEVEL,
            "rotation": "00:00",
            "retention": "30 days",
            "compression": "zip",
            "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            "serialize": True,
            "backtrace": True,
            "diagnose": True,
        },
    ]
)

logger = loguru_logger.bind(service=SERVICE_NAME)
