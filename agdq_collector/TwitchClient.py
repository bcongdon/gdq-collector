import credentials
import settings
import irc.client
import requests
import logging
logger = logging.getLogger(__name__)


class TwitchClient(irc.client.SimpleIRCClient):
    def __init__(self):
        self._message_count = 0
        self._emote_count = 0
        self._channel_id = None
        irc.client.SimpleIRCClient.__init__(self)
        self.connect(settings.twitch_host, settings.twitch_port,
                     nickname=credentials.twitch['nick'],
                     password=credentials.twitch['oauth'])
        self.connection.join(self._to_irc_chan(settings.twitch_channel))

    def _to_irc_chan(self, chan):
        return chan if chan.startswith('#') else '#' + chan

    def _to_url_chan(self, chan):
        return chan[1:] if chan.startswith('#') else chan

    def on_join(self, c, e):
        logger.info("Connected to %s" % e.target)

    def get_message_count(self):
        t = self._message_count
        self._message_count = 0
        return t

    def on_pubmsg(self, connection, event):
        logger.debug(event.arguments[0])
        print event
        self._message_count += 1

    def on_disconnect(self, connection, event):
        # TODO: Setup reconnection
        pass

    def _get_channel_id(self, chan):
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

    def get_num_viewers(self):
        headers = {
            "Accept": "application/vnd.twitchtv.v5+json",
            "Client-ID": credentials.twitch['clientid'],
        }
        url = "https://api.twitch.tv/kraken/streams/"
        url += self._get_channel_id(self._to_url_chan(settings.twitch_channel))
        req = requests.get(url, headers=headers)
        res = req.json()
        if 'stream' in res:
            return res['stream']['viewers']


if __name__ == '__main__':
    t = TwitchClient()
    print t.get_num_viewers()
