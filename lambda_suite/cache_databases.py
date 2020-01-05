# -*- coding: utf-8 -*-
import psycopg2
from credentials import postgres as p_creds
import json
import boto3
from utils import minify, rollback_on_exception
import os
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

BUCKET = os.environ.get("S3_CACHE_BUCKET", "storage.api.gdqstat.us")
s3 = boto3.resource("s3")

logger.info("Connecting to postgres...")
conn = psycopg2.connect(**p_creds)
logger.info("Established connection to DB.")
conn.set_session(readonly=True)
cur = conn.cursor()


@rollback_on_exception(conn)
def refresh_timeseries():
    """
    Refreshes timeseries data S3 cache for use with the main graph
    (i.e. viewers, chats, emotes, total donation number/amount)
    """

    SQL = """
        SELECT row_to_json(r) r FROM
        (SELECT * FROM gdq_timeseries ORDER BY time ASC) r;
    """

    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps(minify([x[0] for x in data]))

    s3.Bucket(BUCKET).put_object(
        Key="latest.json",
        Body=data_json,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(minutes=10),
    )
    return data_json


@rollback_on_exception(conn)
def refresh_schedule():
    """
    Refreshes livestream game schedule S3 cache
    """

    SQL = """
        SELECT row_to_json(r) FROM
        (SELECT * FROM gdq_schedule ORDER BY start_time ASC) r;
    """

    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps([x[0] for x in data])

    s3.Bucket(BUCKET).put_object(
        Key="schedule.json",
        Body=data_json,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(minutes=10),
    )
    return data_json


@rollback_on_exception(conn)
def refresh_chat_words():
    """
    Refreshes the S3 cache of words used in chat
    Lists the top 50 used "words" in chat by frequency
    """

    SQL = """
        SELECT COUNT(*) c, unnest(regexp_matches(content, '\w+')) word
        FROM gdq_chats
        GROUP BY word
        ORDER BY c
        DESC LIMIT 50;
    """

    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps([dict(count=x[0], word=x[1]) for x in data])

    s3.Bucket(BUCKET).put_object(
        Key="chat_words.json",
        Body=data_json,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(hours=1),
    )
    return data_json


@rollback_on_exception(conn)
def refresh_chat_users():
    """
    Refreshes the S3 cache of Twitch chat users
    Lists the top 50 most prolific chat users by message frequency
    """

    SQL = """
        SELECT username, COUNT(*) chat_count
        FROM gdq_chats
        GROUP BY username
        ORDER BY chat_count
        DESC LIMIT 50;
    """

    cur.execute(SQL)
    data = cur.fetchall()
    data_json = json.dumps([dict(user=x[0], count=x[1]) for x in data])

    s3.Bucket(BUCKET).put_object(
        Key="chat_users.json",
        Body=data_json,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(hours=1),
    )
    return data_json


# @rollback_on_exception(conn)
# def refresh_kill_save():
#     SQL = '''
#         SELECT row_to_json(r) FROM
#         (SELECT * FROM gdq_animals ORDER BY time ASC) r;
#     '''

#     cur.execute(SQL)
#     data = cur.fetchall()
#     data_json = json.dumps(minify([x[0] for x in data]))

#     s3.Bucket(BUCKET).put_object(Key='kill_save_animals.json', Body=data_json)


@rollback_on_exception(conn)
def refresh_donation_stats():
    SQL = """
        SELECT has_comment, COUNT(*), sum(amount),
            median(amount), avg(amount)
        FROM gdq_donations GROUP BY has_comment
        ORDER BY has_comment;
    """

    SQL_overall = """
        SELECT COUNT(*), sum(amount), median(amount), avg(amount)
        FROM gdq_donations;
    """

    SQL_anonymous = """
        SELECT (donor_id IS NULL) anonymous,
            COUNT(*), SUM(amount), median(amount), avg(amount)
        FROM gdq_donations GROUP BY anonymous
        ORDER BY anonymous DESC;
    """

    SQL_median_timeseries = """
        SELECT date_trunc('hour', created_at - interval '1 minute') as time,
            median(amount)
        FROM gdq_donations
        WHERE created_at >= '2017-07-02'
        GROUP BY date_trunc('hour', created_at - interval '1 minute')
        ORDER BY time;
    """

    cur.execute(SQL)
    stats = cur.fetchall()

    cur.execute(SQL_anonymous)
    anonymous = cur.fetchall()

    cur.execute(SQL_overall)
    overall = cur.fetchall()

    cur.execute(SQL_median_timeseries)
    medians = cur.fetchall()

    def comment_formatter(x):
        return dict(
            has_comment=x[0],
            count=int(x[1]),
            sum=float(x[2]),
            median=float(x[3]),
            avg=float(x[4]),
        )

    def anonymous_formatter(x):
        return dict(
            anonymous=x[0],
            count=int(x[1]),
            sum=float(x[2]),
            median=float(x[3]),
            avg=float(x[4]),
        )

    def medians_formatter(x):
        return dict(time=str(x[0]), median=float(x[1]))

    def overall_formatter(x):
        return dict(
            count=int(x[0]), sum=float(x[1]), median=float(x[2]), avg=float(x[3])
        )

    stats_list = [comment_formatter(x) for x in stats]
    anonymous_list = [anonymous_formatter(x) for x in anonymous]
    medians_list = [medians_formatter(x) for x in medians]
    overall_list = [overall_formatter(x) for x in overall]
    data = json.dumps(
        dict(
            comment_stats=stats_list,
            medians=medians_list,
            overall=overall_list,
            anonymous=anonymous_list,
        )
    )
    s3.Bucket(BUCKET).put_object(
        Key="donation_stats.json",
        Body=data,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(hours=1),
    )
    return data


@rollback_on_exception(conn)
def refresh_donation_words():
    SQL = """
        SELECT word, nentry AS entries FROM
            ts_stat('SELECT to_tsvector(''simple_english'',
                gdq_donations.comment)
            FROM gdq_donations
            WHERE comment IS NOT NULL')
        WHERE character_length(word) > 2
        ORDER BY entries DESC
        LIMIT 50;
    """
    cur.execute(SQL)
    words = cur.fetchall()
    json_data = json.dumps([dict(word=x[0], entries=x[1]) for x in words])
    s3.Bucket(BUCKET).put_object(
        Key="donation_words.json",
        Body=json_data,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(hours=1),
    )
    return json_data


@rollback_on_exception(conn)
def refresh_top_donors():
    SQL_frequent = """
        SELECT donor_name, COUNT(*) count
        FROM gdq_donations
        WHERE donor_name IS NOT NULL
        GROUP BY donor_id, donor_name
        ORDER BY count DESC LIMIT 50;
    """

    SQL_generous = """
        SELECT donor_name, ceiling(SUM(amount)) total
        FROM gdq_donations
        WHERE donor_name IS NOT NULL
        GROUP BY donor_id, donor_name
        ORDER BY total DESC LIMIT 50;
    """

    cur.execute(SQL_frequent)
    frequent = [dict(name=x[0], count=int(x[1])) for x in cur.fetchall()]

    cur.execute(SQL_generous)
    generous = [dict(name=x[0], total=int(x[1])) for x in cur.fetchall()]

    json_data = json.dumps(dict(frequent=frequent, generous=generous))
    s3.Bucket(BUCKET).put_object(
        Key="top_donors.json",
        Body=json_data,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(hours=1),
    )
    return json_data


@rollback_on_exception(conn)
def refresh_game_stats():
    SQL = """
        SELECT * FROM (
            SELECT name,
                (SELECT MAX(num_viewers)
                    FROM gdq_timeseries
                    WHERE time >= start_time
                    AND time <= (start_time + duration)) max_viewers,
                (SELECT median(amount)
                    FROM gdq_donations
                    WHERE created_at >= start_time
                    AND created_at <= (start_time + duration)) median_donation,
                (SELECT MAX(total_donations) - MIN(total_donations)
                    FROM gdq_timeseries
                    WHERE time >= start_time
                    AND time <= (start_time + duration)) donations,
                (SELECT MAX(total_donations) - MIN(total_donations)
                    FROM gdq_timeseries WHERE time >= start_time
                    AND time <= (start_time + duration))
                        / (EXTRACT(EPOCH FROM duration) / 60)
                    donations_per_min,
                (SELECT SUM(num_chats)
                    FROM gdq_timeseries
                    WHERE time >= start_time
                    AND time <= (start_time + duration)) num_chats
            FROM gdq_schedule
            ) game_stats
        WHERE max_viewers IS NOT NULL;
    """
    cur.execute(SQL)
    games = cur.fetchall()

    def games_formatter(x):
        return dict(
            name=x[0],
            max_viewers=int(x[1]),
            median_donation=float(x[2] or 0),
            total_donations=float(x[3] or 0),
            donations_per_min=float(x[4] or 0),
            num_chats=int(x[5]),
        )

    games_data = [games_formatter(x) for x in games]
    json_data = json.dumps(games_data)
    s3.Bucket(BUCKET).put_object(
        Key="games_stats.json",
        Body=json_data,
        ContentType="application/json",
        Expires=datetime.utcnow() + timedelta(minutes=30),
    )
    return json_data


def chat_users_handler(event, context):
    return refresh_chat_users()


def chat_words_handler(event, context):
    return refresh_chat_words()


def schedule_handler(event, context):
    return refresh_schedule()


def timeseries_handler(event, context):
    return refresh_timeseries()


# def animals_handler(event, context):
#     return refresh_kill_save()


def donation_stats_handler(event, context):
    return refresh_donation_stats()


def donation_words_handler(event, context):
    return refresh_donation_words()


def top_donors_handler(event, context):
    return refresh_top_donors()


def games_stats_handler(event, context):
    return refresh_game_stats()


def all_handler(event, context):
    refresh_timeseries()
    refresh_schedule()
    refresh_chat_words()
    refresh_chat_users()
    refresh_donation_stats()
    refresh_donation_words()
    refresh_top_donors()
    refresh_game_stats()


if __name__ == "__main__":
    BUCKET = "storage.api.gdqstat.us"
    refresh_timeseries()
    refresh_schedule()
    refresh_chat_words()
    refresh_chat_users()
    refresh_donation_stats()
    refresh_donation_words()
    refresh_top_donors()
    refresh_game_stats()
