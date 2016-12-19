from unittest import TestCase
from agdq_collector.DonationClient import DonationClient


test_url = 'https://gamesdonequick.com/tracker/index/sgdq2016'


class DonationClientTests(TestCase):
    def setUp(self):
        self.client = DonationClient(test_url)

    def test_scrape(self):
        res = self.client.scrape()
        assert res.total_donations == 1294139.50
        assert res.total_donators == 30892
        assert res.max_donation == 52000.00
        assert res.avg_donation == 41.89
