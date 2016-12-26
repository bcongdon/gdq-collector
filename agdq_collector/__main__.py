from DonationClient import DonationClient
from ScheduleClient import ScheduleClient
from TwitterClient import TwitterClient
from TwitchClient import TwitchClient
import settings
import utils
import credentials
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
import sys

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger('agdq_collector')

# Setup clients
donations = DonationClient('https://gamesdonequick.com/tracker/index/agdq2017')
schedule = ScheduleClient('https://gamesdonequick.com/schedule')
twitter = TwitterClient(tags=settings.twitter_tags)
twitter.auth()
twitch = TwitchClient()

# Setup db connection
conn = psycopg2.connect(**credentials.postgres)
cur = conn.cursor()


def results_to_psql(tweets, viewers, chats, emotes, donators, donations,
                    max_don):
    """
    Takes results of refresh and inserts them into a new row in the
    timeseries database
    """
    SQL = ("INSERT into agdq_timeseries (time, num_viewers, num_tweets, "
           "    num_chats, num_emotes, num_donations, total_donations, "
           "    max_donation) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s, %s);")
    data = (utils.get_truncated_time(), viewers, tweets, chats, emotes,
            donators, donations, max_don)
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
    viewers = twitch.get_num_viewers()
    chats, emotes = twitch.get_message_count(), twitch.get_emote_count()
    results_to_psql(tweets, viewers, chats, emotes, curr_d.total_donators,
                    curr_d.total_donations, curr_d.max_donation)


def refresh_schedule():
    sched = schedule.scrape()
    update_schedule_psql(sched)


if __name__ == '__main__':
    twitter.start()

    # Add refresh job to scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_timeseries, trigger='interval', minutes=1)
    scheduler.add_job(refresh_schedule, trigger='interval', minutes=10)
    # Needed to maintain IRC event loop
    # scheduler.add_job(twitch.process, trigger='interval', seconds=1)

    # Run scheduler
    logger.info("Starting Scheduler")
    try:
        scheduler.start()
        twitch.start()
    except KeyboardInterrupt:
        logger.info('Got SIGTERM! Terminating...')
        scheduler.shutdown(wait=False)
        sys.exit(0)
