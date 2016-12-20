from DonationClient import DonationClient
from ScheduleClient import ScheduleClient
from TwitterClient import TwitterClient
import settings
import utils
from apscheduler.schedulers.blocking import BlockingScheduler
import psycopg2

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger('agdq_collector')

# Setup clients
donations = DonationClient('https://gamesdonequick.com/tracker/index/agdq2017')
schedule = ScheduleClient('https://gamesdonequick.com/schedule')
twitter = TwitterClient(tags=settings.twitter_tags)
twitter.auth()

# Setup db connection
conn = psycopg2.connect(host='localhost')
cur = conn.cursor()


def results_to_psql(tweets, chats, emotes, donators, donations, max_don):
    """
    Takes results of refresh and inserts them into a new row in the
    timeseries database
    """
    SQL = ("INSERT into agdq_timeseries (time, num_tweets, num_chats, "
           "    num_emotes, num_donations, total_donations, max_donation) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s);")
    data = (utils.get_truncated_time(), tweets, chats, emotes, donators,
            donations, max_don)
    cur.execute(SQL, data)
    conn.commit()


def update_schedule_psql(sched):
    SQL = ("INSERT INTO agdq_schedule (name, start_time, duration, runners) "
           "VALUES (%s, %s, %s, %s) "
           "ON CONFLICT (name) DO UPDATE SET "
           "(start_time, duration, runners) = "
           "(excluded.start_time, excluded.duration, excluded.runners)")
    for entry in sched:
        data = (entry.title, entry.start_time, entry.duration, entry.runner)
        cur.execute(SQL, data)
    conn.commit()


def refresh_timeseries():
    curr_d = donations.scrape()
    tweets = twitter.num_tweets()
    results_to_psql(tweets, 0, 0, curr_d.total_donators,
                    curr_d.total_donations, curr_d.max_donation)


def refresh_schedule():
    sched = schedule.scrape()
    update_schedule_psql(sched)


if __name__ == '__main__':
    twitter.start()

    # Add refresh job to scheduler
    scheduler = BlockingScheduler()
    scheduler.add_job(refresh_timeseries, trigger='interval', minutes=1)
    scheduler.add_job(refresh_schedule, trigger='interval', minutes=10)

    # Run scheduler
    logger.info("Starting Scheduler")
    scheduler.start()
