# -*- coding: utf-8 -*-
import psycopg2
from credentials import postgres as p_creds
import json
import boto3
from utils import minify
import os

BUCKET = os.environ.get('S3_CACHE_BUCKET')
s3 = boto3.resource('s3')

conn = psycopg2.connect(**p_creds)
cur = conn.cursor()


def refresh_timeseries():
    SQL = "SELECT row_to_json(r) FROM (SELECT * FROM gdq_timeseries) r;"
    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(minify(map(lambda x: x[0], data)))

    s3.Bucket(BUCKET).put_object(Key='latest.json', Body=data_json)


def refresh_schedule():
    SQL = "SELECT row_to_json(r) FROM (SELECT * FROM gdq_schedule) r;"
    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(map(lambda x: x[0], data))

    s3.Bucket(BUCKET).put_object(Key='schedule.json', Body=data_json)


def schedule_handler(event, context):
    refresh_schedule()


def timeseries_handler(event, context):
    refresh_timeseries()
