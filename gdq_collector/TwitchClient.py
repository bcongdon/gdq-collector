from . import settings, credentials
import irc.client
import requests
import logging
from time import sleep
from datetime import datetime

logger = logging.getLogger(__name__)
MAX_CHATS_SAVED = 100000
CHAT_ENDPOINT = "https://api.twitch.tv/kraken/chat/emoticon_images"


class TwitchClient(irc.client.SimpleIRCClient):

    def __init__(self):
        self._message_count = 0
        self._emote_count = 0
        self._channel_id = None
        self._chats = []
        self._exponential_backoff = 0
        irc.client.SimpleIRCClient.__init__(self)

    def connect(self):
        if self._exponential_backoff > 0:
            logger.info(
                "Backing off on IRC join for {} sec".format(
                    self._exponential_backoff
                )
            )
            sleep(self._exponential_backoff)
            self._exponential_backoff *= 2
        else:
            self._exponential_backoff = 1

        self._emotes = self._get_emote_list()

        logger.info("Attempting to connect to IRC server.")
        irc.client.SimpleIRCClient.connect(
            self,
            settings.TWITCH_HOST,
            settings.TWITCH_PORT,
            nickname=credentials.twitch["nick"],
            password=credentials.twitch["oauth"],
        )
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
        return chan if chan.startswith("#") else "#" + chan

    def _to_url_chan(self, chan):
        return chan[1:] if chan.startswith("#") else chan

    def _get_channel_id(self, chan):
        """ Gets the numeric channel id of a channel by displayname """
        if not self._channel_id:
            headers = {
                "Accept": "application/vnd.twitchtv.v5+json",
                "Client-ID": credentials.twitch["clientid"],
            }
            r = requests.get(
                "https://api.twitch.tv/kraken/users",
                headers=headers,
                params={"login": chan},
            )
            r.raise_for_status()
            self._channel_id = r.json()["users"][0]["_id"]
        return self._channel_id

    def _get_emote_list(self):
        # Emotes currently causes OOMs due to Twitch's emote list being way too big now
        return []
        logger.info("Fetching emote list")
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": credentials.twitch["clientid"],
        }

        # Pull emote list from twitch
        try:
            r = requests.get(CHAT_ENDPOINT, headers=headers)
            r.raise_for_status()
            r_data = r.json()
        except Exception as e:
            logger.error(
                "Unable to download emoji list for Twitch: {}".format(e)
            )
            return []

        # Parse emotes out of the emote list
        if "emoticons" in r_data:
            logger.info("Downloaded emoticon list successfully.")
            return set([x["code"] for x in r_data["emoticons"]])

        else:
            logger.error("Unable to download emoji list for Twitch!")
            return []

    def _num_emotes(self, s):
        return sum(1 for w in s.split(" ") if w in self._emotes)

    def on_join(self, c, e):
        logger.info("Joined channel: %s" % e.target)

        # Reset exponential backoff on successful join
        self._exponential_backoff = 0

    def get_message_count(self):
        """
        Returns the current number of counted chat messages
        """
        t = self._message_count
        self._message_count = 0
        return t

    def get_emote_count(self):
        """
        Returns the current number of counted chat emotes
        """
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
                self._chats.append(
                    {
                        "user": event.source.split("!")[0],
                        "content": msg,
                        "created_at": datetime.utcnow(),
                    }
                )
            except Exception as e:
                logger.error("Error appending message: {}".format(e))

    def on_disconnect(self, connection, event):
        logger.error("Disconnected from twitch chat. Attempting reconnection")
        self.connect()

    def get_num_viewers(self):
        """ Queries the TwitchAPI for current number of viewers of channel """
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": credentials.twitch["clientid"],
        }
        url = "https://api.twitch.tv/kraken/streams/"
        url += self._get_channel_id(self._to_url_chan(settings.TWITCH_CHANNEL))
        req = requests.get(url, headers=headers)
        data = req.json()
        if "stream" in data and data["stream"]:
            viewers = data["stream"]["viewers"]
            logger.info(
                "Downloaded viewer info. " "Currently viewers: %s" % viewers
            )
            return viewers

        else:
            logger.warn(
                "Unable to get number of viewers. "
                "Possible that stream is offline. "
                "Status code: {}".format(req.status_code)
            )


if __name__ == "__main__":
    t = TwitchClient()
    print(t.get_num_viewers())
