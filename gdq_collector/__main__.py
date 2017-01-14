from DonationClient import DonationClient, DonationResult
from ScheduleClient import ScheduleClient
from TwitterClient import TwitterClient
from TwitchClient import TwitchClient
import settings
import utils
import credentials
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
import os
import argparse
from datetime import datetime
import watchtower
import logging
logger = logging.getLogger('gdq_collector')

# Setup clients
donations = DonationClient('https://gamesdonequick.com/tracker/index/agdq2017')
schedule = ScheduleClient('https://gamesdonequick.com/schedule')
twitter = TwitterClient(tags=settings.twitter_tags)
twitch = TwitchClient()

# Setup db connection
conn = psycopg2.connect(**credentials.postgres)
cur = conn.cursor()


def results_to_psql(tweets, viewers, chats, emotes, donators, donations):
    '''
    Takes results of refresh and inserts them into a new row in the
    timeseries database
    '''
    SQL = ("INSERT into gdq_timeseries (time, num_viewers, num_tweets, "
           "    num_chats, num_emotes, num_donations, total_donations) "
           "VALUES (%s, %s, %s, %s, %s, %s, %s);")
    data = (utils.get_truncated_time(), viewers, tweets, chats, emotes,
            donators, donations)
    try:
        cur.execute(SQL, data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(e)


def update_schedule_psql(sched):
    ''' Inserts updated schedule into db '''
    SQL = ("INSERT INTO gdq_schedule (name, start_time, duration, runners) "
           "VALUES (%s, %s, %s, %s) "
           "ON CONFLICT (name) DO UPDATE SET "
           "(start_time, duration, runners) = "
           "(excluded.start_time, excluded.duration, excluded.runners)")

    try:
        for entry in sched:
            data = (entry.title, entry.start_time, entry.duration,
                    entry.runner)
            cur.execute(SQL, data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(e)


def refresh_timeseries():
    ''' Polls clients for new stat data and inserts timeseries entry to db '''
    curr_d = utils.try_execute(donations.scrape, DonationResult())
    tweets = twitter.num_tweets()
    viewers = twitch.get_num_viewers()
    chats, emotes = twitch.get_message_count(), twitch.get_emote_count()
    results_to_psql(tweets, viewers, chats, emotes, curr_d.total_donators,
                    curr_d.total_donations)
    logger.info("Refreshed time series data")


def refresh_schedule():
    ''' Scrapes schedule and pushes new version to Postgres '''
    sched = schedule.scrape()
    update_schedule_psql(sched)
    logger.info("Refreshed schedule data")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Startup the GDQStatus Collection Service")
    parser.add_argument(
        '--notwitter', action='store_true', default=False,
        help='Disable Twitter (to avoid rate limiting while debugging')
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False,
        help='Raise log level to DEBUG for debugging purposes')
    parser.add_argument(
        '--sched', action='store_true', default=False,
        help='Run schedule scrape on startup')
    parser.add_argument(
        '--cloudwatch', action='store_true', default=False,
        help='Add the CloudWatch logging handler to push logs to AWS.')

    args = parser.parse_args()

    # Setup logging to correct log level
    level = 'DEBUG' if args.verbose else 'INFO'
    logging.basicConfig(level=level)

    # Setup Twitter if not disabled
    if not args.notwitter:
        twitter.auth()
        twitter.start()
    else:
        logger.info("Not starting TwitterClient")

    # Setup CloudWatch handler if requested
    if args.cloudwatch:
        logger.addHandler(watchtower.CloudWatchLogHandler())
        logging.getLogger('apscheduler').addHandler(
            watchtower.CloudWatchLogHandler()
        )

    # Setup connection to twitch IRC channel
    twitch.connect()

    # Add refresh jobs to scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_timeseries, trigger='interval', minutes=1)
    scheduler.add_job(refresh_schedule, trigger='interval', minutes=10)

    # Run schedule scrape immediately if requested
    if args.sched:
        scheduler.add_job(refresh_schedule, next_run_time=datetime.now())

    # Run scheduler
    logger.info("Starting Scheduler")
    try:
        scheduler.start()
        twitch.start()
    except KeyboardInterrupt:
        logger.info('Got SIGTERM! Terminating...')
        scheduler.shutdown(wait=False)
        os._exit(0)
