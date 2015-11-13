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
import logging
from crawler.items import FacilityItem
from crawler.utils import e
from collections import defaultdict

MANUAL_DATA = os.path.join(os.path.dirname(__file__), "..", "manual", "california.csv")

class AddressCheckException(Exception):
    pass

class CaliforniaSpider(scrapy.Spider):
    name = "california"
    contact_address_page = "http://www.cdcr.ca.gov/Reports_Research/howtocontact.html"
    allowed_domains = ["www.cdcr.ca.gov"]
    download_delay = 5

    errors = []

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

        requests_by_url = defaultdict(list)
        for entry in data:
            requests_by_url[entry['url']].append(entry)

        requests = []
        for url, entries in requests_by_url.iteritems():
            req = scrapy.Request(url, callback=self.parse)
            req.meta['entries'] = entries
            requests.append(req)
        return requests

    def check_address(self, entry, content, url, skip=None):
        skip = skip or []

        # Special cases
        content_hacks = {
          "&amp;": "&",
          "Facility 'M'": "Facility M"
        }
        if url == "http://www.cdcr.ca.gov/Facilities_Locator/Community_Correctional_Facilities.html":
            content_hacks['Female Community Reentry Facility'] = 'McFarland Female Community Reentry Facility'
        if url == "http://www.cdcr.ca.gov/Facilities_Locator/ASP-location.html":
            content_hacks['Facility A -901'] = "Facility A, PO Box 901"
            content_hacks['Facility B -902'] = "Facility B, PO Box 902"
            content_hacks['Facility C -903'] = "Facility C, PO Box 903"
            content_hacks['Facility D -904'] = "Facility D, PO Box 904"
            content_hacks['Facility E -905'] = "Facility E, PO Box 905"
            content_hacks['Facility F -906'] = "Facility F, PO Box 906"


        for regex, replacement in content_hacks.iteritems():
            content = re.sub(regex, replacement, content)

        # Regular checks
        esc = lambda p: re.escape(p).replace(r"\ ", r"\s+")
        po_box = lambda p: esc(p).replace("PO\s+Box\s+", r"P\.?O\.?\s+Box\s+")
        checks = {
            'organization': r"{}".format(esc(entry['organization'])),
            'address1': r"{}([^\d]|$)".format(po_box(entry['address1'])),
            'address2': r"{}([^\d]|$)".format(po_box(entry['address2'])),
            'city': r"{}".format(esc(entry['city'])),
            'zip': r"{}".format(esc(entry['zip']))
        }
        passed = {}

        for check, regex in checks.iteritems():
            if check in skip:
                continue
            else:
                passed[check] = bool(re.search(regex, content, re.I))

        format_checks = {
            'zip': r'^\d{5}(-\d{4})?$'
        }
        for check, regex in format_checks.iteritems():
            passed[check + "_format"] = bool(re.search(regex, entry.get(check)))

        return passed

    def parse(self, response):
        # The most likely data entry errors are:
        # 1. Mistyped numbers
        # 2. Eye slips -- grabbing the PO Box for one entry and putting it on
        #    another.
        #
        # As a minimum check, which doesn't perfectly capture those, just make
        # sure that the strings in the address are present in the page.  Highly
        # imperfect.

        entries = response.meta['entries']
        for entry in entries:
            checks = entry.get('checks', {})
            if not checks or not all(checks.values()):
                skip = [c for c,v in checks.iteritems() if v]
                checks = self.check_address(entry, response.body, response.url, skip)

            if not all(checks.values()):
                if response.url == self.contact_address_page:
                    raise AddressCheckException("Address checks failed: {}, {}, {}".format(
                        entry['url'], entry['organization'], [entry[c] for c,v in checks.iteritems() if not v]
                    ))

                # Try the contact address page to check remaining problems.
                entry['checks'] = checks
                req = scrapy.Request(url=self.contact_address_page,
                        callback=self.parse, dont_filter=True)
                req.meta['entries'] = [entry]
                yield req
                continue

            item = FacilityItem()
            for key in ('source', 'url', 'date', 'identifier', 'organization',
                        'address1', 'address2', 'city', 'state', 'zip', 'phone',
                        'operator', 'administrator', 'type'):
                item[key] = entry[key]
            item['alternate_names'] = entry['alternate_names'].split(", ")
            item['general'] = bool(entry['general'])
            yield item

        
