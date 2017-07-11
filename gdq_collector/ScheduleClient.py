import requests
from bs4 import BeautifulSoup
from collections import namedtuple
import json
from settings import SCHEDULE_URL
import logging
logger = logging.getLogger(__name__)


ScheduleItem = namedtuple('ScheduleItem', ['title', 'duration', 'runner',
                          'start_time'])


class ScheduleClient:
    def __init__(self):
        self.url = SCHEDULE_URL

    def _get_page(self):
        try:
            return requests.get(self.url).text
        except Exception as e:
            logger.error("Unable to get Schedule page."
                         "Error: %s" % str(e))

    def scrape(self):
        table = BeautifulSoup(self._get_page(), 'html.parser').find('tbody')

        first_rows = table.findAll('tr', attrs={'class': None})
        games = list()
        for row in first_rows:
            second_row = row.findNext('tr', attrs={'class': 'second-row'})
            duration = 0
            if second_row:
                duration = second_row.findNext('td').text.strip()
            runner_text = row.find('td', attrs={'rowspan': 2})
            runner = runner_text.text.strip() if runner_text else ""
            start_time_text = row.find('td', attrs={'class': "start-time"})
            start_time = start_time_text.text if start_time_text else ""
            game = {
                'title': row.find('td', attrs={'class': None}).text,
                'duration': duration,
                'runner': runner,
                'start_time': start_time,
            }
            games.append(game)
        blacklist = ['Pre-Show', 'Setup Block', 'Finale']
        games = [x for x in games if
                 not any(x['title'].lower().startswith(b.lower())
                         for b in blacklist)]

        logger.info("Successfully scraped schedule")

        return [ScheduleItem(title=x['title'],
                             duration=x['duration'],
                             runner=x['runner'],
                             start_time=x['start_time']) for x in games]

    def scrape_to_json(self):
        res = self.scrape()
        return json.dumps([dict(x._asdict()) for x in res])
