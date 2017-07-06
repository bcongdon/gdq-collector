# -*- coding: utf-8 -*-
from dateutil.parser import parse
from datetime import timedelta
import requests
import json
from bs4 import BeautifulSoup
import logging
import os
import boto3
import psycopg2
from credentials import postgres as p_creds
from datetime import datetime
logger = logging.getLogger(__name__)

BUCKET = os.environ.get('S3_CACHE_BUCKET')
s3 = boto3.resource('s3')
bid_id = 5744

conn = psycopg2.connect(**p_creds)
cur = conn.cursor()


class KillSaveAnimalsClient:
    base_url = 'https://gamesdonequick.com/tracker/bid/'

    def get_data(self):
        r = requests.get(KillSaveAnimalsClient.base_url + str(bid_id))

        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find('tbody')
        rows = table.find_all('tr')
        kill = (rows[0]
                .find_all('td')[-2]
                .text
                .strip()
                .replace(',', '')
                .replace('$', ''))
        save = (rows[1]
                .find_all('td')[-2]
                .text
                .strip()
                .replace(',', '')
                .replace('$', ''))
        return kill, save


def refresh_kill_save_data():
    kill, save = KillSaveAnimalsClient().get_data()

    SQL = ('INSERT INTO gdq_animals (kill, save, time) '
           'VALUES (%s, %s, %s);')

    try:
        cur.execute(SQL, (kill, save, datetime.utcnow()))
        conn.commit()
    except Exception as e:
        logger.error(e)
        conn.rollback()
        raise e


def cache_kill_save_data():
    # TODO
    pass
    # kill_save_json = json.dumps(kill_save_ts)
    # s3.Bucket(BUCKET).put_object(Key='killVsSave.json', Body=kill_save_json)


def refresh_kill_save_handler(event, context):
    refresh_kill_save_data()


if __name__ == '__main__':
    BUCKET = 'storage.api.gdqstat.us'
    # refresh_kill_save_data()
