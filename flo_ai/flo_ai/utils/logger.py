import logging
import os

log_level = os.environ.get('FLO_AI_LOG_LEVEL', 'INFO')
log_format = (
    '%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s'
)

logging.basicConfig(
    level=log_level,
    format=log_format,
    datefmt='%Y-%m-%d %H:%M:%S',
)

logger = logging.getLogger('flo_ai')
