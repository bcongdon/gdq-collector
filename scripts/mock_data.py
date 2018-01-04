import json
import credentials
import psycopg2
import datetime
from datetime import timedelta

conn = psycopg2.connect(**credentials.postgres)
cur = conn.cursor()
start_time = datetime.datetime(2017, 1, 8, 8, 30)


def results_to_psql(time, tweets, viewers, chats, emotes, donators, donations):
    '''
    Takes results of refresh and inserts them into a new row in the
    timeseries database
    '''
    SQL = ("INSERT into gdq_timeseries (time, num_viewers, num_tweets, "
           "    num_chats, num_emotes, num_donations, total_donations) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s);")
    data = (time, viewers, tweets, chats, emotes,
            donators, donations)
    cur.execute(SQL, data)
    conn.commit()


if __name__ == '__main__':
    with open('sgdq-2016.json') as f:
        data = json.load(f)
    first_t = int(data['data'].keys()[0])
    for t in data['data']:
        data['data'][t].update(data['extras'][t])
        d = data['data'][t]
        new_t = start_time + timedelta(microseconds=1000*(int(t) - first_t))
        try:
            results_to_psql(new_t, d['t'], d['v'], d['c'], d['e'],
                            d['d'], d['m'])
        except Exception as e:
            print(e)
