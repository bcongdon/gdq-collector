# -*- coding: utf-8 -*-
import psycopg2
from credentials import postgres as p_creds
import dateutil.parser
from utils import minify
from flask import Flask, request, jsonify
from flask_cors import CORS
app = Flask(__name__)
CORS(app)

conn = psycopg2.connect(**p_creds)
cur = conn.cursor()

SQL_filtered = ("SELECT row_to_json(r) FROM "
                "    (SELECT * FROM agdq_timeseries "
                "    WHERE time > %s"
                "    ORDER BY time DESC "
                "    LIMIT 60) r;")
SQL_unfiltered = ("SELECT row_to_json(r) FROM "
                  "    (SELECT * FROM agdq_timeseries "
                  "    ORDER BY time DESC "
                  "    LIMIT 60) r;")


@app.route('/recentEvents')
def most_recent():
    if 'since' in request.args:
        d = request.args.get('since')
        ts = dateutil.parser.parse(d)
        cur.execute(SQL_filtered, (ts,))
    else:
        cur.execute(SQL_unfiltered)
    data = cur.fetchall()
    return jsonify(minify(map(lambda x: x[0], data)))
