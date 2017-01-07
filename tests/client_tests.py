from unittest import TestCase
from gdq_collector.DonationClient import DonationClient
from gdq_collector.ScheduleClient import ScheduleClient
from gdq_collector.TwitterClient import TwitterClient


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


class TwitterClientTests(TestCase):
    def test_counter(self):
        c = TwitterClient()
        c._increment_tweet_counter()
        assert c.num_tweets() == 1
        assert c.num_tweets() == 0


    def test_needs_auth(self):
        c = TwitterClient()
        with self.assertRaises(RuntimeError):
            c.start()
