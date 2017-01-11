import requests
from dateutil.parser import parse
from datetime import timedelta, datetime
from credentials import sns_arn
import boto3
import pytz
import logging
logger = logging.getLogger(__name__)

api_endpoint = 'https://api.gdqstat.us'
resouce_map = {
    'e': 'num_emotes',
    'm': 'total_donations',
    'd': 'num_donations',
    'c': 'num_chats',
    't': 'num_tweets',
    'v': 'num_viewers'
}

alarm_msg = 'Alarms triggered on: '


def send_alarm(message):
    client = boto3.client('sns')
    client.publish(
        TopicArn=sns_arn,
        Message=message
    )
    logger.warn("Sent alarm: \"{}\"".format(message))


def health_check(event, context):
    logger.debug("Starting connection")
    recent_url = api_endpoint + '/recentEvents'
    r = requests.get(recent_url, timeout=5, verify=False)
    if r.status_code != 200:
        send_alarm("Got status code {} from API".format(r.status_code))
        return
    try:
        data = r.json()
    except:
        send_alarm("API sent bad JSON")
    for d in data:
        d['time'] = parse(d['time'])
    max_time = max(d['time'] for d in data)
    if (max_time + timedelta(minutes=3) <
            datetime.utcnow().replace(tzinfo=pytz.utc)):
        send_alarm("API serving stale data! (Or collector has halted)")
    data = sorted(data, key=lambda x: x['time'], reverse=True)
    alarms = []
    for k in resouce_map:
        num_invalid = sum(1 for i in range(5) if data[i][k] <= 0 or
                          data[i][k] is None)
        if num_invalid >= 3:
            alarms.append(resouce_map[k])
    if len(alarms) > 0:
        msg = alarm_msg + ', '.join(alarms)
        send_alarm(msg)
    else:
        logger.info("Did health check. Nothing to report.")


# if __name__ == '__main__':
#     logging.basicConfig(level='INFO')
#     health_check(None, None)
