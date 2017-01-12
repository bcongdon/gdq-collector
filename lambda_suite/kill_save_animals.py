# -*- coding: utf-8 -*-
from dateutil.parser import parse
from datetime import timedelta
import requests
import json
from bs4 import BeautifulSoup
import logging
import os
import boto3
logger = logging.getLogger(__name__)

BUCKET = os.environ.get('S3_CACHE_BUCKET')
s3 = boto3.resource('s3')


class KillSaveAnimalsClient:
    kill_animals_id = 5142
    save_animals_id = 5141
    base_url = 'https://gamesdonequick.com/tracker/bid/'

    def _get_bid_list(self, bid_id):
        donations = []
        r = requests.get(KillSaveAnimalsClient.base_url + str(bid_id))
        soup = BeautifulSoup(r.text, "html.parser")
        don_table = soup.find_all('table')[2]
        for donation in don_table.find_all('tr')[1:]:
            date = parse(donation.find('span').text)
            amt = float(donation.find_all('a')[-1].text.replace(',', '')[1:])
            donations.append((date, amt))
        return donations

    def get_timeseries(self):
        kill_ts = self._get_bid_list(KillSaveAnimalsClient.kill_animals_id)
        save_ts = self._get_bid_list(KillSaveAnimalsClient.save_animals_id)

        kill_start = min(i[0] for i in kill_ts)
        save_start = min(i[0] for i in save_ts)
        kill_end = max(i[0] for i in kill_ts)
        save_end = max(i[0] for i in save_ts)
        curr = min(kill_start, save_start)
        end = max(kill_end, save_end)

        combined_ts = []
        while curr < end:
            next_time = curr + timedelta(minutes=10)
            kill_tot = sum(i[1] for i in kill_ts
                           if i[0] >= curr and i[0] < next_time)
            save_tot = sum(i[1] for i in save_ts
                           if i[0] >= curr and i[0] < next_time)
            combined_ts.append(dict(time=curr.isoformat(),
                                    kill=kill_tot, save=save_tot))
            curr = next_time
        return combined_ts


def refresh_kill_save_data():
    kill_save_ts = KillSaveAnimalsClient().get_timeseries()
    kill_save_json = json.dumps(kill_save_ts)
    s3.Bucket(BUCKET).put_object(Key='killVsSave.json', Body=kill_save_json)


def refresh_kill_save_handler(event, context):
    refresh_kill_save_data()


if __name__ == '__main__':
    BUCKET = 'storage.api.gdqstat.us'
    refresh_kill_save_data()
