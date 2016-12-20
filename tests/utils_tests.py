from agdq_collector import utils
import pytz


def test_truncated_time():
    t = utils.get_truncated_time()
    assert t.second == 0
    assert t.microsecond == 0
    assert t.tzinfo == pytz.utc
