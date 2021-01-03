import requests
import re
from bs4 import BeautifulSoup
from collections import namedtuple
from .settings import DONATION_INDEX_URL
import logging

logger = logging.getLogger(__name__)


DonationResult = namedtuple(
    "DonationResult",
    ["total_donations", "total_donators", "max_donation", "avg_donation"],
)
DonationResult.__new__.__defaults__ = (None,) * len(DonationResult._fields)


class DonationClient:
    total_donations_re = re.compile(r"\$(\S+)")
    total_donators_re = re.compile(r"\((\d+)\)")
    max_donation_re = re.compile(r"\$(.+)/\$.+/\$.+")
    avg_donation_re = re.compile(r"\$.+/\$(.+)/\$(.+)")

    def _get_page(self):
        """ Explicit get_page function to allow mocking in tests """
        req = requests.get(DONATION_INDEX_URL)
        req.raise_for_status()
        return req.text

    def scrape(self):
        """
        Scrapes Donation Stats page and returns a namedtuple with current
        results
        """

        soup = BeautifulSoup(self._get_page(), "html.parser")
        totals = soup.find("small").text.strip().split("\n")
        tot_mon = float(
            DonationClient.total_donations_re.search(totals[1]).group(
                1
            ).replace(
                ",", ""
            )
        )
        tot_don = int(
            DonationClient.total_donators_re.search(totals[1]).group(1)
        )
        max_don = float(
            DonationClient.max_donation_re.search(totals[3]).group(1).replace(
                ",", ""
            )
        )
        avg_don = float(
            DonationClient.avg_donation_re.search(totals[3]).group(1).replace(
                ",", ""
            )
        )

        logger.info("Successfully scraped donation page")
        logger.info("Total donations: %s" % tot_mon)
        logger.info("Total donators: %s" % tot_don)

        return DonationResult(
            total_donations=tot_mon,
            total_donators=tot_don,
            max_donation=max_don,
            avg_donation=avg_don,
        )


if __name__ == "__main__":
    print(DonationClient().scrape())
    print(DonationResult())
