# -*- coding: utf-8 -*-
import psycopg2
from credentials import postgres as p_creds
import dateutil.parser
import json

conn = psycopg2.connect(**p_creds)
cur = conn.cursor()

SQL = ("SELECT row_to_json(r) FROM "
       "    (SELECT * FROM agdq_timeseries "
       "    WHERE time > %s"
       "    ORDER BY time DESC "
       "    LIMIT 60) r;")


def handler(event, context):
    d = event.get('since')
    ts = dateutil.parser.parse(d)
    cur.execute(SQL, (ts,))
    data = cur.fetchall()
    return json.dumps(map(lambda x: x[0], data))
