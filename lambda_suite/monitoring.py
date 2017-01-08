import requests
from utils import minify_keys
from dateutil.parser import parse
from credentials import sns_arn
import boto3
import logging
logger = logging.getLogger(__name__)

api_endpoint = 'https://wlh6r92oac.execute-api.us-east-1.amazonaws.com/dev'
resouce_map = {v: k for k, v in minify_keys.items()}
del resouce_map['time']
alarm_msg = 'Alarms triggered on: '


def send_alarm(message):
    client = boto3.client('sns')
    client.publish(
        TopicArn=sns_arn,
        Message=message
    )
    logger.warn("Sent alarm: \"{}\"".format(message))


def health_check():
    recent_url = api_endpoint + '/recentEvents'
    r = requests.get(recent_url)
    if r.status_code != 200:
        send_alarm("Got status code {} from API".format(r.status_code))
    try:
        data = r.json()
    except:
        send_alarm("API sent bad JSON")
    for d in data:
        d['time'] = parse(d['time'])
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


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    health_check()
