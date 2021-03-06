import six
import logging
logger = logging.getLogger(__name__)


minify_keys = {
    "num_emotes": "e",
    "total_donations": "m",
    "num_donations": "d",
    "num_chats": "c",
    "num_tweets": "t",
    "num_viewers": "v",
    "time": "time",
}


def minify(rows):
    return [{minify_keys[k]: v for k, v in six.iteritems(i)} for i in rows]


def rollback_on_exception(conn):
    def decorator(func):
        def executor(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                logger.error(e)
                conn.rollback()

        return executor
    return decorator


if __name__ == "__main__":
    in_ = [
        {
            "num_emotes": 0,
            "total_donations": 5.0,
            "time": "2016-12-27T16:57:00+00:00",
            "num_donations": 1,
            "num_chats": 0,
            "num_tweets": 0,
            "num_viewers": None,
        }
    ]
    out_ = [
        {
            "c": 0,
            "e": 0,
            "d": 1,
            "v": None,
            "m": 5.0,
            "t": 0,
            "time": "2016-12-27T16:57:00+00:00",
        }
    ]
    assert minify(in_) == out_
