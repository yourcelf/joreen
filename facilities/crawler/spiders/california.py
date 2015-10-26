# -*- coding: utf-8 -*-


"""
NOTE: California's data consistency is positively *abysmal*.  There is so much
variation and interpretation needed in identifying the addresses for their
facilities that I determined it was easier to manually do data entry on them
rather than trying to actually scrape addresses.

So instead, this crawler simply does some poor-man's *verification*: it makes
sure that the address strings found in the manual spreadsheet are found in the
source pages that they assert.  It then packages and returns the items in the
expected format.
"""

import os
import re
import csv
import scrapy
from crawler.items import FacilityItem
from crawler.utils import e

MANUAL_DATA = os.path.join(os.path.dirname(__file__), "..", "manual", "california.csv")

class AddressCheckException(Exception):
    pass

class CaliforniaSpider(scrapy.Spider):
    name = "california"
    contact_address_page = "http://www.cdcr.ca.gov/Reports_Research/howtocontact.html"
    allowed_domains = ["www.cdcr.ca.gov"]
    download_delay = 5

    def start_requests(self):
        """
        Override default calling of `start_urls` to instead fetch pages from
        the manual spreadsheet.
        """

        data = []
        with open(MANUAL_DATA) as fh:
            reader = csv.reader(fh)
            for i,row in enumerate(reader):
                if i == 0:
                    columns = row
                else:
                    data.append(dict(zip(columns, row)))

        requests = []
        for entry in data:
            req = scrapy.Request(entry['url'], callback=self.parse)
            req.meta['entry'] = entry
            requests.append(req)
        return requests

    def check_address(self, entry, content, url):
        checks = []
        checks.append(r"\b{}\b".format(re.escape(entry['organization'])))
        po_box = lambda p: re.escape(p).replace("PO Box ", "P\.?O\.?\s+B[Oo][Xx]\s+")
        checks.append(r"\b{}\b".format(po_box(entry['address1'])))
        checks.append(r"\b{}\b".format(po_box(entry['address2'])))
        checks.append(r"\b{}\b".format(re.escape(entry['city'])))
        checks.append(r"\b{}\b".format(re.escape(entry['zip'])))

        for check in checks:
            if not re.search(check, content):
                raise AddressCheckException("Check {} failed for {}".format(check, url))
    def parse(self, response):
        # The most likely data entry errors are:
        # 1. Mistyped numbers
        # 2. Eye slips -- grabbing the PO Box for one entry and putting it on
        #    another.
        #
        # As a minimum check, which doesn't perfectly capture those, just make
        # sure that the strings in the address are present in the page.  Highly
        # imperfect.

        entry = response.meta['entry']
        try:
            self.check_address(entry, response.body, response.url)
        except AddressCheckException:
            req = scrapy.Request(self.contact_address_page, callback=self.parse)
            req.meta['entry'] = entry
            yield req

        item = FacilityItem()
        for key in ('source', 'url', 'date', 'identifier', 'organization',
                    'address1', 'address2', 'city', 'state', 'zip', 'phone',
                    'operator', 'administrator', 'type'):
            item[key] = entry[key]
        item['alternate_names'] = entry['alternate_names'].split(", ")
        item['general'] = bool(entry['general'])
        yield item

        
