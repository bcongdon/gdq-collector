import requests
from dateutil.parser import parse
from datetime import timedelta, datetime
from credentials import sns_arn
from credentials import postgres as p_creds
import boto3
import pytz
import logging
import psycopg2
from utils import rollback_on_exception

logger = logging.getLogger(__name__)

api_endpoint = "https://api.gdqstat.us"
resouce_map = {
    "e": "num_emotes",
    "m": "total_donations",
    "d": "num_donations",
    "c": "num_chats",
    "t": "num_tweets",
    "v": "num_viewers",
}

alarm_msg = "Alarms triggered on: "


def send_alarm(message):
    logger.warn('Sending alarm: "{}"'.format(message))
    client = boto3.client("sns")
    client.publish(TopicArn=sns_arn, Message=message)
    logger.warn("Sent alarm")


def health_check_databases(event, context):
    logger.info("Starting connection to database")

    conn = None
    try:
        conn = psycopg2.connect(connect_timeout=10, **p_creds)
        conn.set_session(readonly=True)
    except Exception as e:
        logger.error(e)
        send_alarm("Unable to connect to postgres: {}".format(e))
        return

    tweets_sql = """
        SELECT COUNT(*) FROM gdq_tweets
        WHERE created_at >
            (SELECT now()::TIMESTAMP - INTERVAL '5 min')::TIMESTAMP;
    """

    chats_sql = """
        SELECT COUNT(*) FROM gdq_chats
        WHERE created_at >
            (SELECT now()::TIMESTAMP - INTERVAL '5 min')::TIMESTAMP;
    """

    @rollback_on_exception(conn)
    def _health_check():
        cur = conn.cursor()

        cur.execute(tweets_sql)
        tweets_row = cur.fetchone()
        if tweets_row is None or tweets_row[0] == 0:
            send_alarm("No tweets being saved to gdq_tweets table!")

        cur.execute(chats_sql)
        chats_row = cur.fetchone()
        if chats_row is None or chats_row[0] == 0:
            send_alarm("No chats being saved to gdq_chats table!")

    _health_check()
    logger.info("Did health check on database tables. Nothing to report.")


def health_check_api(event, context):
    logger.info("Starting connection to API")
    recent_url = api_endpoint + "/recentEvents"
    try:
        r = requests.get(recent_url, timeout=5)
        data = r.json()
    except Exception as e:
        logger.info("API resulting in exception", e)
        send_alarm("Something went wrong with the API request: {}".format(e))

    if r.status_code != 200:
        send_alarm("Got status code {} from API".format(r.status_code))
        return

    for d in data:
        d["time"] = parse(d["time"])
    max_time = max(d["time"] for d in data)
    if (max_time + timedelta(minutes=3) < datetime.utcnow().replace(tzinfo=pytz.utc)):
        send_alarm("API serving stale data! (Or collector has halted)")
    data = sorted(data, key=lambda x: x["time"], reverse=True)
    alarms = []
    for k in resouce_map:
        num_invalid = sum(1 for i in range(5) if data[i][k] <= 0 or data[i][k] is None)
        if num_invalid >= 3:
            alarms.append(resouce_map[k])
    if len(alarms) > 0:
        msg = alarm_msg + ", ".join(alarms)
        send_alarm(msg)
    else:
        logger.info("Did health check. Nothing to report.")


# if __name__ == '__main__':
#     logging.basicConfig(level='INFO')
#     health_check_api(None, None)
#     health_check_databases(None, None)
