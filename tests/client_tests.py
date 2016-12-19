from unittest import TestCase
from agdq_collector.DonationClient import DonationClient
from agdq_collector.ScheduleClient import ScheduleClient


class DonationClientTests(TestCase):
    def setUp(self):
        self.client = DonationClient('')
        with open('tests/data/sgdq_donations_index.html', 'r') as f:
            dat = f.read()
            self.client._get_page = lambda: dat

    def test_scrape(self):
        res = self.client.scrape()
        assert type(res)
        assert res.total_donations == 1294139.50
        assert res.total_donators == 30892
        assert res.max_donation == 52000.00
        assert res.avg_donation == 41.89


class ScheduleClientTests(TestCase):
    def setUp(self):
        self.client = ScheduleClient('')
        with open('tests/data/agdq_schedule.html', 'r') as f:
            dat = f.read()
            self.client._get_page = lambda: dat

    def test_scrape(self):
        assert self.client.scrape()
        json_res = self.client.scrape_to_json()
        with open('tests/data/agdq_schedule.json', 'r') as f:
            assert json_res == f.read()
