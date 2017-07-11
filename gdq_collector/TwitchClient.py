import credentials
import settings
import irc.client
import requests
import logging
from datetime import datetime
logger = logging.getLogger(__name__)
MAX_CHATS_SAVED = 10000


class TwitchClient(irc.client.SimpleIRCClient):
    def __init__(self):
        self._message_count = 0
        self._emote_count = 0
        self._channel_id = None
        self._chats = []
        irc.client.SimpleIRCClient.__init__(self)

    def connect(self):
        logger.info("Attempting to connect to IRC server.")
        self._emotes = self._get_emote_list()
        irc.client.SimpleIRCClient.connect(
            self, settings.TWITCH_HOST, settings.TWITCH_PORT,
            nickname=credentials.twitch['nick'],
            password=credentials.twitch['oauth'])
        logger.info("Connected to IRC server: %s" % settings.TWITCH_HOST)
        self.connection.join(self._to_irc_chan(settings.TWITCH_CHANNEL))

    def process(self):
        """
        Needed if not using TwitchClient as the main event loop carrier.
        Allows the IRC client to process new data / events.
        Should be called regularly to allow PINGs to be responded to
        """
        self.reactor.process_once()

    def _to_irc_chan(self, chan):
        return chan if chan.startswith('#') else '#' + chan

    def _to_url_chan(self, chan):
        return chan[1:] if chan.startswith('#') else chan

    def _get_channel_id(self, chan):
        """ Gets the numeric channel id of a channel by displayname """
        if not self._channel_id:
            headers = {
                "Accept": "application/vnd.twitchtv.v5+json",
                "Client-ID": credentials.twitch['clientid'],
            }
            r = requests.get('https://api.twitch.tv/kraken/users',
                             headers=headers,
                             params={
                                "login": chan
                             })
            self._channel_id = r.json()['users'][0]['_id']
        return self._channel_id

    def _get_emote_list(self):
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": credentials.twitch['clientid'],
        }
        r = requests.get("https://api.twitch.tv/kraken/chat/emoticon_images",
                         headers=headers)
        r_data = r.json()
        if 'emoticons' in r_data:
            logger.info("Downloaded emoticon list successfully.")
            return set(map(lambda x: x['code'], r_data['emoticons']))
        else:
            logger.error("Unable to download emoji list for Twitch!")
            return []

    def _num_emotes(self, s):
        return sum(1 for w in s.split(' ') if w in self._emotes)

    def on_join(self, c, e):
        logger.info("Joined channel: %s" % e.target)

    def get_message_count(self):
        t = self._message_count
        self._message_count = 0
        return t

    def get_emote_count(self):
        t = self._emote_count
        self._emote_count = 0
        return t

    def get_chats(self):
        c = self._chats
        self._chats = []
        return c

    def on_pubmsg(self, connection, event):
        msg = event.arguments[0]
        num_emotes = self._num_emotes(msg)
        logger.debug(msg + "; {} emotes".format(num_emotes))
        self._message_count += 1
        self._emote_count += num_emotes

        if len(self._chats) < MAX_CHATS_SAVED:
            try:
                self._chats.append({
                    'user': event.source.split('!')[0],
                    'content': msg,
                    'created_at': datetime.utcnow()
                })
            except Exception as e:
                logger.error('Error appending message: {}'.format(e))

    def on_disconnect(self, connection, event):
        logger.error("Disconnected from twitch chat. Attempting reconnection")
        self.connect()

    def get_num_viewers(self):
        """ Queries the TwitchAPI for current number of viewers of channel """
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": credentials.twitch['clientid'],
        }
        url = "https://api.twitch.tv/kraken/streams/"
        url += self._get_channel_id(self._to_url_chan(settings.TWITCH_CHANNEL))
        req = requests.get(url, headers=headers)
        res = req.json()
        if 'stream' in res and res['stream']:
            viewers = res['stream']['viewers']
            logger.info("Downloaded viewer info. "
                        "Currently viewers: %s" % viewers)
            return viewers
        else:
            logger.warn("Unable to get number of viewers. "
                        "Possible that stream is offline.")


if __name__ == '__main__':
    t = TwitchClient()
    print t.get_num_viewers()
