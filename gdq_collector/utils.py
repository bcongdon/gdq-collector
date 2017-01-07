import pytz
from datetime import datetime


def get_truncated_time():
    u = datetime.utcnow()
    return u.replace(tzinfo=pytz.utc,
                     second=0,
                     microsecond=0)
