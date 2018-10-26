# -*- coding: utf-8 -*-
import re
import datetime
import scrapy
from crawler.items import FacilityItem
from crawler.utils import e, phone_number_re
import usaddress

alternate_names = {
    "ADAPPT Treatment Services": ["ADAPPT TREATMENT SERVICE"],
    "Pittsburgh CCC": ["PITTSBURGH CCC #3"],
    "Transitional Living Center": ["TRANSITIONAL LIVING CTR"],
}

# Update 2018-10-23: PA uses a central mail processing facility in Florida,
# scans mail, and sends emails to the recipients.  Info:
#
# https://www.cor.pa.gov/family-and-friends/Pages/Mailing-Addresses.aspx
#
# Basic template:
#
# Smart Communications/PADOC
# Inmate Name/Inmate Number
# Institution
# PO Box 33028
# St Petersburg, FL 33733
#
# FIXME: The scraper now needs a rewrite.  The SCI addresses were updated live
# in the db to reflect the new Florida aggregate address.  All the URLs in here
# are busted.


class PennsylvaniaSpider(scrapy.Spider):
    name = "pennsylvania"

    county_facilities = "https://www.cor.pa.gov/Facilities/CountyPrisons/Documents/Pennsylvania%20County%20Correctional%20Facility%20Address%20and%20Contact%20Listing.xlsx"

    doc_urls = [
        "http://www.cor.pa.gov/Administration/ContactUsHotlinesandRight-To-Know/Pages/Mailing-Addresses.aspx#.VeWt2qTD99A"
    ]
    ccc_urls = [
        "http://www.cor.pa.gov/Facilities/CommunityCorrections/Pages/Region-I-Facilities.aspx",
        "http://www.cor.pa.gov/Facilities/CommunityCorrections/Pages/Region-II-Facilities.aspx",
        "http://www.cor.pa.gov/Facilities/CommunityCorrections/Pages/Region-III-Facilities.aspx"
    ]

    def start_requests(self):
        raise Exception(
            "Scraper needs to be rewritten; all URLs are busted, and PA's "
            "addressing scheme (at least for SCI's if not others) has changed."
        )

        return [
            scrapy.Request(url, callback=self.parse_doc) for url in self.doc_urls
        ] + [
            scrapy.Request(url, callback=self.parse_ccc) for url in self.ccc_urls
        ]

    
    def get_alternate_names(self, name):
        alts = alternate_names.get(name, [])
        if re.match("^SCI .*$", name):
            alts.append(re.sub("^SCI ", "", name))
        return alts
    
    def parse_doc(self, response):
        lines = e(response.css("div.content-container").xpath('.//text()')).split("\n")
        lines = [l.strip() for l in lines]

        # chunk addresses
        in_addresses = False
        address = []
        for line in lines:
            if line == "DOC Facility Mailing Addresses:":
                in_addresses = True
                continue
            if in_addresses and line:
                address.append(line)
                if re.match("^\(\d{3}\)\s+\d{3}-\d{4}$", line):
                    yield self.make_doc_item(address, response.url)
                    address = []

    def parse_ccc(self, response):
        response = response.replace(
            body=response.body.replace("<br />", "\n")
        )

        lines = e(response.css("div.content-container").xpath('.//text()')).split("\n")
        lines = [l.strip() for l in lines if l]
        lines = [l for l in lines if l]

        # chunk addresses
        skip_lines = [
            "^\(DOC-operated facilities\)$",
            "^Contract Facilities$",
            "^\(Administrative Staff:",
            "^Fax ",
        ]
        preamble = True
        address = []
        for line in lines:
            if line == "Community Corrections Centers":
                preamble = False
                continue
            if preamble or any(map(lambda p: re.search(p, line), skip_lines)):
                continue
            if line.startswith("Gender Specific"):
                yield self.make_ccc_item(address, response.url)
                address = []
                continue
            # Special case: skip a bunch of phone number junk in Region II Facilities
            if line == "York CCC" and address[0] == "Wernersville CCC Building #18":
                address = []

            # Omit county parentheticals from 'City (County) PA, ZIP' line
            line = re.sub("\s\(.*\)(?=,\s*PA\s*\d{5})", "", line)
            line = line.replace(" (Please do NOT put this address in your GPS, instead use the directions provided below.)", "")
            address.append(line)

    def make_ccc_item(self, lines, url):
        item = FacilityItem()
        item['identifier'] = ''
        item['source'] = 'crawler'
        item['administrator'] = "Pennsylvania"
        item['url'] = url
        item['date'] = datetime.datetime.now().isoformat()
        # Eliminate the parenthetical suffix from names
        item['organization'] = re.sub("\s?\(.*\)$", "", lines.pop(0))
        item['organization'] = item['organization'].replace(u"’", "'")
        #print item['organization'], lines
        match = re.match("^Telephone(?:[^:]*):\s+\((\d{3})\)\s+(\d{3})-(\d{4}).*$", lines[-1])
        if match:
            lines.pop(-1)
            item['phone'] = "-".join(
                    (match.group(1), match.group(2), match.group(3))
            )
        item = self.parse_address(item, lines)
        return item

    def make_doc_item(self, lines, url):
        item = FacilityItem()
        item['source'] = "crawler"
        item['administrator'] = 'Pennsylvania'
        item['identifier'] = ''
        item['url'] = url
        item['date'] = datetime.datetime.now().isoformat()
        item['organization'] = lines.pop(0)
        superintendent = lines.pop(0)
        phone = lines.pop(-1)
        phone = re.sub("^\(", "", phone)
        phone = re.sub("\)\s+", "-", phone)
        item['phone'] = phone
        item = self.parse_address(item, lines)
        return item

    def parse_address(self, item, lines):
        joined = ", ".join(lines)
        parts, t = usaddress.tag(", ".join(lines))

        item['address1'] = " ".join([v for k,v in parts.iteritems() if k not in (
            "USPSBoxType", "USPSBoxID", "PlaceName", "StateName", "ZipCode"
        )])
        item['address2'] = " ".join([v for k,v in parts.iteritems() if k in (
            "USPSBoxType", "USPSBoxID"
        )])
        item['city'] = parts['PlaceName']
        item['state'] = parts['StateName']
        item['zip'] = parts['ZipCode']
        # Special case: fix a duplicated zip+4 extension
        item['zip'] = item['zip'].replace("-5961-5961", "-5961")
        item['alternate_names'] = self.get_alternate_names(item['organization'])
        return item


    def print_item(self, item):
        print
        print item['organization']
        print item['address1']
        if item['address2']:
            print item['address2']
        print "{}, {}  {}".format(item['city'], item['state'], item['zip'])
        print item.get('phone')



