import requests
import re
from bs4 import BeautifulSoup
from collections import namedtuple
import logging
logger = logging.getLogger(__name__)


DonationResult = namedtuple('DonationResult', ['total_donations',
                            'total_donators', 'max_donation', 'avg_donation'])


class DonationClient:
    mon_re = re.compile(r'\$(\S+)')
    don_re = re.compile(r'\((\d+)\)')
    max_re = re.compile(r'\$(.+)/')
    avg_re = re.compile(r'/\$(.+)')

    def __init__(self, donation_url):
        self.url = donation_url

    def _get_page(self):
        ''' Explicit get_page function to allow mocking in tests '''
        return requests.get(self.url).text

    def scrape(self):
        '''
        Scrapes Donation Stats page and returns a namedtuple with current
        results
        '''

        soup = BeautifulSoup(self._get_page(), "html.parser")
        totals = soup.find('small').text.strip().split('\n')
        tot_mon = float(DonationClient.mon_re.search(
                        totals[1]).group(1).replace(',', ''))
        tot_don = int(DonationClient.don_re.search(
                        totals[1]).group(1))
        max_don = float(DonationClient.max_re.search(
                        totals[3]).group(1).replace(',', ''))
        avg_don = float(DonationClient.avg_re.search(
                        totals[3]).group(1).replace(',', ''))

        logger.info("Successfully scraped donation page")
        logger.info("Total donations: %s" % tot_mon)
        logger.info("Total donators: %s" % tot_don)

        return DonationResult(total_donations=tot_mon,
                              total_donators=tot_don,
                              max_donation=max_don,
                              avg_donation=avg_don)
