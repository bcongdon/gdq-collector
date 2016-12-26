import tweepy
from credentials import twitter
import logging
logger = logging.getLogger(__name__)


class HashtagStreamListener(tweepy.StreamListener):
    def __init__(self, handler):
        self.handler = handler

    def on_status(self, status):
        self.handler._increment_tweet_counter()

    def on_error(self, status_code):
        logger.warn("Error with status code: %s" % status_code)
        self.handler._setup_stream()
        return False


class TwitterClient:
    def __init__(self, tags=[]):
        self.tags = tags
        self.curr_tweets = 0
        self.api = None

    def auth(self):
        auth = tweepy.OAuthHandler(twitter['consumer_key'],
                                   twitter['consumer_secret'])
        auth.set_access_token(twitter['access_token'],
                              twitter['access_token_secret'])
        self.api = tweepy.API(auth)

    def num_tweets(self):
        '''
        Returns current number of tweets on the counter and resets internal
        counter
        '''
        t = self.curr_tweets
        self.curr_tweets = 0
        return t

    def start(self):
        self._setup_stream()

    def _setup_stream(self):
        if not self.api:
            raise RuntimeError("Client not authenticated!")
        s_listener = HashtagStreamListener(self)
        stream = tweepy.Stream(auth=self.api.auth, listener=s_listener)
        stream.filter(track=self.tags, async=True)

    def _increment_tweet_counter(self):
        self.curr_tweets += 1
