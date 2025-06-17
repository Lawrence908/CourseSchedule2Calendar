import os
import logging

LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO').upper()

logging.basicConfig(
    level=LOGGING_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
