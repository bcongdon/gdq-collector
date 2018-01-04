from .DonationClient import DonationClient, DonationResult
from .ScheduleClient import ScheduleClient
from .TwitterClient import TwitterClient
from .TwitchClient import TwitchClient
from .TrackerClient import TrackerClient
from . import utils, credentials, settings
from apscheduler.schedulers.background import BackgroundScheduler
import psycopg2
import os
import argparse
from datetime import datetime
import watchtower
from time import sleep
import pytz
import logging
logger = logging.getLogger('gdq_collector')

# Setup clients
donations = DonationClient()
tracker = TrackerClient()
schedule = ScheduleClient()
twitter = TwitterClient(tags=settings.TWITTER_TAGS)
twitch = TwitchClient()

# Setup db connection
conn = psycopg2.connect(**credentials.postgres)


def results_to_psql(tweets, viewers, chats, emotes, donators, donations):
    '''
    Takes results of refresh and inserts them into a new row in the
    timeseries database
    '''
    SQL = '''
        INSERT into gdq_timeseries (time, num_viewers, num_tweets,
            num_chats, num_emotes, num_donations, total_donations)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
    '''

    data = (utils.get_truncated_time(), viewers, tweets, chats, emotes,
            donators, donations)
    try:
        cur = conn.cursor()
        cur.execute(SQL, data)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(e)


def update_schedule_psql(sched):
    ''' Inserts updated schedule into db '''
    SQL_upsert = '''
        INSERT INTO gdq_schedule
            (name, start_time, duration, runners, category)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (name, category) DO UPDATE SET
           (start_time, duration, runners) =
           (excluded.start_time, excluded.duration, excluded.runners)
        RETURNING id;
    '''

    SQL_drop_old = '''
        DELETE FROM gdq_schedule
        WHERE NOT (id = ANY (%s));
    '''

    try:
        game_ids = []
        for entry in sched:
            data = (entry.title, entry.start_time, entry.duration,
                    entry.runner, entry.category)
            cur = conn.cursor()
            cur.execute(SQL_upsert, data)
            game = cur.fetchone()
            # Append returned game id
            game_ids.append(game[0])
        # Drop games that weren't created or updated
        cur.execute(SQL_drop_old, (game_ids,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(e)


def save_tweets(tweets):
    if not len(tweets):
        return

    record_template = ','.join(['%s'] * len(tweets))
    SQL = '''
        INSERT INTO gdq_tweets
            (id, created_at, content, username, user_id)
        VALUES {}
    '''

    tweets_formatted = [(t.id, t.created_at, t.text, t.user.name, t.user.id)
                        for t in tweets]
    try:
        cur = conn.cursor()
        cur.execute(SQL.format(record_template), tweets_formatted)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(e)


def save_chats(chats):
    if not len(chats):
        return

    record_template = ','.join(['%s'] * len(chats))
    SQL = '''
        INSERT INTO gdq_chats (username, created_at, content)
        VALUES {}
    '''

    chats_formatted = [(c['user'], c['created_at'], c['content'])
                       for c in chats]
    try:
        cur = conn.cursor()
        cur.execute(SQL.format(record_template), chats_formatted)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(e)


def refresh_timeseries():
    ''' Polls clients for new stat data and inserts timeseries entry to db '''
    curr_d = utils.try_execute(donations.scrape, DonationResult())
    num_tweets = twitter.num_tweets()
    viewers = twitch.get_num_viewers()
    chats, emotes = twitch.get_message_count(), twitch.get_emote_count()
    results_to_psql(num_tweets, viewers, chats, emotes, curr_d.total_donators,
                    curr_d.total_donations)
    logger.info("Refreshed time series data")

    tweets = twitter.get_tweets()
    save_tweets(tweets)
    logger.info("Saved tweets")

    chats = twitch.get_chats()
    save_chats(chats)
    logger.info("Saved Twitch chats")


def refresh_schedule():
    ''' Scrapes schedule and pushes new version to Postgres '''
    sched = schedule.scrape()
    update_schedule_psql(sched)
    logger.info("Refreshed schedule data")


def refresh_tracker_donations():
    SQL = '''
        INSERT INTO gdq_donations
           (donor_id, created_at, amount, donation_id, has_comment, donor_name)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    '''

    SQL_check = '''
        SELECT created_at
        FROM gdq_donations
        ORDER BY created_at DESC
        LIMIT 1;
    '''

    cur = conn.cursor()
    cur.execute(SQL_check)
    latest = cur.fetchone()[0]
    latest = latest.replace(tzinfo=pytz.UTC)
    for idx, donation in enumerate(tracker.scrape()):
        # Every 50 donations, check to see if we can bail early
        if idx % 50 == 0:
            (_, time, _, _, _, _) = donation
            if time < latest:
                message = ('Returning early from scraping donation pages. '
                           'Found latest: {}, current donation is at {}.'
                           .format(latest, time))
                logger.info(message)
                return
        try:
            cur.execute(SQL, donation)
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(e)


def refresh_tracker_donation_messages():
    SQL = '''
        SELECT donation_id
        FROM gdq_donations
        WHERE has_comment=True AND comment IS NULL;
    '''

    SQL_update = '''
        UPDATE gdq_donations
        SET comment=%s
        WHERE donation_id=%s;
    '''

    cur = conn.cursor()
    cur.execute(SQL)
    for row in cur.fetchall():
        donation_id = row[0]
        message = tracker.scrape_donation_message(donation_id)
        sleep(0.5)
        try:
            cur.execute(SQL_update, (message, donation_id))
            conn.commit()
            logger.info('Successfully scraped message for donation {}'
                        .format(donation_id))
        except Exception as e:
            conn.rollback()
            logger.error(e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Startup the GDQStatus Collection Service")
    parser.add_argument(
        '--notwitter', action='store_true', default=False,
        help='Disable Twitter (to avoid rate limiting while debugging')
    parser.add_argument(
        '--nodonations', action='store_true', default=False,
        help='Disable scraping donations')
    parser.add_argument(
        '-v', '--verbose', action='store_true', default=False,
        help='Raise log level to DEBUG for debugging purposes')
    parser.add_argument(
        '--refresh', action='store_true', default=False,
        help='Run scrape operations on startup')
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
        handler = watchtower.CloudWatchLogHandler()
        logger.addHandler(handler)
        logging.getLogger('apscheduler').addHandler(handler)

    # Setup connection to twitch IRC channel
    twitch.connect()

    # Add refresh jobs to scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(refresh_timeseries, trigger='interval', minutes=1)
    scheduler.add_job(refresh_schedule, trigger='interval', minutes=10)

    if not args.nodonations:
        scheduler.add_job(refresh_tracker_donations,
                          trigger='interval',
                          minutes=20,
                          max_instances=1)
        scheduler.add_job(refresh_tracker_donation_messages,
                          trigger='interval',
                          minutes=60,
                          max_instances=1)

    # Run schedule scrape immediately if requested
    if args.refresh:
        scheduler.add_job(refresh_schedule, next_run_time=datetime.now())

        if not args.nodonations:
            scheduler.add_job(refresh_tracker_donations,
                              next_run_time=datetime.now())
            scheduler.add_job(refresh_tracker_donation_messages,
                              next_run_time=datetime.now())

    # Run scheduler
    logger.info("Starting Scheduler")
    try:
        scheduler.start()
        twitch.start()
    except KeyboardInterrupt:
        logger.info('Got SIGTERM! Terminating...')
        scheduler.shutdown(wait=False)
        os._exit(0)
