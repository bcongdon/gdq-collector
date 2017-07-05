# -*- coding: utf-8 -*-
import psycopg2
from credentials import postgres as p_creds
import json
import boto3
from utils import minify
import os
import logging
logger = logging.getLogger(__name__)

BUCKET = os.environ.get('S3_CACHE_BUCKET')
s3 = boto3.resource('s3')

conn = psycopg2.connect(**p_creds)
conn.set_session(readonly=True)
cur = conn.cursor()


def refresh_timeseries():
    SQL = ("SELECT row_to_json(r) r FROM "
           "(SELECT * FROM gdq_timeseries ORDER BY time ASC) r;")
    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(minify(map(lambda x: x[0], data)))

    s3.Bucket(BUCKET).put_object(Key='latest.json', Body=data_json)


def refresh_schedule():
    SQL = ("SELECT row_to_json(r) FROM "
           "(SELECT * FROM gdq_schedule ORDER BY start_time ASC) r;")
    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(map(lambda x: x[0], data))

    s3.Bucket(BUCKET).put_object(Key='schedule.json', Body=data_json)


def refresh_chat_words():
    SQL = ("SELECT COUNT(*) c, unnest(regexp_matches(content, '\w+')) word "
           "FROM gdq_chats "
           "GROUP BY word "
           "ORDER BY c "
           "DESC LIMIT 50;")
    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(map(lambda x: dict(count=x[0], word=x[1]), data))

    s3.Bucket(BUCKET).put_object(Key='chat_words.json', Body=data_json)


def refresh_chat_users():
    SQL = ("SELECT username, COUNT(*) chat_count "
           "FROM gdq_chats "
           "GROUP BY username "
           "ORDER BY chat_count "
           "DESC LIMIT 50;")
    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(map(lambda x: dict(user=x[0], count=x[1]), data))

    s3.Bucket(BUCKET).put_object(Key='chat_users.json', Body=data_json)


def execute_safe(func):
    try:
        func()
    except Exception as e:
        logger.error(e)
        conn.rollback()


def chat_users_handler(event, context):
    execute_safe(refresh_chat_users)


def chat_words_handler(event, context):
    execute_safe(refresh_chat_words)


def schedule_handler(event, context):
    execute_safe(refresh_schedule)


def timeseries_handler(event, context):
    execute_safe(refresh_timeseries)


if __name__ == '__main__':
    BUCKET = 'storage.api.gdqstat.us'
    # refresh_timeseries()
    # refresh_schedule()
    refresh_chat_words()
    refresh_chat_users()
