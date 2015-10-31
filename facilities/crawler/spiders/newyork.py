import re
import datetime
import scrapy
from crawler.items import FacilityItem
from crawler.utils import e, phone_number_re
from urlparse import urljoin
import usaddress
import logging

class NewYorkSpider(scrapy.Spider):
    name = "newyork"
    allowed_domains = ["www.doccs.ny.gov"]
    start_urls = ["http://www.doccs.ny.gov/faclist.html"]

    def parse(self, response):
        table = response.css("table[summary='Listing of Correctional Facilities']")[0]
        for tr in table.css("tbody tr"):
            address_cell = e(tr.css("td")[0].xpath(".//text()"))
            raw_lines = [a.strip() for a in address_cell.split("\n")]
            lines = []
            line_start = ""
            for line in raw_lines:
                # Join some lines that get split in a way that breaks us.
                if line == "(Inmate Mail:":
                    line_start = line
                    continue
                if line_start:
                    line = line_start + " " + line
                    line_start = ""

                # Special case: split out an "Annex" address into 2 items
                if line:
                    if "Annex" in line:
                        yield self.make_item(lines, response.url)
                        lines = []
                    lines.append(line)
            yield self.make_item(lines, response.url)

    def make_item(self, lines, url):
        # separate organization name
        organization = lines.pop(0)

        # separate phone number
        phone = None
        for i in range(len(lines)):
            match = re.match("^(\(\d{3}\)\s\d{3}-\d{4})\s\([\w\.\s]+\)$", lines[i])
            if match:
                lines.pop(i)
                phone = match.group(1)
                phone = re.sub("^\(", "", phone)
                phone = re.sub("\)\s+", "-", phone)
                break

        # Split addenda that qualify mailing address
        is_mailing_line = lambda line: "Mailing Address" in line or "Inmate Mail" in line

        orig_address_lines = []
        mailing_lines = []
        for line in lines:
            if is_mailing_line(line):
                line = re.sub("^\(Inmate Mail: ", "", line)
                line = re.sub("^\(Mailing Address: ", "", line)
                line = re.sub("\)$", "", line)
                line = re.sub("Zip\s+", "", line)
                mailing_lines.append(line)
            else:
                orig_address_lines.append(line)

        address_parts, t = usaddress.tag(", ".join(orig_address_lines))
        mailing_addenda, t = usaddress.tag(", ".join(mailing_lines))

        # Reconstruct address1 and address2 lines from usaddress tagged parts
        address = []
        line = []
        for key in address_parts:
            if key == "USPSBoxType":
                # newline
                if line:
                    address.append(" ".join(line))
                    line = []
            if key == "PlaceName":
                # Finish
                address.append(" ".join(line))
                break
            if key in mailing_addenda:
                line.append(mailing_addenda[key])
            else:
                line.append(address_parts[key])

        line = []
        for key in mailing_addenda:
            if key not in address_parts:
                line.append(mailing_addenda[key])
        address.append(" ".join(line))

        item = FacilityItem()
        item['source'] = 'crawler'
        item['identifier'] = ''
        item['url'] = url
        item['date'] = datetime.datetime.utcnow().isoformat()
        item['organization'] = organization
        item['phone'] = phone
        item['address1'] = address[0]
        if len(address) > 1:
            item['address2'] = address[1]
        item['city'] = mailing_addenda.get("PlaceName", None) or address_parts['PlaceName']
        item['state'] = mailing_addenda.get("StateName", None) or address_parts['StateName']
        item['zip'] = mailing_addenda.get("ZipCode", None) or address_parts['ZipCode']
        item['administrator'] = "New York"
        item['operator'] = "New York State Department of Corrections and Community Supervision"

        return item
