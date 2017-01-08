import requests
from utils import minify_keys
from dateutil.parser import parse
import logging
logger = logging.getLogger(__name__)

api_endpoint = 'https://wlh6r92oac.execute-api.us-east-1.amazonaws.com/dev'
resouce_map = {v: k for k, v in minify_keys.items()}
alarm_msg = 'Alarms triggered on: '


def send_alarm(message):
    pass


def do_health_check():
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
        num_invalid = sum(1 for i in range(5) if data[i] <= 0 or
                          data[i] is None)
        if num_invalid >= 3:
            alarms += resouce_map[k]
    if len(alarms) > 0:
        msg = alarm_msg + ', '.join(alarms)
        send_alarm(msg)
        logger.warn("Sent alarm: \"{}\"".format(msg))
    else:
        logger.info("Did health check. Nothing to report.")


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    do_health_check()
