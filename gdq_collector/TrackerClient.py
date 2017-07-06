import requests
import re
from bs4 import BeautifulSoup
from time import sleep
from dateutil.parser import parse
import logging
logger = logging.getLogger(__name__)


class TrackerClient:
    mon_re = re.compile(r'\$(\S+)')
    don_re = re.compile(r'\((\d+)\)')
    max_re = re.compile(r'\$(.+)/')
    avg_re = re.compile(r'/\$(.+)')

    def __init__(self, donation_url):
        self.url = donation_url

    def _get_donation_page(self, page_num):
        ''' Explicit get_page function to allow mocking in tests '''
        return requests.get(self.url + '?page={}'.format(page_num)).text

    def _get_donation(self, donation_id):
        return requests.get('https://gamesdonequick.com/tracker/donation/{}'.format(donation_id)).text

    def _determine_page_num(self, soup):
        page_num = soup.find('form').find_all('label')[1].text.split(' ')[-1]
        return int(page_num)

    def _scrape_page(self, soup):
        results = []
        for row in soup.find_all('tr')[1:]:
            name_el, time_el, amount_el, comment_el = row.find_all('td')

            donor = None
            if name_el.find('a', href=True):
                donor = name_el.find('a', href=True)['href'].split('/')[3]

            time = parse(time_el.text)

            amount = amount_el.text.replace(',', '').split('$')[1].strip()

            donation_id = None
            if amount_el.find('a'):
                donation_id = int(amount_el.find('a')['href'].split('/')[-1])

            has_comment = comment_el.text.strip() == 'Yes'
            results.append((donor,
                            time,
                            amount,
                            donation_id,
                            has_comment))
        return results

    def scrape(self):
        initial_page = self._get_donation_page(10000)
        soup = BeautifulSoup(initial_page, "html.parser")
        max_page = self._determine_page_num(soup)
        for page_num in range(1, -1, -1):
            page_data = self._get_donation_page(page_num)
            soup = BeautifulSoup(page_data, "html.parser")

            page_results = self._scrape_page(soup)
            for result in reversed(page_results):
                yield result
            logger.info("Scraped page: %s" % page_num)
            sleep(1)

    def scrape_donation_message(self, donation_id):
        page = self._get_donation(donation_id)
        soup = BeautifulSoup(page, "html.parser")
        return soup.find('td').text.strip()


if __name__ == '__main__':
    print list(TrackerClient('https://gamesdonequick.com/tracker/donations/sgdq2017').scrape())
    # print TrackerClient('https://gamesdonequick.com/tracker/donation/').scrape_donation_message(358572)
