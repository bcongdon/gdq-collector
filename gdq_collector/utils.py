import pytz
from datetime import datetime
import logging
logger = logging.getLogger('gdq_collector.utils')


def get_truncated_time():
    u = datetime.utcnow()
    return u.replace(tzinfo=pytz.utc,
                     second=0,
                     microsecond=0)


def try_execute(func, default):
    try:
        return func()
    except Exception as e:
        logger.error(str(e))
        return default
