import requests
from bs4 import BeautifulSoup
from collections import namedtuple
import json
from .settings import SCHEDULE_URL
from pprint import pprint
import logging
logger = logging.getLogger(__name__)


ScheduleItem = namedtuple('ScheduleItem', ['title', 'duration', 'runner',
                          'start_time', 'category', 'host'])


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
        page_body = self._get_page()
        table = BeautifulSoup(page_body, 'html.parser').find('tbody')

        first_rows = table.findAll('tr', attrs={'class': None})
        games = list()
        for row in first_rows:
            second_row = row.findNext('tr', attrs={'class': 'second-row'})
            duration, category, host = 0, None, None
            if second_row:
                duration = second_row.find_all('td')[0].text.strip()
                category = second_row.find_all('td')[1].text.strip()
                host = second_row.find_all('td')[2].text.strip()

            runner_text = row.find_all('td', attrs={'class': None})[1]
            runner = runner_text.text.strip() if runner_text else ""

            start_time_text = row.find('td', attrs={'class': "start-time"})
            start_time = start_time_text.text if start_time_text else ""

            title = row.find_all('td', attrs={'class': None})[0].text

            game = ScheduleItem(title=title,
                                duration=duration,
                                runner=runner,
                                start_time=start_time,
                                category=category,
                                host=host)
            games.append(game)

        blacklist = ['pre-show', 'setup block', 'finale']
        games = [x for x in games if
                 not any(x.title.lower().startswith(b.lower())
                         for b in blacklist)]

        logger.info("Successfully scraped schedule")
        return games

    def scrape_to_json(self):
        res = self.scrape()
        return json.dumps([dict(x._asdict()) for x in res])


if __name__ == '__main__':
    pprint(ScheduleClient().scrape())
