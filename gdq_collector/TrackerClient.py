import requests
from bs4 import BeautifulSoup
from time import sleep
from dateutil.parser import parse
from .settings import DONATION_INDEX_URL, DONATION_DETAIL_URL, DONOR_URL
import logging

logger = logging.getLogger(__name__)


class TrackerClient:

    def _get_donation_page(self, page_num):
        """ Explicit get_page function to allow mocking in tests """
        page_url = "{}?page={}".format(DONATION_INDEX_URL, page_num)
        req = requests.get(page_url)
        req.raise_for_status()
        return req.text

    def _get_donation(self, donation_id):
        donation_url = "{}/{}".format(DONATION_DETAIL_URL, donation_id)
        req = requests.get(donation_url)
        req.raise_for_status()
        return req.text

    def _get_donor(self, donor_id):
        req = requests.get("{}/{}".format(DONOR_URL, donor_id))
        req.raise_for_status()
        return req.text

    def _determine_page_num(self, soup):
        page_num = soup.find("form").find_all("label")[1].text.split(" ")[-1]
        return int(page_num)

    def _scrape_page(self, soup):
        results = []
        for row in soup.find_all("tr")[1:]:
            name_el, time_el, amount_el, comment_el = row.find_all("td")

            donor_id = None
            name = None
            if name_el.find("a", href=True):
                donor_id = name_el.find("a", href=True)["href"].split("/")[3]
                name = name_el.find("a", href=True).text.strip()

            time = parse(time_el.text)

            amount = amount_el.text.replace(",", "").split("$")[1].strip()

            donation_id = None
            if amount_el.find("a"):
                donation_id = int(amount_el.find("a")["href"].split("/")[-1])

            has_comment = comment_el.text.strip() == "Yes"
            results.append((donor_id, time, amount, donation_id, has_comment, name))
        return results

    def scrape(self):
        initial_page = self._get_donation_page(10000)
        soup = BeautifulSoup(initial_page, "html.parser")
        max_page = self._determine_page_num(soup)
        for page_num in range(1, max_page + 1):
            page_data = self._get_donation_page(page_num)
            soup = BeautifulSoup(page_data, "html.parser")

            page_results = self._scrape_page(soup)
            for result in page_results:
                yield result

            logger.info("Scraped page: %s" % page_num)
            sleep(1)

    def scrape_donation_message(self, donation_id):
        page = self._get_donation(donation_id)
        soup = BeautifulSoup(page, "html.parser")
        if soup.find("td"):
            return soup.find("td").text.strip()

    def get_donor_name(self, donor_id):
        page = self._get_donor(donor_id)
        soup = BeautifulSoup(page, "html.parser")
        if soup.find("h2"):
            return soup.find("h2").contents[0].strip()


# if __name__ == '__main__':
#     print(list(TrackerClient().scrape()))  # Danger!
#     print(TrackerClient().get_donor_name(847))
#     print(TrackerClient().scrape_donation_message(358572))
